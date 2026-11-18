# Model Card — Churn Risk Classifier

> **E-Commerce Sales & Customer Analytics** · synthetic retail dataset · decision-support demo

## 1. Model details

| | |
|---|---|
| **Task** | Binary classification — predict customer churn (no purchase with status Delivered or Returned in the 180 days after cutoff) |
| **Algorithms compared** | Logistic Regression, Random Forest, Gradient Boosting (selected by **5-fold CV ROC-AUC on the training split**) |
| **Features** | RFM + behavioral features computed **strictly before** the cutoff date only |
| **Training code** | `python/churn/03_churn_analysis.py` |
| **Selected model** | **Logistic Regression** (CV AUC 0.6742 ± 0.0303; RF 0.6417, GB 0.6149) |
| **Evaluation** | 5-fold CV model selection on the training split; single held-out 20% evaluation; separate 5-origin rolling backtest in `reports/churn_temporal_backtest.json` |

## 2. Intended use

- **In scope:** prioritizing a win-back campaign audience (the cooling-off band), quantified with a gains/lift chart.
- **Out of scope:** per-customer punishment, credit decisions, or any claim about real customers — the dataset is synthetic (12,000 orders, 1,991 customers, 2022–24, disclosed).

## 3. Leakage control (why the score is honest)

The original project version reported AUC ≈ 1.0 — that was **target leakage**: recency-style features were derived from the same window that defines the label. The shipped design fixes it:

1. **Hard cutoff date** — every feature is computable at prediction time.
2. **Label** — no purchase (Delivered or Returned, from raw orders) in the 180 days *after* the cutoff.
3. **No in-sample scores published** — training customers receive `cross_val_predict` out-of-fold probabilities; test customers receive predictions from the model fitted on training only. The selected model is chosen by CV, not by the holdout.
4. **Separate temporal evidence** — a rolling-origin backtest (5 cutoffs, 2023-07 → 2024-07) is published in `reports/churn_temporal_backtest.json`. The 80/20 holdout is **not** called a temporal split.

This is documented in `reports/methodology.md` and enforced by the pipeline code.

## 4. Metrics

| Metric | Value | Interpretation |
|---|---|---|
| ROC-AUC (5-fold CV, training split) | **0.6742 ± 0.0303** | Model-selection metric; realistic for churn |
| ROC-AUC (untouched 20% holdout) | **0.6621** | Honest post-leakage number |
| PR-AUC (holdout) | **0.3322** | vs prevalence 0.2354 — the ranking metric that matters on this imbalance |
| Brier (holdout, raw → isotonic on 1,278 OOF rows) | 0.1726 → **0.1715** | Small, genuine improvement from a larger calibration sample |
| Gains/lift | top decile concentrates churners | The targeting story that makes a campaign profitable (see `docs/figures/11b_churn_lift.png`) |
| Rolling-origin CV AUC | 0.5611 → 0.6710 over 5 cutoffs | Published separately; early cutoffs are weaker |

**Baselines:** random targeting (lift = 1) is the reference; the lift chart is the operating justification.

## 4b. Calibration & decision thresholds (added 2026-10-16)

Full analysis: [`reports/churn_calibration_and_thresholds.md`](../reports/churn_calibration_and_thresholds.md) ·
metrics pinned by `tests/test_churn_calibration.py`.

**Are the probabilities honest?** On a fit/calibration/test split (64/16/20, n = 1,597):

| Variant | Brier ↓ | ECE (10-bin) ↓ | Calibration slope (=1 ideal) |
|---|---|---|---|
| Raw LR (test slice) | 0.1720 | 0.0320 | 0.7875 (over-confident) |
| Platt-scaled | 0.1734 | 0.0482 | 0.6761 |
| Isotonic (256-row calibration slice) | 0.1815 | 0.0774 | 0.1299 |

**Operational rule:** use the pipeline in `03_churn_analysis.py`, which fits isotonic on
1,278 out-of-fold training predictions and improves holdout Brier 0.1726 → 0.1715.
The separate calibration script's isotonic fit on only 256 rows **overfits** (Brier
0.172 → 0.1815, slope 0.13); both results are reported rather than averaged away.
Raw probabilities are also retained as `churn_probability_raw`.

**Which customers should a campaign contact?** Under the stated illustrative cost model
(₹250/contact, 15% recovery, retained value = observed 180-day spend of retained customers = ₹13,292.2):

| Policy | Contacts | Churners captured | Expected net revenue (before COGS) |
|---|---|---|---|
| Contact all | 320 | 75 (100%) | ₹69,537 |
| Current bands (p ≥ 0.33) | 80 | 30 (40.0%) | ₹39,815 |
| Current bands, high only (p ≥ 0.66) | 5 | 1 (1.3%) | ₹744 |
| **Data-driven t\* = 0.12** | **227** | **65 (86.7%)** | **₹72,849** |
| Oracle (upper bound) | 75 | 75 | ₹149,537 |

The t\* policy beats contact-all by ₹3,312 while making 93 fewer contacts; the 0.33/0.66 risk
bands are **communication** bands, not action thresholds. Sensitivity (±30% on cost and
recovery rate) moves the Bayes threshold between 0.09 and 0.23 — recovery rate is the
assumption that matters most. No campaign has been run; these are expected values.

**Revenue, not profit.** The value proxy is 180-day *spend*, so the column above is net
revenue after contact cost but **before cost of goods**. At the 54.0% gross margin,
₹523 per contact is roughly ₹167 of contribution and the break-even churn probability
rises from 12.54% to about 23.2% — still below the Medium Risk band mean of 38.75%.

## 5. Limitations

1. Synthetic data — metrics do not transfer to a real customer base.
2. CV AUC 0.674 (holdout 0.662) means meaningful ranking signal, not per-customer certainty; use bands (high/medium/low), not binary verdicts.
3. Raw LR probabilities are over-confident (calibration slope 0.7875); isotonic on a large out-of-fold sample helps slightly, on the small calibration slice it hurts. Use the published OOF-calibrated scores in `churn_features.csv`.
4. The 441-customer cooling-off audience (₹1.30 Cr *historical* spend) is a targeting pool — not future revenue at risk.
5. The win-back intervention itself is a **design only** (`docs/experiment_design_winback.md`); no uplift has been measured. All net-revenue figures in the threshold analysis are expected values under illustrative cost assumptions, before cost of goods.

## 6. Responsible use

A churn score should trigger a *better offer*, never a penalty. Every claim tied to this model in the README, dashboard, and reports carries the honest-AUC caveat. See `reports/assumptions_and_limitations.md`.
