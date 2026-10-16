# ARCHITECTURE & INTERFACES — E-Commerce

## Data flow
```
raw synthetic orders (12,000 rows, seeded)
   └─> run_pipeline.py  (cleaning -> features -> aggregates)
         ├─> data/processed/*.csv, reports/decision_layer.json
         └─> dashboard.html (Chart.js, static, Vercel)
python/ modules: RFM | cohorts | churn | BCG | forecast | discount
scripts/ evaluation layer: churn_calibration | forecast_backtest | nl_to_sql | weekly_brief
tests/ : every figure and metric pinned
```

## Module interfaces (contract-level)
| Module | Input | Output |
|---|---|---|
| run_pipeline.py | raw orders CSV | processed CSVs + decision_layer.json |
| python/ (RFM, cohorts, churn, BCG, forecast) | processed frames | metric dicts consumed by dashboard + tests |
| scripts/churn_calibration.py | master_orders.csv | reports/churn_calibration_and_thresholds.md + _metrics.json + figure |
| scripts/forecast_backtest.py | monthly revenue series | reports/forecast_backtest.md + _metrics.json + figure |
| scripts/nl_to_sql.py | natural-language question | SQL + result; refuses unanswerable questions |

## Deployment targets
- **Dashboard:** static HTML/Chart.js on Vercel — https://ecomanalytics-dashboard.vercel.app/
- **CI:** GitHub Actions (Python 3.11): flake8 -> pipeline -> eval scripts -> pytest

## Design rules
- Train/serve separation is conceptual here (static dashboard reads precomputed
  JSON): no live inference endpoint, which is honest for a portfolio product.
- Evaluation scripts are first-class CI citizens: they run BEFORE tests, so the
  pinned metrics are always regenerated from code, never hand-edited.
