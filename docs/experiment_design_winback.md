# Win-Back Experiment Design v2 — Cooling-Off Customers

> **STATUS: DESIGN, NOT RESULTS.** No experiment has been run. This dataset is
> synthetic; this document exists to show how the win-back campaign *would* be
> tested responsibly. Every baseline below is computed from the data — nothing
> is assumed.
>
> **v2 (2026-10-17):** adds explicit stopping rules, sample-ratio-mismatch
> checks, a decision framework tied to the churn threshold analysis
> (`reports/churn_calibration_and_thresholds.md`), and — most importantly —
> recognizes that **this experiment measures the recovery rate `r`**, the
> single assumption the Day-2 cost model is most sensitive to.

---

## 1. Background

The churn model (leakage-free, AUC 0.65, 5-fold CV, calibrated via isotonic
scaling) flags **448 medium-risk ("cooling-off") customers** whose historical
spend is **₹1.24 Cr** (`churn_features.csv`). Historical spend — NOT future
revenue at risk.

The business question: **does a win-back offer cause these customers to
repeat-purchase?** Only an experiment can answer that — observational lift is
confounded (offer-targeted customers differ from non-targeted by construction).

### Why this experiment is the top priority (the Day-2 connection)

The threshold analysis (`reports/churn_calibration_and_thresholds.md`) shows the
optimal contact threshold is **t = C/(r·V)** — and that the answer moves the
most with **r, the recovery rate** (±30% on r moves the Bayes threshold from
0.09 to 0.19 and swings expected profit by tens of thousands of ₹). r is
**unidentifiable from observational data**. This experiment is the instrument
that measures it: the treatment effect on repeat-purchase *is* the incremental
recovery rate for contacted at-risk customers.

## 2. Objective & hypothesis

- **Primary question:** Does a win-back offer increase 90-day repeat purchase?
- **H0:** repeat rate(treatment) = repeat rate(control)
- **H1:** repeat rate(treatment) > repeat rate(control)
- **Primary estimand:** incremental repeat rate Δ = p_treatment − p_control
  (this is the measurable version of r for the cost model)

## 3. Audience

| Pool | Size | Source |
|---|---|---|
| Core: medium churn-risk ("cooling-off") | 448 | `churn_features.csv` |
| Expanded: + About To Sleep + At Risk (RFM) | 1,023 | `rfm_segments.csv` |

**Eligibility filters (pre-randomization):** ≥1 delivered order before cutoff;
no offer contact in the previous 30 days (prerequisite — not measurable in this
dataset, flagged); opted-in for marketing. Filters are applied BEFORE
randomization so the analyzed population equals the randomized population.

## 4. Design

- **Type:** randomized controlled experiment, 50/50 allocation
- **Unit of randomization:** customer (not order — orders within a customer
  are not independent)
- **Core pool:** 224 treatment / 224 control
- **Randomization:** seeded stratified assignment on risk band and historical
  revenue tercile (balances spend across arms); allocation table is
  pre-registered and immutable
- **Primary metric:** 90-day repeat purchase rate (share of the audience with
  ≥1 purchase within 90 days of assignment)
- **Baseline (measured, not assumed):** the cooling-off segment's historical
  90-day repeat rate = **34.5%** (447 of 448 evaluable; computed from
  `master_orders.csv`, purchase = Delivered/Returned — see `data/metrics.json`)
- **Secondary metrics:** 90-day revenue per customer; second-purchase latency;
  unsubscribe/complaint rate (guardrail)
- **Guardrails:** unsubscribe rate must not rise by >2 pp; complaint volume
  monitored weekly; offer cost per incremental order tracked

## 5. Power analysis (α = 0.05 two-sided, power = 80%)

Formula used (two-proportion, equal arms):

    n per arm = ( z_{1-α/2}·√(2·p̄·(1-p̄)) + z_{1-β}·√(p1·(1-p1)+p2·(1-p2)) )² / (p2-p1)²

with p1 = 0.345 (baseline), p̄ = midpoint, z_{1-α/2} = 1.96, z_{1-β} = 0.84.

| Audience | n/arm | Detectable lift (MDE) | Verdict |
|---|---|---|---|
| Core pool (448) | 224 | **+13.0 pp** (34.5% → 47.5%) | Only large effects |
| Expanded pool (1,023) | 511 | **+8.5 pp** | Recommended if offers are cheap |

**Honest limitation:** with 448 customers the experiment is only powered for
big lifts. If the expected effect is ~5 pp, the honest options are (a) expand
the audience, or (b) accept a wider confidence interval and treat the result as
directional. Running an underpowered test and celebrating noise is the failure
mode this section exists to prevent.

## 6. Stopping rules (pre-registered — decided BEFORE launch)

1. **Fixed horizon:** the experiment runs until every customer has 90 days of
   follow-up. No early stopping for efficacy. No peeking-driven extension.
2. **Exception — harm guardrail:** if the treatment arm's unsubscribe rate
   exceeds control by >2 pp with p < 0.01 at the pre-specified weekly look
   (weeks 2, 4, 6), the offer is suspended and the steering group reviews.
   This is the ONLY interim look, and it is for harm, not benefit.
3. **Sample ratio mismatch (SRM):** at analysis start, test observed vs
   expected arm sizes (chi-square, α = 0.001). If SRM fails, STOP — do not
   analyze. Investigate randomization; the results are not trustworthy.
4. **Minimum run:** 2 full weeks of enrollment minimum; 90-day metric readout
   at day 100 (90 + 10-day lag buffer).
5. **No exclusions after randomization.** Intention-to-treat only.

## 7. Analysis plan

1. **Intention-to-treat:** every randomized customer analyzed in their assigned
   arm, regardless of whether the offer was opened/redeemed.
2. **Primary test:** two-proportion z-test on 90-day repeat rate; report the
   absolute lift Δ with a **95% CI**, not just a p-value.
3. **Covariate adjustment (pre-specified):** logistic regression with arm +
   risk band + historical revenue tercile (improves precision; the unadjusted
   test remains the headline).
4. **Heterogeneity (pre-specified, exploratory):** Δ by risk band and spend
   tercile — labeled exploratory regardless of significance.
5. **Economic readout:** plug Δ (as r) into the Day-2 threshold model:
   recompute t\* and expected profit with the *measured* r. If the measured r
   falls outside the sensitivity range (10.5%–19.5%), the threshold analysis is
   updated and re-published.
6. **Pre-registration:** this document, timestamped before launch, is the
   registration. Metric, MDE, stopping rules, and analysis plan are fixed.

## 8. Decision framework (what result → what action)

| Outcome | Action |
|---|---|
| Δ significant, lower CI > +13 pp | Roll out to the expanded pool; recompute t\* with measured r |
| Δ significant, lower CI between +5 and +13 pp | Roll out to core pool only; treat effect as modest; re-estimate power for expansion |
| Δ not significant, CI wide (includes 0 and +13) | Inconclusive (underpowered) — expand audience or pool with a later cohort; do NOT claim "no effect" |
| Δ CI entirely below 0 | Offer harms repeat purchase — kill the campaign; investigate offer design |
| Guardrail breach (unsubscribe > +2 pp) | Suspend offer regardless of primary result |

## 9. What this experiment cannot tell us

- Whether the *model* is right (that is the AUC/leakage/calibration work, done).
- Long-term retention (90-day window only).
- Effects below ~13 pp on the core pool (underpowered — stated up front).
- Offer economics end-to-end (offer cost data does not exist in this dataset —
  tracked as a real-world prerequisite).

---

*Baselines recomputed by `tests/test_decision_layer.py` — if the data changes,
this document's numbers must change with it (the test fails otherwise).*
*Threshold-model connection: `reports/churn_calibration_and_thresholds.md`
(`tests/test_churn_calibration.py` pins the inputs).*
