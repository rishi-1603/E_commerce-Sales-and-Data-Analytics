# MODEL & AI EVALUATION — E-Commerce

## Models
1. **Churn classifier** (gradient boosting, RFM-derived features). Forward-time
   split; honest CV AUC 0.65 (an earlier 1.0 was leakage — caught and fixed).
2. **Revenue forecast** (Holt-Winters + trend ensemble).
3. **NL-to-SQL assistant** (LLM-backed; evaluated, not assumed).

## Evaluation chain (each stage produced a published artifact)
| Stage | Method | Finding |
|---|---|---|
| Discrimination | ROC-AUC + PR-AUC on untouched test | 0.6489 / 0.3664 vs prevalence 0.254 |
| Calibration | reliability curve, Brier, slope; isotonic fix | slope 0.39 -> Brier 0.195->0.181 |
| Decision | cost matrix, profit-maximizing threshold | t*=0.10 beats contact-all with 100 fewer contacts |
| Robustness | sensitivity +/-30% on cost and recovery rate | Bayes threshold range 0.09-0.24 |
| Backtest | rolling-origin (10 origins x 3 horizons), MASE | drift baseline wins (0.468 vs 0.680) |
| Uncertainty | CI empirical coverage | 9.5% vs 95% nominal — flagged |
| Errors | FN/FP customer catalogs at t*=0.10 | FNs = new customers; FPs = seasonal returners |
| AI system | 37-question NL-to-SQL benchmark | 48.6% -> 97.3% exact match, 0 fabricated answers |

## Limitations (standing)
Synthetic data; illustrative cost assumptions; no campaign has validated the
retention lift; forecast series is short; V-proxy (retained-customer spend) is a
proxy, not measured CLV.

## What this evaluation defends in interviews
"Why is AUC 0.65 good?" · "How do you choose a threshold?" · "How do you prove a
forecast beats naive?" · "What's the worst failure you found?" (see reports/interview_prep.md)
