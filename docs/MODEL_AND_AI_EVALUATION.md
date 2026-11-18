# MODEL & AI EVALUATION — E-Commerce

## Models
1. **Churn classifier** (gradient boosting, RFM-derived features). Forward-time
   split; honest ROC-AUC 0.6484 (an earlier 1.0 was leakage — caught and fixed).
2. **Revenue forecast** (Holt-Winters + trend ensemble).
3. **NL-to-SQL assistant** (LLM-backed; evaluated, not assumed).

## Evaluation chain (each stage produced a published artifact)
| Stage | Method | Finding |
|---|---|---|
| Discrimination | ROC-AUC + PR-AUC on untouched test | 0.6484 / 0.3616 vs prevalence 0.2535 |
| Calibration | reliability curve, Brier, slope; isotonic fix | slope 0.388 -> Brier 0.1957->0.1829, ECE 0.0963->0.0378 |
| Decision | cost matrix, profit-maximizing threshold | t*=0.10 beats contact-all with 101 fewer contacts |
| Robustness | sensitivity +/-30% on cost and recovery rate | Bayes threshold range 0.09-0.24 |
| Backtest | rolling-origin (10 origins x 3 horizons), MASE | drift baseline wins (0.468 vs 0.680); holt_linear challenger 0.3752 not deployed |
| Uncertainty | CI empirical coverage | 9.5% vs 95% nominal — flagged |
| Errors | FN/FP customer catalogs at t*=0.10 | FNs = new customers; FPs = seasonal returners |
| AI system | 37-question NL-to-SQL benchmark (v1.1) | 48.6% -> 97.3% execution accuracy, 100% refusal correctness, 0 fabricated numbers |

## Limitations (standing)
Synthetic data; illustrative cost assumptions; no campaign has validated the
retention lift; forecast series is short; V-proxy (retained-customer spend) is a
proxy, not measured CLV. The 97.3% figure is execution accuracy **on this
37-question benchmark only**, not a general accuracy claim.

## What this evaluation defends in interviews
"Why is AUC 0.65 good?" · "How do you choose a threshold?" · "How do you prove a
forecast beats naive?" · "What's the worst failure you found?" (see reports/interview_prep.md)
