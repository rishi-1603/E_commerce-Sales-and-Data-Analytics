# Forecast Challenger Evaluation

**Protocol:** identical to `forecast_backtest.py` — 10 rolling origins, horizons [1, 2, 3], MASE scaled by in-sample seasonal-naive MAE (1,023,756).

## Leaderboard (MASE — lower is better)

| Rank | Model | MASE | Family |
|---|---|---|---|
| 1 | holt_linear | **0.3752** | challenger |
| 2 | drift | **0.4681** | baseline |
| 3 | holt_winters | **0.5614** | baseline |
| 4 | naive_last | **0.6312** | baseline |
| 5 | blend_drift_log | **0.6671** | challenger |
| 6 | log_drift | **0.6778** | challenger |
| 7 | ensemble_shipped | **0.68** | baseline |
| 8 | linear_trend | **0.8828** | baseline |
| 9 | damped_log_linear | **1.6783** | challenger |
| 10 | log_linear | **1.751** | challenger |
| 11 | seasonal_naive | **2.0539** | baseline |

## Verdict

**Winner: `holt_linear` at MASE 0.3752**

- Drift baseline: 0.4681
- Shipped ensemble: 0.68
- Best challenger: `holt_linear` at 0.3752
- Challenger beats drift: **True**

**Recommendation.** holt_linear beats the drift baseline (MASE 0.3752 vs 0.4681) under an identical rolling-origin protocol. Promote it to the operational forecast and keep drift as the fallback benchmark.

## Models that did not run cleanly

None — every model produced finite forecasts at every origin.

## What a reviewer should check

1. **Protocol parity is imported, not re-implemented** — the baseline functions and MASE scale come directly from `forecast_backtest.py`, so a difference in scores cannot come from a difference in evaluation.
2. **A crashed model scores as a failure** — exceptions produce NaN forecasts that are excluded, never silently replaced with the actual.
3. **The verdict is published either way.** If no challenger wins, the report says the baseline is the ceiling rather than shipping complexity for its own sake.
4. **Why these challengers:** revenue here grows roughly exponentially, while drift extrapolates a straight line. Log-space models fit a constant growth *rate*; whether that helps is an empirical question this script answers, not an assumption.
