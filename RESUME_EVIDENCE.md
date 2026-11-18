# E-Commerce Sales & Customer Analytics — Resume Evidence Index
**Repository:** https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics
**Live Application:** https://ecomanalytics-dashboard.vercel.app/
**Verification Date:** 2026-11-18
**CI Test Status:** 235 Passing Tests (verified against the local venv run; same suite runs in GitHub Actions)

---

## 1. Resume Claim Verification Matrix

| # | Resume Claim | Canonical Metric Value | Target Population / Grain | Source / Implementation | Automated Test File | Documented Limitation |
|---|---|---|---|---|---|---|
| 1 | **Sales Revenue Analyzed** | ₹5.93 Cr (₹59,283,619.32) | 9,933 valid (Delivered + Processing) orders, 21,066 order lines | `python/eda/01_eda_preprocessing.py`, `sql/04_sales_analysis.sql` | `tests/test_dashboard_consistency.py`, `tests/test_data_quality.py` | Synthetic, seeded dataset generated from standard retail distributions. |
| 2 | **Customer Base** | 1,991 active customers | Distinct customers with ≥1 valid (Delivered/Processing) order, out of 2,000 customer records | `sql/05_customer_analysis.sql`, `data/processed/churn_features.csv` | `tests/test_data_quality.py` | Excludes the 8 customers whose every order was Cancelled/Returned (inactive by the documented definition). |
| 3 | **Product Catalog** | 150 SKUs across 5 categories, 40 subcategories | Active product dimension | `data/raw/products.csv`, `sql/06_product_analysis.sql` | `tests/test_data_quality.py` | Fixed synthetic product catalog. |
| 4 | **SQL Analytics Layer** | Schema + 11 analysis scripts (star schema, CTEs, window functions, cohorts, funnel, returns) | Analytical data mart over `data/raw/*` | `sql/01_…` through `sql/12_…` (usage in `sql/README.md`) | Constraints and metric definitions mirrored by `tests/test_data_quality.py`, `tests/test_decision_layer.py` | PostgreSQL syntax; the scripts are an analytical layer and are not executed by CI. |
| 5 | **Order Funnel Semantics** | 12,000 placed → 9,312 Delivered (77.6%) + 621 Processing (5.2%) + 844 Cancelled (7.0%) + 1,223 Returned (10.19% of placed) | All placed orders; statuses mutually exclusive | `data/metrics.json` (`order_funnel`), `sql/11_order_funnel.sql` | `tests/test_dashboard_consistency.py` | `Returned` is its own exit — never subtracted from `Delivered`. |
| 6 | **Cooling-Off / Win-Back Economics** | 441 medium-risk customers · ₹1.30 Cr historical spend · EV ₹523/contact · campaign EV ₹2.30L · break-even churn probability 12.54% | Churn-risk "Medium Risk" band | `python/pricing/winback.py`, `reports/winback_economics.json` | `tests/test_winback_economics.py` | Spend is historical; win-back recovery rates are simulated assumptions, not measured outcomes. |
| 7 | **Churn Model Integrity** | Leakage-free Logistic Regression selected by 5-fold CV (CV ROC-AUC 0.674 / holdout 0.662, PR-AUC 0.332); 5-origin rolling backtest AUC 0.56–0.67; OOF isotonic improves Brier 0.1726 → 0.1715, the 256-row slice overfits | Customer-level churn risk | `python/churn/03_churn_analysis.py`, `scripts/churn_data.py`, `scripts/churn_calibration.py` | `tests/test_churn_model_metrics.py`, `tests/test_churn_calibration.py` | Modest ranking power; a targeting tool, not a per-customer oracle. Calibration is sample-size sensitive and reported both ways. |
| 8 | **Discount Analysis** | No statistically significant overall quantity response (Kruskal-Wallis p = 0.305); break-even lift at 20% depth = +59.2%; a 10% discount cap recovers ₹6.45L margin (2.0% of total) | Order line items by discount depth | `python/pricing/elasticity.py`, `reports/discount_analysis.json` | `tests/test_discount_engine.py` | Observational data — measures association, not causality; assumes demand is otherwise fixed. |
| 9 | **Forecast Honesty** | Ensemble MASE 0.68 loses to the drift baseline (0.468); shipped bootstrap CI covers 9.5% of actuals; challenger `holt_linear` (MASE 0.375) beats drift under the same protocol | Monthly revenue series, 10 rolling origins | `scripts/forecast_backtest.py`, `scripts/forecast_challenger.py` | `tests/test_forecast_backtest.py`, `tests/test_forecast_challenger.py` | Short synthetic series; empirical uncertainty is understated and stated as such. |
| 10 | **NL-to-SQL Assistant** | 97.3% execution accuracy (36/37), refusals 100%, 0 fabricated numbers on unanswerable questions | Benchmark v1.1 — 37 retail questions, 4 classes, `mode=fallback` | `evals/run_eval.py`, `reports/ai_eval_report.md` | `tests/test_ai_eval.py`, `tests/test_nl_to_sql.py` | Benchmark scope is limited; answers are grounded in a verified fact sheet with refusals on out-of-scope questions. |
| 11 | **Reproducibility** | Seeded generator reproduces raw CSVs byte-identically; pipeline completes 8/8 steps; full suite green | Whole pipeline | `data/raw/generate_data.py`, `run_pipeline.py` | full `pytest` suite | Pipeline reruns produce benign last-ulp float diffs in `data/processed` CSVs. |
| 12 | **CI Footprint** | 243 tests + flake8 + evals gate (`--min-accuracy 0.90`) + dashboard byte-identity across 4 deployment copies | Every push / pull request | `.github/workflows/ci.yml` | GitHub Actions run history | Local runs should use the project venv (Python 3.14 global lacks pinned deps). |

---

## 2. Population & Order Status Hierarchy

```
Total Placed Orders: 12,000 (100.0%)
 ├── Cancelled:  844 (7.0%)    --> never transacted; excluded from revenue & margin
 ├── Returned: 1,223 (10.19%)  --> own exit (NOT subtracted from Delivered); excluded from revenue, analyzed in sql/08_return_analysis.sql
 └── Valid Population: 9,933 (82.8%)  --> revenue ₹59,283,619.32 · COGS ₹27,286,277.68 · margin 53.97%
      ├── Delivered:  9,312 (77.6%)  --> fully realized revenue
      └── Processing:   621 (5.2%)  --> in-flight committed pipeline revenue
```

Customer populations are reported on two clearly separated grains:
- **2,000** customer records in `customers.csv` (raw dimension).
- **1,991** active customers = distinct customers with ≥1 valid (Delivered/Processing) order. Of the 2,000 records, the remaining 9 are: 8 that placed only Cancelled/Returned orders and 1 with no orders at all — inactive by the documented definition in `data/metrics.json`.
