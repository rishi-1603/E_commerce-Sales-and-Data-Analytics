"""
churn_data.py — single source of truth for the churn dataset
============================================================
Two definitions, both from data/metrics.json, deliberately kept separate:

  * ACTIVITY / label: a "purchase" is an order with status Delivered or
    Returned (Cancelled never transacted; Processing is not yet a purchase).
    This is the same purchase definition used by cohort retention and the
    win-back experiment baselines.
  * VALUE features: revenue uses the project revenue convention —
    master_orders.csv (Delivered + Processing) — so a customer's historical
    spend matches every other revenue figure in the repo.

Features are computed strictly before the cutoff; the label is "no purchase
in the 180 days after the cutoff". Both churn scripts import this module so
the two definitions cannot drift apart.

Run: imported by python/churn/03_churn_analysis.py and
     scripts/churn_calibration.py (not a standalone script).
"""
from __future__ import annotations

import os

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
RAW = os.path.join(BASE, "data", "raw")

PURCHASE_STATUSES = ("Delivered", "Returned")
HORIZON_DAYS = 180

FEATURES = [
    "total_orders", "total_revenue", "avg_order_value", "total_items",
    "avg_discount", "unique_categories", "recency_days", "tenure_days",
    "order_frequency", "avg_days_between", "age",
    "segment_enc", "region_enc", "acquisition_channel_enc", "gender_enc",
]


def load_purchase_lines() -> pd.DataFrame:
    """Line-level frame of orders that transacted (Delivered or Returned)."""
    orders = pd.read_csv(os.path.join(RAW, "orders.csv"), parse_dates=["order_date"])
    items = pd.read_csv(os.path.join(RAW, "order_items.csv"))
    products = pd.read_csv(os.path.join(RAW, "products.csv"))

    purchases = orders[orders["status"].isin(PURCHASE_STATUSES)]
    return (
        items.merge(
            purchases[["order_id", "customer_id", "order_date", "status"]],
            on="order_id", how="inner")
        .merge(products[["product_id", "category"]], on="product_id", how="left")
    )


def build_churn_frame(cutoff: pd.Timestamp | None = None) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Eligible customers (purchased before cutoff) with features + label."""
    from sklearn.preprocessing import LabelEncoder

    master = pd.read_csv(os.path.join(PROC, "master_orders.csv"), parse_dates=["order_date"])
    customers = pd.read_csv(os.path.join(RAW, "customers.csv"),
                            parse_dates=["registration_date"])
    lines = load_purchase_lines()

    data_end = master["order_date"].max()
    if cutoff is None:
        cutoff = data_end - pd.Timedelta(days=HORIZON_DAYS)

    past_lines = lines[lines["order_date"] < cutoff]
    past_value = master[master["order_date"] < cutoff]
    future = lines[lines["order_date"] >= cutoff]

    activity = past_lines.groupby("customer_id").agg(
        total_orders=("order_id", "nunique"),
        total_items=("quantity", "sum"),
        unique_categories=("category", "nunique"),
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
    )
    value = past_value.groupby("customer_id").agg(
        total_revenue=("line_total", "sum"),
        avg_order_value=("line_total", "mean"),
        avg_discount=("discount_pct_x", "mean"),
    )

    feat = activity.join(value, how="left").reset_index()
    for col in ("total_revenue", "avg_order_value", "avg_discount"):
        feat[col] = feat[col].fillna(0.0)

    feat["recency_days"] = (cutoff - feat["last_order_date"]).dt.days
    feat["tenure_days"] = (cutoff - feat["first_order_date"]).dt.days
    feat["order_frequency"] = feat["total_orders"] / (feat["tenure_days"] / 30).clip(lower=1)
    feat["avg_days_between"] = feat["tenure_days"] / feat["total_orders"].clip(lower=1)

    feat = feat.merge(
        customers[["customer_id", "segment", "region", "acquisition_channel", "age", "gender"]],
        on="customer_id", how="left")

    le = LabelEncoder()
    for col in ["segment", "region", "acquisition_channel", "gender"]:
        feat[col + "_enc"] = le.fit_transform(feat[col].fillna("Unknown"))

    eligible = set(feat["customer_id"])
    future_buyers = set(future["customer_id"]) & eligible
    feat["churned"] = (~feat["customer_id"].isin(future_buyers)).astype(int)
    return feat, cutoff
