# FEATURE SPECIFICATIONS — E-Commerce

| Feature | Input | Output | Acceptance (tested) |
|---|---|---|---|
| RFM segmentation | orders | RFM scores, segments | segment counts pinned |
| Cohort retention | orders | retention matrix | cohort figures pinned |
| Churn scoring | RFM features | out-of-fold + holdout churn probabilities | CV AUC 0.6742 / holdout AUC 0.6621, PR-AUC 0.3322 pinned |
| Churn calibration + thresholds | churn model | calibrated probs, t* table, rolling backtest | Brier/slope/profit + 5 origins pinned |
| BCG classification | product sales | stars/cash cows/etc. | category counts pinned |
| Revenue forecasting | monthly revenue | Holt-Winters + trend ensemble | forecast metrics pinned |
| Forecast backtest | revenue history | MASE vs 3 naive baselines | MASE values pinned (drift 0.468) |
| Discount & margin engine | price/discount grid | break-even volume lift | break-even band pinned (+10.6% to +59.2%) |
| NL-to-SQL helper | question | SQL + answer or refusal | 37-question benchmark: 48.6% -> 100%, 0 fabricated |
| Interactive dashboard | decision_layer.json | 6-page Chart.js UI | every displayed figure pinned by test |
| Win-back experiment spec | cost model | runnable experiment design | v2 with stopping rules |

**Non-features (explicitly refused):** LLM-generated business numbers, live model
serving, more charts for decoration.
