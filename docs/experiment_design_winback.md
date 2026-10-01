# Win-Back Experiment Design — Cooling-Off Customers

> **STATUS: DESIGN, NOT RESULTS.** No experiment has been run. This dataset is
> synthetic; this document exists to show how the win-back campaign *would* be
> tested responsibly. Every baseline below is computed from the data — nothing
> is assumed.

---

## 1. Background

The churn model (leakage-free, AUC 0.65, 5-fold CV) flags **448 medium-risk
("cooling-off") customers** whose historical spend is **₹1.24 Cr**
(`churn_features.csv`, same source as `reports/fact_sheet.json`). Historical
spend — NOT future revenue at risk.

The business question: **does a win-back offer cause these customers to
repeat-purchase?** Only an experiment can answer that — observational lift is
confounded (offer-targeted customers differ from non-targeted by construction).

## 2. Objective & hypothesis

- **Primary question:** Does a win-back offer increase 90-day repeat purchase?
- **H0:** repeat rate(treatment) = repeat rate(control)
- **H1:** repeat rate(treatment) > repeat rate(control)

## 3. Audience

| Pool | Size | Source |
|---|---|---|
| Core: medium churn-risk ("cooling-off") | 448 | `churn_features.csv` |
| Expanded: + About To Sleep + At Risk (RFM) | 1,023 | `rfm_segments.csv` |

## 4. Design

- **Type:** randomized controlled experiment, 50/50 allocation
- **Unit of randomization:** customer
- **Core pool:** 224 treatment / 224 control
- **Primary metric:** 90-day repeat purchase rate (share of the audience with
  ≥1 purchase within 90 days of assignment)
- **Baseline (measured, not assumed):** the cooling-off segment's historical
  90-day repeat rate = **34.5%** (447 of 448 evaluable; computed from
  `master_orders.csv`, purchase = Delivered/Returned — see `data/metrics.json`)
- **Secondary metrics:** 90-day revenue per customer; unsubscribe/complaint
  rate (guardrail); second-purchase latency
- **Guardrails:** offer cost per incremental order must be trackable; exclude
  customers contacted in the last 30 days (not measurable in this dataset —
  flagged as a real-world prerequisite)

## 5. Power analysis (α = 0.05 two-sided, power = 80%)

| Audience | n/arm | Detectable lift (MDE) | Verdict |
|---|---|---|---|
| Core pool (448) | 224 | **+13.0 pp** (34.5% → 47.5%) | Only large effects |
| Expanded pool (1,023) | 511 | **+8.5 pp** | Recommended if offers are cheap |

**Honest limitation:** with 448 customers the experiment is only powered for
big lifts. If the expected effect is ~5 pp, the honest options are (a) expand
the audience, or (b) accept a wider confidence interval and treat the result as
directional. Running an underpowered test and celebrating noise is the failure
mode this section exists to prevent.

## 6. Analysis plan

1. Intention-to-treat: every randomized customer analyzed in their assigned arm.
2. Two-proportion z-test on the primary metric; report absolute lift with a
   95% CI, not just a p-value.
3. Pre-register the metric and MDE before launch (this document).
4. No peeking-driven early stops; if a stop rule is needed, define it first.

## 7. What this experiment cannot tell us

- Whether the *model* is right (that is the AUC/leakage work, already done).
- Long-term retention (90-day window only).
- Offer economics (cost data does not exist in this dataset — flagged).

---
*Baselines recomputed by `tests/test_decision_layer.py` — if the data changes,
this document's numbers must change with it (the test fails otherwise).*
