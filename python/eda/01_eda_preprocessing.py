"""
01_eda_preprocessing.py
Exploratory Data Analysis + Data Preprocessing
Outputs processed CSVs to data/processed/
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

# ── Paths ───────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW  = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "docs", "figures")
os.makedirs(PROC, exist_ok=True)
os.makedirs(FIGS, exist_ok=True)

# ── Style ────────────────────────────────────────────────
plt.style.use('seaborn-v0_8-whitegrid')
PALETTE = ["#2563EB","#7C3AED","#DB2777","#D97706","#059669"]
sns.set_palette(PALETTE)

# ── Load ─────────────────────────────────────────────────
print("Loading data...")
customers  = pd.read_csv(f"{RAW}/customers.csv",   parse_dates=["registration_date"])
products   = pd.read_csv(f"{RAW}/products.csv",    parse_dates=["launch_date"])
orders     = pd.read_csv(f"{RAW}/orders.csv",      parse_dates=["order_date"])
items      = pd.read_csv(f"{RAW}/order_items.csv")

print(f"  Customers:   {len(customers):,}")
print(f"  Products:    {len(products):,}")
print(f"  Orders:      {len(orders):,}")
print(f"  Order Items: {len(items):,}")

# ── Basic Info ───────────────────────────────────────────
for name, df in [("customers",customers),("products",products),("orders",orders),("items",items)]:
    nulls = df.isnull().sum().sum()
    print(f"\n[{name}] shape={df.shape}, nulls={nulls}")

# ── Merge master dataset ──────────────────────────────────
valid_orders = orders[~orders["status"].isin(["Cancelled","Returned"])]
master = (items
    .merge(valid_orders, on="order_id", how="inner")
    .merge(customers,    on="customer_id", how="left")
    .merge(products[["product_id","product_name","category","subcategory","cost_price","rating"]],
           on="product_id", how="left"))

master["year"]  = master["order_date"].dt.year
master["month"] = master["order_date"].dt.month
master["month_name"] = master["order_date"].dt.strftime("%b")
master["quarter"] = master["order_date"].dt.to_period("Q").astype(str)
master["profit"] = master["line_total"] - master["cost_total"]

master.to_csv(f"{PROC}/master_orders.csv", index=False)
print(f"\nMaster dataset saved: {len(master):,} rows")

# ── Plot 1: Monthly Revenue Trend ────────────────────────
monthly = master.groupby(master["order_date"].dt.to_period("M")).agg(
    revenue=("line_total","sum"),
    orders=("order_id","nunique")
).reset_index()
monthly["order_date"] = monthly["order_date"].dt.to_timestamp()

fig, ax1 = plt.subplots(figsize=(14, 5))
ax1.fill_between(monthly["order_date"], monthly["revenue"]/1000, alpha=0.25, color=PALETTE[0])
ax1.plot(monthly["order_date"], monthly["revenue"]/1000, color=PALETTE[0], lw=2.5, marker="o", ms=4)
ax1.set_ylabel("Revenue (₹000s)", color=PALETTE[0], fontsize=11)
ax1.set_xlabel("")
ax2 = ax1.twinx()
ax2.bar(monthly["order_date"], monthly["orders"], width=20, alpha=0.3, color=PALETTE[1])
ax2.set_ylabel("Order Count", color=PALETTE[1], fontsize=11)
plt.title("Monthly Revenue & Order Volume (2022–2024)", fontsize=14, pad=12)
plt.tight_layout()
plt.savefig(f"{FIGS}/01_monthly_revenue.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 2: Revenue by Category ───────────────────────────
cat_rev = master.groupby("category")["line_total"].sum().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.barh(cat_rev.index, cat_rev.values/1e6, color=PALETTE[:len(cat_rev)])
ax.set_xlabel("Revenue (₹ Millions)", fontsize=11)
ax.set_title("Revenue by Product Category", fontsize=14, pad=10)
for bar, val in zip(bars, cat_rev.values):
    ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
            f"₹{val/1e6:.2f}M", va='center', fontsize=10)
plt.tight_layout()
plt.savefig(f"{FIGS}/02_revenue_by_category.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 3: Order Status Distribution ────────────────────
status_counts = orders["status"].value_counts()
colors = [PALETTE[0], "#EF4444", "#F59E0B", "#6B7280"]
fig, ax = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax.pie(
    status_counts, labels=status_counts.index, autopct='%1.1f%%',
    colors=colors[:len(status_counts)], startangle=90,
    wedgeprops=dict(edgecolor='white', linewidth=2))
for t in autotexts: t.set_fontsize(11); t.set_fontweight('bold')
ax.set_title("Order Status Distribution", fontsize=14, pad=15)
plt.tight_layout()
plt.savefig(f"{FIGS}/03_order_status.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 4: Revenue by Region ─────────────────────────────
region_data = master.groupby("region").agg(
    revenue=("line_total","sum"),
    customers=("customer_id","nunique")
).reset_index().sort_values("revenue", ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].bar(region_data["region"], region_data["revenue"]/1e6, color=PALETTE)
axes[0].set_title("Revenue by Region", fontsize=12)
axes[0].set_ylabel("Revenue (₹M)")
axes[1].bar(region_data["region"], region_data["customers"], color=PALETTE)
axes[1].set_title("Unique Customers by Region", fontsize=12)
axes[1].set_ylabel("Customers")
plt.suptitle("Regional Performance", fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(f"{FIGS}/04_regional_analysis.png", dpi=150, bbox_inches="tight")
plt.close()

print("\nEDA complete. Figures saved to docs/figures/")
print("Run 02_rfm_segmentation.py next.")
