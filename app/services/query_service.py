from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas.query import NLQueryResponse
import sqlglot
from sqlglot import exp
from typing import Tuple
import logging

logger = logging.getLogger("commerce_api")

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
                if table_name not in QueryService.ALLOWED_TABLES:
                    return False, "", f"Security Violation: Access to table '{table_name}' is not permitted."

            # 4. Enforce Limit 100
            limit_node = parsed.args.get("limit")
            if not limit_node:
                parsed = parsed.limit(100)

            sanitized_sql = parsed.sql(dialect="sqlite")
            return True, sanitized_sql, "Query passed AST security verification."

        except Exception as e:
            return False, "", f"Syntax or parsing error: {str(e)}"

    @staticmethod
    def generate_sql_from_question(question: str) -> Tuple[str, str]:
        """
        Grounded NL-to-SQL logic adhering to the e-commerce semantic layer.
        Maps common leadership questions into validated analytical queries.
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

        elif "average order" in q or "aov" in q:
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

        else:
            # Fallback safe query
            sql = """
            SELECT status, COUNT(*) AS order_count
            FROM orders
            GROUP BY status
            ORDER BY order_count DESC;
            """
            exp = "Distribution of orders by operational status."
            return sql.strip(), exp

    @staticmethod
    async def process_natural_language_query(db: AsyncSession, question: str) -> NLQueryResponse:
        sql, explanation = QueryService.generate_sql_from_question(question)
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
