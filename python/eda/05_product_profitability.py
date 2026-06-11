"""
05_product_profitability.py
Product Profitability Analysis:
  - Margin analysis per product/category
  - BCG Matrix (Stars, Cash Cows, Question Marks, Dogs)
  - Discount impact on profit
  - Top/Bottom performers
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os, warnings
warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "docs", "figures")
os.makedirs(PROC, exist_ok=True); os.makedirs(FIGS, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
PALETTE = ["#2563EB","#7C3AED","#DB2777","#D97706","#059669"]

# ── Load ─────────────────────────────────────────────────
master = pd.read_csv(f"{PROC}/master_orders.csv", parse_dates=["order_date"])

# ── Product-level summary ─────────────────────────────────
prod_df = master.groupby(["product_id","product_name","category","subcategory"]).agg(
    units_sold =("quantity","sum"),
    revenue    =("line_total","sum"),
    cost       =("cost_total","sum"),
    avg_discount=("discount_pct_x","mean"),
    orders     =("order_id","nunique"),
).reset_index()

prod_df["profit"]     = prod_df["revenue"] - prod_df["cost"]
prod_df["margin_pct"] = (prod_df["profit"] / prod_df["revenue"].replace(0, np.nan)) * 100
prod_df.to_csv(f"{PROC}/product_profitability.csv", index=False)
print(f"Product profitability saved: {len(prod_df)} products")

# ── BCG Matrix ────────────────────────────────────────────
med_units  = prod_df["units_sold"].median()
med_margin = prod_df["margin_pct"].median()

def bcg(row):
    hi_vol = row["units_sold"] > med_units
    hi_mar = row["margin_pct"] > med_margin
    if hi_vol and hi_mar:   return "Star ⭐"
    if hi_vol and not hi_mar: return "Cash Cow 🐄"
    if not hi_vol and hi_mar: return "Question Mark ❓"
    return "Dog 🐕"

prod_df["bcg_quadrant"] = prod_df.apply(bcg, axis=1)
print("\nBCG Distribution:")
print(prod_df["bcg_quadrant"].value_counts().to_string())

# ── Plot 1: BCG Scatter ────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 8))
colors_bcg = {"Star ⭐":"#059669","Cash Cow 🐄":"#2563EB",
              "Question Mark ❓":"#D97706","Dog 🐕":"#DC2626"}
for quad, grp in prod_df.groupby("bcg_quadrant"):
    ax.scatter(grp["units_sold"], grp["margin_pct"],
               s=grp["revenue"]/1500, alpha=0.6, color=colors_bcg[quad],
               edgecolors='white', linewidth=0.8, label=quad)

ax.axvline(med_units,  color='gray', linestyle='--', lw=1.2, alpha=0.6)
ax.axhline(med_margin, color='gray', linestyle='--', lw=1.2, alpha=0.6)
ax.set_xlabel("Units Sold (Volume)", fontsize=12)
ax.set_ylabel("Profit Margin %", fontsize=12)
ax.set_title("BCG Product Matrix\n(bubble size = revenue)", fontsize=14, pad=10)
ax.legend(title="Quadrant", bbox_to_anchor=(1.02, 1), loc='upper left')
ax.text(med_units*0.05, ax.get_ylim()[1]*0.95, "Question\nMarks", color="#D97706", fontsize=10, alpha=0.7)
ax.text(med_units*1.05, ax.get_ylim()[1]*0.95, "Stars", color="#059669", fontsize=10, alpha=0.7)
ax.text(med_units*0.05, ax.get_ylim()[0]*0.5, "Dogs", color="#DC2626", fontsize=10, alpha=0.7)
ax.text(med_units*1.05, ax.get_ylim()[0]*0.5, "Cash\nCows", color="#2563EB", fontsize=10, alpha=0.7)
plt.tight_layout()
plt.savefig(f"{FIGS}/14_bcg_matrix.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 2: Category Profitability ────────────────────────
cat_df = prod_df.groupby("category").agg(
    revenue=("revenue","sum"),
    profit =("profit","sum"),
    units  =("units_sold","sum"),
    products=("product_id","count")
).reset_index()
cat_df["margin_pct"] = cat_df["profit"] / cat_df["revenue"] * 100
cat_df = cat_df.sort_values("profit", ascending=False)

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
colors = PALETTE[:len(cat_df)]
axes[0].bar(cat_df["category"], cat_df["revenue"]/1e6, color=colors)
axes[0].set_title("Revenue by Category (₹M)"); axes[0].set_ylabel("₹ Millions")
axes[0].tick_params(axis='x', rotation=20)

axes[1].bar(cat_df["category"], cat_df["profit"]/1e6, color=colors)
axes[1].set_title("Gross Profit by Category (₹M)"); axes[1].set_ylabel("₹ Millions")
axes[1].tick_params(axis='x', rotation=20)

axes[2].bar(cat_df["category"], cat_df["margin_pct"], color=colors)
axes[2].set_title("Profit Margin % by Category"); axes[2].set_ylabel("Margin %")
axes[2].tick_params(axis='x', rotation=20)
for ax in axes:
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.suptitle("Category-Level Profitability Analysis", fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(f"{FIGS}/15_category_profitability.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 3: Top & Bottom 10 Products ─────────────────────
top10    = prod_df.nlargest(10, "profit")
bottom10 = prod_df.nsmallest(10, "profit")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
axes[0].barh(top10["product_name"].str[:25], top10["profit"]/1e3, color="#059669")
axes[0].set_title("Top 10 Most Profitable Products")
axes[0].set_xlabel("Gross Profit (₹000s)")
axes[1].barh(bottom10["product_name"].str[:25], bottom10["profit"]/1e3, color="#DC2626")
axes[1].set_title("Bottom 10 Least Profitable Products")
axes[1].set_xlabel("Gross Profit (₹000s)")
plt.suptitle("Product Profitability Extremes", fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(f"{FIGS}/16_top_bottom_products.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 4: Discount vs Margin ────────────────────────────
disc_bins = pd.cut(master["discount_pct_x"], bins=[-0.01,0,0.05,0.10,0.15,0.20],
                   labels=["0%","1-5%","6-10%","11-15%","16-20%"])
disc_analysis = master.groupby(disc_bins).agg(
    revenue=("line_total","sum"),
    cost   =("cost_total","sum"),
    orders =("order_id","nunique")
).reset_index()
disc_analysis["margin_pct"] = (disc_analysis["revenue"] - disc_analysis["cost"]) / disc_analysis["revenue"] * 100

fig, ax1 = plt.subplots(figsize=(10, 5))
x = np.arange(len(disc_analysis))
bars = ax1.bar(x, disc_analysis["revenue"]/1e6, color=PALETTE[0], alpha=0.7, label="Revenue (₹M)")
ax2  = ax1.twinx()
ax2.plot(x, disc_analysis["margin_pct"], color=PALETTE[2], marker='o', ms=8, lw=2.5, label="Margin %")
ax1.set_xticks(x); ax1.set_xticklabels(disc_analysis["discount_pct_x"])
ax1.set_xlabel("Discount Band"); ax1.set_ylabel("Revenue (₹M)", color=PALETTE[0])
ax2.set_ylabel("Profit Margin %", color=PALETTE[2])
ax1.set_title("Discount Band Impact on Revenue & Margin", fontsize=13)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
plt.tight_layout()
plt.savefig(f"{FIGS}/17_discount_impact.png", dpi=150, bbox_inches="tight")
plt.close()

print("\nProduct profitability analysis complete.")
print("Run the dashboard script last: dashboard/app.py")
