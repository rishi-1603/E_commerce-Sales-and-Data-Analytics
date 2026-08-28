"""
test_data_quality.py — Data quality checks for the E-Commerce Analytics pipeline.

Run after `python run_pipeline.py` has generated data/raw and data/processed:
    pytest tests/test_data_quality.py -v

These tests validate the same constraints implied by sql/01_database_schema.sql
(primary keys, foreign keys, non-null columns) plus a few business-logic
sanity checks (no negative amounts, valid categorical values, etc).
"""
import os
import pandas as pd
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
PROCESSED = os.path.join(BASE, "data", "processed")

VALID_ORDER_STATUSES = {"Delivered", "Returned", "Cancelled", "Processing"}


# ── Fixtures: load each CSV once per test session ──────────────────────────

@pytest.fixture(scope="session")
def customers():
    return pd.read_csv(os.path.join(RAW, "customers.csv"))


@pytest.fixture(scope="session")
def products():
    return pd.read_csv(os.path.join(RAW, "products.csv"))


@pytest.fixture(scope="session")
def orders():
    return pd.read_csv(os.path.join(RAW, "orders.csv"))


@pytest.fixture(scope="session")
def order_items():
    return pd.read_csv(os.path.join(RAW, "order_items.csv"))


# ── customers.csv ───────────────────────────────────────────────────────────

def test_customers_id_unique_and_not_null(customers):
    assert customers["customer_id"].notna().all(), "customer_id has null values"
    assert customers["customer_id"].is_unique, "customer_id has duplicates (violates PRIMARY KEY)"


def test_customers_email_unique_and_not_null(customers):
    assert customers["email"].notna().all(), "email has null values"
    assert customers["email"].is_unique, "email has duplicates (violates UNIQUE constraint)"


def test_customers_required_fields_not_null(customers):
    for col in ["first_name", "last_name"]:
        assert customers[col].notna().all(), f"{col} has null values (violates NOT NULL)"


def test_customers_age_is_reasonable(customers):
    ages = customers["age"].dropna()
    assert (ages >= 13).all() and (ages <= 100).all(), "age contains implausible values"


# ── products.csv ─────────────────────────────────────────────────────────

def test_products_id_unique_and_not_null(products):
    assert products["product_id"].notna().all(), "product_id has null values"
    assert products["product_id"].is_unique, "product_id has duplicates (violates PRIMARY KEY)"


def test_products_prices_are_positive(products):
    assert (products["cost_price"] > 0).all(), "cost_price contains zero/negative values"
    assert (products["selling_price"] > 0).all(), "selling_price contains zero/negative values"


def test_products_stock_qty_not_negative(products):
    assert (products["stock_qty"] >= 0).all(), "stock_qty contains negative values"


def test_products_rating_in_valid_range(products):
    ratings = products["rating"].dropna()
    assert (ratings >= 0).all() and (ratings <= 5).all(), "rating outside 0-5 range"


# ── orders.csv ───────────────────────────────────────────────────────────

def test_orders_id_unique_and_not_null(orders):
    assert orders["order_id"].notna().all(), "order_id has null values"
    assert orders["order_id"].is_unique, "order_id has duplicates (violates PRIMARY KEY)"


def test_orders_customer_id_references_valid_customer(orders, customers):
    valid_ids = set(customers["customer_id"])
    orphaned = ~orders["customer_id"].isin(valid_ids)
    assert not orphaned.any(), (
        f"{orphaned.sum()} orders reference a customer_id not present in "
        f"customers.csv (violates FOREIGN KEY)"
    )


def test_orders_status_is_valid_category(orders):
    bad = ~orders["status"].isin(VALID_ORDER_STATUSES)
    assert not bad.any(), (
        f"{bad.sum()} orders have a status outside {VALID_ORDER_STATUSES}: "
        f"{sorted(orders.loc[bad, 'status'].unique())}"
    )


def test_orders_discount_pct_in_valid_range(orders):
    discounts = orders["discount_pct"].dropna()
    assert (discounts >= 0).all() and (discounts <= 100).all(), \
        "discount_pct outside 0-100 range"


def test_orders_shipping_cost_not_negative(orders):
    assert (orders["shipping_cost"] >= 0).all(), "shipping_cost contains negative values"


# ── order_items.csv ─────────────────────────────────────────────────────

def test_order_items_id_unique_and_not_null(order_items):
    assert order_items["item_id"].notna().all(), "item_id has null values"
    assert order_items["item_id"].is_unique, "item_id has duplicates (violates PRIMARY KEY)"


def test_order_items_order_id_references_valid_order(order_items, orders):
    valid_ids = set(orders["order_id"])
    orphaned = ~order_items["order_id"].isin(valid_ids)
    assert not orphaned.any(), (
        f"{orphaned.sum()} order_items reference an order_id not present in "
        f"orders.csv (violates FOREIGN KEY)"
    )


def test_order_items_product_id_references_valid_product(order_items, products):
    valid_ids = set(products["product_id"])
    orphaned = ~order_items["product_id"].isin(valid_ids)
    assert not orphaned.any(), (
        f"{orphaned.sum()} order_items reference a product_id not present in "
        f"products.csv (violates FOREIGN KEY)"
    )


def test_order_items_quantity_is_positive(order_items):
    assert (order_items["quantity"] > 0).all(), "quantity contains zero/negative values"


def test_order_items_line_total_is_positive(order_items):
    assert (order_items["line_total"] > 0).all(), "line_total contains zero/negative values"


def test_order_items_cost_total_not_negative(order_items):
    assert (order_items["cost_total"] >= 0).all(), "cost_total contains negative values"


# ── data/processed outputs (what the dashboards actually read) ─────────────

@pytest.mark.skipif(
    not os.path.exists(os.path.join(PROCESSED, "rfm_segments.csv")),
    reason="rfm_segments.csv not generated yet — run the pipeline first",
)
def test_rfm_segments_customer_id_unique_and_not_null():
    rfm = pd.read_csv(os.path.join(PROCESSED, "rfm_segments.csv"))
    assert rfm["customer_id"].notna().all(), "customer_id has null values in rfm_segments.csv"
    assert rfm["customer_id"].is_unique, "customer_id has duplicates in rfm_segments.csv"


@pytest.mark.skipif(
    not os.path.exists(os.path.join(PROCESSED, "churn_features.csv")),
    reason="churn_features.csv not generated yet — run the pipeline first",
)
def test_churn_features_probability_in_valid_range():
    churn = pd.read_csv(os.path.join(PROCESSED, "churn_features.csv"))
    prob_cols = [c for c in churn.columns if "prob" in c.lower()]
    for col in prob_cols:
        vals = churn[col].dropna()
        assert (vals >= 0).all() and (vals <= 1).all(), f"{col} outside 0-1 probability range"


@pytest.mark.skipif(
    not os.path.exists(os.path.join(PROCESSED, "clv.csv")),
    reason="clv.csv not generated yet — run the pipeline first",
)
def test_clv_non_negative_and_ranked():
    """Predictive CLV must be non-negative and every value tier assigned."""
    clv = pd.read_csv(os.path.join(PROCESSED, "clv.csv"))
    assert clv["pred_clv"].notna().all(), "pred_clv has nulls"
    assert (clv["pred_clv"] >= 0).all(), "pred_clv contains negative values"
    assert clv["value_tier"].notna().all(), "value_tier has nulls"


@pytest.mark.skipif(
    not os.path.exists(os.path.join(PROCESSED, "revenue_forecast.csv")),
    reason="revenue_forecast.csv not generated yet — run the pipeline first",
)
def test_forecast_ci_brackets_point_estimate():
    """Bootstrap CI must correctly bracket the ensemble point estimate."""
    fc = pd.read_csv(os.path.join(PROCESSED, "revenue_forecast.csv"))
    assert (fc["ci_lo_95"] <= fc["ensemble_forecast"]).all(), "CI lower > point estimate"
    assert (fc["ensemble_forecast"] <= fc["ci_hi_95"]).all(), "CI upper < point estimate"
