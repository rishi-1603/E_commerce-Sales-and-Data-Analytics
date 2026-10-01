"""
test_decision_layer.py — the decision layer cannot drift from the data
================================================================================
Day-2 upgrade pin. Everything the new dashboard sections display (What-changed
strip, MoM chips, cohort heatmap, funnel, segment playbook) is computed by
scripts/decision_layer.py and embedded as DATA.decision. These tests pin the
verified values AND assert the embedded block equals the computed JSON — so
the live site can never silently diverge from the analysis.
"""
import json
import os
import re
import subprocess
import sys

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
sys.path.insert(0, os.path.join(BASE, "scripts"))

from decision_layer import (  # noqa: E402
    cohort_matrix,
    funnel,
    load_master,
    mom_block,
    monthly_kpis,
    segment_actions,
    what_changed,
)


def _master():
    return load_master()


# ── MoM engine ───────────────────────────────────────────────────────────────

def test_mom_pins_verified_december_move():
    g = monthly_kpis(_master())
    m = mom_block(g)
    assert m["label"] == "2024-12" and m["prev_label"] == "2024-11"
    assert m["revenue_delta_pct"] == 17.0
    assert m["orders_delta_pct"] == 21.3
    assert m["active_customers_delta_pct"] == 8.2
    assert m["aov_delta_pct"] == -3.5
    # revenue values must reconcile with the embedded monthly series
    dash = _dash_data()
    assert abs(m["revenue"][1] - dash["monthly_revenue"][-1]) < 2


def test_monthly_revenue_matches_dashboard_series():
    g = monthly_kpis(_master())
    dash = _dash_data()
    assert len(g) == len(dash["monthly_revenue"])
    for a, b in zip(g["revenue"], dash["monthly_revenue"]):
        assert abs(a - b) / b < 0.001


# ── Funnel ───────────────────────────────────────────────────────────────────

def test_funnel_pins_verified_values():
    f = funnel(_master())
    assert f["values"] == [12000, 9312, 8089]
    assert f["exits"] == {"Cancelled": 844, "Processing": 621, "Returned": 1223}
    assert f["delivery_rate_pct"] == 77.6
    assert f["keep_rate_pct"] == 86.9


def test_funnel_matches_dashboard_status_series():
    f = funnel(_master())
    dash = _dash_data()
    by_status = dict(zip(dash["status_labels"], dash["status_vals"]))
    assert f["values"][1] == by_status["Delivered"]
    assert f["exits"]["Cancelled"] == by_status["Cancelled"]
    assert f["exits"]["Returned"] == by_status["Returned"]
    assert f["exits"]["Processing"] == by_status["Processing"]


# ── Cohorts ──────────────────────────────────────────────────────────────────

def test_cohort_matrix_shape_and_definition():
    c = cohort_matrix(_master())
    assert len(c["labels"]) == 18
    assert c["labels"][0] == "2023-07" and c["labels"][-1] == "2024-12"
    assert all(row[0] == 100.0 for row in c["matrix"])  # M0 = 100% by definition
    assert all(len(row) == c["max_months"] + 1 for row in c["matrix"])
    # no retention value above 100 or below 0
    for row in c["matrix"]:
        for v in row:
            if v is not None:
                assert 0 <= v <= 100


def test_cohort_retention_improves_over_time():
    c = cohort_matrix(_master())
    m1 = [row[1] for row in c["matrix"] if row[1] is not None]
    early = m1[: len(m1) // 2]
    late = m1[len(m1) // 2 :]
    assert sum(late) / len(late) > sum(early) / len(early), (
        "verified pattern broken: newer cohorts should retain better")


# ── What-changed + segment playbook ──────────────────────────────────────────

def test_what_changed_carries_verified_structural_facts():
    master = _master()
    rfm = pd.read_csv(os.path.join(PROC, "rfm_segments.csv"))
    clv = pd.read_csv(os.path.join(PROC, "clv.csv"))
    from decision_layer import structural_facts  # noqa: E402
    wc = what_changed(mom_block(monthly_kpis(master)), structural_facts(master, rfm, clv))
    assert len(wc) == 6
    cooling = [w for w in wc if "cooling-off" in w["headline"]]
    assert cooling and "448" in cooling[0]["headline"] and "1.24" in cooling[0]["headline"]
    for w in wc:
        assert w["level"] in {"ok", "watch", "alert", "info"}


def test_segment_playbook_covers_all_customers_and_spend():
    master = _master()
    rfm = pd.read_csv(os.path.join(PROC, "rfm_segments.csv"))
    segs = segment_actions(master, rfm)
    assert len(segs) == 8
    assert sum(s["customers"] for s in segs) == 1991
    total = master["line_total"].sum()
    assert abs(sum(s["spend"] for s in segs) - total) / total < 0.001


# ── Dashboard embed: DATA.decision must equal the computed layer ─────────────

def _dash_data():
    with open(os.path.join(BASE, "dashboard", "dashboard.html"), encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"const DATA = (\{.*?\});\s*\n\s*const C", html, re.S)
    assert m, "DATA object not found"
    raw = m.group(1)
    raw = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_ ]*?)\s*:", r'\1"\2":', raw)
    raw = raw.replace("'", '"')
    raw = re.sub(r",\s*([\]}])", r"\1", raw)
    return json.loads(raw)


def test_dashboard_decision_block_matches_computed_layer():
    dash = _dash_data()
    with open(os.path.join(BASE, "reports", "decision_layer.json"), encoding="utf-8") as f:
        computed = json.load(f)
    d = dash["decision"]
    assert d["mom"] == computed["mom"]
    assert d["funnel"] == computed["funnel"]
    assert d["cohorts"] == computed["cohorts"]
    assert d["segActions"] == computed["segment_actions"]
    assert len(d["whatChanged"]) == len(computed["what_changed"])


def test_dashboard_has_new_page_and_renderers():
    with open(os.path.join(BASE, "dashboard", "dashboard.html"), encoding="utf-8") as f:
        html = f.read()
    for anchor in [
        'id="page-cohorts"', "Retention &amp; Cohorts",
        'id="wcStrip"', 'id="momRow"', 'id="funnelBox"', 'id="cohHeat"',
        'id="segTable"', "renderWhatChanged", "buildCohortCurve",
        "nav('cohorts',this)",
    ]:
        assert anchor in html, f"missing dashboard element: {anchor}"


# ── Semantic layer + experiment design ───────────────────────────────────────

def test_metrics_json_semantic_layer():
    with open(os.path.join(BASE, "data", "metrics.json"), encoding="utf-8") as f:
        defs = json.load(f)
    m = defs["metrics"]
    for key in ["revenue", "churn_model", "cooling_off_customers", "purchase",
                "cohort_retention", "order_funnel", "mom_delta", "winback_experiment"]:
        assert key in m and "definition" in m[key], f"missing: {key}"
    assert m["cooling_off_customers"]["full_dataset_value"] == 448
    assert m["order_funnel"]["delivery_rate_pct"] == 77.6


def test_experiment_doc_is_design_with_real_baselines():
    path = os.path.join(BASE, "docs", "experiment_design_winback.md")
    assert os.path.exists(path), "experiment design doc missing"
    text = open(path, encoding="utf-8").read()
    assert "DESIGN, NOT RESULTS" in text
    assert "34.5%" in text          # measured segment baseline
    assert "+13.0 pp" in text       # core-pool MDE
    assert "+8.5 pp" in text        # expanded-pool MDE


def test_experiment_baselines_recompute_from_data():
    """The doc's 34.5% baseline must be reproducible from the data."""
    m = load_master()
    churn = pd.read_csv(os.path.join(PROC, "churn_features.csv"))
    med = churn[churn["churn_risk"].str.contains("Medium")]
    pu = m[m["status"].isin(["Delivered", "Returned"])]
    first = pu.groupby("customer_id")["order_date"].min()
    second = pu[pu["order_date"] > pu.groupby("customer_id")["order_date"].transform("min")] \
        .groupby("customer_id")["order_date"].min()
    df = pd.DataFrame({"first": first, "second": second})
    df = df[df.index.isin(med["customer_id"])]
    df = df[df["first"] <= m["order_date"].max() - pd.Timedelta(days=90)]
    baseline = (df["second"] - df["first"] <= pd.Timedelta(days=90)).mean()
    assert abs(baseline - 0.345) < 0.005


def test_decision_layer_script_runs_and_writes_report():
    r = subprocess.run(
        [sys.executable, os.path.join(BASE, "scripts", "decision_layer.py")],
        capture_output=True, text=True, timeout=300,
    )
    assert r.returncode == 0, r.stderr[-500:]
    assert "decision:" in r.stdout
    assert os.path.exists(os.path.join(BASE, "reports", "decision_layer.json"))
