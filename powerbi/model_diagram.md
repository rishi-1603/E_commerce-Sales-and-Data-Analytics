# Power BI Star Schema & Relationship Architecture

```
                      +----------------------------+
                      |        Dim_Calendar        |
                      +----------------------------+
                      | Date (PK)                  |
                      | Year, Quarter, Month       |
                      | MonthName, DayOfWeek       |
                      +-------------+--------------+
                                    | 1
                                    | 
                                    | *
+---------------------------+       |       +---------------------------+
|       Dim_Customers       |       |       |       Dim_Products        |
+---------------------------+       |       +---------------------------+
| customer_id (PK)          +-------+-------+ product_id (PK)           |
| signup_date               | 1   * | *   1 | product_name, category    |
| customer_segment          |       |       | unit_cost, list_price     |
| region, city              |       v       | target_margin_pct         |
+---------------------------+ +-----------+ +---------------------------+
                              |Fact_Orders|
                              +-----------+
                              |order_id   |
                              |customer_id|
                              |product_id |
                              |order_date |
                              |status     |
                              |quantity   |
                              |unit_price |
                              |discount   |
                              |item_total |
                              +-----------+
```

### Relationship Properties
1. **Fact_Orders[customer_id] -> Dim_Customers[customer_id]:** Many-to-One (*:1), Single Direction Filter.
2. **Fact_Orders[product_id] -> Dim_Products[product_id]:** Many-to-One (*:1), Single Direction Filter.
3. **Fact_Orders[order_date] -> Dim_Calendar[Date]:** Many-to-One (*:1), Single Direction Filter.
