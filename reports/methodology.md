# Methodology & Validation
### How this analysis was built — and how we know it's reliable

> The goal of this document is **trust**. A reviewer (or a future you) should
> be able to reproduce every number and understand every assumption without
> reading a line of code. For the code itself, see `python/` and `sql/`.

---

## 1. End-to-end pipeline
`run_pipeline.py` orchestrates **eight steps** with timestamped logging:

1. `data/raw/generate_data.py` — generate the synthetic source tables
2. `python/eda/01_eda_preprocessing.py` — clean, join, build `master_orders`
3. `python/segmentation/02_rfm_segmentation.py` — RFM + K-Means (silhouette-chosen k)
4. `python/churn/03_churn_analysis.py` — **leakage-free** churn model + gains/lift chart
5. `python/forecasting/04_revenue_forecasting.py` — revenue forecast (bootstrap CI)
6. `python/eda/05_product_profitability.py` — product profitability + BCG proxy matrix
7. `python/stats/06_statistical_analysis.py` — hypothesis tests (t/ANOVA/chi-square)
8. `python/clv/07_customer_lifetime_value.py` — historical + predictive CLV

## 2. Data model
Four source tables (`customers`, `products`, `orders`, `order_items`) defined
in `sql/01_database_schema.sql`, joined into a single analytical `master_orders`
table that every downstream artifact is derived from. Processed outputs live
in `data/processed/` (see `data/DATA_DICTIONARY.md`).

## 3. Key analytical choices
- **RFM scoring** uses 5-quantile (`qcut`) bucketing on Recency, Frequency,
  and Monetary, mapped to 8 named segments. RFM is computed on the
  **revenue-eligible population** (`master_orders`: Delivered + Processing;
  Cancelled and Returned excluded).
- **K-Means** runs on standardized R/F/M; **`k` is chosen by silhouette score**
  (data-driven), not hardcoded. The elbow curve is shown alongside for context.
- **Churn model** uses a **hard cutoff** (2024-07-03): features are computed
  only from behaviour *before* the cutoff; the label is "no purchase (Delivered
  or Returned, from raw orders) in the 180 days *after* the cutoff." This removes
  the target leakage present in the original version (where `recency_days`
  was both a feature and the basis of the label). Model selection is a
  **5-fold CV ROC-AUC mean ± std on the training split** (LR 0.6742 ± 0.0303,
  RF 0.6417, GB 0.6149); the selected model is scored once on a held-out 20%
  (ROC-AUC 0.6621, PR-AUC 0.3322). Training customers get out-of-fold scores,
  never in-sample refits. A **cumulative gains/lift chart** quantifies targeting
  efficiency, and a separate **5-origin rolling backtest** (`reports/churn_temporal_backtest.json`,
  AUC 0.56–0.67) supplies the actual temporal evidence. The 80/20 split is not
  called temporal.
- **Forecasting** combines a linear-trend baseline with Holt-Winters triple
  exponential smoothing and an ensemble average. Skill is measured by a
  **rolling-origin backtest** (10 origins × horizons 1–3 months) and reported
  as MASE against the in-sample seasonal-naive scale (₹1,023,756). The shipped
  ensemble scores 0.68, the drift baseline 0.468, and the `holt_linear`
  challenger 0.3752 (not deployed). The residual-bootstrap 95% interval
  under-covers (9.5% empirical), which is disclosed rather than hidden.
- **Statistical analysis** runs Welch's t-test, one-way ANOVA (+ Kruskal-Wallis
  cross-check), and chi-square with effect sizes (Cohen's d, η², Cramér's V).
  On synthetic data these correctly return non-significant results.
- **CLV** is reported two ways: *historical* (observed profit, a floor) and
  *predictive* (AOV × annual frequency × margin × horizon × (1 − churn prob),
  risk-adjusted). Customers are ranked into value tiers for retention budgeting.

## 4. How this analysis was validated (the Trust Layer)
| Check | Where | What it guarantees |
|-------|-------|--------------------|
| Primary keys unique & not null | `tests/test_data_quality.py` | No duplicate entity rows |
| Foreign keys resolve | `tests/test_data_quality.py` | No orphaned orders/items |
| Business-logic sanity (positive amounts, valid categories, age ranges) | `tests/test_data_quality.py` | No impossible values |
| 243 pytest tests, run in CI | `.github/workflows/ci.yml` | Pipeline output is reproducible on a clean checkout |
| Dashboard pinned to pipeline output | `tests/test_dashboard_consistency.py` | No hand-typed headline can drift from the data |
| AI assistant gated on a benchmark | `evals/run_eval.py` | 37/37 execution accuracy; refusals and fabricated answers counted |
| No target leakage in churn | CV selection + OOF scores in `03_churn_analysis.py`, `scripts/churn_data.py` | Metrics are honest, not inflated |
| Temporal churn evidence | `reports/churn_temporal_backtest.json` | 5 rolling origins; not conflated with the 80/20 split |
| Forecast evaluated out-of-sample | `scripts/forecast_backtest.py` | Forecast skill is measured against naive baselines |
| Reproducibility | fixed `random_state=42` throughout | Same input → same output |

## 5. Reproducibility
```bash
git clone <repo>
pip install -r requirements.txt
python run_pipeline.py            # regenerates all data + outputs
python -m pytest tests/ -v        # re-runs all validation
```
The CI workflow does exactly this on every push, so the repo is in a known-good state.

## 6. Metric definitions (so everyone means the same thing)
- **Revenue-eligible order:** status Delivered or Processing. Cancelled and Returned are separate exits and are never subtracted from Delivered.
- **Recency:** days since the customer's last revenue-eligible order, at the snapshot date.
- **Frequency:** count of distinct revenue-eligible orders.
- **Monetary:** sum of `line_total` over revenue-eligible orders.
- **Churn (model label):** no revenue-eligible purchase in the 180-day window after the cutoff.
- **Gross profit:** `line_total − cost_total` per line item.
- **BCG buckets:** a **proxy** matrix on median units sold (vertical) vs median line margin (horizontal), not classic market share vs market growth.

## 7. Known statistical caveats (stated, not buried)
- **Discount test:** discount is assigned at order level and copied to every line, so the 21,066 line-level Kruskal-Wallis observations are clustered within 12,000 orders. The effective sample is smaller than the line count; the p = 0.305 result is reported with that caveat and with the effect size at 20pp.
- **Cohort retention:** cohorts are right-censored. Late-2024 cohorts have fewer than 12 observed months, so apparent retention gains in those cohorts are an observation-window artifact, not a behavioural improvement.
- **Win-back EV:** `p × r × V − C` uses 180-day spend as V and applies no COGS. It is net revenue before cost of goods; at the 54.0% gross margin, ₹541 per contact is about ₹177 of contribution.
- **Margin curve:** the discount curve uses an unweighted mean of line-level margin rates (53.79% at 0%), while the headline margin is value-weighted (53.97%). The gap is a mix effect, not an arithmetic error.
