# Interview Preparation Pack
### E-Commerce Sales & Customer Analytics — questions and answers based ONLY on the actual project

---

## Resume Bullets (verified numbers only)

- **Built a 6-page decision-layer analytics product over 12,000 orders / 1,991 customers / 150 SKUs (2022–24)** — RFM + K-Means segmentation, cohort retention, churn modeling, BCG product matrix, Holt-Winters forecasting with bootstrap CIs, and an NL-to-SQL assistant where the LLM never computes numbers; **60 automated tests pin every dashboard figure to the pipeline**.
- **Rebuilt the churn model to be leakage-free** (forward-time split: features strictly before cutoff, label = no purchase in the next 180 days) after identifying that the original recency-based features leaked the label — the honest 5-fold CV AUC is **0.65**, and the gains/lift chart quantifies targeting efficiency instead of chasing a fake 0.99.
- **Delivered a decision layer, not just charts**: MoM decomposition (Dec 2024: revenue +17.0%, orders +21.3%, AOV −3.5% → volume-led growth), 18-cohort retention analysis (month-1 retention rose from ~15–28% in 2023 to 55–88% in late 2024), and a statistically powered win-back experiment design (baseline 34.5% 90-day repeat rate; MDE +13pp core pool / +8.5pp expanded) — design only, results not fabricated.

## One-Line Description

An end-to-end e-commerce analytics product — SQL + Python pipeline, leakage-free churn model, cohort retention, forecasting with uncertainty, and a tested decision layer that answers "what changed and what should we do."

## 5-Minute Presentation Script

**[30s] Business problem**
"An e-commerce business has orders, customers, and products — and no reliable answer to three questions: is the business actually growing, which customers are about to leave, and what should we do next. Dashboards show what happened; this project adds why it changed and what to do about it."

**[60s] Data & pipeline**
"12,000 orders across 1,991 customers and 150 SKUs over 2022–24, generated reproducibly and documented with a data dictionary. Eleven SQL scripts and a pandas pipeline compute the same metrics with zero drift — and 60 automated tests pin every number on the deployed dashboard to the pipeline output, so the live site can never silently disagree with the analysis."

**[90s] Modeling — the churn story**
"The churn model is where I show judgment. The first version scored AUC near 1.0 — and that was target leakage: recency features that defined the label were also feeding the model. I rebuilt it with a forward-time split: all features computed strictly before a cutoff date, label = no purchase in the 180 days after. The honest score is AUC 0.65 by 5-fold CV — and that's a realistic number for churn. A gains/lift chart shows the top decile concentrates churners well enough to target a campaign profitably. The lesson I'd bring to a team: a believable 0.65 with a clear targeting story beats an unbelievable 0.99 every time."

**[60s] Decision layer**
"Three upgrades turn analysis into decisions. First, the 'What changed?' strip: December revenue grew 17% on 21% more orders while AOV fell 3.5% — volume-led growth, not price-led. Second, cohort retention: month-1 retention improved from 15–28% in 2023 to 55–88% in late 2024. Third, a win-back experiment design for the 448 cooling-off customers (₹1.24 Cr historical spend): power analysis puts the minimum detectable effect at +13pp against a 34.5% baseline — designed, not fabricated."

**[30s] Limitations**
"The data is synthetic and disclosed as such. Historical spend is not revenue at risk. The forecast assumes trend and seasonality continue. The experiment is a design — no results are claimed. Every one of those caveats lives in the reports, and the tests enforce the numbers."

## 10 Business Questions

1. **Is revenue growing?** Yes — Dec 2024: +17.0% revenue, +21.3% orders, +8.2% active customers, but AOV −3.5% — volume-led, not price-led growth.
2. **Do customers stick?** Month-1 cohort retention improved from ~15–28% (2023 cohorts) to 55–88% (late 2024) across 18 first-purchase cohorts.
3. **Where do orders leak?** Funnel: 12,000 placed → 9,312 delivered (77.6%) → 8,089 kept; exits are 844 cancelled, 621 processing, 1,223 returned.
4. **Who should we win back?** 448 cooling-off customers (medium churn-risk band) with ₹1.24 Cr historical spend — *historical, not future revenue at risk*.
5. **What's the win-back plan?** A designed experiment: baseline 34.5% 90-day repeat rate, MDE +13pp (core pool) / +8.5pp (expanded), with held-out control — design only.
6. **How concentrated is CLV?** Top decile of customers holds ~42% of projected lifetime value.
7. **Is the churn model trustworthy?** Yes, as a targeting tool: leakage-free temporal split, AUC 0.65 CV, gains/lift chart. Not a per-customer oracle.
8. **What's the forecast?** H1 2025 projected ≈ ₹3.27 Cr — ensemble of linear trend + Holt-Winters with bootstrap 95% CI; assumes trend/seasonality continue.
9. **How do you prevent the dashboard from lying?** Every figure is computed by the pipeline and pinned by an automated test; metric definitions live in `data/metrics.json`.
10. **What would you do next with real data?** Run the win-back experiment as designed, validate the forecast against actuals, and retrain churn monthly with a temporal backtest.

## 10 SQL Questions

1. **How do you compute month-over-month revenue change?** LAG window function: `(revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month)` — implemented in `sql/10_mom_variance.sql`.
2. **How is cohort retention computed in SQL?** Join each customer's first-purchase month to later orders, then `COUNT(DISTINCT CASE WHEN months_after = k THEN customer END) / cohort_size` per cohort — `sql/09_cohort_retention.sql`.
3. **How do you build an order funnel?** Conditional counts per status stage with exit reasons: `COUNT(*) FILTER`-style `SUM(CASE WHEN status='delivered' ...)` — `sql/11_order_funnel.sql`.
4. **Window functions used?** `LAG` (MoM), `SUM() OVER()` (cumulative), `ROW_NUMBER()`/`NTILE` (RFM quintiles, top-N).
5. **How do SQL and pandas stay consistent?** Both implement the same metric definitions from `data/metrics.json`; the test suite reconciles them with zero drift.
6. **How would you find customers who churned?** No order in the last N days *as of a cutoff date* — the cutoff is what makes the label leak-free.
7. **How do you compute RFM in SQL?** Recency (days since last order), Frequency (order count), Monetary (total spend) per customer, then quintile buckets via `NTILE(5)`.
8. **What's a BCG matrix query?** Category-level growth × share computed by joining revenue by category over two periods and quadrant-casing the result.
9. **How do you handle returned orders in revenue?** Keep vs returned are separate stages in the funnel; revenue metrics are defined on kept orders and the definitions are documented in the data dictionary.
10. **Why PostgreSQL for this project?** Window functions, date arithmetic, and reliable decimal handling for ₹ metrics; the schema and 11 analysis scripts live in `sql/`.

## 10 Python Questions

1. **How is the churn model leak-free?** `python/churn/03_churn_analysis.py`: features computed strictly before the cutoff, label = no purchase 180 days after; forward-time split replaces random split.
2. **Why is AUC 0.65 the honest number?** 5-fold CV on the leakage-free design; the earlier ~1.0 came from using the label's own ingredients as features. Real churn models land 0.65–0.80 without leakage.
3. **How do you evaluate a churn model beyond AUC?** Cumulative gains/lift: how many churners the top decile captures vs random targeting — that's what makes a campaign profitable.
4. **How does the NL-to-SQL assistant work?** The LLM generates SQL from the schema; the engine executes it; **the LLM never computes or states numbers itself** — results come from the database only.
5. **How is the forecast built?** Holt-Winters triple exponential smoothing + linear-trend ensemble with bootstrap 95% CI — naive baseline comparison included (`python/forecasting/04_revenue_forecasting.py`).
6. **What does the test suite check?** 60 tests: data quality invariants, metric reconciliation (pipeline vs dashboard embed), decision-layer consistency, and NL-to-SQL behavior.
7. **How do you keep the deployed dashboard in sync?** `tests/test_dashboard_consistency.py` asserts the dashboard's embedded data equals the pipeline output — the live site can't silently drift.
8. **How were RFM segments built?** Recency/Frequency/Monetary quintiles + K-Means with elbow analysis; segment actions documented in the retention playbook.
9. **What statistical tests did you use?** `python/stats/06_statistical_analysis.py` — significance tests on segment differences (documented in `reports/statistical_analysis.md`).
10. **What's in `run_pipeline.py`?** One command runs all 8 stages (EDA → RFM → churn → forecast → products → stats → CLV → context), logging each with timing — reproducible end to end.

## 10 ML / Analytics Questions

1. **What is target leakage?** When information from after (or inside) the label definition enters the features — e.g., using "days since last purchase" to predict "no purchase next 180 days." It inflates metrics and destroys trust.
2. **How do you prevent it?** Time-based splits and a hard cutoff: every feature must be computable at prediction time, and validation must respect time order.
3. **Why does churn AUC of 0.65 matter more than a 0.99?** Because it's reproducible on future data. A believable modest score with lift beats a fake perfect one.
4. **When do you pick precision vs recall for churn?** When the intervention (discount) is cheap, favor recall (reach more at-risk customers); when it's expensive, favor precision — which is why the gains chart matters.
5. **What's the naive forecast baseline and why check it?** Last-period value or drift; Holt-Winters must beat it on a temporal backtest or it adds nothing.
6. **How do you interpret a bootstrap CI on the forecast?** The range holding 95% of bootstrap projections — uncertainty the business should plan around, not a single promised number.
7. **What is an MDE?** Minimum detectable effect — the smallest lift an experiment can reliably detect at its sample size. +13pp on a 34.5% baseline for the core pool here.
8. **Why is the win-back plan called 'design only'?** No experiment was run; reporting uplift now would be fabrication. The design (baseline, MDE, control) is the deliverable.
9. **What does the CLV number actually mean?** Share of *projected* lifetime value in the top decile (42%) — a concentration statistic under CLV assumptions, not booked revenue.
10. **How do you explain AOV falling while revenue grows?** Volume-led growth: more orders at lower average value — the MoM decomposition makes that distinction explicit.

## 10 Project Deep-Dive Questions

1. **What did you build end-to-end?** Synthetic-but-documented data → SQL + pandas pipeline (8 stages) → analytics (RFM, churn, forecast, BCG, CLV) → decision layer (MoM, cohorts, funnel, experiment design) → NL-to-SQL → deployed 6-page dashboard with 60 pinning tests.
2. **Why 60 tests for a dashboard project?** Because dashboards silently lie when data drifts; pinning every figure to the pipeline makes the live artifact auditable.
3. **What's the 'Trust Layer'?** The test suite + `data/metrics.json` definitions + SQL/pandas parity: every visible number has a definition, a computation, and a test.
4. **What would you improve?** Real data with a true temporal horizon (to run the win-back experiment and a proper backtest), calibrated churn probabilities, and a decision-threshold analysis per campaign cost.
5. **Why not deep learning here?** Tabular data with 12K rows; gradient-boosted or linear models are the right tool. Choosing simple models on purpose is part of the judgment I'd show a team.
6. **How does the project show business thinking?** Every module ends in a decision: what changed (MoM), who to target (churn bands + lift), what to test (win-back design), what to stock (forecast + BCG).
7. **What's the risk of this project?** Someone reads ₹1.24 Cr as recoverable revenue — mitigated by the caveat in `data/metrics.json` and the reports (historical spend only).
8. **How do you defend synthetic data?** It's disclosed everywhere; its value is that it lets me demonstrate leakage-free design, reconciliation, and testing — the methods transfer, the numbers don't.
9. **How is the forecast presented honestly?** Ensemble with bootstrap CI plus a caveat that it assumes trend/seasonality continue — and the pipeline compares against naive baselines.
10. **If the CTO asked 'why should I trust this dashboard?', what do you say?** Because every number is computed once, defined in one place, reconciled between SQL and Python, and tested on every commit — trust comes from the pipeline, not the charts.
