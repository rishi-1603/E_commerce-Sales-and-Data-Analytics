# EcomAnalytics — Upgrade Roadmap

**Goal:** turn the existing E-Commerce Sales & Customer Analytics project into a polished,
AI-assisted business intelligence portfolio piece — without rebuilding the dataset or the dashboard.

Status: **planned** (current project is complete at 222/222 tests; this roadmap describes the next phase).

---

## 1. What to keep (foundation)

The existing dataset, dashboard and analysis stay as the foundation. Do not replace them.

Seven existing pages, each upgraded rather than redesigned:

| Existing page | Upgrade |
|---|---|
| Executive Overview | KPI comparisons and business insights |
| Sales Performance | Product/category contribution and trend analysis |
| Customer RFM | Segment performance and recommendations |
| Retention & Cohorts | Mature-cohort comparisons and retention analysis |
| Churn Analysis | Customer inactivity and reactivation priorities |
| Product Profitability | Profit contribution and margin analysis |
| Revenue Forecast | Backtesting, forecast accuracy and scenarios |

Keep the dark dashboard style, existing navigation, frontend and Chart.js visualisations.
First, resolve metric inconsistencies (including the differing completed/delivered order counts) so
every calculation uses one consistent definition.

## 2. The four upgrades

### A. Power BI — main additional BI deliverable

Build one Power BI report on the **same existing dataset**. Four pages only:

1. Executive Sales Overview
2. Product & Category Performance
3. Customer Segmentation & Retention
4. Revenue Forecast & Business Insights

Skills demonstrated: Power Query, star-schema modelling where the dataset supports it, relationships,
DAX measures (CALCULATE, FILTER, DIVIDE, DISTINCTCOUNT), time intelligence, drill-through, bookmarks,
tooltips, slicers, report performance and access control.

Deliverable: `EcomAnalytics_PowerBI.pbix`

### B. Advanced Excel — one professional business reporting workbook

`EcomAnalytics_Business_Reporting.xlsx`

| Sheet | Work |
|---|---|
| Executive KPIs | Monthly performance and PivotTables |
| Sales Analysis | Category, product and regional analysis |
| Customer RFM | Segment distribution and customer values |
| Retention | Cohort reporting |
| Forecast | Historical forecasts and scenarios |
| Reconciliation | Excel vs SQL vs dashboard figures |

Skills: XLOOKUP, INDEX/MATCH, SUMIFS/COUNTIFS/AVERAGEIFS, IF/IFERROR/date functions, PivotTables and
PivotCharts, Power Query, conditional formatting, data validation, Power Pivot basics, What-If Analysis.

The reconciliation sheet is the most valuable feature: the same KPI must produce the same value in
Excel, SQL and Power BI under identical filters.

### C. AI Data Analyst — the differentiating feature

Build one assistant inside the existing dashboard: **EcomAI Analyst**.

It answers questions such as:
- "Why did revenue decline this month?"
- "Which category contributes most to revenue?"
- "Which customer segment has the highest historical spend?"
- "Show customers inactive for more than 180 days."
- "Compare this month's orders with the previous month."
- "Which products have declining performance?"

Implementation workflow:

1. User question → LLM understands intent
2. Approved KPI definitions → generate SQL
3. SQLGlot validates the read-only query
4. Query runs against the existing dataset
5. Validate results
6. Generate chart + evidence-backed explanation
7. Show SQL and evidence to the user

Components: Gemini API, Python application logic, existing database/source, SQLGlot for SQL validation,
Pydantic for structured output, existing dashboard as the interface.

Add three AI capabilities only:
1. Natural-language questions to validated SQL
2. Evidence-backed business insight summaries
3. Weekly executive report generation

Important: use approved metric definitions and read-only database access. Show the SQL and source
calculations. AI must never invent a KPI or claim that correlation proves causation.

### D. Data Quality & Business Insights

Add one supporting section to the dashboard.

**Data Quality Centre:**
- Missing-value checks
- Duplicate-record checks
- Invalid order-status checks
- Primary/foreign-key validation where applicable
- Revenue reconciliation
- Customer-count reconciliation
- Dataset reporting period
- Failed data-quality tests

**Business Insights Centre** — every insight follows:

| Section | Example |
|---|---|
| Observation | Category revenue declined |
| Evidence | Actual period comparison from the dataset |
| Impact | Contribution to total revenue movement |
| Recommendation | Investigate affected product groups |
| Measurement | Track category revenue in the next reporting period |

Do not add new analytical domains, external datasets or fictional business figures.

## 3. Final technical stack

| Category | Technology |
|---|---|
| Programming | Python |
| Data analysis | Pandas, NumPy |
| Database | PostgreSQL |
| Advanced SQL | Joins, CTEs, window functions, subqueries |
| Statistics | SciPy, statsmodels |
| Machine learning | Scikit-learn |
| Existing dashboard | JavaScript, Chart.js, existing frontend |
| BI | Power BI, DAX, Power Query |
| Spreadsheets | Advanced Excel, PivotTables, Power Query |
| AI | Gemini API, prompt engineering, text-to-SQL |
| AI safety | SQLGlot, Pydantic, read-only queries |
| Testing | pytest |
| Data quality | SQL validation, Python checks |
| Version control | Git, GitHub |
| Automation | GitHub Actions |

Do not add Tableau (Zomato covers that), Kafka, Spark, Airflow, multi-agent AI or extra databases.

## 4. Implementation order

| Phase | Work | Result |
|---|---|---|
| 1 | Audit existing dataset, calculations and source code | Verified baseline |
| 2 | Correct revenue, profit, order and cohort calculations | Trusted KPIs |
| 3 | Improve all seven existing pages | Better e-commerce dashboard |
| 4 | Build Power BI report | `.pbix` report |
| 5 | Create Excel reporting workbook | `.xlsx` workbook |
| 6 | Add EcomAI Analyst | Working AI assistant |
| 7 | Add data quality and business insights | Reliable reporting layer |
| 8 | Test and document everything | Recruiter-ready release |

## 5. Target evaluation (90+/100)

| Evaluation area | Weight |
|---|---|
| Business understanding and KPI design | 20 |
| SQL and Python analysis | 20 |
| Data correctness and quality | 15 |
| Power BI and Excel | 15 |
| Existing dashboard and storytelling | 10 |
| AI integration and evaluation | 10 |
| Documentation and reproducibility | 10 |
| **Total** | **100** |

The score becomes realistic when every KPI is verified, all three reporting interfaces reconcile,
AI answers are traceable, and the project is reproducible.

## 6. Resume bullet (after implementation)

**EcomAnalytics | Revenue & Growth Intelligence Platform**
*Python, SQL, PostgreSQL, Power BI, Advanced Excel, Pandas, Scikit-learn, Generative AI*

- Analysed 12,000 orders across 1,991 customers and 150 products using Python and SQL, identifying
  sales trends, customer segments and product-performance patterns across the 2022–2024 reporting period.
- Applied RFM segmentation and cohort analysis to evaluate customer purchasing behaviour and retention,
  identifying 441 medium-risk cooling-off customers from a leakage-free churn model for targeted
  re-engagement analysis.
- Developed an interactive commerce intelligence platform with Power BI reporting, Excel-based KPI
  reconciliation and an AI-assisted analytics copilot, enabling business users to explore performance
  trends through validated SQL and evidence-backed insights.

Use the third bullet only after completing those upgrades. Verify every metric against the current
source before publishing the first two.

## 7. Final decision

Keep EcomAnalytics structurally as it is, upgrade its analytical quality, and add only Power BI,
Excel, EcomAI and data-quality/business-insight capabilities. This is the right balance: strong
traditional Data Analyst foundations plus practical AI skills, without turning one project into an
oversized collection of technologies.

For the current Indian Data Analyst market, SQL, Excel, Python and Power BI continue to appear
prominently in job-posting skill summaries. Treat those figures as a sample, not the entire market.
