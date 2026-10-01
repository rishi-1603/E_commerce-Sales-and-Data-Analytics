"""
decision_layer.py — period-over-period, cohorts, funnel, what-changed
=====================================================================
Day-2 upgrade: computes the "decision layer" for the Chart.js dashboard.
Same design principle as build_context.py — every number is computed
directly from data/processed/*.csv with pandas. Nothing hardcoded, nothing
invented; the LLM (if used) never computes these values.

Outputs:
    reports/decision_layer.json  — machine-readable (tests verify against this)
    stdout                       — the exact JS `DATA` extension block to paste
                                   into dashboard/index.html

Run:  python scripts/decision_layer.py
"""
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
REPO = os.path.join(BASE, "reports")
os.makedirs(REPO, exist_ok=True)

# A "purchase" for retention purposes: an order that transacted
# (cancelled orders never completed; processing is not yet a purchase).
PURCHASE_STATUSES = ["Delivered", "Returned"]

# MoM alert thresholds (relative % change)
ALERT_PCT = 10.0
WATCH_PCT = 5.0


def load_master() -> pd.DataFrame:
    m = pd.read_csv(os.path.join(PROC, "master_orders.csv"), parse_dates=["order_date"])
    return m


def monthly_kpis(master: pd.DataFrame) -> pd.DataFrame:
    """Monthly revenue / orders / active customers / AOV.

    Revenue follows the project convention (test-pinned): line_total summed
    across ALL order statuses — identical to DATA.monthly_revenue.
    """
    g = (
        master.assign(ym=master["order_date"].dt.to_period("M"))
        .groupby("ym")
        .agg(revenue=("line_total", "sum"),
             orders=("order_id", "nunique"),
             customers=("customer_id", "nunique"))
    )
    g["aov"] = g["revenue"] / g["orders"]
    return g


def mom_block(g: pd.DataFrame) -> dict:
    """Latest month vs previous month for the KPI chip row."""
    cur, prev = g.iloc[-1], g.iloc[-2]

    def pct(col):
        return round((cur[col] - prev[col]) / prev[col] * 100, 1)

    return {
        "label": str(g.index[-1]),
        "prev_label": str(g.index[-2]),
        "revenue": [round(prev["revenue"]), round(cur["revenue"])],
        "revenue_delta_pct": pct("revenue"),
        "orders": [int(prev["orders"]), int(cur["orders"])],
        "orders_delta_pct": pct("orders"),
        "active_customers": [int(prev["customers"]), int(cur["customers"])],
        "active_customers_delta_pct": pct("customers"),
        "aov": [round(prev["aov"]), round(cur["aov"])],
        "aov_delta_pct": pct("aov"),
    }


def _level(delta_pct: float) -> str:
    if abs(delta_pct) >= ALERT_PCT:
        return "alert"
    if abs(delta_pct) >= WATCH_PCT:
        return "watch"
    return "ok"


def what_changed(mom: dict, structural: list[dict]) -> list[dict]:
    """Rule-based signals: MoM moves + verified structural facts."""
    items = []
    specs = [
        ("revenue", "Revenue", "₹{:,.0f}"),
        ("orders", "Orders", "{:,}"),
        ("active_customers", "Active customers", "{:,}"),
        ("aov", "Average order value", "₹{:,.0f}"),
    ]
    for key, name, fmt in specs:
        d = mom[f"{key}_delta_pct"]
        items.append({
            "headline": f"{name} {abs(d):.1f}% {'up' if d >= 0 else 'down'} in {mom['label']}",
            "detail": f"{fmt.format(mom[key][0])} in {mom['prev_label']} to "
                      f"{fmt.format(mom[key][1])} in {mom['label']}, month over month.",
            "level": _level(d),
        })
    items.extend(structural)
    return items


def structural_facts(master: pd.DataFrame, rfm: pd.DataFrame, clv: pd.DataFrame) -> list[dict]:
    """Verified context items surfaced alongside the MoM signals."""
    facts = []
    # Cooling-off (medium churn risk) customers and their historical spend
    churn = pd.read_csv(os.path.join(PROC, "churn_features.csv"))
    band_col = next(
        (c for c in ("churn_risk", "risk_band", "Risk_Band") if c in churn.columns), None
    )
    if band_col:
        med = churn[churn[band_col].str.contains("Medium", na=False)]
        # Same source of truth as build_context.py (fact_sheet): churn_features.total_revenue
        med_spend = med["total_revenue"].sum()
        facts.append({
            "headline": f"{len(med):,} cooling-off customers hold ₹{med_spend/1e7:.2f} Cr historical spend",
            "detail": "Medium churn-risk band — the primary win-back audience "
                      "(experiment design in docs/experiment_design_winback.md).",
            "level": "watch",
        })
    # CLV concentration
    top10 = clv.sort_values("pred_clv", ascending=False).head(int(np.ceil(len(clv) * 0.10)))
    share = top10["pred_clv"].sum() / clv["pred_clv"].sum() * 100
    facts.append({
        "headline": f"Top 10% of customers hold {share:.0f}% of projected lifetime value",
        "detail": "Retention is risk management — protect the decile that carries the value.",
        "level": "info",
    })
    return facts


def cohort_matrix(master: pd.DataFrame, max_cohorts: int = 18, max_months: int = 12) -> dict:
    """First-purchase-month cohorts x months-since retention (%).

    Definition: a 'purchase' = order with status Delivered or Returned
    (cancelled orders never transacted; processing is not yet a purchase).
    Retention(month k) = share of the cohort with at least one purchase
    k months after the cohort's first-purchase month.
    """
    pu = master[master["status"].isin(PURCHASE_STATUSES)]
    first = pu.groupby("customer_id")["order_date"].min().dt.to_period("M").rename("cohort")
    act = (
        pu.assign(ym=pu["order_date"].dt.to_period("M"))
        .groupby(["customer_id", "ym"]).size().reset_index(name="n")
        [["customer_id", "ym"]]
        .merge(first, on="customer_id")
    )
    act["k"] = (act["ym"] - act["cohort"]).apply(lambda x: x.n)
    act = act[(act["k"] >= 0) & (act["k"] <= max_months)]
    cohort_sizes = first.value_counts().sort_index()
    recent = cohort_sizes.tail(max_cohorts)
    rows, sizes = [], []
    for cohort, size in recent.items():
        active = act[act["cohort"] == cohort].groupby("k")["customer_id"].nunique()
        row = [round(active.get(k, 0) / size * 100, 1) if k <= (recent.index[-1] - cohort).n else None
               for k in range(max_months + 1)]
        rows.append(row)
        sizes.append(int(size))
    return {
        "labels": [str(c) for c in recent.index],
        "sizes": sizes,
        "matrix": rows,
        "max_months": max_months,
    }


def funnel(master: pd.DataFrame) -> dict:
    """Order-status funnel: placed -> delivered -> kept.

    Uses the RAW orders file (data/raw/orders.csv, 12,000 rows, all statuses)
    because master_orders.csv only carries Delivered/Processing rows.
    """
    raw = pd.read_csv(os.path.join(BASE, "data", "raw", "orders.csv"))
    counts = raw["status"].value_counts().to_dict()
    placed = int(len(raw))
    delivered = int(counts.get("Delivered", 0))
    returned = int(counts.get("Returned", 0))
    cancelled = int(counts.get("Cancelled", 0))
    processing = int(counts.get("Processing", 0))
    kept = delivered - returned
    return {
        "stages": ["Placed", "Delivered", "Kept"],
        "values": [placed, delivered, kept],
        "exits": {"Cancelled": cancelled, "Processing": processing, "Returned": returned},
        "delivery_rate_pct": round(delivered / placed * 100, 1),
        "keep_rate_pct": round(kept / delivered * 100, 1),
    }


SEGMENT_ACTIONS = {
    "Champions": "Retain — loyalty perks, early access, protect at all costs",
    "Loyal Customers": "Grow — cross-sell adjacent categories",
    "Potential Loyalists": "Nurture — onboarding offers, second-purchase push",
    "Recent Customers": "Activate — welcome flow plus first-repeat incentive",
    "About To Sleep": "Re-engage now, before the lapse",
    "Needs Attention": "Win-back — incentive plus feedback capture",
    "At Risk": "Win-back — high-touch offer, personal outreach",
    "Lost Customers": "Low-cost reactivation only — do not overspend",
}


def segment_actions(master: pd.DataFrame, rfm: pd.DataFrame) -> list[dict]:
    spend = master.groupby("customer_id")["line_total"].sum()
    seg = rfm[["customer_id", "segment"]].copy()
    seg["spend"] = seg["customer_id"].map(spend)
    g = seg.groupby("segment").agg(customers=("customer_id", "count"), spend=("spend", "sum"))
    g = g.sort_values("spend", ascending=False)
    out = []
    for seg_name, row in g.iterrows():
        out.append({
            "segment": seg_name,
            "customers": int(row["customers"]),
            "spend": round(row["spend"]),
            "action": SEGMENT_ACTIONS.get(seg_name, "Review"),
        })
    return out


def main() -> None:
    master = load_master()
    rfm = pd.read_csv(os.path.join(PROC, "rfm_segments.csv"))
    clv = pd.read_csv(os.path.join(PROC, "clv.csv"))

    g = monthly_kpis(master)
    mom = mom_block(g)
    structural = structural_facts(master, rfm, clv)
    wc = what_changed(mom, structural)
    cohorts = cohort_matrix(master)
    fun = funnel(master)
    segs = segment_actions(master, rfm)

    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "mom": mom,
        "what_changed": wc,
        "cohorts": cohorts,
        "funnel": fun,
        "segment_actions": segs,
    }
    out_path = os.path.join(REPO, "decision_layer.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    # ── JS DATA extension block (paste into dashboard/index.html) ──
    def js_str(s: str) -> str:
        return json.dumps(s)  # double-quoted, apostrophe-free by construction

    print("// ── Day-2 decision layer (generated by scripts/decision_layer.py — do not hand-edit) ──")
    print("  decision: {")
    print(f"    mom: {json.dumps(mom)},")
    print(f"    whatChanged: {json.dumps(wc)},")
    print(f"    funnel: {json.dumps(fun)},")
    print(f"    segActions: {json.dumps(segs)},")
    print(f"    cohorts: {json.dumps(cohorts)}")
    print("  },")
    print(f"\nWrote {out_path}")
    print(f"Cohort window: {cohorts['labels'][0]} .. {cohorts['labels'][-1]} "
          f"({len(cohorts['labels'])} cohorts, sizes {cohorts['sizes'][:3]}...{cohorts['sizes'][-3:]})")
    print(f"MoM {mom['prev_label']} -> {mom['label']}: revenue {mom['revenue_delta_pct']}%, "
          f"orders {mom['orders_delta_pct']}%, active {mom['active_customers_delta_pct']}%, aov {mom['aov_delta_pct']}%")


if __name__ == "__main__":
    main()
