# AGENT TASK BOARD — E-Commerce
### Completed work items (week of 2026-10-15). Nothing here is aspirational.

| # | Task | Output | State |
|---|---|---|---|
| 1 | Pipeline + dashboard + CI baseline | run_pipeline.py, dashboard.html, .github/workflows/ci.yml | Done |
| 2 | Evidence layer (release report, model cards, interview prep) | reports/FINAL_RELEASE_REPORT.md, docs/MODEL_CARD.md, reports/interview_prep.md | Done |
| 3 | Churn calibration (fit/cal/test 64/16/20) | scripts/churn_calibration.py + reports | Done |
| 4 | Cost-based thresholds + sensitivity | t*=0.10 table, Bayes t=0.129 | Done |
| 5 | Forecast rolling-origin backtest (10x3) | scripts/forecast_backtest.py + reports | Done |
| 6 | Win-back experiment spec v2 | docs/experiment_design_winback.md | Done |
| 7 | Error catalog (FN/FP customer cases) | reports/error_analysis.md | Done |
| 8 | Metric registry sync | data/metrics.json | Done |
| 9 | CI pins eval scripts pre-pytest | .github/workflows/ci.yml | Done |
| 10 | Discount & margin engine (break-even analysis) | scripts/decision_layer.py + tests | Done |
| 11 | NL-to-SQL eval harness (37 questions) | scripts/nl_to_sql.py + evals/ | Done |
| 12 | Release gates A-E | docs/RELEASE_GATES.md | Done |

**Rule enforced on every item:** reproducible script + metric-pinning test +
limitation note + an interview question it defends.
