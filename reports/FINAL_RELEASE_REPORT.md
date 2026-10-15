# Final Release Report — E-Commerce Sales & Customer Analytics
**Date:** 2026-10-15 · **Release commit:** `57c980e` · **CI:** green (60/60 tests)

## A. Overall result
**READY TO PUBLISH** — all dashboard figures pinned to the pipeline by tests; synthetic data disclosed.

## B. Work completed (this release)
- Added `reports/interview_prep.md` — resume bullets, 5-minute script, 50 Q&A with verified numbers
- Added `docs/MODEL_CARD.md` — churn model card: leakage-control design, honest 5-fold CV AUC 0.65, gains/lift framing, limitations

## C. Features & verification
| Feature | Status |
|---|---|
| 6-page live dashboard (Vercel) | Verified 200 |
| 8-stage pipeline (`run_pipeline.py`) | Runs clean end-to-end |
| Leakage-free churn model (temporal split) | AUC 0.65 CV + gains/lift |
| Forecast (Holt-Winters + trend, bootstrap CI) | Naive-baseline comparison in pipeline |
| Decision layer (MoM, cohorts, funnel, win-back design) | Numbers pinned by tests |
| NL-to-SQL assistant (LLM never computes numbers) | `tests/test_nl_to_sql.py` |

## D. Data & models
- 12,000 orders / 1,991 customers / 150 SKUs (2022–24), generated reproducibly, documented in `data/DATA_DICTIONARY.md`
- Original AUC ≈ 1.0 identified as target leakage and fixed; honest number published with caveats

## E. Quality
60/60 tests green (data quality, dashboard consistency, decision layer, NL-to-SQL). SQL/pandas parity with zero drift.

## F. Known issues / disclosed limitations
1. Synthetic data — methods transfer, numbers don't
2. Win-back experiment is design-only (no results claimed)
3. ₹1.24 Cr is historical spend of the cooling-off band, not revenue at risk

## H. Deployment
Live: https://ecomanalytics-dashboard.vercel.app/ (verified 200 after release)
