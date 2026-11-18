# DATA & METRIC AUDIT — E-Commerce

## Data provenance
- **Synthetic retail dataset** (seeded generator): 12,000 orders. Labeled synthetic
  in the README, reports, and model card. No real customers, no real revenue.
- Schema: four tables — `customers`, `products`, `orders` (one row per order), `order_items` (one row per product line).

## Metric registry
Canonical definitions live in `data/metrics.json` (single source of truth; tests
read the generated `reports/*_metrics.json` and pin values). Key entries:
| Metric | Definition | Pinned value |
|---|---|---|
| ROC-AUC | 5-fold CV model selection / untouched 20% holdout | 0.6742 CV / 0.6621 holdout |
| PR-AUC | precision-recall AUC on the holdout (label prevalence 23.5%) | 0.3322 |
| Brier | mean squared probability error (holdout) | 0.1726 raw → 0.1715 OOF-isotonic |
| Brier (256-row calibration slice) | same metric, small-slice isotonic fit | 0.1720 raw → 0.1815 isotonic (overfit) |
| Calibration slope | logistic recalibration slope on the calibration slice | 0.7875 raw / 0.1299 isotonic |
| Temporal evidence | 5-origin rolling backtest, CV AUC | 0.5611 / 0.5515 / 0.5861 / 0.6378 / 0.6710 |
| MASE | MAE / in-sample seasonal-naive MAE (INR 1,023,756) | drift 0.468 / ensemble 0.680 / holt_linear 0.3752 (not shipped) |
| CI coverage | empirical coverage of shipped 95% band | 9.5% (under-covers; disclosed) |
| Expected net revenue | C=INR 250/contact, r=15%, V=INR 13,292 revenue before COGS | t*=0.12: INR 72,849 vs 69,537 |

## Audit findings (published, not hidden)
1. Shipped forecast ensemble LOSES to the drift baseline on MASE.
2. Shipped bootstrap CI covers 9.5% of actuals vs 95% nominal.
3. Raw churn probabilities are over-confident (slope 0.7875). Isotonic helps on 1,278 OOF rows (Brier 0.1726 → 0.1715) but hurts on the 256-row calibration slice (0.172 → 0.1815) — both published.
4. The 80/20 holdout is random, not temporal; a separate 5-origin rolling backtest is published in `reports/churn_temporal_backtest.json`.
5. Profit figures are expected values under stated assumptions — no campaign run.

## Reproducibility
Exact dependency pins (requirements.txt) + fixed seeds + CI regeneration of every
metric artifact before tests run.
