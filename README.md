# E-Commerce Sales & Customer Analytics

<p align="center">
<a href="https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics">View GitHub Repository</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
<a href="https://1drv.ms/p/s!AkB2pJZ-j1tWgjobz6ynoTsO1EkQ?e=K7lqJ2">View Live Power BI Dashboard</a>
</p>

## SECTION 1 — PROFESSIONAL PROJECT HEADER

<p align="center">
<img src="screenshots/dashboard_executive_overview.png" alt="E-Commerce Executive Overview Dashboard" width="700"/>
</p>

<p align="center">
<h1>E-Commerce Sales & Customer Analytics</h1>
<p>Comprehensive Business Intelligence project analyzing e-commerce transaction data to reveal sales performance, customer behavior, and operational insights. The project connects a synthetic INR-denominated dataset (12,000 orders, 150 products, 2,000 customers) through a star-schema model to a professional 4-page Power BI dashboard and a Python analytics pipeline.</p>
<p>Technologies: Python · Pandas · Scikit-learn · Power BI · SQL · Mermaid · Git</p>
</p>

<p align="center">
<a href="https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics">GitHub Repository</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
<a href="https://1drv.ms/p/s!AkB2pJZ-j1tWgjobz6ynoTsO1EkQ?e=K7lqJ2">View Live Power BI Dashboard</a>
</p>

## SECTION 2 — DASHBOARD PREVIEW / HERO VISUAL

<p align="center">
<img src="screenshots/dashboard_executive_overview.png" alt="Executive Overview Dashboard - KPI cards and charts showing e-commerce metrics" />
<br>
<i>Executive Overview — 6 KPI cards with verified revenue 59.28M / profit 32.00M / margin 53.97% / 9,312 delivered orders / 5.97K AOV / 1,991 customers</i>
</p>

<p align="center">
<a href="https://1drv.ms/p/s!AkB2pJZ-j1tWgjobz6ynoTsO1EkQ?e=K7lqJ2">View Live Power BI Dashboard</a>
</p>

## SECTION 3 — PROJECT OVERVIEW

**E-Commerce Sales & Customer Analytics** is a comprehensive Business Intelligence project that analyzes e-commerce transaction data to reveal sales performance, customer behavior, and operational insights. The project connects a synthetic INR-denominated dataset (12,000 orders, 150 products, 2,000 customers) through a star-schema model to a professional 4-page Power BI dashboard and a Python analytics pipeline.

The project demonstrates end-to-end data analytics: from raw data cleaning and validation, through star-schema modeling, to executive-ready visualizations and statistical analysis. Every KPI, chart, and insight is grounded in verified data with full reconciliation across SQL, Python, and Power BI implementations.

The analytical objective is to provide stakeholders with actionable insights into sales performance, customer behavior, and operational efficiency. The business value lies in enabling data-driven decisions about product performance, customer segmentation, fulfillment efficiency, and retention patterns — all backed by reconciled figures and documented methodology.

## SECTION 4 — BUSINESS PROBLEM AND OBJECTIVES

**Business Problem**: Analyze e-commerce sales and customer data to provide actionable insights into sales performance, customer behavior, and operational efficiency. The project must reconcile all figures across SQL queries, Python preprocessing, and the Power BI model while disclosing the synthetic-data nature of the dataset.

**Analytical Objectives**:
- Measure sales performance and revenue trends across products, categories, and time
- Segment customers by value, behavior, and acquisition channel
- Analyze order fulfillment and operational metrics (delivered vs. processing vs. returned/cancelled)
- Identify factors associated with churn and repeat purchase
- Provide forecasting and cohort retention insights

**Business Value**: Stakeholders can answer: Which products drive revenue? Which customer segments are most valuable? What is the true fulfillment efficiency? What does the retention curve look like? All insights are backed by reconciled figures and documented methodology.

## SECTION 5 — PROJECT HIGHLIGHTS / KEY FEATURES

### Sales and Revenue Analytics
- **Revenue performance**: Total revenue ₹5.93 Cr across Delivered + Processing orders (Cancelled and Returned excluded per documented convention)
- **Order trends**: 12,000 orders placed → 9,312 delivered + 621 processing + 844 cancelled + 1,223 returned
- **Product and category performance**: 150 products across 5 categories with revenue, margin and contribution analysis
- **Regional analysis**: North/South/East/West/Central segmentation with revenue and order volume

### Customer Analytics
- **Customer segmentation**: 1,991 active customers segmented by value and behavior into cohorts
- **Purchase behavior**: Order frequency, average order value (₹5,968.35), repeat purchase patterns
- **Churn risk**: 448 cooling-off customers identified for win-back modeling

### Retention and Churn Analytics
- **Cohort retention**: Customer retention by first-purchase month with verified M0=100% pattern
- **Retention trends**: Month-1 retention rises from ~15-28% (2023 cohorts) to 55-88% (late 2024)
- **Funnel**: Placed (12,000) → Delivered (9,312) → Kept (8,089 after returns) — delivery rate 77.6%, keep rate 86.9%

### Advanced Analytics
- **Sales forecasting**: H1 2025 projection ensemble (linear trend + Holt-Winters) with bootstrap 95% CI
- **RFM segmentation**: 8 named segments (Champions, Loyal Customers, Potential Loyalists, Recent Customers, About To Sleep, Needs Attention, At Risk, Lost Customers)
- **Churn modeling**: 5-fold cross-validated AUC 0.65 with post-leakage honest evaluation
- **Discount analysis**: Economics of discount ladder with break-even lift calculations

## SECTION 6 — DASHBOARD SHOWCASE

### Executive Overview

<p align="center">
<img src="screenshots/dashboard_executive_overview.png" alt="Executive Overview Dashboard" />
</p>

<p>This page displays the dashboard's top-level KPIs and overall analytical purpose. The 6 KPI cards provide immediate access to the most critical metrics: revenue, profit, margin, delivered orders, AOV, and active customers. The line chart shows revenue by month (Jan→Dec), category columns compare performance, payment bars show distribution, and the segment table includes an exact total row.</p>

### Sales Performance Analysis

<p align="center">
<img src="screenshots/dashboard_sales_performance.png" alt="Sales Performance Dashboard" />
</p>

<p>This page explores sales performance in detail. Subcategory columns show revenue by product subtype, the line chart tracks delivered orders by month (Jan→Dec), the reconciliation table provides exact verified totals (Revenue 59.28M / COGS 27.29M / Gross Profit 32.00M / Margin 53.97%), and the Gross Profit by category chart highlights profitability by product category.</p>

### Customer Analytics

<p align="center">
<img src="screenshots/dashboard_customer_insights.png" alt="Customer Insights Dashboard" />
</p>

<p>This page analyzes customer behavior. Segment bars show revenue by customer segment, region bars compare performance by geography, acquisition channel columns illustrate the effectiveness of different marketing channels, and the top customers table includes exact revenue and delivered order totals.</p>

### Order Operations

<p align="center">
<img src="screenshots/dashboard_order_operations.png" alt="Order Operations Dashboard" />
</p>

<p>This page focuses on operational metrics. The stacked column chart shows order item total by month with a legend for order status, the clustered column chart displays absolute values by status, 3 performance KPI cards (Return Rate %, Delivered Orders, Delivered Revenue), and the shipping cost line tracks monthly shipping expenses.</p>

## SECTION 7 — KEY PERFORMANCE INDICATORS

| KPI | Definition | Analytical Purpose |
| --- | --- | --- |
| **Total Revenue** | Revenue across Delivered + Processing orders (INR) | Core sales metric — excludes Cancelled and Returned orders |
| **Gross Margin** | Gross Profit / Revenue (percentage) | Profitability as a share of revenue |
| **Completed Orders** | Orders with status Delivered (9,312 of 12,000 placed) | Core volume metric — delivered only |
| **Active Customers** | Distinct customers with at least one order | Reach and audience metric |
| **Average Order Value** | Revenue / COUNT(DISTINCT order_id) (₹5,968.35) | Efficiency per transaction |
| **Delivery Rate** | Delivered Orders / Placed Orders (77.6%) | Funnel efficiency — orders that reach delivery |
| **Churn Model AUC** | 5-fold cross-validated AUC 0.65 (post-leakage) | Predictive modeling quality — honest evaluation |

*All KPI definitions are documented in `data/metrics.json` with independent verification across SQL, Python, and Power BI implementations.*

## SECTION 8 — DATASET OVERVIEW

| Property | Value |
| --- | --- |
| **Source** | Synthetic dataset generated for portfolio project (INR-denominated) |
| **Original Link** | `data/raw/` directory (orders.csv, order_items.csv, customers.csv, products.csv) |
| **Records** | 12,000 orders • 25,000+ order items • 2,000 customers • 150 products |
| **Granularity** | Order line-item level |
| **Time Coverage** | 3-year window (2022–2024) |
| **Currency** | Indian Rupee (INR) |
| **Disclosure** | Fully synthetic, seeded dataset — reproducible methods are the story |

**Data Dictionary**: See `data/DATA_DICTIONARY.md` for complete column definitions and conventions.

**Key Conventions** (from `metrics.json`):
- Revenue = SUM(line_total) over orders with status **Delivered or Processing** (Cancelled and Returned excluded)
- Completed Orders = Distinct orders with status **Delivered** (9,312 of 12,000 placed)
- Churn Model features strictly before cutoff; label = no purchase in the 180 days after cutoff
- All figures reconciled across SQL queries, Python preprocessing, and Power BI model

## SECTION 9 — DATA CLEANING AND PREPROCESSING

The preprocessing pipeline performs the following validated steps:

1. **Duplicate detection**: Removed exact duplicate records; verified legitimate duplicates retained
2. **Missing-value treatment**: Imputed based on column meaning — not blindly replaced with zero or mean
3. **Data type conversion**: All date columns normalized to consistent format; categorical fields standardized
4. **Data validation**: Cross-column referential integrity checked (every customer_id in orders references customers table)
5. **Date normalization**: Order dates parsed; fiscal months and year extracted for trend analysis
6. **Category standardization**: Product categories normalized to 5 consistent values (Electronics, Clothing, Home & Garden, Sports, Beauty)
7. **Outlier investigation**: Extreme values investigated — determined legitimate observations or data errors case-by-case
8. **Feature engineering**: RFM metrics (Recency, Frequency, Monetary) computed; derived columns for margin, discount impact, cohort markers
9. **Data transformation**: Aggregations performed at correct grain; many-to-many join mistakes avoided

Important: The **same data-cleaning pipeline produces consistent results when executed again** — reproducibility is verified by the test suite.

## SECTION 10 — ANALYTICAL METHODOLOGY

### Exploratory Data Analysis
- Initial investigation of distributions, ranges, and relationships across all source tables
- Identification of key analytical questions and metric definitions
- Validation of data quality before any modeling

### Descriptive Analytics
- **Revenue and margin calculation**: SUM(line_total) where orders.status IN ('Delivered','Processing'); Gross Profit = Revenue – COGS; Margin = Gross Profit / Revenue
- **Order funnel**: Placed (all 12,000) → Delivered (9,312) → Kept (8,089 after returns) — with exact counts from SQL `valid_orders` definition
- **Segmentation**: Customer segmentation by value, acquisition channel, and product preference

### RFM Analysis
- Recency = days since last purchase; Frequency = order count; Monetary = total spend
- 8 named segments from K-Means clustering on RFM quintiles
- Segment sizes: Champions 317, Loyal Customers 495, Potential Loyalists 29, Recent Customers 248, About To Sleep 354, Needs Attention 194, At Risk 221, Lost Customers 133

### Cohort Retention Analysis
- Customers grouped by first-purchase month; retention M_k = share with ≥1 purchase k months after cohort month
- M0 = 100% by definition; verified pattern: Month-1 retention rises from ~15-28% (2023 cohorts) to 55-88% (late 2024)

### Sales Forecasting
- H1 2025 projection: ensemble of linear trend + Holt-Winters, bootstrap 95% CI
- Rolling-origin backtest vs naive baselines (10 origins x 3 horizons)
- MASE scale: in-sample seasonal-naive MAE = INR 1,023,756

### Churn Modeling
- Features strictly before cutoff; label = no purchase in 180 days after cutoff
- 5-fold CV: ROC-AUC 0.6484, PR-AUC 0.3616, Brier score 0.1829 (isotonic calibrated)
- Operating threshold t* = 0.1 selected via expected-profit maximizing on calibration slice
- Caveat: Profit figures are expected values under illustrative assumptions; no campaign has been run

### Discount Economics
- Margin as a share of LIST price: margin_pct_of_list = profit / (line_total / (1 – discount_pct))
- Break-even volume lift: (margin_pct_of_list at 0%) / (margin_pct_of_list at depth) – 1
- Kruskal-Wallis test of quantity across discount depths, alpha = 0.05; p = 0.305 (no significant volume response detected)

## SECTION 11 — KEY BUSINESS FINDINGS

1. **Delivery efficiency**: Only 77.6% of placed orders reach delivery — 22.4% exit via cancellation (844) or return (1,223). Of those delivered, 86.9% are kept (not returned), meaning 13.1% of delivered orders are returned.

2. **Revenue concentration**: Top 10% of customers by revenue contribute disproportionately — the project's concentration metric shows the top decile holds ~42% of projected CLV, consistent with typical e-commerce patterns.

3. **Category performance**: Sports category generates the highest revenue per product but exhibits a negative discount effect (-6.96% at 20pp), while other categories show different discount-response patterns.

4. **Retention improvement**: Later-cohort customers (2024) show significantly higher retention (55-88% month-1) compared to early cohorts (2023: 15-28%), suggesting operational improvements over the 3-year window.

5. **Churn risk bands**: 448 cooling-off customers identified with mean churn probability 0.408; the win-back campaign economics show expected profit per contact of ₹541 but require a 12.89% churn probability to break even.

6. **Discount impact**: No significant volume response detected (Kruskal-Wallis p = 0.305), but margin erosion is substantial — break-even lift at 10% discount = 10.61%, at 20% = 23.12%.

## SECTION 12 — TECHNOLOGY STACK

| Category | Technologies |
| --- | --- |
| **Programming** | Python |
| **Data Manipulation** | Pandas, NumPy |
| **Database** | SQL Server (TMDL star-schema model) |
| **Querying** | SQL (12 KPI analysis scripts in `sql/`) |
| **Statistics** | Scikit-learn 1.6.1, NumPy 2.3.5, SciPy 1.17.1 |
| **Visualization** | Power BI Desktop, Matplotlib, seaborn |
| **Forecasting** | Holt-Winters, linear trend, bootstrap resampling |
| **Deployment** | Power BI Service (.pbix file), GitHub Pages |

## SECTION 13 — PROJECT ARCHITECTURE AND WORKFLOW

```
flowchart TD
    A[Raw Dataset] --> B[Data Validation]
    B --> C[Data Cleaning]
    C --> D[Data Transformation]
    D --> E[Analytical Processing]
    E --> F[KPI Calculation]
    F --> G[Dashboard]
```

**Data Flow**:
Raw Dataset (CSVs) → Data Cleaning (pipeline in `python/eda/`) → Data Transformation (star-schema TMDL) → Analytical Processing (SQL queries + Python scripts) → KPI Calculation (documented in `metrics.json`) → Dashboard (4-page Power BI report)

**Workflow**:
1. Data ingestion from `data/raw/`
2. Cleaning and validation in `python/eda/01_eda_preprocessing.py`
3. Feature engineering and metric computation in `python/kpi_analysis.py`
4. Power BI model creation with star-schema in `powerbi/pbix/EcomAnalytics.SemanticModel/`
5. Report authoring with PBIR JSON in `powerbi/pbix/EcomAnalytics.Report/definition/`
6. Verification across SQL, Python, and Power BI implementations

## SECTION 14 — REPOSITORY STRUCTURE

```
E_commerce-Sales-and-Data-Analytics/
├─ dashboard/              # HTML dashboard files
├─ data/                   # Dataset and analytical outputs
│   ├─ raw/                # Source CSVs (orders, order_items, customers, products)
│   ├─ processed/          # Analytical outputs (RFM, CLV, forecast, churn)
│   ├─ DATA_DICTIONARY.md  # Complete column definitions and conventions
│   ├─ metrics.json        # KPI definitions with formulas and verified values
│   └─ metrics.json        # KPI definitions with formulas and verified values
├─ powerbi/                # Power BI project
│   ├─ pbix/               # .pbix file and PBIP project
│   ├─ EcomAnalytics.Report/definition/  # PBIR JSON (4 pages, 28 visuals)
│   ├─ EcomAnalytics.SemanticModel/definition/tables/  # TMDL star-schema
│   ├─ dax_measures.md     # 10 DAX measures with format strings
│   └─ reconciliation_matrix.csv  # Cross-validation across SQL/Python/PI
├─ sql/                    # 12 KPI analysis and data cleaning scripts
├─ python/                 # Python pipeline scripts
├─ tests/                  # 227 analytical and API tests
├─ reports/                # Detailed report artifacts
├─ docs/                   # Documentation and experiment designs
├─ screenshots/            # Dashboard screenshots for README
├─ .github/                # GitHub Actions and CI configuration
├─ README.md               # This file
├─ requirements.txt
├─ RESUME_EVIDENCE.md
├─ DELIVERY_SUMMARY.md
└─ FINAL_ANSWER.md
```

## SECTION 15 — HOW TO RUN THE PROJECT LOCALLY

### Prerequisites

- Python 3.9+
- Git
- Power BI Desktop (for .pbix file inspection)

### Installation

```bash
# Clone the repository
git clone https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics.git
cd E_commerce-Sales-and-Data-Analytics

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Set up environment variables (no secrets required for this project)
```

### Data Loading

The dataset is included in the repository:

```bash
# Raw data is in data/raw/
# Processed outputs are in data/processed/
# No external data download required
```

### Running the Pipeline

```bash
# Example: Run the EDA preprocessing
python python/eda/01_eda_preprocessing.py

# Example: Run the KPI analysis
python python/kpi_analysis.py

# Example: Run the test suite
python -m pytest tests/ -v
# 227 tests pass
```

### Power BI Dashboard

1. Open `powerbi/pbix/EcomAnalytics.pbix` in Power BI Desktop
2. The report has 4 pages: Executive Overview, Sales Performance, Customer Insights, Order Operations
3. All measures are verified to the decimal benchmarks documented in `data/metrics.json`

## SECTION 16 — LIVE APPLICATION AND DEMO

- **Power BI Dashboard**: Open `powerbi/pbix/EcomAnalytics.pbix` in Power BI Desktop
- **Key navigation**: Four tabbed pages at the top of the canvas
- **Interactive features**: Filters on Year (slicer), category selection, status filtering
- **Verified data**: Every KPI tooltip displays reconciled figures

## SECTION 17 — TESTING AND VALIDATION

The project includes **227 passing tests** covering:

- Data quality checks (missing values, duplicates, types, outliers)
- KPI verification (independent calculation across SQL, Python, Power BI)
- Dashboard consistency (filter behavior, KPI-card alignment)
- SQL query validation
- Python pipeline correctness
- analytical formula validation

Test files are in `tests/` and include:
- `test_data_quality.py` — dataset validation
- `test_dashboard_consistency.py` — KPI and filter verification
- `test_business_reporting_workbook.py` — business logic checks
- `test_churn_calibration.py` — ML model calibration
- `test_discount_engine.py` — discount economics
- `test_forecast_backtest.py` — forecasting validation
- And 10 more specialized test files

## SECTION 18 — LIMITATIONS

- **Synthetic dataset**: This is a deliberately created portfolio dataset, not real commercial e-commerce data. All methods are reproducible; the synthetic nature is disclosed.
- **Churn model**: Post-leakage honest evaluation; AUC 0.65 reflects realistic separability — no inflated claims.
- **Forecasting**: H1 2025 projection assumes trend/seasonality continues; evaluate against actuals over time.
- **Discount analysis**: Observational data; discount depth is chosen by business, not randomly assigned — association is not automatically causal.
- **Cohort retention**: 3-year window limits longitudinal insights; newer cohorts have fewer observed months.

## SECTION 19 — FUTURE IMPROVEMENTS

- Automated data refresh pipeline
- Additional analytical dimensions (product rating, gender, age segmentation)
- Improved churn model with feature engineering and hyperparameter tuning
- Scheduled email reports for stakeholder delivery
- Interactive web dashboard (Power BI Web or Streamlit) for broader accessibility
- Advanced predictive modeling (XGBoost, LightGBM) with proper out-of-time validation
- Integration with live e-commerce API sources (if/when real data becomes available)

## SECTION 20 — AUTHOR AND PROJECT LINKS

- **GitHub**: [@rishi-1603](https://github.com/rishi-1603)
- **Project**: [E_commerce-Sales-and-Data-Analytics](https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics)
- **Live Dashboard**: Power BI `.pbix` file — open in Power BI Desktop
- **LinkedIn**: [linkedin.com/in/rishi-1603](https://linkedin.com/in/rishi-1603)

---

*This project was developed as a portfolio demonstration of end-to-end data analytics: from synthetic dataset through verified KPIs, reconciled across SQL, Python, and Power BI implementations. All figures are documented and reconcilable. The synthetic-data disclosure is intentional and prominent.*