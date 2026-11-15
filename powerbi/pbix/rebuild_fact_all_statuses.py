"""Rebuild Fact_Orders.csv with ALL order statuses (Delivered/Processing/Returned/Cancelled).

The Power BI model must be able to show the real order-status mix, not just the
revenue-valid population. Revenue measures already filter to Delivered+Processing,
so adding Returned/Cancelled rows cannot move any revenue KPI. This script proves
that by reconciling the Delivered+Processing subset against the previous export.
"""
import os

import pandas as pd

BASE = r"C:\Users\user\portfolio-roadmaps\repos\ecom"
HERE = os.path.join(BASE, "powerbi", "pbix")
OUT = os.path.join(HERE, "data")

orders = pd.read_csv(os.path.join(BASE, "data", "raw", "orders.csv"))
items = pd.read_csv(os.path.join(BASE, "data", "raw", "order_items.csv"))
products = pd.read_csv(os.path.join(BASE, "data", "raw", "products.csv"))

print("raw orders:", len(orders), "| raw items:", len(items),
      "| item orders:", items["order_id"].nunique())

cost = products.set_index("product_id")["cost_price"]

df = items.merge(orders[["order_id", "order_date", "status", "customer_id",
                         "payment_method", "shipping_cost"]], on="order_id", how="left")
assert df["status"].notna().all(), "orphan order_items rows"

df["unit_cost"] = df["product_id"].map(cost)
assert df["unit_cost"].notna().all(), "missing product cost"

# Match the pipeline exactly: discount is applied to the unit price (rounded to
# paise), then multiplied by quantity. Do NOT round the line total from the
# unrounded unit price — that drifts by a few rupees across 21k rows.
df["final_price"] = (df["unit_price"] * (1 - df["discount_pct"])).round(2)
df["order_item_total"] = (df["final_price"] * df["quantity"]).round(2)
df["cost_total"] = (df["quantity"] * df["unit_cost"]).round(2)
df["profit"] = (df["order_item_total"] - df["cost_total"]).round(2)

fact = pd.DataFrame({
    "item_id": df["item_id"],
    "order_id": df["order_id"],
    "order_date": pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m-%d"),
    "order_status": df["status"],
    "customer_id": df["customer_id"],
    "product_id": df["product_id"],
    "quantity": df["quantity"].astype(int),
    "unit_price": df["unit_price"].astype(float),
    "discount_pct": df["discount_pct"].astype(float),
    "order_item_total": df["order_item_total"].astype(float),
    "cost_total": df["cost_total"].astype(float),
    "profit": df["profit"].astype(float),
    "payment_method": df["payment_method"],
    "shipping_cost": df["shipping_cost"].astype(float),
})

# ---- reconciliation against the previous (valid-orders-only) export ----
prev_path = os.path.join(OUT, "Fact_Orders.csv")
prev = pd.read_csv(prev_path)
prev_valid = prev[prev["order_status"].isin(["Delivered", "Processing"])]
new_valid = fact[fact["order_status"].isin(["Delivered", "Processing"])]

print("\n--- reconciliation: Delivered+Processing subset ---")
for label, a, b in [
    ("rows", len(prev_valid), len(new_valid)),
    ("orders", prev_valid["order_id"].nunique(), new_valid["order_id"].nunique()),
    ("revenue", round(prev_valid["order_item_total"].sum(), 2), round(new_valid["order_item_total"].sum(), 2)),
    ("cogs", round(prev_valid["cost_total"].sum(), 2), round(new_valid["cost_total"].sum(), 2)),
    ("profit", round(prev_valid["profit"].sum(), 2), round(new_valid["profit"].sum(), 2)),
]:
    flag = "OK " if a == b else "MISMATCH"
    print(f"  {flag:9} {label:8} previous={a}  new={b}")
    assert a == b, f"{label} mismatch"

print("\n--- full status mix ---")
print(fact.groupby("order_status").agg(
    item_rows=("item_id", "size"),
    orders=("order_id", "nunique"),
).to_string())
print("\nfull revenue (all statuses):", round(fact["order_item_total"].sum(), 2))
print("valid revenue:", round(new_valid["order_item_total"].sum(), 2))
print("valid profit:", round(new_valid["profit"].sum(), 2))
print("valid margin %:", round(new_valid["profit"].sum() / new_valid["order_item_total"].sum() * 100, 2))

fact.to_csv(prev_path, index=False, encoding="utf-8")
print("\nwrote", prev_path, len(fact), "rows")
