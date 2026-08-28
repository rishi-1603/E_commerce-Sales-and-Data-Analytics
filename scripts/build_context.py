"""
build_context.py — deterministic fact extraction from processed CSVs
=====================================================================
Purpose: turn the pipeline outputs into a single, verified "fact sheet"
that any downstream tool (dashboard, report, LLM brief) can consume.

DESIGN PRINCIPLE (anti-hallucination):
    Every number here is computed directly from data/processed/*.csv with
    pandas. Nothing is hardcoded, assumed, or invented. An LLM that narrates
    this file is therefore *grounded* — it cannot fabricate figures because
    it never computes them; it only assembles facts that already exist.

Outputs:
    reports/fact_sheet.json   — machine-readable facts
    reports/fact_card.md      — human-readable fact card

Run:  python scripts/build_context.py     (after run_pipeline.py)
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

INR_LAKH = 1e5      # 1 lakh = 100,000
INR_CR   = 1e7      # 1 crore = 10,000,000


def fmt_inr(x):
    """Human-friendly INR string."""
    x = float(x)
    if abs(x) >= INR_CR:
        return f"₹{x/INR_CR:,.2f} Cr"
    if abs(x) >= INR_LAKH:
        return f"₹{x/INR_LAKH:,.1f} L"
    return f"₹{x:,.0f}"


def main():
    master = pd.read_csv(f"{PROC}/master_orders.csv", parse_dates=["order_date"])
    rfm    = pd.read_csv(f"{PROC}/rfm_segments.csv")
    churn  = pd.read_csv(f"{PROC}/churn_features.csv")
    prod   = pd.read_csv(f"{PROC}/product_profitability.csv")
    fc     = pd.read_csv(f"{PROC}/revenue_forecast.csv", parse_dates=["date"])

    facts = {}
    facts["generated_at"] = datetime.now(tz=None).strftime("%Y-%m-%d %H:%M (local)")
    facts["data_period"] = {
        "start": str(master["order_date"].min().date()),
        "end": str(master["order_date"].max().date()),
    }

    # ── Sales ─────────────────────────────────────────────
    facts["sales"] = {
        "total_revenue": fmt_inr(master["line_total"].sum()),
        "total_profit": fmt_inr(master["profit"].sum()),
        "gross_margin_pct": round(
            master["profit"].sum() / master["line_total"].sum() * 100, 1),
        "total_orders": int(master["order_id"].nunique()),
        "unique_customers": int(master["customer_id"].nunique()),
        "top_category_by_revenue": str(
            master.groupby("category")["line_total"].sum().idxmax()),
        "top_region_by_revenue": str(
            master.groupby("region")["line_total"].sum().idxmax()),
    }

    # ── RFM segments ──────────────────────────────────────
    seg = rfm.groupby("segment").agg(
        customers=("customer_id", "count"),
        spend=("monetary", "sum")).sort_values("spend", ascending=False)
    facts["segments"] = {
        "total_customers_segmented": int(len(rfm)),
        "by_segment": [
            {"segment": str(idx),
             "customers": int(row["customers"]),
             "historical_spend": fmt_inr(row["spend"])}
            for idx, row in seg.iterrows()],
    }

    # ── Churn (leakage-free model output) ─────────────────
    risk = churn["churn_risk"].value_counts().to_dict()
    # "At-risk" = medium + high bands; spend at risk is HISTORICAL spend
    at_risk = churn[churn["churn_risk"].isin(["Medium Risk", "High Risk"])]
    facts["churn"] = {
        "definition": "no purchase in the 180 days after the model cutoff",
        "model_note": "forward-time split; target-leakage-free",
        "overall_churn_rate_pct": round(churn["churned"].mean() * 100, 1),
        "risk_band_counts": {str(k): int(v) for k, v in risk.items()},
        "cooling_off_customers": int(len(at_risk)),
        "historical_spend_of_cooling_off": fmt_inr(at_risk["total_revenue"].sum()),
        "spend_disclaimer": "historical spend, NOT future revenue at risk",
    }

    # ── Product profitability ─────────────────────────────
    top_profit = prod.nlargest(1, "profit").iloc[0]
    worst_margin = prod.sort_values("margin_pct").iloc[0]
    facts["products"] = {
        "total_products": int(len(prod)),
        "most_profitable": {
            "name": str(top_profit["product_name"]),
            "profit": fmt_inr(top_profit["profit"]),
            "margin_pct": round(float(top_profit["margin_pct"]), 1)},
        "lowest_margin": {
            "name": str(worst_margin["product_name"]),
            "margin_pct": round(float(worst_margin["margin_pct"]), 1)},
    }

    # ── Forecast ──────────────────────────────────────────
    total_fc = fc["ensemble_forecast"].sum()
    fc_rows = [
        {"month": r["date"].strftime("%b %Y"),
         "forecast": fmt_inr(r["ensemble_forecast"])}
        for _, r in fc.iterrows()]
    # identify the softest month (relative dip) for the "watch" insight
    dip_idx = int(fc["ensemble_forecast"].idxmin())
    facts["forecast"] = {
        "method": "ensemble of linear-trend + Holt-Winters",
        "horizon_months": int(len(fc)),
        "total_projected": fmt_inr(total_fc),
        "softest_month": fc.loc[dip_idx, "date"].strftime("%b %Y"),
        "caveat": "assumes the recent trend/seasonality continues; "
                  "evaluate against actuals over time",
        "monthly": fc_rows,
    }

    # ── Write JSON + markdown ─────────────────────────────
    with open(f"{REPO}/fact_sheet.json", "w") as f:
        json.dump(facts, f, indent=2, ensure_ascii=False)

    md = ["# Fact Card (auto-generated, verified from data)",
          f"_Generated {facts['generated_at']} · "
          f"data {facts['data_period']['start']} → {facts['data_period']['end']}_",
          "",
          "## Sales",
          f"- Total revenue: **{facts['sales']['total_revenue']}**",
          f"- Gross margin: **{facts['sales']['gross_margin_pct']}%**",
          f"- Top category: **{facts['sales']['top_category_by_revenue']}** · "
          f"Top region: **{facts['sales']['top_region_by_revenue']}**",
          "",
          "## Customer segments (RFM)"]
    for s in facts["segments"]["by_segment"]:
        md.append(f"- {s['segment']}: {s['customers']} customers, "
                  f"{s['historical_spend']} spend")
    md += ["",
           "## Churn (leakage-free)",
           f"- Overall churn rate: **{facts['churn']['overall_churn_rate_pct']}%**",
           f"- Cooling-off customers (Med+High risk): "
           f"**{facts['churn']['cooling_off_customers']}**",
           f"- Their historical spend: "
           f"**{facts['churn']['historical_spend_of_cooling_off']}** "
           f"({facts['churn']['spend_disclaimer']})",
           "",
           "## Forecast",
           f"- Projected over {facts['forecast']['horizon_months']} months: "
           f"**{facts['forecast']['total_projected']}**",
           f"- Softest month to watch: **{facts['forecast']['softest_month']}**",
           "",
           "## Products",
           f"- Most profitable: **{facts['products']['most_profitable']['name']}** "
           f"({facts['products']['most_profitable']['profit']})",
           f"- Lowest margin: **{facts['products']['lowest_margin']['name']}** "
           f"({facts['products']['lowest_margin']['margin_pct']}%)"]

    with open(f"{REPO}/fact_card.md", "w") as f:
        f.write("\n".join(md) + "\n")

    print("Fact sheet written:")
    print(f"  {REPO}/fact_sheet.json")
    print(f"  {REPO}/fact_card.md")
    print("\nKey figures:")
    print(f"  Revenue: {facts['sales']['total_revenue']} | "
          f"Margin: {facts['sales']['gross_margin_pct']}%")
    print(f"  Churn rate: {facts['churn']['overall_churn_rate_pct']}% | "
          f"Cooling-off: {facts['churn']['cooling_off_customers']}")
    print(f"  Forecast total: {facts['forecast']['total_projected']}")


if __name__ == "__main__":
    main()
