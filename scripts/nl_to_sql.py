"""
nl_to_sql.py — natural-language business questions answered from the data
================================================================================
AI Business Analytics layer: converts natural-language questions into SQL,
executes them, and returns results with explanations.

GUARDRAILS:
    - The LLM generates SQL; the SQL executes against the real data
    - Every number in the answer comes from the query result
    - If the SQL fails or returns no data, the system says so — never guesses
    - The LLM explains results; it never computes them

Architecture:
    User question
    → LLM generates SQL (using schema as context)
    → SQL validated (read-only, no DROP/DELETE/UPDATE)
    → SQL executed against SQLite/PostgreSQL
    → Result returned
    → LLM explains the result (grounded in the actual output)

Run:  python scripts/nl_to_sql.py
"""
import os
import re
import sqlite3
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "master_orders.csv"

# ── Schema context for the LLM ──
SCHEMA = """
Table: orders (denormalized from 4 source tables — customers, products, orders, order_items)
Grain: 1 row = 1 order line item

Key columns:
- order_date (date): when the order was placed (2022-01 to 2024-12)
- line_total (real): revenue for this line item
- profit (real): line_total - cost_total
- quantity (int): units sold
- category (text): Electronics, Clothing, Home & Garden, Sports, Beauty
- region (text): North, South, East, West, Central
- customer_id (text): CUST00001 format, 2000 customers
- product_name (text): product name
- status (text): Delivered, Processing (revenue orders only in this table)
- year (int), month (int): derived from order_date
- discount_pct (real): 0, 0.05, 0.10, 0.15, 0.20

Business rules:
- Revenue = SUM(line_total)
- Profit = SUM(profit)
- Margin % = SUM(profit) / SUM(line_total) * 100
- AOV = SUM(line_total) / COUNT(DISTINCT order_id)
- All queries should filter valid orders only (this table is already filtered)

SQLite notes:
- Use standard SQL (SELECT, GROUP BY, ORDER BY, etc.)
- Column names are case-sensitive as listed above
- Use single quotes for string literals
"""

SYSTEM_PROMPT = f"""You are a business analytics assistant for an e-commerce company.
Convert the user's natural-language question into a SQLite query.

{SCHEMA}

RULES:
1. Generate ONLY a SQLite-compatible SELECT query. No INSERT, UPDATE, DELETE, DROP, or ALTER.
2. Every number in your answer must come from the query result — never calculate or invent figures.
3. If the query returns no rows, say "No data found for that question."
4. Format numbers appropriately (e.g., ₹5.93 Cr, 54.0%, 1,991).
5. Keep answers concise and business-focused.
6. Respond in JSON: {{"sql": "SELECT ...", "explanation": "brief what this query does"}}

Example:
User: "What is total revenue?"
Response: {{"sql": "SELECT ROUND(SUM(line_total), 2) as total_revenue FROM orders", "explanation": "Total revenue across all orders"}}

Example:
User: "Which category has the highest margin?"
Response: {{"sql": "SELECT category, ROUND(SUM(profit)/SUM(line_total)*100, 1) as margin_pct FROM orders GROUP BY category ORDER BY margin_pct DESC LIMIT 1", "explanation": "Category with highest profit margin percentage"}}"""

# ── SQL safety validation ──
FORBIDDEN = re.compile(
    r'\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|TRUNCATE|ATTACH|DETACH)\b',
    re.IGNORECASE
)

def validate_sql(sql: str) -> tuple[bool, str]:
    """Ensure the SQL is a read-only SELECT query."""
    sql_clean = sql.strip().rstrip(';')
    if not sql_clean.upper().startswith('SELECT') and not sql_clean.upper().startswith('WITH'):
        return False, "Only SELECT or WITH queries are allowed."
    if FORBIDDEN.search(sql_clean):
        return False, "Destructive SQL operations are not permitted."
    return True, sql_clean


def execute_sql(sql: str) -> pd.DataFrame:
    """Execute SQL against the master orders data."""
    df = pd.read_csv(DATA)
    conn = sqlite3.connect(":memory:")
    df.to_sql("orders", conn, index=False, dtype={"order_date": "TEXT"})
    try:
        result = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return result


def answer_question(question: str, use_llm: bool = True) -> dict:
    """Full pipeline: question → SQL → result → explanation."""
    # Try LLM for SQL generation
    if use_llm and os.environ.get("OPENAI_API_KEY"):
        sql, llm_note = _generate_sql_openai(question)
    elif use_llm and os.environ.get("GOOGLE_API_KEY"):
        sql, llm_note = _generate_sql_gemini(question)
    else:
        sql, llm_note = _fallback_sql(question), "No LLM key — using pattern-matching fallback"

    if not sql:
        return {"ok": False, "error": "Could not generate SQL for that question.",
                "note": llm_note}

    valid, msg = validate_sql(sql)
    if not valid:
        return {"ok": False, "error": f"SQL validation failed: {msg}", "sql": sql}

    try:
        result = execute_sql(sql)
    except Exception as e:
        return {"ok": False, "error": f"SQL execution failed: {str(e)}",
                "sql": sql, "note": llm_note}

    if result.empty:
        return {"ok": True, "sql": sql, "result": None,
                "answer": "No data found for that question.", "note": llm_note}

    # Format the result
    result_str = result.to_string(index=False)

    # LLM explanation (if available)
    explanation = None
    if os.environ.get("OPENAI_API_KEY"):
        explanation = _explain_openai(question, result_str)
    elif os.environ.get("GOOGLE_API_KEY"):
        explanation = _explain_gemini(question, result_str)

    return {
        "ok": True, "sql": sql, "result": result.to_dict(orient="records"),
        "result_str": result_str, "answer": explanation or result_str,
        "note": llm_note,
    }


def _generate_sql_openai(question: str) -> tuple[str, str]:
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=os.environ.get("SQL_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(resp.choices[0].message.content)
        return parsed.get("sql", ""), "OpenAI"
    except Exception:
        return _fallback_sql(question), "OpenAI failed — using fallback"


def _generate_sql_gemini(question: str) -> tuple[str, str]:
    try:
        import google.genai as genai
        client = genai.Client()
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{SYSTEM_PROMPT}\n\nUser question: {question}"
        )
        # try to parse JSON from response
        text = resp.text
        match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return parsed.get("sql", ""), "Gemini"
        return "", "Gemini response parsing failed"
    except Exception:
        return _fallback_sql(question), "Gemini failed — using fallback"


def _explain_openai(question, result_str):
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content":
                    "You are a business analyst. Explain the query result in 2-3 sentences. "
                    "Use ONLY the numbers in the result — never invent or calculate figures. "
                    "Format large numbers appropriately (₹5.93 Cr, 54.0%)."},
                {"role": "user", "content": f"Question: {question}\n\nResult:\n{result_str}"}
            ],
            temperature=0.1,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


def _explain_gemini(question, result_str):
    try:
        import google.genai as genai
        client = genai.Client()
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"You are a business analyst. Explain this result in 2-3 sentences. "
                     f"Use ONLY the numbers shown. Question: {question}\nResult:\n{result_str}"
        )
        return resp.text
    except Exception:
        return None


def _fallback_sql(question: str) -> str:
    """Pattern-matching fallback when no LLM is available."""
    q = question.lower()
    if "total revenue" in q or "total sales" in q:
        return "SELECT ROUND(SUM(line_total), 2) as total_revenue FROM orders"
    if "total profit" in q:
        return "SELECT ROUND(SUM(profit), 2) as total_profit FROM orders"
    if "total orders" in q:
        return "SELECT COUNT(DISTINCT order_id) as total_orders FROM orders"
    if "customers" in q and ("how many" in q or "total" in q):
        return "SELECT COUNT(DISTINCT customer_id) as total_customers FROM orders"
    if "average order value" in q or "aov" in q:
        return "SELECT ROUND(SUM(line_total)/COUNT(DISTINCT order_id), 2) as aov FROM orders"
    if "margin" in q and "category" in q:
        return ("SELECT category, ROUND(SUM(profit)/SUM(line_total)*100, 1) as margin_pct "
                "FROM orders GROUP BY category ORDER BY margin_pct DESC")
    if "revenue by category" in q or "category revenue" in q:
        return ("SELECT category, ROUND(SUM(line_total), 2) as revenue "
                "FROM orders GROUP BY category ORDER BY revenue DESC")
    if "top" in q and "product" in q:
        return ("SELECT product_name, ROUND(SUM(line_total), 2) as revenue "
                "FROM orders GROUP BY product_name ORDER BY revenue DESC LIMIT 10")
    if "region" in q:
        return ("SELECT region, ROUND(SUM(line_total), 2) as revenue "
                "FROM orders GROUP BY region ORDER BY revenue DESC")
    if "monthly" in q or "trend" in q or "by month" in q:
        return ("SELECT year, month, ROUND(SUM(line_total), 2) as revenue "
                "FROM orders GROUP BY year, month ORDER BY year, month")
    return ""  # no pattern matched
