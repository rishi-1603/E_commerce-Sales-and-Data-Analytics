# TEST REPORT — E-Commerce
### Last full run: 2026-10-17 — 119/119 passed

| Suite | File | Pins |
|---|---|---|
| Data quality | test_data_quality.py | schema, ranges, referential integrity |
| Dashboard consistency | test_dashboard_consistency.py | every displayed figure == pipeline output |
| Churn calibration | test_churn_calibration.py | AUC, PR-AUC, Brier, slope, threshold, profits |
| Forecast backtest | test_forecast_backtest.py | MASE values, coverage, verdict flags |
| Decision layer | test_decision_layer.py | decision_layer.json contents |
| Discount engine | test_discount_engine.py | break-even band |
| NL-to-SQL | test_nl_to_sql.py | eval harness invariants |
| AI eval | test_ai_eval.py | benchmark results (97.3%, 0 fabricated) |

## How numbers are pinned
Each analysis writes `reports/*_metrics.json`; tests assert values against those
artifacts with tolerances chosen for cross-version stability (exact for structural
properties, ~rel 5% for profit figures, wider bins for ECE). Directional
invariants (calibration improves Brier; t* policy beats contact-all) are separate
tests, so a drifting float cannot silently pass a changed conclusion.

## CI
GitHub Actions (Python 3.11): flake8 -> pipeline -> churn_calibration ->
forecast_backtest -> pytest. Status at audit: **success**.

## Not covered (disclosed)
No load/performance tests (static dashboard); no browser automation; Streamlit
demos are checked manually (see docs/DEPLOYMENT_VERIFICATION.md).
