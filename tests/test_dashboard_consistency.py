"""
test_dashboard_consistency.py — the dashboard cannot drift from the data.
=========================================================================
WHY THIS EXISTS: an earlier version of the dashboard displayed hand-typed
numbers that did not match the pipeline output (including fabricated product
names and a leaked AUC of 1.0). This test parses the dashboard's DATA object
and asserts its headline values equal the values computed from
data/processed/*.csv — so the live site can never silently diverge from the
analysis again.

Run:  python -m pytest tests/test_dashboard_consistency.py -v
"""
import os
import re
import json

import pandas as pd
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
DASH = os.path.join(BASE, "dashboard", "dashboard.html")


@pytest.fixture(scope="session")
def dash_data():
    """Extract the JS `const DATA = {...}` object and convert to a dict."""
    with open(DASH, encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"const DATA = (\{.*?\});\s*\n\s*const C", html, re.S)
    assert m, "DATA object not found in dashboard.html"
    raw = m.group(1)
    # Convert JS object to JSON: quote unquoted keys, strip trailing commas
    raw = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_ ]*?)\s*:", r'\1"\2":', raw)
    raw = raw.replace("'", '"')
    raw = re.sub(r",\s*([\]}])", r"\1", raw)  # remove trailing commas
    return json.loads(raw)


@pytest.fixture(scope="session")
def master():
    return pd.read_csv(os.path.join(PROC, "master_orders.csv"), parse_dates=["order_date"])


def test_dashboard_exists():
    assert os.path.exists(DASH), "dashboard/dashboard.html missing"


def test_dashboard_copies_are_identical():
    """Deployment requires 3 copies of the dashboard (root index.html
    redirects into dashboard/, and vercel.json rewrites between them).
    If any copy drifts, the live site serves stale numbers — so all
    three must be byte-identical."""
    copies = [
        os.path.join(BASE, "dashboard", "dashboard.html"),
        os.path.join(BASE, "dashboard", "index.html"),
        os.path.join(BASE, "dashboard.html"),
    ]
    hashes = set()
    for path in copies:
        assert os.path.exists(path), f"{path} missing"
        with open(path, "rb") as f:
            hashes.add(hash(f.read()))
    assert len(hashes) == 1, "Dashboard copies have drifted — sync them before deploying"


def test_revenue_matches_pipeline(dash_data, master):
    total = master["line_total"].sum()
    claimed = sum(dash_data["monthly_revenue"])
    assert abs(claimed - total) / total < 0.01, (
        f"Dashboard monthly revenue sums to {claimed:,.0f} but pipeline says {total:,.0f}")


def test_category_revenue_matches(dash_data, master):
    actual = master.groupby("category")["line_total"].sum().sort_values(ascending=False)
    claimed = dict(zip(dash_data["cat_labels"], dash_data["cat_revenue"]))
    for cat, val in claimed.items():
        assert abs(val - actual[cat]) / actual[cat] < 0.01, f"{cat} revenue mismatch"


def test_segment_counts_match(dash_data):
    rfm = pd.read_csv(os.path.join(PROC, "rfm_segments.csv"))
    actual = rfm["segment"].value_counts()
    claimed = dict(zip(dash_data["seg_labels"], dash_data["seg_values"]))
    for seg, val in claimed.items():
        assert actual.get(seg, 0) == val, (
            f"Segment '{seg}': dashboard says {val}, pipeline says {actual.get(seg, 0)}")


def test_churn_risk_bands_match(dash_data):
    churn = pd.read_csv(os.path.join(PROC, "churn_features.csv"))
    actual = churn["churn_risk"].value_counts()
    claimed = dict(zip(dash_data["risk_labels"], dash_data["risk_values"]))
    for band, val in claimed.items():
        assert actual.get(band, 0) == val, (
            f"Risk band '{band}': dashboard says {val}, pipeline says {actual.get(band, 0)}")


def test_forecast_matches(dash_data):
    fc = pd.read_csv(os.path.join(PROC, "revenue_forecast.csv"))
    actual = fc["ensemble_forecast"].astype(int).tolist()
    assert dash_data["forecast_vals"] == actual, "Forecast values differ from pipeline"


def test_top_product_is_real(dash_data):
    prod = pd.read_csv(os.path.join(PROC, "product_profitability.csv"))
    best = prod.nlargest(1, "profit").iloc[0]
    claimed = dash_data["top10"][0]
    assert claimed["product_name"] == best["product_name"], (
        f"Dashboard top product '{claimed['product_name']}' != pipeline's "
        f"'{best['product_name']}' (fabricated names are not allowed)")
    assert abs(claimed["profit"] - best["profit"]) < 1, "Top product profit mismatch"


def test_no_leaked_auc_in_dashboard():
    """The AUC=1.0 leakage artifact must never be presented as a result."""
    with open(DASH, encoding="utf-8") as f:
        html = f.read()
    # The integrity note explaining the fix is allowed; a live KPI of 1.000 is not.
    kpi_auc = re.findall(r'kpi-value[^>]*>\s*1\.0{3}\s*<', html)
    assert not kpi_auc, "Dashboard displays AUC 1.000 as a KPI (leakage artifact)"
