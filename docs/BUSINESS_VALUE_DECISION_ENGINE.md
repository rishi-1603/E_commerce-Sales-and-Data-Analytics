# Business value & decision record — Revenue and Growth

## Question and scope

How much of the latest observed change in sales is consistent with a change in order count versus average basket size? What do a few *assumed* campaign outcomes imply for incremental contribution?

The expandable **Decision & value** panel in the Executive Overview uses the dashboard's existing precomputed latest two monthly observations. The data is synthetic. Revenue is the sum of order-line `line_total` for Delivered + Processing orders; order count is distinct `order_id`. Embedded rupee totals are rounded to whole rupees. The dashboard is a static snapshot, not a live transaction feed.

## Calculations

For two periods with nonzero order counts, define `AOV = revenue / distinct orders`:

```
revenue change = (orders_current − orders_previous) × AOV_previous
               + orders_current × (AOV_current − AOV_previous)
```

The two terms reconcile to the displayed revenue change. This is a chosen algebraic decomposition; it does **not** separately identify unit price, quantity or product mix, and does not establish causes. Python/pandas and a fixed SQLite aggregate independently check the dashboard totals/order counts against the committed source in tests. This does not establish data correctness for an external dataset.

A user specifies expected incremental orders, assumed contribution per order and campaign cost. The low/base/high cases use 0.5×/1×/1.5× the assumed incremental orders:

```
modeled net = assumed incremental orders × assumed contribution per order − assumed campaign cost
break-even incremental orders = ceil(campaign cost / contribution per order)
```

A zero-contribution, positive-cost case has no finite break-even. Contribution is a user assumption, **not the project's measured revenue per order or an estimated causal margin**. The panel does not pick a segment, infer an effect or report realized profit/savings. Validate any action with an appropriately designed comparison.

## Decision record and boundaries

The user can record a proposed/approved/deferred status, action, success KPI, follow-up plan and an optional **user-entered, unverified** outcome note. The versioned JSON export separates source, scope, evidence, assumptions, scenarios, decision and `observed_outcome`. With no note, the outcome is `null`. A snapshot may be explicitly saved into browser-local history, but it is not server-side case management, an authenticated approval system, a verified impact tracker or an audit-proof record. It is not automatically saved; changing an input clears the prepared snapshot until rebuilt. Do not include confidential or personal data in notes.

No LLM is used to compute this panel. Existing natural-language SQL capabilities and their separate benchmark are unchanged; this feature does not evaluate unrestricted AI explanations. No new DB, dbt, Power BI report or provider integration was introduced.

## Verify

```
python -m pytest tests/test_business_value_engine.py tests/test_dashboard_consistency.py -q
```

These checks require Node.js for the JavaScript math. Four served HTML copies and both relative-path JavaScript copies must remain identical; tests enforce this. `scripts/inject_pricing_dashboard.py` preserves the separate panel but should be followed by tests before publishing.

## Excel / Power BI-ready companion

[`powerbi/Ecommerce_BI_Companion.xlsx`](../powerbi/Ecommerce_BI_Companion.xlsx) is a synthetic static Excel data workbook with an order-line fact table, customer/product/date dimensions and a monthly reconciliation sheet. It is **not** a Power BI report or `.pbix`, and no Power BI Service deployment is claimed. No names or emails are exported. Relationships are described on the Read Me sheet and in `powerbi/model_diagram.md`; the monthly check table is not a fact table to join to the detail. Regenerate with `python scripts/build_excel_companion.py`. Tests compare the committed monthly checks to the current source data and verify required keys and totals; a static workbook must be rebuilt when the source changes.

## Product price / volume / mix bridge

`scripts/build_revenue_pvm.py` aggregates the latest two observed months at product grain, then reconciles those quantities and revenues independently in SQLite and pandas. It separates products observed in both periods from products entering or exiting the observed dataset. For common products, realized unit price is product revenue divided by units; total unit volume, unit mix and realized-price components sum with observed entry/exit revenue to the total change. The price/quantity interaction is assigned to the realized-price term. Other valid ordering conventions can allocate effects differently.

This is a **descriptive, path-dependent accounting decomposition**, not causal attribution. A change in realized unit price can reflect discounts or within-product composition. New/exited means observed in one period only, not necessarily a product launch/discontinuation. The observed months are not certified complete. The dashboard consumes the generated `revenue_pvm_data.js`; tests validate the aggregate, bridge and deployed copies.

## User-managed decision history

The decision panel can explicitly save snapshots to unencrypted browser-local storage, add a user-entered metric/baseline/observed follow-up, and export/import a bounded versioned JSON history. The difference is arithmetic, not measured causal impact. Imported contents and follow-ups are unverified. Browser storage can be cleared, is not authenticated or shared, and is unsuitable for sensitive data. This is not a server-side multi-user approval system or an audit-proof realized-value ledger.

## Excel companion additions

The companion now has an Executive sheet with a monthly revenue chart and formulas, plus a Scenario sheet with editable assumptions and formula-driven low/base/high values. Open in Excel or compatible spreadsheet software to recalculate; the generator does not evaluate formulas, and some previews will show blank cached values. The file remains `.xlsx`, not a `.pbix` or a Power BI Service deployment.
