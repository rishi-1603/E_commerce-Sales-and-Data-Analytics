# MODEL & AI EVALUATION — E-Commerce

## Models
1. **Churn classifier** (Logistic Regression selected by 5-fold CV, RFM-derived
   features). Hard cutoff with out-of-fold training scores; CV ROC-AUC 0.6742,
   holdout 0.6621 (an earlier 1.0 was leakage — caught and fixed).
2. **Revenue forecast** (Holt-Winters + trend ensemble).
3. **NL-to-SQL assistant** (deterministic grounded path evaluated; optional LLM path).

## Evaluation chain (each stage produced a published artifact)
| Stage | Method | Finding |
|---|---|---|
| Discrimination | 5-fold CV ROC-AUC / holdout ROC-AUC + PR-AUC | 0.6742 CV / 0.6621 + 0.3322 holdout vs prevalence 0.2354 |
| Calibration | reliability curve, Brier, slope; isotonic sample-size check | slope 0.7875; OOF isotonic Brier 0.1726->0.1715, 256-row slice 0.172->0.1815 (overfit) |
| Decision | cost matrix, profit-maximizing threshold | t*=0.12 beats contact-all with 93 fewer contacts |
| Robustness | sensitivity +/-30% on cost and recovery rate | Bayes threshold range 0.09-0.23 |
| Backtest | rolling-origin (10 origins x 3 horizons), MASE | drift baseline wins (0.468 vs 0.680); holt_linear challenger 0.3752 not deployed |
| Uncertainty | CI empirical coverage | 9.5% vs 95% nominal — flagged |
| Errors | FN/FP aggregates at t*=0.12 | all 10 FNs are new-tenure customers; FPs = seasonal returners |
| AI system | 37-question NL-to-SQL benchmark (v1.1) on `scripts/nl_to_sql.py` | 48.6% -> 97.3% execution accuracy, 100% refusal correctness, 0 fabricated numbers |

The FastAPI `/api/v1/query/nl-to-sql` endpoint is a separate deterministic intent router. Its
aggregates and refusals are pinned by `tests/api/test_nl_query_accuracy.py` and are not part of the
97.3% benchmark.

## Limitations (standing)
Synthetic data; illustrative cost assumptions; no campaign has validated the
retention lift; forecast series is short; V-proxy (retained-customer spend) is a
proxy, not measured CLV. The 97.3% figure is execution accuracy **on this
37-question benchmark only**, not a general accuracy claim.

## What this evaluation defends in interviews
"Why is AUC ~0.67 good?" · "How do you choose a threshold?" · "How do you prove a
forecast beats naive?" · "What's the worst failure you found?" (see reports/interview_prep.md)
