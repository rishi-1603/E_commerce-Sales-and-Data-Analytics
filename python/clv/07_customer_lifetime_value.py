"""
07_customer_lifetime_value.py — defensible Customer Lifetime Value
===================================================================
Fills the "no real CLV" gap flagged in the review. Produces THREE CLV views,
each with its stated assumption, then ranks customers into value tiers so the
retention team can budget win-back spend per customer.

1) HISTORICAL CLV (sunk, observed):
     CLV_hist = AOV × frequency × gross margin
   What it is: money already captured. A floor, not a forecast.

2) PREDICTIVE CLV (forward-looking, risk-adjusted):
     CLV_pred = AOV × annual_frequency × gross_margin × horizon_years × (1 - churn_prob)
   Risk-adjusted by the leakage-free churn model's probability. This is the
   number to use when deciding "how much is this customer worth keeping?"

3) VALUE TIER:
     Customers ranked into Top 10% / Next 25% / Mid 50% / Bottom 15% by
     predictive CLV — directly maps to how much retention budget each gets.

Outputs:
    data/processed/clv.csv
    docs/figures/15_clv_distribution.png
    (CLV summary printed to console)
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "docs", "figures")
os.makedirs(FIGS, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
PALETTE = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DB2777"]
INR_LAKH, INR_CR = 1e5, 1e7

# ── Load ──────────────────────────────────────────────────────────────
master = pd.read_csv(f"{PROC}/master_orders.csv", parse_dates=["order_date"])
churn  = pd.read_csv(f"{PROC}/churn_features.csv")
SNAPSHOT = master["order_date"].max()
YEARS_OF_DATA = (master["order_date"].max() - master["order_date"].min()).days / 365.25

# Per-customer aggregates (on delivered orders)
cust = master.groupby("customer_id").agg(
    total_revenue=("line_total", "sum"),
    total_profit=("profit", "sum"),
    total_orders=("order_id", "nunique"),
    first_order=("order_date", "min"),
    last_order=("order_date", "max"),
).reset_index()
cust["tenure_years"] = (cust["last_order"] - cust["first_order"]).dt.days / 365.25

# Whole-customer rates
gross_margin = master["profit"].sum() / master["line_total"].sum()
print(f"Blended gross margin: {gross_margin*100:.1f}% | data span: {YEARS_OF_DATA:.1f} yrs")

# ── 1) Historical CLV ─────────────────────────────────────────────────
cust["hist_clv"] = cust["total_profit"]   # profit already captured = observed CLV

# ── 2) Predictive (risk-adjusted) CLV ─────────────────────────────────
cust["aov"]            = cust["total_revenue"] / cust["total_orders"]
cust["annual_freq"]    = cust["total_orders"] / cust["tenure_years"].clip(lower=1/12)
HORIZON_YEARS          = 2.0
# merge churn probability (risk adjustment)
cust = cust.merge(churn[["customer_id", "churn_probability"]], on="customer_id", how="left")
cust["churn_probability"] = cust["churn_probability"].fillna(cust["churn_probability"].median())
retention = 1 - cust["churn_probability"]
cust["pred_clv"] = (cust["aov"] * cust["annual_freq"] * gross_margin
                    * HORIZON_YEARS * retention)

# ── 3) Value tiers ────────────────────────────────────────────────────
cust = cust.sort_values("pred_clv", ascending=False).reset_index(drop=True)
n = len(cust)
def tier(i):
    frac = i / n
    if frac < 0.10: return "Top 10%"
    if frac < 0.35: return "Next 25%"
    if frac < 0.85: return "Mid 50%"
    return "Bottom 15%"
cust["value_tier"] = [tier(i) for i in range(n)]

cust[["customer_id", "total_revenue", "hist_clv", "aov", "annual_freq",
      "churn_probability", "pred_clv", "value_tier"]].to_csv(
    f"{PROC}/clv.csv", index=False)

# ── Summary ───────────────────────────────────────────────────────────
tier_sum = cust.groupby("value_tier").agg(
    customers=("customer_id", "count"),
    pred_clv_total=("pred_clv", "sum"),
    pred_clv_mean=("pred_clv", "mean"),
    hist_clv_total=("hist_clv", "sum"),
).reindex(["Top 10%", "Next 25%", "Mid 50%", "Bottom 15%"])

print("\nCLV by value tier:")
print(tier_sum.to_string())
print(f"\nTotal predictive CLV (2yr horizon): ₹{cust['pred_clv'].sum()/INR_CR:.2f} Cr")
print(f"Total historical profit captured:   ₹{cust['hist_clv'].sum()/INR_CR:.2f} Cr")

# ── Chart: value tier contribution (Pareto) ───────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
colors = ["#059669", "#2563EB", "#D97706", "#DB2777"]
axes[0].bar(tier_sum.index, tier_sum["pred_clv_total"]/INR_LAKH, color=colors)
axes[0].set_ylabel("Predictive CLV (₹ Lakhs, 2yr)")
axes[0].set_title("Future Value by Customer Tier")
for i, v in enumerate(tier_sum["pred_clv_total"]/INR_LAKH):
    axes[0].text(i, v, f"₹{v:.0f}L", ha='center', va='bottom', fontweight='bold')

# Cumulative share curve (Pareto)
sorted_clv = cust["pred_clv"].sort_values(ascending=False).values
cum_share = np.cumsum(sorted_clv) / sorted_clv.sum() * 100
x = np.arange(1, len(cum_share)+1) / len(cum_share) * 100
axes[1].plot(x, cum_share, color=PALETTE[0], lw=2.5)
axes[1].axhline(80, color=PALETTE[4], ls='--', alpha=0.6)
axes[1].axvline(np.interp(80, cum_share, x), color=PALETTE[4], ls='--', alpha=0.6)
axes[1].set_xlabel("Customers (%)")
axes[1].set_ylabel("Cumulative CLV share (%)")
axes[1].set_title(f"Value concentration: top "
                  f"{np.interp(80, cum_share, x):.0f}% of customers "
                  f"= 80% of future value")
plt.tight_layout()
plt.savefig(f"{FIGS}/15_clv_distribution.png", dpi=150, bbox_inches="tight")
plt.close()

print(f"\nCLV saved -> {PROC}/clv.csv | chart -> {FIGS}/15_clv_distribution.png")
