# Power BI measure dictionary

The PBIP semantic model is the source of truth for these measures:
`powerbi/pbix/EcomAnalytics.SemanticModel/definition/tables/Fact_Orders.tmdl`.
The fact table is at order-line grain. Revenue measures include only
`Delivered` and `Processing` rows; order-status measures use all 12,000 order
headers. Statuses are mutually exclusive.

## Commercial measures

```DAX
Total Revenue =
CALCULATE(SUM(Fact_Orders[order_item_total]),
    Fact_Orders[order_status] IN {"Delivered", "Processing"})

Delivered Revenue =
CALCULATE(SUM(Fact_Orders[order_item_total]),
    Fact_Orders[order_status] = "Delivered")

Total COGS =
CALCULATE(SUMX(Fact_Orders,
    Fact_Orders[quantity] * RELATED(Dim_Products[unit_cost])),
    Fact_Orders[order_status] IN {"Delivered", "Processing"})

Gross Profit = [Total Revenue] - [Total COGS]
Gross Margin % = DIVIDE([Gross Profit], [Total Revenue], 0)

Delivered Orders =
CALCULATE(DISTINCTCOUNT(Fact_Orders[order_id]),
    Fact_Orders[order_status] = "Delivered")

Average Order Value =
DIVIDE([Total Revenue],
    CALCULATE(DISTINCTCOUNT(Fact_Orders[order_id]),
        Fact_Orders[order_status] IN {"Delivered", "Processing"}), 0)

Active Customers =
CALCULATE(DISTINCTCOUNT(Fact_Orders[customer_id]),
    Fact_Orders[order_status] IN {"Delivered", "Processing"})

MoM Revenue Change % =
VAR CurrentMonthRev = [Total Revenue]
VAR PrevMonthRev = CALCULATE([Total Revenue],
    DATEADD(Dim_Calendar[Date], -1, MONTH))
RETURN DIVIDE(CurrentMonthRev - PrevMonthRev, PrevMonthRev, 0)
```

Verified headline values:

| Measure | Value |
|---|---:|
| Total Revenue | ₹59,283,619.32 |
| Total COGS | ₹27,286,277.68 |
| Gross Profit | ₹31,997,341.64 |
| Gross Margin % | 53.97% |
| Delivered Orders | 9,312 |
| Average Order Value | ₹5,968.35 |
| Active Customers | 1,991 |

## Operational measures

```DAX
Placed Orders = DISTINCTCOUNT(Fact_Orders[order_id])
Orders by Status = DISTINCTCOUNT(Fact_Orders[order_id])
Returned Orders = CALCULATE(DISTINCTCOUNT(Fact_Orders[order_id]),
    Fact_Orders[order_status] = "Returned")
Cancelled Orders = CALCULATE(DISTINCTCOUNT(Fact_Orders[order_id]),
    Fact_Orders[order_status] = "Cancelled")
Processing Orders = CALCULATE(DISTINCTCOUNT(Fact_Orders[order_id]),
    Fact_Orders[order_status] = "Processing")
Delivery Rate % = DIVIDE([Delivered Orders], [Placed Orders], 0)
Return Rate % = DIVIDE([Returned Orders], [Placed Orders], 0)
Shipping Cost = CALCULATE(SUM(Fact_Orders[shipping_cost]),
    Fact_Orders[order_status] IN {"Delivered", "Processing"})
Units Sold = CALCULATE(SUM(Fact_Orders[quantity]),
    Fact_Orders[order_status] IN {"Delivered", "Processing"})
```

Verified order-status values:

| Measure | Value |
|---|---:|
| Placed Orders | 12,000 |
| Delivered Orders | 9,312 |
| Processing Orders | 621 |
| Returned Orders | 1,223 |
| Cancelled Orders | 844 |
| Delivery Rate % | 77.60% |
| Return Rate % | 10.19% |

`Returned` is not subtracted from `Delivered`. The funnel uses `Placed ->
Delivered`, with Cancelled, Processing and Returned shown as mutually exclusive
exit categories. See `sql/11_order_funnel.sql` and `data/metrics.json`.
