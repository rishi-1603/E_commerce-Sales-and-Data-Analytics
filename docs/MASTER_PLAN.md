# MASTER PLAN — E-Commerce Sales & Customer Analytics
### Portfolio project · week of 2026-10-15 · status: COMPLETE

## Objective
A decision-layer analytics product over a synthetic retail dataset (12,000 orders):
RFM, cohorts, churn scoring, BCG classification, revenue forecasting — with every
dashboard figure pinned by an automated test and every model evaluated honestly
(calibration, cost-based thresholds, baseline backtests, error analysis).

## Scope
**In:** analytics pipeline, interactive dashboard, churn model with decision
thresholds, revenue forecast with backtest, NL-to-SQL helper, discount/margin
analysis, evaluation rigor (calibration, cost curves, error catalogs).
**Out (deliberately):** real e-commerce integration, production ML serving,
new chart types, keyword-driven AI features.

## Timeline (planned vs actual)
| Day | Plan | Status |
|---|---|---|
| D1 (Oct 15) | Baseline verification, evidence layer | Done |
| D2 (Oct 16) | Churn calibration + cost thresholds | Done |
| D3 (Oct 17) | Forecast backtest + experiment spec v2 | Done |
| D6 | Error catalog, metric registry, CI pinning | Done |
| D7 | Resume/interview/release kit | Done |
| Follow-on | Discount engine, NL-to-SQL eval harness | Done (119 tests) |

## Success criteria (from the week's plan) — all met
- Threshold recommendation with stated cost assumptions: t*=0.10, assumptions box in reports/churn_calibration_and_thresholds.md
- Calibration chart regenerable: scripts/churn_calibration.py
- Backtest table with MASE per origin + honest verdict vs naive: reports/forecast_backtest.md
- Experiment spec runnable by a marketing team: docs/experiment_design_winback.md
- Test suite green: 119/119 (verified 2026-10-17)

## Key links
- Live dashboard: https://ecomanalytics-dashboard.vercel.app/
- Evaluation report: reports/churn_calibration_and_thresholds.md
- Backtest report: reports/forecast_backtest.md
- Error catalog: reports/error_analysis.md
- Release gates: docs/RELEASE_GATES.md
