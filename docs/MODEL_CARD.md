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
| Gains/lift | top decile concentrates churners | The targeting story that makes a campaign profitable (see `docs/figures/11b_churn_lift.png`) |

**Baselines:** random targeting (lift = 1) is the reference; the lift chart is the operating justification.

## 5. Limitations

1. Synthetic data — metrics do not transfer to a real customer base.
2. AUC 0.65 means meaningful ranking signal, not per-customer certainty; use bands (high/medium/low), not binary verdicts.
3. No calibration analysis shipped; probabilities are relative scores.
4. The 448-customer cooling-off audience (₹1.24 Cr *historical* spend) is a targeting pool — not future revenue at risk.
5. The win-back intervention itself is a **design only** (`docs/experiment_design_winback.md`); no uplift has been measured.

## 6. Responsible use

A churn score should trigger a *better offer*, never a penalty. Every claim tied to this model in the README, dashboard, and reports carries the honest-AUC caveat. See `reports/assumptions_and_limitations.md`.
