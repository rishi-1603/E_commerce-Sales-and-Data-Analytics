# Model Card — Churn Risk Classifier

> **E-Commerce Sales & Customer Analytics** · synthetic retail dataset · decision-support demo

## 1. Model details

| | |
|---|---|
| **Task** | Binary classification — predict customer churn (no purchase in the 180 days after cutoff) |
| **Algorithms compared** | Logistic Regression, Random Forest, Gradient Boosting (best by held-out AUC) |
| **Features** | RFM + behavioral features computed **strictly before** the cutoff date only |
| **Training code** | `python/churn/03_churn_analysis.py` |
| **Evaluation** | Forward-time (temporal) split + 5-fold cross-validation |

## 2. Intended use

- **In scope:** prioritizing a win-back campaign audience (the cooling-off band), quantified with a gains/lift chart.
- **Out of scope:** per-customer punishment, credit decisions, or any claim about real customers — the dataset is synthetic (12,000 orders, 1,991 customers, 2022–24, disclosed).

## 3. Leakage control (why the score is honest)

The original project version reported AUC ≈ 1.0 — that was **target leakage**: recency-style features were derived from the same window that defines the label. The shipped design fixes it:

1. **Hard cutoff date** — every feature is computable at prediction time.
2. **Label** — no purchase in the 180 days *after* the cutoff.
3. **Forward-time split** — training precedes validation in time; no random shuffle across the cutoff.

This is documented in `reports/methodology.md` and enforced by the pipeline code.

## 4. Metrics

| Metric | Value | Interpretation |
|---|---|---|
| 5-fold CV ROC-AUC | **0.65** | Realistic for churn; real-world models land 0.65–0.80 without leakage |
| PR-AUC (fit/cal/test protocol) | **0.366** | vs prevalence 0.254 — the ranking metric that matters on this imbalance |
| Gains/lift | top decile concentrates churners | The targeting story that makes a campaign profitable (see `docs/figures/11b_churn_lift.png`) |

**Baselines:** random targeting (lift = 1) is the reference; the lift chart is the operating justification.

## 4b. Calibration & decision thresholds (added 2026-10-16)

Full analysis: [`reports/churn_calibration_and_thresholds.md`](../reports/churn_calibration_and_thresholds.md) ·
metrics pinned by `tests/test_churn_calibration.py`.

**Are the probabilities honest?** No — not raw. On a fit/calibration/test split (64/16/20):

| Variant | Brier ↓ | ECE (10-bin) ↓ | Calibration slope (=1 ideal) |
|---|---|---|---|
| Raw GBM | 0.195 | 0.097 | 0.39 (over-confident) |
| Platt-scaled | 0.182 | 0.060 | 0.88 |
| **Isotonic** | **0.181** | **0.030** | 0.65 |

**Operational rule:** consume probabilities through the isotonic calibrator, not the raw GBM output.

**Which customers should a campaign contact?** Under the stated illustrative cost model
(₹250/contact, 15% recovery, retained value = observed 180-day spend of retained customers ≈ ₹12,931):

| Policy | Contacts | Churners captured | Expected profit |
|---|---|---|---|
| Contact all | 318 | 81 (100%) | ₹77,615 |
| Current bands (p ≥ 0.33) | 39 | 14 (17%) | ₹17,406 |
| **Data-driven t\* = 0.10** | **218** | **70 (86%)** | **₹81,279** |
| Oracle (upper bound) | 81 | 81 | ₹157,115 |

The t\* policy beats contact-all while contacting 100 fewer customers; the 0.33/0.66 risk
bands are **communication** bands, not action thresholds. Sensitivity (±30% on cost and
recovery rate) moves the Bayes threshold between 0.09 and 0.24 — recovery rate is the
assumption that matters most. No campaign has been run; profits are expected values.

## 5. Limitations

1. Synthetic data — metrics do not transfer to a real customer base.
2. AUC 0.65 means meaningful ranking signal, not per-customer certainty; use bands (high/medium/low), not binary verdicts.
3. Raw GBM probabilities are over-confident (calibration slope 0.39) — use the isotonic calibrator; even after scaling, the slope (0.65) shows residual spread issues.
4. The 448-customer cooling-off audience (₹1.24 Cr *historical* spend) is a targeting pool — not future revenue at risk.
5. The win-back intervention itself is a **design only** (`docs/experiment_design_winback.md`); no uplift has been measured. All profit figures in the threshold analysis are expected values under illustrative cost assumptions.

## 6. Responsible use

A churn score should trigger a *better offer*, never a penalty. Every claim tied to this model in the README, dashboard, and reports carries the honest-AUC caveat. See `reports/assumptions_and_limitations.md`.
