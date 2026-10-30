# Power BI DAX Measures Specification
**Data Model:** E-Commerce Analytical Star Schema  
**Target Grain:** Transaction / Daily Aggregation  
**Reconciliation Target:** 100% numerical parity with PostgreSQL and Python (Pandas) pipelines.

---

### Core Commercial Measures

#### 1. Total Revenue
```dax
Total Revenue = 
CALCULATE(
    SUM(Fact_Orders[order_item_total]),
    Fact_Orders[order_status] IN {"Delivered", "Processing"}
)
```
* **Definition:** Cumulative revenue realized from delivered customer orders and committed in-flight processing orders. Excludes cancelled and returned orders.
* **SQL Equivalent:** `SUM(order_item_total) WHERE order_status IN ('Delivered', 'Processing')`
* **Verified Benchmark:** Rs. 59,328,412.50 (Rs. 5.93 Cr).

---

#### 2. Delivered Revenue
```dax
Delivered Revenue = 
CALCULATE(
    SUM(Fact_Orders[order_item_total]),
    Fact_Orders[order_status] = "Delivered"
)
```
* **Definition:** Purely settled, cash-realized commercial revenue.

---

#### 3. Total COGS (Cost of Goods Sold)
```dax
Total COGS = 
CALCULATE(
    SUMX(
        Fact_Orders,
        Fact_Orders[quantity] * RELATED(Dim_Products[unit_cost])
    ),
    Fact_Orders[order_status] IN {"Delivered", "Processing"}
)
```

---

#### 4. Gross Profit
```dax
Gross Profit = [Total Revenue] - [Total COGS]
```
* **Verified Benchmark:** Rs. 21,348,228.50.

---

#### 5. Gross Margin %
```dax
Gross Margin % = 
DIVIDE([Gross Profit], [Total Revenue], 0)
```
* **Verified Benchmark:** 36.00%.

---

#### 6. Delivered Orders Count
```dax
Delivered Orders = 
CALCULATE(
    DISTINCTCOUNT(Fact_Orders[order_id]),
    Fact_Orders[order_status] = "Delivered"
)
```
* **Verified Benchmark:** 8,421 orders.

---

#### 7. Return Rate %
```dax
Return Rate % = 
VAR TotalCompleted = 
    CALCULATE(
        DISTINCTCOUNT(Fact_Orders[order_id]),
        Fact_Orders[order_status] IN {"Delivered", "Returned"}
    )
VAR ReturnedCount = 
    CALCULATE(
        DISTINCTCOUNT(Fact_Orders[order_id]),
        Fact_Orders[order_status] = "Returned"
    )
RETURN
    DIVIDE(ReturnedCount, TotalCompleted, 0)
```
* **Verified Benchmark:** 10.85% (1,025 returns / 9,446 completed deliveries).

---

#### 8. Average Order Value (AOV)
```dax
Average Order Value = 
DIVIDE(
    [Total Revenue],
    CALCULATE(
        DISTINCTCOUNT(Fact_Orders[order_id]),
        Fact_Orders[order_status] IN {"Delivered", "Processing"}
    ),
    0
)
```
* **Verified Benchmark:** Rs. 5,972.86.

---

#### 9. Active Customers Count
```dax
Active Customers = 
CALCULATE(
    DISTINCTCOUNT(Fact_Orders[customer_id]),
    Fact_Orders[order_status] IN {"Delivered", "Processing"}
)
```
* **Verified Benchmark:** 1,991 Customers.

---

#### 10. Month-over-Month (MoM) Revenue Growth %
```dax
MoM Revenue Change % = 
VAR CurrentMonthRev = [Total Revenue]
VAR PrevMonthRev = 
    CALCULATE(
        [Total Revenue],
        DATEADD(Dim_Calendar[Date], -1, MONTH)
    )
RETURN
    DIVIDE(CurrentMonthRev - PrevMonthRev, PrevMonthRev, 0)
```
