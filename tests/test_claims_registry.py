"""Pin data/claims.json to the artifacts it claims to summarise.

The claims registry is the file a recruiter or interviewer reads, and it had
drifted from the dashboard: revenue was still quoted at the pre-fix 15.93 Cr,
the win-back audience at a stale 448, and the churn AUC/PR-AUC at superseded
values. Nothing consumed it, so nothing caught it.

This module makes the registry self-checking: every number must equal its
source artifact, and the test count must agree with README and
RESUME_EVIDENCE.md so the three surfaces cannot drift apart again.
"""
import json
import os
import re

import pandas as pd
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(*parts):
    with open(os.path.join(BASE, *parts), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def claims():
    return _load("data", "claims.json")


@pytest.fixture(scope="module")
def by_id(claims):
    return {c["metric_id"]: c for c in claims["claims"]}


def test_revenue_claim_matches_metrics_registry(by_id):
    claim = by_id["ecom_sales_revenue"]
    registry = _load("data", "metrics.json")["metrics"]["revenue"]["full_dataset_value"]

    assert claim["value"] == 59283619.32
    # The formatted string is what humans read; it must agree with the value.
    assert claim["formatted_value"] == "\u20b95.93 Cr (\u20b959,283,619.32)"
    assert registry == "\u20b95.93 Cr"


def test_revenue_claim_matches_raw_csv_total(by_id):
    orders = pd.read_csv(os.path.join(BASE, "data", "raw", "orders.csv"))
    items = pd.read_csv(os.path.join(BASE, "data", "raw", "order_items.csv"))
    merged = orders.merge(items, on="order_id", how="inner")
    valid = merged[merged.status.isin(["Delivered", "Processing"])]

    assert round(valid.line_total.sum(), 2) == by_id["ecom_sales_revenue"]["value"]
    assert len(valid) == 21066  # population string in the claim


def test_winback_claim_matches_report(by_id):
    claim = by_id["ecom_cooling_off_customers"]
    report = _load("reports", "winback_economics.json")

    assert claim["value"] == report["pool"]["customers"] == 441
    assert "\u20b91.30 Cr" in claim["formatted_value"]
    assert round(report["pool"]["historical_spend_inr"] / 1e7, 2) == 1.30
    assert round(report["baseline_campaign"]["expected_profit_per_contact"], 2) == 522.55
    assert round(report["baseline_campaign"]["expected_profit_total"], 2) == 230443.56
    assert round(report["break_even"]["break_even_churn_probability"] * 100, 2) == 12.54
    # Guard the two stale figures that used to live here.
    assert "448" not in claim["formatted_value"]
    assert "11.24" not in claim["formatted_value"]


def test_churn_claim_matches_holdout_metrics(by_id):
    claim = by_id["ecom_leakage_correction_auc"]
    holdout = _load("reports", "churn_model_metrics.json")["holdout"]

    assert claim["value"] == round(holdout["roc_auc"], 3) == 0.662
    assert round(holdout["pr_auc"], 3) == 0.332
    assert round(holdout["brier_raw"], 4) == 0.1726
    assert round(holdout["brier_calibrated"], 4) == 0.1715
    assert "0.36" not in claim["definition"]


def test_discount_claim_matches_report(by_id):
    claim = by_id["ecom_discount_repricing"]
    headline = _load("reports", "discount_analysis.json")["headline"]

    assert claim["value"] == headline["margin_recovered_by_10pct_cap"] == 644517.95
    assert round(headline["break_even_lift_at_20pct"] * 100, 1) == 59.2
    assert headline["kruskal_p"] == 0.305


def test_catalog_claim_matches_products_csv(by_id):
    products = pd.read_csv(os.path.join(BASE, "data", "raw", "products.csv"))
    claim = by_id["ecom_product_catalog"]

    assert claim["value"] == products.product_id.nunique() == 150
    assert products.category.nunique() == 5
    assert products.subcategory.nunique() == 40


def test_test_count_agrees_across_public_surfaces(claims):
    """claims.json, README and RESUME_EVIDENCE must quote one test count."""
    stated = claims["verified_ci_tests"]
    assert stated == by_id_count(claims)

    readme = open(os.path.join(BASE, "README.md"), encoding="utf-8").read()
    resume = open(os.path.join(BASE, "RESUME_EVIDENCE.md"), encoding="utf-8").read()

    assert f"CI: {stated} tests" in readme
    assert f"{stated} tests" in resume
    assert f"{stated} Passing Tests" in resume


def by_id_count(claims):
    test_claim = next(c for c in claims["claims"] if c["metric_id"] == "ecom_automated_ci_tests")
    assert test_claim["value"] == claims["verified_ci_tests"]
    assert test_claim["formatted_value"] == f"{claims['verified_ci_tests']} Passing Tests"
    return test_claim["value"]
