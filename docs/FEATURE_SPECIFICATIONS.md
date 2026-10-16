# FEATURE SPECIFICATIONS — E-Commerce

| Feature | Input | Output | Acceptance (tested) |
|---|---|---|---|
| RFM segmentation | orders | RFM scores, segments | segment counts pinned |
| Cohort retention | orders | retention matrix | cohort figures pinned |
| Churn scoring | RFM features | churn probabilities | AUC/PR-AUC pinned (0.6489 / 0.3664) |
| Churn calibration + thresholds | churn model | calibrated probs, t* table | Brier/slope/profit pinned |
| BCG classification | product sales | stars/cash cows/etc. | category counts pinned |
| Revenue forecasting | monthly revenue | Holt-Winters + trend ensemble | forecast metrics pinned |
| Forecast backtest | revenue history | MASE vs 3 naive baselines | MASE values pinned (drift 0.468) |
| Discount & margin engine | price/discount grid | break-even volume lift | break-even band pinned (+10.6% to +59.2%) |
| NL-to-SQL helper | question | SQL + answer or refusal | 37-question benchmark: 48.6% -> 97.3%, 0 fabricated |
| Interactive dashboard | decision_layer.json | 6-page Chart.js UI | every displayed figure pinned by test |
| Win-back experiment spec | cost model | runnable experiment design | v2 with stopping rules |

**Non-features (explicitly refused):** LLM-generated business numbers, live model
serving, more charts for decoration.
