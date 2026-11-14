# Power BI Build Specification — EcomAnalytics

**Status:** documentation complete; the `.pbix` itself must be built in Power BI Desktop
(Power BI Desktop is a Windows GUI application and cannot be generated programmatically).
This document is the build guide: follow it step by step to produce `EcomAnalytics_PowerBI.pbix`.

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
- Load `data/processed/master_orders.csv` as `Fact_Orders`, `data/raw/customers.csv` as `Dim_Customers`,
  `data/raw/products.csv` as `Dim_Products`.
- Build `Dim_Calendar` in Power Query (date range from min to max order_date, with Year/Quarter/Month/DayOfWeek).

## 3. Data model (star schema)
Follow `powerbi/model_diagram.md` exactly:
- `Fact_Orders[customer_id] -> Dim_Customers[customer_id]` (Many-to-One, single direction)
- `Fact_Orders[product_id] -> Dim_Products[product_id]` (Many-to-One, single direction)
- `Fact_Orders[order_date] -> Dim_Calendar[Date]` (Many-to-One, single direction)

## 4. DAX measures
Enter every measure from `powerbi/dax_measures.md` (10 measures) into the model. Verified benchmarks:
- Total Revenue = Rs. 5.93 Cr (59,283,619.32)
- Gross Profit = Rs. 3.20 Cr (31,997,341.64)
- Gross Margin % = 53.97%
- Delivered Orders = 9,312
- Processing Orders = 621
- Return Rate % = 0.00% (no Returned orders in the revenue population)
- AOV = Rs. 5,968.35
- Active Customers = 1,991
- MoM Revenue Change % (time intelligence)

## 5. Report pages (4 pages only — do not recreate all 7 dashboard pages)

### Page 1 — Executive Sales Overview
- KPI cards: Total Revenue, Gross Profit, Gross Margin %, Delivered Orders, Active Customers, AOV
- Line chart: Total Revenue by Month (Dim_Calendar)
- Bar chart: Revenue by Category (Dim_Products)
- Slicers: Year, Quarter, Region
- Bookmark: "Reset filters"

### Page 2 — Product & Category Performance
- Matrix: Category x Subcategory with Revenue, Gross Profit, Margin %
- Bar chart: Top 10 products by revenue
- Scatter: Revenue vs Margin % by product
- Drill-through to product detail tooltip

### Page 3 — Customer Segmentation & Retention
- Donut: customer count by segment
- Bar: revenue by segment
- Line: monthly active customers trend
- Matrix: cohort retention (first-purchase month x months since)

### Page 4 — Revenue Forecast & Business Insights
- Line chart: historical revenue + forecast (use the forecast values from `reports/forecast_challenger.md`)
- KPI cards: forecast next 6 months, MASE
- Text box: "Business Insights" panel (Observation/Evidence/Impact/Recommendation/Measurement)

## 6. Interactivity
- Drill-through from Page 1 category bar to Page 2 filtered by category.
- Bookmarks for "Reset filters" and "Focus view".
- Tooltips on KPI cards showing the underlying measure definition.
- Slicers synced across pages via sync slicers.

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
- [ ] Return Rate % = 0.00% (no Returned orders in revenue population)
- [ ] AOV = Rs. 5,968.35
- [ ] Active Customers = 1,991
- [ ] Reconciliation matrix (`powerbi/reconciliation_matrix.csv`) all rows "OK"
- [ ] All 4 pages render without errors
- [ ] Drill-through and bookmarks work
- [ ] Save as `powerbi/EcomAnalytics_PowerBI.pbix`

## 9. What I (the agent) can and cannot do
- Can: write and verify the DAX, data model, page layout, and this spec.
- Cannot: generate a `.pbix` binary (Power BI Desktop is a GUI application). The `.pbix` is the
  one deliverable you must produce manually using this spec — estimated 2-4 hours of work.
