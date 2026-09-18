"""
test_nl_to_sql.py — NL-to-SQL must produce correct, safe, grounded answers.
==============================================================================
Tests the fallback SQL generation (deterministic), SQL safety validation,
and result accuracy against known pipeline values.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from nl_to_sql import answer_question, validate_sql, execute_sql, _fallback_sql


class TestSQLSafety:
    """Generated SQL must be read-only."""

    def test_select_allowed(self):
        ok, _ = validate_sql("SELECT * FROM orders")
        assert ok

    def test_with_cte_allowed(self):
        ok, _ = validate_sql("WITH t AS (SELECT 1) SELECT * FROM t")
        assert ok

    def test_drop_blocked(self):
        ok, msg = validate_sql("DROP TABLE orders")
        assert not ok

    def test_delete_blocked(self):
        ok, msg = validate_sql("DELETE FROM orders")
        assert not ok

    def test_insert_blocked(self):
        ok, msg = validate_sql("INSERT INTO orders VALUES (1)")
        assert not ok

    def test_update_blocked(self):
        ok, msg = validate_sql("UPDATE orders SET line_total = 0")
        assert not ok


class TestFallbackSQL:
    """Pattern-matching fallback must produce correct SQL."""

    def test_total_revenue(self):
        r = answer_question("What is total revenue?", use_llm=False)
        assert r["ok"]
        assert r["result"][0]["total_revenue"] == pytest.approx(59283619.32, rel=0.001)

    def test_highest_margin_category(self):
        r = answer_question("Which category has the highest margin?", use_llm=False)
        assert r["ok"]
        assert r["result"][0]["category"] == "Sports"
        assert r["result"][0]["margin_pct"] == pytest.approx(56.5, abs=0.1)

    def test_customer_count(self):
        r = answer_question("How many customers?", use_llm=False)
        assert r["ok"]
        assert r["result"][0]["total_customers"] == 1991

    def test_unknown_question(self):
        sql = _fallback_sql("What is the meaning of life?")
        assert sql == ""  # no pattern match → empty


class TestResultAccuracy:
    """Results must match the pipeline's verified numbers."""

    def test_revenue_matches_pipeline(self):
        df = pd.read_csv(ROOT / "data" / "processed" / "master_orders.csv")
        expected = df["line_total"].sum()
        r = answer_question("What is total revenue?", use_llm=False)
        assert r["result"][0]["total_revenue"] == pytest.approx(expected, rel=0.001)

    def test_margin_matches_dashboard(self):
        r = answer_question("Which category has the highest margin?", use_llm=False)
        # Sports is the verified top-margin category at 56.5%
        assert r["result"][0]["category"] == "Sports"


class TestGuardrails:
    """The system must never hide failures or invent results."""

    def test_invalid_sql_returns_error(self):
        r = answer_question("DROP TABLE orders", use_llm=False)
        assert not r["ok"] or "error" in r  # either blocked or error

    def test_no_data_returns_honest_answer(self):
        r = answer_question("What is total revenue?", use_llm=False)
        assert r["ok"]
        # result should never be None for a valid question
        assert r["result"] is not None
