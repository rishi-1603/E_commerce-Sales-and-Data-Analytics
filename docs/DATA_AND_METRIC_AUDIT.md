# DATA & METRIC AUDIT — E-Commerce

## Data provenance
- **Synthetic retail dataset** (seeded generator): 12,000 orders. Labeled synthetic
  in the README, reports, and model card. No real customers, no real revenue.
- Schema: order_id, customer_id, order_date, product, category, qty, price, discount.

## Metric registry
Canonical definitions live in `data/metrics.json` (single source of truth; tests
read the generated `reports/*_metrics.json` and pin values). Key entries:
| Metric | Definition | Pinned value |
|---|---|---|
| ROC-AUC | forward-time-split churn discrimination | 0.6489 |
| PR-AUC | precision-recall AUC (class ~25% positive) | 0.3664 |
| Brier | mean squared probability error | 0.1952 raw / 0.1811 isotonic |
| Calibration slope | logistic recalibration slope | 0.3913 raw (over-confident) |
| MASE | MAE / in-sample seasonal-naive MAE (INR 1,023,756) | drift 0.468 / ensemble 0.680 |
| CI coverage | empirical coverage of shipped 95% band | 9.5% (under-covers; disclosed) |
| Expected profit | C=INR 250/contact, r=15%, V=INR 12,931 | t*=0.10: INR 81,279 vs 77,615 |

## Audit findings (published, not hidden)
1. Shipped forecast ensemble LOSES to the drift baseline on MASE.
2. Shipped bootstrap CI covers 9.5% of actuals vs 95% nominal.
3. Raw churn probabilities were over-confident until isotonic calibration.
4. Profit figures are expected values under stated assumptions — no campaign run.

## Reproducibility
Exact dependency pins (requirements.txt) + fixed seeds + CI regeneration of every
metric artifact before tests run.
