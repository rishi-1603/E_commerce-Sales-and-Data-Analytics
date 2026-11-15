# Power BI Build Specification — EcomAnalytics

**Status:** implemented and verified as a PBIP/PBIR project. Open
`powerbi/pbix/EcomAnalytics.pbip` in Power BI Desktop. A legacy `.pbix` binary is
not shipped; the PBIP is the source of truth and can be saved as `.pbix` locally
if a binary handoff is specifically required.

**Sources of truth**
- Data model: `powerbi/model_diagram.md`
- DAX measures: `powerbi/dax_measures.md`
- Reconciliation targets: `powerbi/reconciliation_matrix.csv`
- Power Query steps: `powerbi/power_query/`
- Underlying data: `data/processed/master_orders.csv`, `data/raw/customers.csv`, `data/raw/products.csv`

---

## 1. Prerequisites
- Power BI Desktop (latest, free) installed.
- The repo cloned locally; data files present.
- Familiarity with the schema in `powerbi/model_diagram.md`.

## 2. Data source
- **Mode:** Import (not DirectQuery) — static snapshot, matches the dashboard's data.
- The committed PBIP imports `powerbi/pbix/data/Fact_Orders.csv` as `Fact_Orders`,
  `powerbi/pbix/data/Dim_Customers.csv` as `Dim_Customers`,
  `powerbi/pbix/data/Dim_Products.csv` as `Dim_Products`, and
  `powerbi/pbix/data/Dim_Calendar.csv` as `Dim_Calendar`.
- Build `Dim_Calendar` in Power Query (date range from min to max order_date, with Year/Quarter/Month/DayOfWeek).

## 3. Data model (star schema)
Follow `powerbi/model_diagram.md` exactly:
- `Fact_Orders[customer_id] -> Dim_Customers[customer_id]` (Many-to-One, single direction)
- `Fact_Orders[product_id] -> Dim_Products[product_id]` (Many-to-One, single direction)
- `Fact_Orders[order_date] -> Dim_Calendar[Date]` (Many-to-One, single direction)

## 4. DAX measures
The model contains the 18 measures documented in `powerbi/dax_measures.md`. Verified benchmarks:
- Total Revenue = Rs. 5.93 Cr (59,283,619.32)
- Gross Profit = Rs. 3.20 Cr (31,997,341.64)
- Gross Margin % = 53.97%
- Delivered Orders = 9,312
- Processing Orders = 621
- Placed Orders = 12,000
- Returned Orders = 1,223
- Return Rate % = 10.19% of placed orders
- AOV = Rs. 5,968.35
- Active Customers = 1,991
- MoM Revenue Change % (time intelligence)

## 5. Report pages (4 Power BI pages)

### Page 1 — Executive Overview
- KPI cards: Total Revenue, Gross Profit, Gross Margin %, Delivered Orders, Active Customers, AOV
- Line chart: Total Revenue by Month (Dim_Calendar)
- Bar chart: Revenue by Category (Dim_Products)
- Slicer: Year

### Page 2 — Sales Performance
- Revenue by subcategory and month
- Category reconciliation table
- Gross profit by category

### Page 3 — Customer Insights
- Revenue by segment, region and acquisition channel
- Top-customer table
- Segment economics table

### Page 4 — Order Operations
- Orders by status and month
- Order-status mix
- Shipping cost and return-rate trends

## 6. Interactivity
- Year slicer on the Executive Overview page.
- Cross-filtering between visuals where supported by the report definition.
- Tooltips and labels are provided by Power BI's visual configuration.

## 7. Performance & access
- Hide unused columns; mark Dim_Calendar as a date table.
- Set RLS roles if publishing (optional): Region-based filtering.
- Verify with Performance Analyzer before publishing.

## 8. Verification checklist (before declaring done)
- [ ] Total Revenue = Rs. 5.93 Cr (59,283,619.32)
- [ ] Gross Profit = Rs. 3.20 Cr (31,997,341.64)
- [ ] Gross Margin % = 53.97%
- [ ] Delivered Orders = 9,312
- [ ] Processing Orders = 621
- [ ] Placed Orders = 12,000
- [ ] Returned Orders = 1,223
- [ ] Return Rate % = 10.19% of placed orders
- [ ] AOV = Rs. 5,968.35
- [ ] Active Customers = 1,991
- [ ] Reconciliation matrix (`powerbi/reconciliation_matrix.csv`) all rows "OK"
- [ ] Four pages render without errors after Refresh now
- [ ] Save a local `.pbix` only when a binary handoff is required

## 9. Current verification boundary
- PBIP/PBIR structure, TMDL, relationships, UTF-8 BOM status and visual JSON are
  validated in the repository.
- Power BI Desktop must be available to refresh imported CSV data and perform
  the final local save/export. The repository does not claim that a `.pbix`
  binary is committed.
