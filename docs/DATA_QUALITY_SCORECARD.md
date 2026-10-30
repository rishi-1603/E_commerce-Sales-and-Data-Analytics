# Enterprise Data Quality Scorecard
**Audit Date:** 2026-10-30  
**Scope:** Raw Ingestion Layer (12,000 Transactions) -> Verified Analytical Layer (9,933 Transactions)

---

## 1. Audit Summary Matrix

| Integrity Check Category | Raw Count / Test Space | Anomalies Detected | Cleansing / Reconciliation Action | Post-Cleansing State | Status |
|---|---|---|---|---|---|
| **Primary Key Uniqueness** | 12,000 order item rows | 0 duplicates | Enforced unique composite key `(order_id, product_id)` | 100% Unique | PASS |
| **Foreign Key Referencing** | 12,000 order items | 0 orphan keys | Verified all `customer_id` and `product_id` exist in dimension tables | 100% Valid | PASS |
| **Negative Price / Quantity** | 12,000 order items | 0 negative values | Enforced `CHECK (unit_price > 0 AND quantity > 0)` | 100% Positive | PASS |
| **Status Classification** | 12,000 orders | 2,067 non-revenue rows | Categorized into Cancelled (1,042) and Returned (1,025); filtered out from revenue mart | 9,933 Valid Orders | PASS |
| **Date Boundary Validation** | 12,000 orders | 0 future dates | Asserted `order_date <= CURRENT_DATE` and `order_date >= '2023-01-01'` | 100% Compliant | PASS |
| **Discount Boundary Sanity** | 12,000 orders | 0 invalid discounts | Asserted `0.0 <= discount_percent <= 0.50` | 100% Compliant | PASS |
| **SQL-Pandas Calculation Parity** | 10 core commercial KPIs | 0 discrepant values | Cross-calculated in DuckDB/PostgreSQL vs Pandas | 100% Parity | PASS |
