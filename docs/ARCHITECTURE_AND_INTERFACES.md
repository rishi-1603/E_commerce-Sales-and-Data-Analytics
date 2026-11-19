# ARCHITECTURE & INTERFACES — E-Commerce

> Two database engines, one schema. PostgreSQL is the analytics target for the SQL
> portfolio; SQLite is the zero-config runtime for the FastAPI app. They are never
> mixed in one query path.

## 1. Data flow

```
data/raw/*.csv  (seeded generator: 12,000 orders / 25,384 lines / 2,000 customers / 150 products)
   │
   ├─> run_pipeline.py  (8 steps, timestamped log)
   │      ├─> data/processed/*.csv        cleaned frames + master_orders (Delivered + Processing)
   │      ├─> data/metrics.json           semantic layer: every headline KPI + caveat
   │      ├─> reports/*.json / *.md       churn, forecast, discount, win-back, CLV, RFM evidence
   │      ├─> docs/figures/*.png          static analysis charts
   │      └─> decision_layer.json         dashboard feed
   │
   ├─> sql/01..12  (PostgreSQL 14+)       schema, cleaning, 10 analysis scripts
   │
   └─> data/ecommerce.db  (SQLite)        auto-created and seeded by app/db/session.py
          └─> app/ (FastAPI)              REST endpoints + grounded NL-to-SQL assistant

dashboard/dashboard.html  (canonical Chart.js source)
   └─> scripts/inject_pricing_dashboard.py  injects pricing/win-back pages, syncs 4 copies
          └─> Vercel static deploy
```

## 2. Module interfaces (contract level)

| Module | Input | Output | Contract |
|---|---|---|---|
| `run_pipeline.py` | raw CSVs | processed CSVs, figures | exits non-zero on any step failure; logs to `pipeline.log` (metrics JSON is written by the evaluation scripts, not this pipeline) |
| `python/eda/01_eda_preprocessing.py` | raw CSVs | `master_orders.csv` | revenue population = Delivered + Processing only |
| `python/segmentation/02_rfm_segmentation.py` | `master_orders.csv` | RFM segments, cluster labels | 5-quantile scoring; 8 named segments; sizes sum to 1,991 |
| `python/churn/03_churn_analysis.py` | `master_orders.csv` | churn scores, features, gains chart | features strictly pre-cutoff; label is the 180-day post-cutoff window |
| `python/forecasting/04_revenue_forecasting.py` | monthly revenue series | forecast + bootstrap band | band is indicative: empirical coverage 9.5% |
| `python/eda/05_product_profitability.py` | `master_orders.csv` | BCG proxy buckets | median units vs median margin, not market share/growth |
| `python/stats/06_statistical_analysis.py` | `master_orders.csv` | test results | effect sizes reported with p-values |
| `python/clv/07_customer_lifetime_value.py` | `master_orders.csv` | historical + predictive CLV | top decile ≈ 42% of projected CLV |
| `scripts/churn_calibration.py` | `master_orders.csv` | `churn_calibration_metrics.json` + report + figure | 64/16/20 fit/cal/cal-test split; isotonic is the shipped calibrator |
| `scripts/forecast_backtest.py` | monthly revenue series | `forecast_backtest.md` + metrics | 10 origins × 3 horizons; MASE vs drift and seasonal-naive |
| `scripts/nl_to_sql.py` | natural-language question | SQL + result, or refusal | read-only SQL; refuses unanswerable questions |
| `evals/run_eval.py` | 37-question benchmark | `results_fallback.json` | gate: accuracy ≥ 0.90, refusals counted, fabricated numbers counted |
| `scripts/inject_pricing_dashboard.py` | `dashboard/dashboard.html` + reports | 4 byte-identical dashboard copies | SHA256 equality enforced by tests |

## 3. Two databases, on purpose

| | PostgreSQL (`sql/`) | SQLite (`data/ecommerce.db`) |
|---|---|---|
| Role | Analytics warehouse: schema + 12 scripts (cleaning, KPIs, 10 analyses) a reviewer can run | Application runtime for the FastAPI demo |
| Setup | `psql -f sql/01_database_schema.sql`, then `\COPY` from `data/raw/` | auto-created and seeded on first app start |
| Grain | `orders` = order header, `order_items` = product line | same four tables, same grain |
| Why | Window functions, CTEs, `FILTER`, date math — the SQL skills being demonstrated | zero-config: `uvicorn app.main:app` works on a clean checkout |
| Config | not wired into the Python pipeline | `DATABASE_URL` / `SYNC_DATABASE_URL` in `app/core/config.py` |

The SQL scripts are **not** executed by CI (no PostgreSQL service in the workflow);
they are verified by review and by the fact that every figure they produce is
recomputed in Python and pinned by tests. Say "SQL showcase", not "SQL pipeline".

## 4. Deployment targets

- **Dashboard:** static HTML/Chart.js on Vercel — https://ecomanalytics-dashboard.vercel.app/
  (four byte-identical copies in the repo; Vercel serves the root `index.html`).
- **API:** FastAPI + SQLAlchemy async, SQLite by default, Dockerfile included; not deployed
  to a public host — run locally with `uvicorn app.main:app --reload`.
- **Power BI:** `.pbix` compiled with embedded data (opens without refresh) and `.pbip`
  editable source (needs "Refresh now"). Separate artifact from the web dashboard.
- **CI:** GitHub Actions (Python 3.11): flake8 → generate → pipeline → calibration/backtest →
  pricing/win-back/eval/challenger/inject → init DB → pytest (272).

## 5. Design rules

- **Precompute, don't serve a model.** The dashboard reads pinned JSON. There is no live
  inference endpoint, which is honest for a portfolio product and keeps the demo free.
- **Evaluation scripts run before tests in CI**, so pinned metrics are always regenerated
  from code, never hand-edited.
- **One semantic layer.** `data/metrics.json` is the single source of truth; the README,
  dashboard, and tests all quote it.
- **Fail closed.** The NL-to-SQL assistant refuses unanswerable questions rather than
  inventing a query; the eval gate counts fabrications.
