from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas.query import NLQueryResponse
import sqlglot
from sqlglot import exp
from typing import Tuple
import logging
import re

logger = logging.getLogger("commerce_api")

# Dimensions and time scopes this router does not break down by. If one appears
# in an aggregate question, the question is refused rather than answered at the
# wrong grain (e.g. "total revenue by customer segment").
_SCOPE_TERMS = (
    "category", "region", "product", "segment", "subcategory", "customer",
    "status", "city", "state", "month", "year", "quarter",
)
_MONTH_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|"
    r"october|november|december)\b",
    re.IGNORECASE,
)


def _has_other_scope(q: str) -> bool:
    return bool(
        _MONTH_RE.search(q)
        or re.search(r"\b20\d{2}\b", q)
        or any(term in q for term in _SCOPE_TERMS)
    )

class QueryService:
    ALLOWED_TABLES = {"orders", "order_items", "customers", "products"}

    @staticmethod
    def sanitize_sql(sql_query: str) -> Tuple[bool, str, str]:
        """
        Uses an Abstract Syntax Tree (AST) parser (sqlglot) to strictly inspect
        the SQL query. Guarantees:
        1. Only SELECT statements are permitted.
        2. Any DROP, DELETE, UPDATE, INSERT, ALTER, or DDL/DML statements are blocked.
        3. Only whitelisted analytical tables can be queried.
        4. Injects LIMIT 100 if none is provided.
        """
        try:
            parsed = sqlglot.parse_one(sql_query, read="sqlite")

            # 1. Enforce root query is strictly a Select
            if not isinstance(parsed, exp.Select):
                return False, "", "Security Violation: Only SELECT queries are permitted."

            # 2. Block any destructive or mutation expressions
            forbidden_types = (
                exp.Drop, exp.Delete, exp.Update, exp.Insert, exp.Alter,
                exp.Create, exp.Command, exp.TruncateTable
            )
            for node in parsed.walk():
                if isinstance(node, forbidden_types):
                    return False, "", f"Security Violation: Mutating operation '{type(node).__name__}' is forbidden."

            # 3. Check table whitelist
            for table in parsed.find_all(exp.Table):
                table_name = table.name.lower()
                if table_name not in QueryService.ALLOWED_TABLES or table.db or table.catalog:
                    return False, "", f"Security Violation: Access to table '{table_name}' is not permitted."

            # 4. Enforce Limit 100
            limit_node = parsed.args.get("limit")
            if not limit_node:
                parsed = parsed.limit(100)
            else:
                value = limit_node.expression
                if not isinstance(value, exp.Literal) or not value.is_int or int(value.this) < 0:
                    return False, "", "Security Violation: LIMIT must be a non-negative integer."
                if int(value.this) > 100:
                    parsed = parsed.limit(100)

            sanitized_sql = parsed.sql(dialect="sqlite")
            return True, sanitized_sql, "Query passed AST security verification."

        except Exception as e:
            return False, "", f"Syntax or parsing error: {str(e)}"

    @staticmethod
    def generate_sql_from_question(question: str) -> Tuple[str, str]:
        """
        Grounded NL-to-SQL logic adhering to the e-commerce semantic layer.

        Answers only questions this deterministic router can ground in the
        relational schema. Anything else returns ("", "") so the endpoint can
        refuse -- never an unrelated query that looks like an answer.
        """
        q = question.lower().strip()

        if "revenue" in q and "category" in q:
            sql = """
            SELECT p.category, ROUND(SUM(oi.line_total), 2) AS category_revenue
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned')
            GROUP BY p.category
            ORDER BY category_revenue DESC
            LIMIT 10;
            """
            exp = "Total revenue grouped by product category for delivered and processing orders."
            return sql.strip(), exp

        elif "top" in q and ("product" in q or "selling" in q):
            sql = """
            SELECT p.product_name, p.category, SUM(oi.quantity) AS units_sold, ROUND(SUM(oi.line_total), 2) AS total_revenue
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned')
            GROUP BY p.product_name, p.category
            ORDER BY total_revenue DESC
            LIMIT 5;
            """
            exp = "Top 5 best-selling products ranked by revenue."
            return sql.strip(), exp

        elif ("average order" in q or "aov" in q) and not _has_other_scope(q):
            sql = """
            SELECT ROUND(SUM(oi.line_total) / COUNT(DISTINCT o.order_id), 2) AS average_order_value
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned');
            """
            exp = "Average Order Value (AOV) across all eligible orders."
            return sql.strip(), exp

        elif "cancel" in q:
            sql = """
            SELECT
                COUNT(*) AS total_orders,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
                ROUND(SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS cancellation_rate_pct
            FROM orders;
            """
            exp = "Order cancellation rate across total orders."
            return sql.strip(), exp

        elif "customer" in q and ("region" in q or "state" in q or "city" in q):
            sql = """
            SELECT region, COUNT(*) AS customer_count
            FROM customers
            GROUP BY region
            ORDER BY customer_count DESC;
            """
            exp = "Customer geographic distribution across regions."
            return sql.strip(), exp

        elif "margin" in q and "category" in q:
            sql = """
            SELECT p.category,
                   ROUND(100.0 * SUM(oi.line_total - oi.cost_total) / SUM(oi.line_total), 1) AS margin_pct
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned')
            GROUP BY p.category
            ORDER BY margin_pct DESC;
            """
            exp = "Gross margin by product category for delivered and processing orders."
            return sql.strip(), exp

        elif "region" in q and ("revenue" in q or "sales" in q or "profit" in q):
            sql = """
            SELECT c.region, ROUND(SUM(oi.line_total), 2) AS region_revenue
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned')
            GROUP BY c.region
            ORDER BY region_revenue DESC;
            """
            exp = "Revenue by customer region for delivered and processing orders."
            return sql.strip(), exp

        elif ("revenue" in q or "sales" in q or "turnover" in q) and not _has_other_scope(q):
            sql = """
            SELECT ROUND(SUM(oi.line_total), 2) AS total_revenue
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned');
            """
            exp = "Total revenue across delivered and processing orders."
            return sql.strip(), exp

        elif "profit" in q and not _has_other_scope(q):
            sql = """
            SELECT ROUND(SUM(oi.line_total - oi.cost_total), 2) AS total_profit
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned');
            """
            exp = "Total gross profit across delivered and processing orders."
            return sql.strip(), exp

        elif "margin" in q and not _has_other_scope(q):
            sql = """
            SELECT ROUND(100.0 * SUM(oi.line_total - oi.cost_total) / SUM(oi.line_total), 2) AS margin_pct
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned');
            """
            exp = "Overall gross margin across delivered and processing orders."
            return sql.strip(), exp

        elif "customer" in q and ("how many" in q or "how big" in q or "customer base" in q) \
                and not any(t in q for t in ("region", "state", "city", "segment", "category")):
            sql = """
            SELECT COUNT(DISTINCT o.customer_id) AS total_customers
            FROM orders o
            WHERE o.status NOT IN ('Cancelled', 'Returned');
            """
            exp = "Customers with at least one delivered or processing order."
            return sql.strip(), exp

        elif "order" in q and ("how many" in q or "total" in q) and not _has_other_scope(q):
            sql = """
            SELECT COUNT(DISTINCT o.order_id) AS total_orders
            FROM orders o
            WHERE o.status NOT IN ('Cancelled', 'Returned');
            """
            exp = "Orders that are delivered or processing (excludes cancelled and returned)."
            return sql.strip(), exp

        elif "status" in q and ("order" in q or "distribution" in q):
            sql = """
            SELECT status, COUNT(*) AS order_count
            FROM orders
            GROUP BY status
            ORDER BY order_count DESC;
            """
            exp = "Distribution of orders by operational status."
            return sql.strip(), exp

        # No grounded query: refuse instead of answering a different question.
        return "", ""

    @staticmethod
    async def process_natural_language_query(db: AsyncSession, question: str) -> NLQueryResponse:
        sql, explanation = QueryService.generate_sql_from_question(question)

        if not sql:
            return NLQueryResponse(
                question=question,
                generated_sql="",
                is_safe=True,
                row_count=0,
                data=[],
                explanation=(
                    "Refused: this question is outside the supported NL-to-SQL scope. "
                    "No SQL was generated or executed. Supported: revenue/profit/margin "
                    "totals and category/region breakdowns, top products, AOV, order and "
                    "customer counts, cancellations, and order-status distribution."
                ),
            )

        is_safe, sanitized_sql, reason = QueryService.sanitize_sql(sql)

        if not is_safe:
            return NLQueryResponse(
                question=question,
                generated_sql=sql,
                is_safe=False,
                row_count=0,
                data=[],
                explanation=reason
            )

        try:
            result = await db.execute(text(sanitized_sql))
            rows = [dict(row) for row in result.mappings().all()]
            return NLQueryResponse(
                question=question,
                generated_sql=sanitized_sql,
                is_safe=True,
                row_count=len(rows),
                data=rows,
                explanation=explanation
            )
        except Exception as e:
            return NLQueryResponse(
                question=question,
                generated_sql=sanitized_sql,
                is_safe=False,
                row_count=0,
                data=[],
                explanation=f"Execution error: {str(e)}"
            )
