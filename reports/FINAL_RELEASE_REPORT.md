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

---

## Release v2 (2026-10-21) — evaluation-depth week (Days 2–6)

| Evidence | Status |
|---|---|
| Calibration + cost-based thresholds / decision curves | Published + CI-pinned |
| Naive-baseline / rules-vs-ML / temporal comparisons | Published with honest verdicts |
| Error analysis with concrete failure cases | `reports/error_analysis.md` |
| Metric-registry entries for every new metric | `data/metrics.json` |
| New analysis scripts run in CI on every push | ✅ |
| Interview-prep eval-depth Q&A | ✅ |

**Test totals:** E-Commerce 84 · Zomato 80 · HealthGuard 56 (220 combined, all green).

**Notable honest findings shipped this week:** churn calibration slope 0.39 → isotonic fix; t\*=0.10 beats contact-all; forecast ensemble loses to drift baseline (MASE 0.68 vs 0.47); shipped 95% CI covers 9.5%; rules tie ML at investigation cut sizes; readmission model errors sit exactly in the generator's stochastic conditions.

**Status unchanged:** READY / READY WITH DISCLOSED LIMITATIONS — nothing this week weakened a claim; several were tightened downward on purpose.
