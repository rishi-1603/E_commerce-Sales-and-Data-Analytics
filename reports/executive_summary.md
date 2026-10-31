# E-Commerce: findings for a commercial review

**Scope:** synthetic orders from January 2022 to December 2024. These results illustrate an analytical workflow; they are not observed company performance or realized financial impact.

## Sales movement

December 2024 revenue increased 17.0% month over month, while orders increased 21.3% and average order value fell 3.5%. The movement was volume-led in this dataset. It does not identify a campaign or channel as the cause.

The reporting population contains 9,933 Delivered or Processing orders, with revenue of ₹59,283,619.32. Cancelled and Returned orders are excluded under the project's stated convention. The order funnel uses all 12,000 order headers, so its denominator is different.

## Pricing

Quantity did not differ significantly across discount depths in the overall comparison (Kruskal–Wallis p ≈ 0.305). At a 20% discount, the modeled volume increase required to preserve margin is 59.2%.

A 10% discount-cap scenario adds approximately ₹6.45 lakh of margin if volume is held constant. That assumption needs an experiment before the figure could support a pricing decision. The analysis does not estimate causal price elasticity.

## Retention

The win-back scenario covers 448 cooling-off customers. Under its documented contact-cost, recovery-rate and customer-value assumptions, expected profit is approximately ₹541 per contact. Historical spend is not future revenue at risk, and no campaign uplift has been measured.

A proposed campaign should therefore be evaluated against a control group. The useful outcomes would be incremental reactivation and contribution after contact and offer costs—not the number of messages sent.

## Forecasting

The original ensemble underperformed a drift baseline. A shared rolling-origin comparison found `holt_linear` at a reported MASE of 0.3752, versus 0.4681 for drift. The report retains the losing results and records the aggregation convention. Model selection used the evaluation origins; an untouched confirmation period would be needed for a stronger prospective claim.

## Suggested next decisions

1. Test a discount policy with a suitable control rather than assuming volume will stay unchanged.
2. Use customer segments and the win-back sensitivity analysis to design a limited retention experiment.
3. Keep simple forecast baselines in the review and check uncertainty calibration before using projections for planning.

[Metric definitions](../data/metrics.json) · [Assumptions](assumptions_and_limitations.md) · [Forecast comparison](forecast_challenger.md) · [Win-back calculation](winback_economics.json)
