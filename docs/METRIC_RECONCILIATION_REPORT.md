# Metric Reconciliation Report

> **Historical snapshot (2026-11-19).** The 273-test evidence below describes that
> audit commit. Current suite: **284 tests**; current KPI values live in
> `data/metrics.json`.

**Date:** 2026-11-19<br>
**Scope:** synthetic, seeded INR dataset; raw-CSV reconciliation, recorded automated-test evidence, recorded live-dashboard evidence, and PostgreSQL verification boundaries.

## Status and evidence standard

- **VERIFIED** — supported by the named evidence at the stated precision.
- **FAILED-UNRESOLVED** — a contradiction remains open.
- **NOT VERIFIED** — the required execution or evidence is unavailable; source review alone is not execution.

| Evidence layer | Result | Boundary |
|---|---|---|
| Independent raw recomputation | **VERIFIED** | Two independent supplied scripts were run against raw CSVs, then cross-checked with a separate read-only `Decimal` calculation. No project metric function was used. |
| Automated-test evidence | **VERIFIED** | Recorded evidence is 273/273 locally and GitHub Actions `test` = success. Pytest was not rerun for this document. |
| Live display evidence | **VERIFIED** at displayed rounding | Recorded 2026-11-19 result: 96/96 browser checks and 22/22 chart-series reconciliations. No new browser run or stronger current-live claim is made here. |
| PostgreSQL runtime execution | **NOT VERIFIED** | Local PG 17 SCRAM authentication requires an unavailable password; SQL source review is not execution. |
| Narrative crore conversions in `README.md`, `reports/assumptions_and_limitations.md`, and `docs/AUDIT_2026-11-18.md` | **VERIFIED — fixed** | The figures previously said “₹59.28 Cr” and “₹55.49 Cr”, ten times the exact ₹59,283,619.32 = **₹5.928361932 Cr** and ₹55,492,687.66 = **₹5.549268766 Cr**. All three surfaces now use **₹5.93 Cr** and **₹5.55 Cr** as applicable; logged as fixed P0 DOC-04 in `QA_REMEDIATION_LOG.md`. |

## 1. Raw grain and eligible population

Direct reads of [`orders.csv`](../data/raw/orders.csv), [`order_items.csv`](../data/raw/order_items.csv), [`customers.csv`](../data/raw/customers.csv), and [`products.csv`](../data/raw/products.csv) gave:

| Entity | Raw rows | Reconciliation |
|---|---:|---|
| Orders | **12,000** | One mutually exclusive status per `order_id` |
| Order lines | **25,384** | Join to orders retains 25,384 lines: no join multiplication |
| Customers | **2,000** | 2,000 unique `customer_id` values |
| Products | **150** | 150 unique `product_id` values across 5 categories |

Revenue eligibility is `status IN ('Delivered','Processing')`, matching [`metrics.json`](../data/metrics.json), [`02_data_cleaning.sql`](../sql/02_data_cleaning.sql), and [`04_sales_analysis.sql`](../sql/04_sales_analysis.sql):

- Eligible orders = 9,312 Delivered + 621 Processing = **9,933**.
- Eligible lines = **21,066** of 25,384 raw lines.
- Cancelled and Returned orders are excluded from booked revenue.

## 2. Headline KPI reconciliation

Formulas were evaluated from raw order lines after joining `order_items.order_id → orders.order_id`.

| Metric | Formula and exact independent result | Registry/display reconciliation | Status |
|---|---|---|---|
| Revenue | `Σ line_total` over Delivered + Processing = **₹59,283,619.32**; `59,283,619.32 / 10,000,000 = 5.928361932 Cr` | [`claims.json`](../data/claims.json) and [`metrics.json`](../data/metrics.json): **₹5.93 Cr**; exact claim value agrees | **VERIFIED** |
| COGS | `Σ cost_total` over the same 21,066 lines = **₹27,286,277.68** | Exact raw and documented values agree | **VERIFIED** |
| Gross profit | `59,283,619.32 − 27,286,277.68 = ₹31,997,341.64` | **₹3.20 Cr** at live-card precision | **VERIFIED** |
| Gross margin | `31,997,341.64 / 59,283,619.32 × 100 = 53.9733%` | **53.97%** at 2 dp; **54.0%** at 1 dp | **VERIFIED** |
| AOV | `59,283,619.32 / 9,933 eligible orders = ₹5,968.3499` | **₹5,968.35** at 2 dp; **₹5,968** on the live card | **VERIFIED** |
| Active customers | Distinct customers with ≥1 Delivered/Processing order = **1,991** | Registry and live card agree | **VERIFIED** |

Recorded test evidence: [`test_claims_registry.py`](../tests/test_claims_registry.py) exactly pins the revenue claim to ₹59,283,619.32 and independently recomputes it from raw CSVs; [`test_dashboard_consistency.py`](../tests/test_dashboard_consistency.py) pins dashboard data to processed outputs. [`TEST_REPORT.md`](TEST_REPORT.md) records 273/273 locally, while [`COMPLETE_PROJECT_QA_REPORT.md`](COMPLETE_PROJECT_QA_REPORT.md) §J records CI run `44496785646`, job `135465903572`, as successful.

## 3. Mutually exclusive statuses and value bridge

| Status | Orders | Share of 12,000 placed | Raw line value | Revenue treatment |
|---|---:|---:|---:|---|
| Delivered | **9,312** | 77.6000% | **₹55,492,687.66** | Included |
| Processing | **621** | 5.1750% (5.2% displayed) | **₹3,790,931.66** | Included |
| Cancelled | **844** | 7.0333% | — | Excluded |
| Returned | **1,223** | 10.1917% | **₹7,234,984.25** | Excluded; analytic line value only, **not booked revenue** |
| **Total placed** | **12,000** | **100%** | **₹71,489,098.20** across all statuses | All-placed value is not the revenue KPI |

Revenue bridge: **₹55,492,687.66 Delivered-only + ₹3,790,931.66 Processing = ₹59,283,619.32**.

Return rate on the placed-order denominator:

```text
1,223 / 12,000 × 100 = 10.191666…% → 10.19% at 2 dp → 10.2% at 1 dp
```

The **10.2%** live display is therefore consistent with the raw calculation. Most importantly, statuses are mutually exclusive: **Returned is never subtracted from Delivered**. The 1,223 Returned orders are their own exit; Delivered remains 9,312. See [`11_order_funnel.sql`](../sql/11_order_funnel.sql) and [`claims.json`](../data/claims.json).

## 4. Customer-population reconciliation

| Step | Count |
|---|---:|
| Registered customer records | **2,000** |
| Customers appearing in orders | **1,999** |
| Customers with ≥1 Delivered/Processing order | **1,991** |
| Ordering customers with only Cancelled/Returned orders | **8** — 4 Returned-only, 2 Cancelled-only, 2 with both |
| Registered customers who placed no orders | **1** |

Thus `1,999 − 8 = 1,991`, and `2,000 − 1,999 = 1` never ordered. The eight are not missing records; they are inactive under the documented revenue-eligible definition. This matches [`metrics.json`](../data/metrics.json) and the population hierarchy in [`RESUME_EVIDENCE.md`](../RESUME_EVIDENCE.md). **VERIFIED** by both independent scripts and the `Decimal` cross-check.

## 5. Category and customer-segment reconciliation

### Exact category totals — Delivered + Processing only

Each category uses `revenue = Σ line_total`, `COGS = Σ cost_total`, `profit = revenue − COGS`, and `margin = profit / revenue × 100`.

| Category | Revenue (INR) | COGS (INR) | Gross profit (INR) | Margin |
|---|---:|---:|---:|---:|
| Sports | 13,898,423.41 | 6,039,381.80 | 7,859,041.61 | 56.5463% |
| Electronics | 13,631,986.91 | 6,342,610.00 | 7,289,376.91 | 53.4726% |
| Clothing | 12,657,101.96 | 5,714,419.95 | 6,942,682.01 | 54.8521% |
| Home & Garden | 11,606,496.68 | 5,245,679.47 | 6,360,817.21 | 54.8039% |
| Beauty | 7,489,610.36 | 3,944,186.46 | 3,545,423.90 | 47.3379% |
| **Total** | **59,283,619.32** | **27,286,277.68** | **31,997,341.64** | **53.9733%** |

**VERIFIED** from raw order lines joined to products; the totals reconcile exactly to the headline. The web [`DATA` block](../dashboard/dashboard.html) stores whole-rupee truncations for `cat_revenue`/`cat_profit` and one-decimal margins, so the exact penny-level bridge is the table above, not a sum of truncated chart components. [`test_dashboard_consistency.py`](../tests/test_dashboard_consistency.py) applies a documented 1% category-tolerance test; the separately recorded live evidence reconciled 22/22 chart series.

### Customer segments

The eligible raw-CSV recomputation gives:

| Segment | Active customers | Revenue (INR) |
|---|---:|---:|
| B2B | **403** | **12,398,153.11** |
| B2C | **1,379** | **40,690,692.59** |
| Enterprise | **209** | **6,194,773.62** |
| **Total** | **1,991** | **59,283,619.32** |

**VERIFIED** from raw orders, lines, and customers; these exact values also match the rendered Power BI evidence recorded in [`AUDIT_2026-11-18.md`](AUDIT_2026-11-18.md) §9. Do not confuse them with the full raw dimension: all 2,000 customer records comprise **B2C 1,387 + B2B 403 + Enterprise 210**. The eligible population excludes eight B2C records and one Enterprise record, yielding the 1,991 active customers above.

The derived RFM artifact also reconciles exactly: **Loyal Customers 495, About To Sleep 354, Champions 317, Recent Customers 248, At Risk 221, Needs Attention 194, Lost Customers 133, Potential Loyalists 29 = 1,991**. These counts agree across [`rfm_segments.csv`](../data/processed/rfm_segments.csv), [`metrics.json`](../data/metrics.json), and the dashboard `DATA` block. This is **VERIFIED** at processed-artifact/test/live-evidence level, not claimed as a raw-CSV RFM recomputation; the master QA report records `chart:seg_values` max diff 0.

## 6. Data-quality checks independently recomputed

The separate `Decimal` pass checked every raw row and all three foreign-key relationships.

| Check | Independent result | Status |
|---|---:|---|
| Duplicate PKs: `order_id`, `item_id`, `customer_id`, `product_id` | **0 each** | **VERIFIED** |
| Null cells across all four raw CSVs | **0** | **VERIFIED** |
| Orphans: order→customer, item→order, item→product | **0 each** | **VERIFIED** |
| Nonpositive `line_total` | **0** | **VERIFIED** |
| Negative `cost_total` | **0** | **VERIFIED** |
| Nonpositive quantities / product selling prices | **0 / 0** | **VERIFIED** |
| Statuses outside Delivered, Processing, Cancelled, Returned | **0** | **VERIFIED** |
| Raw line discounts outside **0–0.2**, across all 25,384 lines | **0** | **VERIFIED** |

The corresponding repository checks are in [`test_data_quality.py`](../tests/test_data_quality.py) and [`02_data_cleaning.sql`](../sql/02_data_cleaning.sql). Their presence is supporting test/source evidence; the zero counts above come from the independent raw recomputation.

## 7. Live-display and PostgreSQL boundaries

- **Live display — VERIFIED from recorded evidence, not a fresh run.** [`DASHBOARD_TEST_REPORT.md`](DASHBOARD_TEST_REPORT.md) and [`COMPLETE_PROJECT_QA_REPORT.md`](COMPLETE_PROJECT_QA_REPORT.md) record 96/96 Chromium/Firefox/WebKit checks, 12 pages, 15 charts, 0 console errors, and 22/22 chart-series reconciliations on 2026-11-19. [`TEST_REPORT.md`](TEST_REPORT.md) identifies this as a standalone suite, separate from the 273 pytest tests. The earlier real-browser readback in [`AUDIT_2026-11-18.md`](AUDIT_2026-11-18.md) §10 specifically records the 10.2% return-rate display. This report does not claim any additional live measurements.
- **PostgreSQL — NOT VERIFIED.** The recorded local PG 17 attempt requires `scram-sha-256`; no password was available and `psql -w` failed with `fe_sendauth`. The 12 SQL files / 75 statements received static source review, but parsing/source inspection is not runtime execution. The older [`DATA_AND_METRIC_VALIDATION.md`](DATA_AND_METRIC_VALIDATION.md) execution account is dated 2026-10-30 and does not establish a successful 2026-11-19 local runtime run. See [`COMPLETE_PROJECT_QA_REPORT.md`](COMPLETE_PROJECT_QA_REPORT.md) §K and [`TEST_REPORT.md`](TEST_REPORT.md) “Not covered.”

## Reproduction evidence

Independent scripts executed read-only from the repository root:

- `C:\Users\user\AppData\Local\Temp\opencode\kpi_audit.py` — pandas/SciPy raw-CSV audit.
- `C:\Users\user\AppData\Local\Temp\opencode\audit_kpis.py` — separate standard-library CSV implementation.
- A third inline standard-library `Decimal` cross-check supplied exact decimal totals, all-PK/FK/data-quality checks, and the category/segment bridges above; it wrote no artifact.

Primary semantic references: [`metrics.json`](../data/metrics.json), [`claims.json`](../data/claims.json), [`COMPLETE_PROJECT_QA_REPORT.md`](COMPLETE_PROJECT_QA_REPORT.md), and [`QA_REMEDIATION_LOG.md`](QA_REMEDIATION_LOG.md). All three DOC-04 narrative surfaces were corrected and verified; no unresolved mismatch remains in the scoped raw metrics, test evidence, corrected revenue comparisons, or recorded live displays.
