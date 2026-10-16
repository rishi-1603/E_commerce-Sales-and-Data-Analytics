# E-Commerce Sales & Customer Analytics

**An analytics-first portfolio case study** that turns three years of synthetic e-commerce transactions into reconciled KPIs, customer and product analysis, decision-ready reporting, and a carefully evaluated predictive layer.

[Live dashboard](https://ecomanalytics-dashboard.vercel.app/) · [SQL analysis](sql/README.md) · [Executive brief](reports/executive_summary.md) · [Decision log](reports/decision_log.md) · [Data dictionary](data/DATA_DICTIONARY.md) · [Tests](tests/) · [Release gates](docs/RELEASE_GATES.md)

[![CI](https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics/actions/workflows/ci.yml)

> **Data and claims notice:** The transaction data is seeded and synthetic. Figures below are reproducible outputs from that dataset—not observed company results, causal effects, realized savings, or campaign outcomes. Methods are demonstrated; business conclusions require validation on real data.

## Executive summary

This repository answers a practical set of commercial questions: what changed in sales, which customers and products deserve attention, where orders exit the funnel, and whether promotions or forecasts support a decision. The main deliverable is an analytics workflow—data definitions, SQL and Python analyses, an interactive dashboard, documented recommendations, and automated checks. Predictive models are included as a supporting layer, not as the headline.

**Role emphasis:** Data Analyst first (SQL, KPI design, trend and cohort analysis, dashboarding, decision support); applied Data Science second (churn evaluation, calibration, forecasting backtests, and a measured natural-language-to-SQL benchmark).

| Area | Evidence from the project | Business interpretation |
|---|---|---|
| Sales movement | December 2024 revenue **+17.0%**, orders **+21.3%**, active customers **+8.2%**, AOV **−3.5%** month over month | The change is volume-led in this dataset; it is not evidence that a specific campaign caused growth. |
| Order funnel | **12,000** placed → **9,312** delivered → **8,089** kept | A funnel view makes cancellation, processing, and return exits visible. |
| Customer retention | 18 first-purchase cohorts; observed month-1 retention varies across cohorts | Compare like-for-like cohort windows before allocating retention effort. |
| Discount economics | No statistically detectable overall quantity response by discount depth (**Kruskal–Wallis p = 0.305**); break-even lift rises from **10.6%** at a 5% discount to **59.2%** at 20% | Do not recommend blanket discounting from these observational synthetic data; test a policy causally. |
| Forecast evaluation | Rolling-origin ensemble MASE **0.680** versus drift baseline **0.468**; nominal 95% interval covered **9.5%** of evaluated points | The ensemble did not beat the simpler baseline and its interval under-covered; it is not planning-ready. |

## Project experience

### 1. Business questions and analytical outputs

| Stakeholder question | Analysis / artifact | Decision it can inform |
|---|---|---|
| Is revenue changing because of order volume, customer count, or basket size? | Monthly KPI variance and MoM decomposition (`sql/10_mom_variance.sql`) | Investigate the driver before changing acquisition or pricing strategy. |
| Which customers need a different retention treatment? | RFM segmentation, cohort retention, churn-risk bands, and a win-back experiment design | Prioritize a controlled test; the experiment is designed, **not run**. |
| Which products contribute to the catalog's economics? | SKU-level profitability, category margins, and BCG-style portfolio view | Review low-margin items and protect profitable assortment; validate changes with actual demand data. |
| Where do orders leave the operating funnel? | Placed → delivered → kept reconciliation (`sql/11_order_funnel.sql`) | Separate fulfillment and return issues instead of collapsing them into one sales KPI. |
| Are discounts buying incremental demand? | Discount response, margin curve, and break-even volume analysis | Compare measured response with the lift required to preserve margin. |

### 2. Key findings and recommended interpretation

- **Sales movement:** December 2024 revenue rose 17.0% while AOV fell 3.5%; order growth was 21.3%. This is a descriptive decomposition, not a causal campaign readout.
- **Retention planning:** 448 customers are in the medium-risk “cooling-off” group, with **₹1.24 Cr of historical spend**. That is historical spend—not future revenue at risk. The measured 90-day repeat baseline is 34.5%; a randomized win-back experiment is documented, but no treatment effect has been observed. See [`docs/experiment_design_winback.md`](docs/experiment_design_winback.md).
- **Promotion discipline:** the data does not show a statistically detectable overall quantity response to discount depth. A 20% discount requires an estimated 59.2% volume lift to break even under the model's margin assumptions. That is a sensitivity calculation, not a forecast of actual lift.
- **Forecast discipline:** rolling-origin testing favored a simple drift baseline over the ensemble. The nominal 95% interval achieved only 9.5% empirical coverage across the evaluated points. The report recommends against using the current ensemble as an operational forecast.
- **No invented impact:** no retention campaign, pricing experiment, or live business intervention was run; no revenue saved or uplift achieved is claimed.

### 3. Analyst workflow (the core of the project)

1. **Define the data and measures.** Four seeded source tables, a documented data dictionary, and explicit rules for revenue, purchase, churn, and retention. Definitions live in [`data/metrics.json`](data/metrics.json).
2. **Audit data quality.** Schema, key integrity, business-rule, and dashboard-consistency checks run in the test suite.
3. **Analyze in SQL and Python.** Twelve SQL files cover schema, data checks, KPIs, sales, customers, products, regions, returns, cohorts, MoM variance, funnel, and discount economics. Python supplies the reproducible pipeline and analytical extensions. Where SQL and pandas use different segmentation semantics (for example, `NTILE` versus `qcut`), the difference is documented rather than hidden.
4. **Translate results into decisions.** The dashboard and [`reports/decision_log.md`](reports/decision_log.md) connect evidence to an owner, a next action, and a KPI to monitor.
5. **Reproduce and verify.** CI regenerates analytical artifacts and runs the full automated suite; the dashboard figures are checked against pipeline outputs.

### 4. Data and measurement

| Table / grain | Size | Notes |
|---|---:|---|
| Customers | 2,000 records; 1,991 active in order history | Seeded synthetic profiles and acquisition attributes |
| Products | 150 SKUs | Category, price, cost, and product attributes |
| Orders | 12,000 | January 2022–December 2024; one row per order |
| Order items | 21,066 | Line-item grain used for product and margin analysis |

**Important metric definitions**

- Revenue uses line totals for orders with status `Delivered` or `Processing`; cancelled and returned orders are excluded.
- The order funnel separately reports placed, delivered, and kept orders; the cohort and experiment analyses use their own documented purchase definition.
- Churn is defined as no purchase in the 180 days after a cutoff; model features use only information available before that cutoff.
- The exact definitions, formulas, and caveats are in [`data/metrics.json`](data/metrics.json) and [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).

**Selected dataset outputs (illustrative):** ₹5.93 Cr revenue over the covered period; 54.0% gross margin; 9,312 delivered orders; 1,991 active customers. These describe the generated dataset only.

### 5. Applied Data Science (supporting layer)

**Churn risk and calibration.** A leakage-aware 180-day churn label is evaluated using a time-ordered feature cutoff. On the reproducible 64/16/20 fit/calibration/test protocol (1,586 eligible customers), the held-out results are ROC-AUC **0.6484** and PR-AUC **0.3616** at 25.4% prevalence. Isotonic calibration improves Brier score from **0.1957** to **0.1829** and 10-bin ECE from **0.0963** to **0.0378**. A threshold of 0.10 is selected on the calibration slice under an explicitly assumed contact-cost/recovery/value model; it is **not** a proven campaign policy. Full protocol and sensitivity analysis: [`reports/churn_calibration_and_thresholds.md`](reports/churn_calibration_and_thresholds.md).

**Forecasting.** Holt–Winters and a linear-trend ensemble are compared against naïve baselines with a rolling-origin backtest. The comparison is included to demonstrate model selection—not to promote the weaker ensemble.

**Natural-language-to-SQL evaluation.** The deterministic fallback path scored **36/37 (97.3%)** on an authored 37-question benchmark, with 100% refusal correctness and zero fabricated answers in that run. One benchmark paraphrase still fails; this is not a claim of general language understanding or an evaluation of the optional LLM path. See [`reports/ai_eval_report.md`](reports/ai_eval_report.md).

**Modeling and decision boundaries:** [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) · [`reports/forecast_backtest.md`](reports/forecast_backtest.md) · [`reports/statistical_analysis.md`](reports/statistical_analysis.md).

## Dashboard preview

[Open the live dashboard](https://ecomanalytics-dashboard.vercel.app/)

![Executive overview: headline KPIs and changes](dashboard/screenshots/v2_executive_overview.png)

![Cohort retention heatmap](dashboard/screenshots/day2_cohort_heatmap.png)

The dashboard is a static HTML/CSS/JavaScript application with Chart.js. It includes executive KPIs, sales trends, customer analysis, churn, product profitability, and forecasting views.

## Reproduce locally

The CI workflow uses Python 3.11. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt

# Regenerate the seeded source data and run the core analytical pipeline
python data/raw/generate_data.py
python run_pipeline.py

# Reproduce the additional evaluation artifacts
python scripts/churn_calibration.py
python scripts/forecast_backtest.py
python python/pricing/elasticity.py
python evals/run_eval.py --min-accuracy 0.90

# Run all automated checks
python -m pytest -q
```

Open `dashboard/dashboard.html` in a browser for the local dashboard. PostgreSQL is optional for the SQL layer; see [`sql/README.md`](sql/README.md) for the schema and query instructions. The app and reports do not require an API key; optional model-backed narration is separate from the deterministic fact-generation layer.

## Repository map

```text
├── data/                 # seeded inputs, processed data, data dictionary, metric registry
├── sql/                  # 12 SQL scripts + query documentation
├── python/               # EDA, customer segmentation, churn, forecast, statistics, CLV, pricing
├── scripts/              # calibration, backtesting, decision layer, NL-to-SQL, weekly brief
├── evals/                # authored NL-to-SQL benchmark and evaluation harness
├── dashboard/            # static interactive dashboard and screenshots
├── reports/              # executive, model, experiment, decision, and error analyses
├── docs/                 # model card, experiment design, release and governance notes
└── tests/                # 119 automated checks
```

## Limitations

- The dataset is synthetic and seeded; it does not represent a real retailer or customer base.
- Observational differences do not identify causality. Discount response, returns, channel performance, and customer behavior need real-world experiments or an appropriate causal design before policy changes.
- The win-back experiment is a design only; no campaign or uplift was measured.
- The CLV output is a proxy, not a validated customer-lifetime forecast.
- The historical H1 2025 projection is not a current forecast. The rolling-origin evidence shows the current ensemble loses to a simpler baseline and its nominal interval is under-calibrated.
- Model and benchmark metrics are dataset- and protocol-specific; they should not be generalized to production without fresh data, monitoring, and validation.

For the full caveat register, see [`reports/assumptions_and_limitations.md`](reports/assumptions_and_limitations.md). The project's release checks are documented in [`docs/RELEASE_GATES.md`](docs/RELEASE_GATES.md); latest audited suite: **119 tests passed** (2026-10-17).
