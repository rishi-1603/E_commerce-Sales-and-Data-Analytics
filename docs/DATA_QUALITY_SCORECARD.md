# Enterprise Data Quality Scorecard
**Audit Date:** 2026-10-30  
**Scope:** Raw ingestion layer (12,000 order headers / 25,384 order lines) -> verified analytical revenue layer (9,933 Delivered + Processing orders)

---

## 1. Audit Summary Matrix

| Integrity Check Category | Raw Count / Test Space | Anomalies Detected | Cleansing / Reconciliation Action | Post-Cleansing State | Status |
|---|---|---|---|---|---|
| **Primary Key Uniqueness** | 25,384 order-line rows | 0 duplicate `item_id` values | Enforced unique item identifier; `(order_id, product_id)` is also unique in this generated dataset | 100% Unique | PASS |
| **Foreign Key Referencing** | 25,384 order lines | 0 orphan keys | Verified all order, customer and product references exist in their dimensions | 100% Valid | PASS |
| **Negative Price / Quantity** | 25,384 order lines | 0 negative values | Validated `unit_price > 0` and `quantity > 0` | 100% Positive | PASS |
| **Status Classification** | 12,000 orders | 2,067 non-revenue rows | Categorized into Cancelled (844) and Returned (1,223); excluded from revenue measures | 9,933 Revenue-eligible Orders | PASS |
| **Date Boundary Validation** | 12,000 orders | 0 future dates | Asserted `order_date <= CURRENT_DATE` and `order_date >= '2023-01-01'` | 100% Compliant | PASS |
| **Discount Boundary Sanity** | 12,000 orders | 0 invalid discounts | Asserted `0.0 <= discount_percent <= 0.50` | 100% Compliant | PASS |
| **SQL-Pandas Calculation Parity** | 10 core commercial KPIs | 0 discrepant values | Cross-calculated in DuckDB/PostgreSQL vs Pandas | 100% Parity | PASS |
