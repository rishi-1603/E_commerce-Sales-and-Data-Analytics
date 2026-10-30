# Independent data, SQL and statistical validation

Audit date: 2026-10-30. Calculations below were rebuilt from CSVs without importing project metric functions, then compared with PostgreSQL execution. Reproduction scripts and detailed machine output are included in the external audit evidence pack.

## Independent calculations
```json
{
  "raw_orders": 12000,
  "raw_order_lines": 25384,
  "joined_lines": 25384,
  "valid_orders": 9933,
  "valid_order_lines": 21066,
  "revenue": 59283619.32,
  "profit": 31997341.64,
  "aov": 5968.35,
  "purchasing_customers": 1991,
  "status_counts": {
    "Delivered": 9312,
    "Returned": 1223,
    "Cancelled": 844,
    "Processing": 621
  },
  "quantity_discount_kw_H": 4.8342,
  "quantity_discount_kw_p": 0.304733,
  "cohorts": 36,
  "independent_forecast_origin_scaled_mean": {
    "drift": 0.4393,
    "holt_linear": 0.3533
  },
  "independent_forecast_published_aggregation": {
    "drift": 0.4681,
    "holt_linear": 0.3752
  },
  "statistical_scope": "Exploratory observational comparisons; challenger selection reuses evaluation origins, so not an untouched confirmation set."
}
```

## Actual PostgreSQL execution
PostgreSQL scripts executed without dialect translation

| File | Executed statements | Failures |
|---|---:|---:|
| 01_database_schema.sql | 16 | 0 |
| 02_data_cleaning.sql | 8 | 0 |
| 03_kpi_analysis.sql | 5 | 0 |
| 04_sales_analysis.sql | 8 | 0 |
| 05_customer_analysis.sql | 8 | 0 |
| 06_product_analysis.sql | 6 | 0 |
| 07_regional_analysis.sql | 5 | 0 |
| 08_return_analysis.sql | 6 | 0 |
| 09_cohort_retention.sql | 2 | 0 |
| 10_mom_variance.sql | 2 | 0 |
| 11_order_funnel.sql | 3 | 0 |
| 12_discount_margin.sql | 6 | 0 |

## Forecast aggregation and selection
The published comparison divides pooled MAE by the mean seasonal-naive in-sample scale across origins. Independent replication produces drift 0.4681 and holt_linear 0.3752. Averaging origin-scaled errors instead gives 0.4393 and 0.3533; these are different aggregation conventions, not competing versions of the same number.
All forecasts use only past data at each origin. Challenger selection uses those same origins, so a separate untouched confirmation period would be needed before a prospective performance claim.
There are 36 first-purchase cohorts in the source reconstruction. The dashboard intentionally displays the most recent 18; these counts have different scopes.
Kruskal–Wallis p≈0.304733 reproduces the rounded .305. This is observational, synthetic data and does not estimate a causal discount effect.
