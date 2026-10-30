# E-Commerce Sales & Customer Analytics — Resume Evidence Index
**Repository:** https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics  
**Live Application:** https://ecomanalytics-dashboard.vercel.app/  
**Verification Date:** 2026-10-30  
**CI Test Status:** 195 Passing Tests (100% Passing)

---

## 1. Resume Claim Verification Matrix

| # | Resume Claim | Canonical Metric Value | Target Population / Grain | Source File / Implementation | Reproduction Command | Automated Test File | Documented Limitation |
|---|---|---|---|---|---|---|---|
| 1 | **Sales Revenue Analyzed** | Rs. 5.93 Cr (Rs. 59,328,412.50) | 9,933 Delivered & Processing orders | sql/01_revenue_overview.sql, src/metrics.py | python -m src.metrics --metric revenue | 	ests/test_dashboard_consistency.py | Synthetic dataset generated based on standard retail distributions. |
| 2 | **Customer Base** | 1,991 Unique Customers | Unique customer IDs in valid orders | sql/02_customer_segmentation.sql | python -m src.metrics --metric customers | 	ests/test_data_quality.py | Excludes customer records with zero valid completed orders. |
| 3 | **Product Catalog** | 150 SKUs across 8 Categories | Active product dimension | sql/03_product_profitability.sql | python -m src.metrics --metric skus | 	ests/test_data_quality.py | Fixed synthetic product catalog. |
| 4 | **SQL Analytics Layer** | 8 Core Scripts, 45+ Queries | Analytical data mart queries | sql/01_ through sql/08_ | psql -f sql/run_all.sql | 	ests/test_decision_layer.py | Queries optimized for PostgreSQL / DuckDB syntax. |
| 5 | **SQL vs Pandas Parity** | 100% Numerical Parity | Revenue, AOV, MoM, Margins | src/reconciliation.py | python -m src.reconciliation | 	ests/test_dashboard_consistency.py | Discrepancies bounded at < Rs. 0.01 floating-point precision. |
| 6 | **Cooling-Off Customers** | 448 Customers (Rs. 1.24 Cr historical spend) | Recency > 90 days, spend > median | sql/05_customer_churn_cohorts.sql | python -m src.churn_analysis | 	ests/test_winback_economics.py | Spend is historical; win-back recovery is simulated potential. |
| 7 | **Target Leakage Correction** | Forward-time validation split (AUC 0.65) | Churn modeling observation window | src/churn_model.py | python -m src.churn_model --eval | 	ests/test_churn_calibration.py | Random K-Fold splits produce inflated AUC (0.89) due to lookahead bias. |
| 8 | **Discount Price Elasticity** | Discount erosion of Rs. 16.45L margin | 150 SKUs, elasticity vs discount depth | src/pricing_engine.py | python -m src.pricing_engine | 	ests/test_discount_engine.py | Assumes fixed demand elasticity under non-promotional baseline. |
| 9 | **NL-to-SQL Assistant** | 97.3% execution accuracy (36/37) | 37 benchmark retail questions | src/nl_to_sql.py | python -m src.eval_nl_to_sql | 	ests/test_nl_to_sql.py | Zero hallucinations; 1 failed query is a complex multi-nested subquery. |
| 10 | **Automated CI Footprint** | 195 Passing Tests | Unit, regression, API, & schema tests | 	ests/ directory | python -m pytest | GitHub Actions workflow .github/workflows/ci.yml | Requires statsmodels, pandas, fastapi, pytest. |

---

## 2. Population & Order Status Hierarchy

`
Total Generated Orders: 12,000 (100.0%)
 ├── Excluded: Cancelled Orders: 1,042 (8.68%)  --> Excluded from Revenue & Margin calculations
 ├── Excluded: Returned Orders:  1,025 (8.54%)  --> Evaluated separately in Return Rate analytics
 └── Retained Valid Population: 9,933 (82.78%)
      ├── Delivered Orders:   8,421 (70.18%)   --> Full realized revenue & customer loyalty
      └── Processing Orders:  1,512 (12.60%)   --> In-flight committed pipeline revenue
`
