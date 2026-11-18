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
| ROC-AUC (fit/cal/test protocol) | **0.6484** | Realistic for churn; real-world models land 0.65–0.80 without leakage |
| PR-AUC (fit/cal/test protocol) | **0.3616** | vs prevalence 0.2535 — the ranking metric that matters on this imbalance |
| Gains/lift | top decile concentrates churners | The targeting story that makes a campaign profitable (see `docs/figures/11b_churn_lift.png`) |

**Baselines:** random targeting (lift = 1) is the reference; the lift chart is the operating justification.

## 4b. Calibration & decision thresholds (added 2026-10-16)

Full analysis: [`reports/churn_calibration_and_thresholds.md`](../reports/churn_calibration_and_thresholds.md) ·
metrics pinned by `tests/test_churn_calibration.py`.

**Are the probabilities honest?** No — not raw. On a fit/calibration/test split (64/16/20):

| Variant | Brier ↓ | ECE (10-bin) ↓ | Calibration slope (=1 ideal) |
|---|---|---|---|
| Raw GBM | 0.1957 | 0.0963 | 0.388 (over-confident) |
| Platt-scaled | 0.1819 | 0.0581 | 0.855 |
| **Isotonic** | **0.1829** | **0.0378** | 0.618 |

**Operational rule:** consume probabilities through the isotonic calibrator, not the raw GBM output.

**Which customers should a campaign contact?** Under the stated illustrative cost model
(₹250/contact, 15% recovery, retained value = observed 180-day spend of retained customers ≈ ₹12,931):

| Policy | Contacts | Churners captured | Expected net revenue (before COGS) |
|---|---|---|---|
| Contact all | 318 | 81 (100%) | ₹77,615 |
| Current bands (p ≥ 0.33) | 63 | 22 (27.2%) | ₹26,923 |
| Current bands, high only (p ≥ 0.66) | 3 | 2 (2.5%) | ₹3,129 |
| **Data-driven t\* = 0.10** | **217** | **70 (86.4%)** | **₹81,529** |
| Oracle (upper bound) | 81 | 81 | ₹157,115 |

The t\* policy beats contact-all while contacting 101 fewer customers; the 0.33/0.66 risk
bands are **communication** bands, not action thresholds. Sensitivity (±30% on cost and
recovery rate) moves the Bayes threshold between 0.09 and 0.24 — recovery rate is the
assumption that matters most. No campaign has been run; these are expected values.

**Revenue, not profit.** The value proxy is 180-day *spend*, so the column above is net
revenue after contact cost but **before cost of goods**. At the 54.0% gross margin,
₹541 per contact is roughly ₹177 of contribution and the break-even churn probability
rises from 12.9% to about 23.9% — still below the Medium Risk band mean of 40.8%.

## 5. Limitations

1. Synthetic data — metrics do not transfer to a real customer base.
2. AUC 0.65 means meaningful ranking signal, not per-customer certainty; use bands (high/medium/low), not binary verdicts.
3. Raw GBM probabilities are over-confident (calibration slope 0.388) — use the isotonic calibrator; even after scaling, the slope (0.618) shows residual spread issues.
4. The 448-customer cooling-off audience (₹1.24 Cr *historical* spend) is a targeting pool — not future revenue at risk.
5. The win-back intervention itself is a **design only** (`docs/experiment_design_winback.md`); no uplift has been measured. All net-revenue figures in the threshold analysis are expected values under illustrative cost assumptions, before cost of goods.

## 6. Responsible use

A churn score should trigger a *better offer*, never a penalty. Every claim tied to this model in the README, dashboard, and reports carries the honest-AUC caveat. See `reports/assumptions_and_limitations.md`.
