# Methodology & Validation
### How this analysis was built — and how we know it's reliable

> The goal of this document is **trust**. A reviewer (or a future you) should
> be able to reproduce every number and understand every assumption without
> reading a line of code. For the code itself, see `python/` and `sql/`.

---

## 1. End-to-end pipeline
`run_pipeline.py` orchestrates five steps with timestamped logging:

1. `data/raw/generate_data.py` — generate the synthetic source tables
2. `python/eda/01_eda_preprocessing.py` — clean, join, build `master_orders`
3. `python/segmentation/02_rfm_segmentation.py` — RFM + K-Means (silhouette-chosen k)
4. `python/churn/03_churn_analysis.py` — **leakage-free** churn model + gains/lift chart
5. `python/forecasting/04_revenue_forecasting.py` — revenue forecast (bootstrap CI)
6. `python/stats/06_statistical_analysis.py` — hypothesis tests (t/ANOVA/chi-square)
7. `python/clv/07_customer_lifetime_value.py` — historical + predictive CLV

## 2. Data model
Four source tables (`customers`, `products`, `orders`, `order_items`) defined
in `sql/01_database_schema.sql`, joined into a single analytical `master_orders`
table that every downstream artifact is derived from. Processed outputs live
in `data/processed/` (see `data/DATA_DICTIONARY.md`).

## 3. Key analytical choices
- **RFM scoring** uses 5-quantile (`qcut`) bucketing on Recency, Frequency,
  and Monetary, mapped to 8 named segments. Recency/Frequency/Monetary are
  computed on delivered (non-cancelled, non-returned) orders.
- **K-Means** runs on standardized R/F/M; **`k` is chosen by silhouette score**
  (data-driven), not hardcoded. The elbow curve is shown alongside for context.
- **Churn model** uses a **forward-time (temporal) split**: features are
  computed only from behaviour *before* a cutoff (~6 months before data end);
  the label is "no purchase in the 180 days *after* the cutoff." This removes
  the target leakage present in the original version (where `recency_days`
  was both a feature and the basis of the label). AUC is reported as a
  **5-fold cross-validated mean ± std** (not a single split), and a
  **cumulative gains/lift chart** quantifies targeting efficiency.
- **Forecasting** combines a linear-trend baseline with Holt-Winters triple
  exponential smoothing and an ensemble average. Accuracy is reported as
  MAE/RMSE/MAPE on a held-out 3-month test window, and **uncertainty is a
  residual bootstrap 95% interval** (not an assumed constant), with test-set
  bias reported separately.
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
| 21 automated checks, run in CI | `.github/workflows/ci.yml` | Pipeline output is reproducible on a clean checkout |
| No target leakage in churn | temporal split in `03_churn_analysis.py` | Metrics are honest, not inflated |
| Forecast evaluated out-of-sample | `04_revenue_forecasting.py` | Forecast skill is measured, not assumed |
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
- **Recency:** days since the customer's last *delivered* order, at the snapshot date.
- **Frequency:** count of distinct delivered orders.
- **Monetary:** sum of `line_total` over delivered orders.
- **Churn (model label):** no delivered purchase in the 180-day window after the cutoff.
- **Gross profit:** `line_total − cost_total` per line item.
- **BCG buckets:** relative share of growth (frequency/proxy) vs. margin.
