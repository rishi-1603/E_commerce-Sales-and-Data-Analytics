<div align="center">

# 📊 E-Commerce Sales & Customer Analytics

**An end-to-end data analytics project that analyzes sales performance, customer behavior,
product profitability, churn risk, and future revenue — to support data-driven business decisions.**

[🚀 Live Dashboard](https://ecomanalytics-dashboard.vercel.app/) ·
[🗄️ SQL Analysis](sql/README.md) ·
[📄 Analytics Reports](reports/) ·
[🧪 31 Passing Tests](tests/)

</div>

---

## 1. 🚀 Live Project

**Dashboard (deployed on Vercel):**

> ### 👉 https://ecomanalytics-dashboard.vercel.app/

A 6-page interactive analytics product — Executive Overview, Sales Performance,
Customer RFM, Churn, Product Profitability (BCG), and Revenue Forecast.
Every KPI on the live dashboard is verified against the pipeline output by an
automated test (see [Trust Layer](#7-analytics-modules)).

**GitHub Repository:**

> ### 👉 https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics

---

## 2. 💼 Business Problem

An e-commerce business with 3 years of transaction data is flying blind on four
questions that decide its profitability:

| # | Business Question | Where It's Answered |
|---|---|---|
| 1 | Which products generate the most revenue **and profit**? | SQL product analysis + Python BCG matrix |
| 2 | Which customer groups are most valuable? | RFM segmentation + CLV model |
| 3 | Which customers are at risk of leaving? | Leakage-free churn model |
| 4 | Which regions and channels perform best? | SQL regional & channel analysis |
| 5 | Which products deserve investment vs. delisting? | BCG Stars / Cash Cows / Question Marks / Dogs |
| 6 | What future revenue can the business plan for? | Holt-Winters ensemble forecast |

**The cost of not answering these:** retention budget sprayed evenly instead of
targeted, margin leaking into low-return SKUs, and inventory planning based on
guesswork instead of a forecast with honest error bars.

> **Honesty note:** the dataset is synthetically generated (seeded, fully
> reproducible) to demonstrate the complete methodology end-to-end. Numbers are
> illustrative; methods are production-grade. Details in
> [`reports/assumptions_and_limitations.md`](reports/assumptions_and_limitations.md).

---

## 3. 🔄 Project Overview — The Complete Workflow

```
Raw Data (4 CSV tables)
        ↓
Data Cleaning & Quality Audit — SQL (02) + 31 pytest checks
        ↓
Exploratory Data Analysis — Python (pandas)
        ↓
SQL Business Analysis — KPIs, sales, customers, products, regions, returns
        ↓
Customer Analytics — RFM segmentation + K-Means (silhouette-selected k)
        ↓
Machine Learning — churn prediction (forward-time split) + CLV
        ↓
Forecasting — statsmodels Holt-Winters + linear ensemble, bootstrap CI
        ↓
Interactive Dashboard — HTML/CSS/JS + Chart.js, deployed on Vercel
        ↓
Business Recommendations — decision log with owners, KPIs, and success metrics
```

The workflow runs **end-to-end with one command** (`python run_pipeline.py`,
8 automated steps with logging), and every output is validated by CI.

---

## 4. 📦 Dataset

| Table | Rows | Grain |
|---|---|---|
| `customers` | 2,000 | 1 row per customer (region, segment, acquisition channel, demographics) |
| `products` | 150 | 1 row per SKU (5 categories, cost & selling price, stock, rating) |
| `orders` | 12,000 | 1 row per order (date, status, payment method, discount, shipping) |
| `order_items` | ~21,000 | 1 row per line item (quantity, unit price, line total, cost) |

- **Date range:** January 2022 – December 2024 (3 years)
- **Important columns:** `order_date`, `status`, `discount_pct`, `line_total`,
  `cost_total`, `customer_id`, `product_id`, `region`, `category`
- **Canonical business rule** (identical in SQL, Python, and dashboard):
  revenue/profit metrics count only `Delivered` + `Processing` orders
- Full column documentation: [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md)

**Generated headline figures** (from this dataset, via the pipeline):

| Metric | Value |
|---|---|
| Total revenue (3 yrs) | ₹5.93 Cr |
| Gross profit / margin | ₹3.20 Cr / 54.0% |
| Revenue orders / active customers | 9,933 / 1,991 |
| Churn rate (180-day forward window) | 25.3% |
| 6-month revenue forecast | ₹3.27 Cr (bootstrap 95% CI) |

---

## 5. 🛠 Tech Stack

**Only technologies genuinely used in this repository.**

### Data & Analysis
`Python` · `pandas` · `NumPy`

### Database & SQL
`PostgreSQL` — schema design, CTEs, window functions (`NTILE`, `RANK`, `DENSE_RANK`, `LAG`, `PERCENTILE_CONT`), cohort analysis, indexes

### Machine Learning
`scikit-learn` — Logistic Regression, Random Forest, Gradient Boosting (churn) · K-Means (segmentation)

### Statistics
`SciPy` — Welch's t-test, ANOVA, Kruskal-Wallis, chi-square, effect sizes

### Forecasting
`statsmodels` (Holt-Winters) + linear-trend ensemble, residual-bootstrap confidence intervals

### Visualization
`Matplotlib` / `Seaborn` (20 pipeline charts) · `Chart.js` (live dashboard)

### Frontend
`HTML` · `CSS` · `JavaScript` (vanilla, no build step)

### Deployment & Version Control
`Vercel` (dashboard) · `Git` / `GitHub` · `GitHub Actions` (CI) · `pytest` (31 tests)

---

## 6. 🗄️ SQL Analysis — A Core Layer, Not a Keyword

**The entire analytical logic exists twice — once in PostgreSQL, once in pandas —
so results are cross-validated across two independent implementations.**

**8 professionally documented scripts** in [`sql/`](sql/README.md), each query
carrying a *Business Question → Why It Matters → Key Insight* contract:

| Script | Business focus | SQL techniques |
|---|---|---|
| [01_database_schema.sql](sql/01_database_schema.sql) | Warehouse structure | DDL, PK/FK constraints, indexes, views |
| [02_data_cleaning.sql](sql/02_data_cleaning.sql) | Data trustworthiness | Duplicate/orphan/impossible-value audits, `FILTER` |
| [03_kpi_analysis.sql](sql/03_kpi_analysis.sql) | Executive KPIs & growth | **`LAG`** for MoM/YoY growth, `NTILE` Pareto deciles |
| [04_sales_analysis.sql](sql/04_sales_analysis.sql) | Sales performance | **`RANK()`**, 7-day moving average (`ROWS BETWEEN`), conditional pivots |
| [05_customer_analysis.sql](sql/05_customer_analysis.sql) | RFM, CLV, cohorts | **`NTILE`** quintile RFM, cohort month-diff, **`LAG`** purchase gaps, `DENSE_RANK` VIPs |
| [06_product_analysis.sql](sql/06_product_analysis.sql) | Profitability & BCG | **`PERCENTILE_CONT ... OVER ()`** median-split BCG |
| [07_regional_analysis.sql](sql/07_regional_analysis.sql) | Regional performance | Partitioned `LAG` for regional YoY, dual `RANK` comparison |
| [08_return_analysis.sql](sql/08_return_analysis.sql) | Returns & leakage | `FILTER (WHERE)`, conditional rates, abuse watchlist |

📄 **Full SQL documentation with schema diagram and run instructions: [`sql/README.md`](sql/README.md)**

---

## 7. 🧩 Analytics Modules

### Executive Dashboard (KPIs)
Revenue, profit, margin, orders, customers, AOV, churn, and return rate in one view — the numbers a leadership review opens with.

### Sales Performance
Monthly revenue trend (2022–24), YoY comparison, category and regional breakdown, channel performance, payment mix, top-20 products by revenue with `RANK()`.

### Customer Analytics (RFM)
Recency/Frequency/Monetary quintile scoring → **8 actionable segments**
(Champions 317, Loyal 495, At Risk 221, …). K-Means overlay with **k selected
by silhouette score** (not hardcoded), PCA visualization.

### Churn Analysis — Honest by Design
- **Methodology:** forward-time (temporal) split — features are computed only
  from behavior *before* a cutoff; the label is "no purchase in the next 180
  days." Three models benchmarked (Logistic Regression, Random Forest,
  Gradient Boosting).
- **Result:** AUC **0.649 ± 0.020** (5-fold cross-validation), churn rate
  25.3%, 448 medium-risk (cooling-off) customers flagged with ₹1.24 Cr of
  historical spend.
- **⚠️ Why not AUC 1.00?** An early version *did* report AUC = 1.0 — which was
  **target leakage** (`recency_days` was both a feature and the basis of the
  label). It was found, fixed, and documented. A perfect churn AUC is almost
  always a bug; a realistic 0.65 is honest.
- Includes a **cumulative gains/lift chart** — the artifact retention teams
  actually use to size campaigns.

### Customer Lifetime Value (CLV)
Two views: *historical* (observed profit) and *predictive* (AOV × frequency ×
margin × horizon × (1 − churn probability)). Customers ranked into value tiers
— the top 10% hold ≈ 42% of projected 2-year value.

### Product Profitability (BCG Matrix)
Per-SKU P&L → BCG quadrants by median-split volume × margin:
**Stars 36 · Cash Cows 38 · Question Marks 39 · Dogs 37** — with the strategic
action for each quadrant.

### Revenue Forecasting
Holt-Winters (statsmodels) + linear-trend **ensemble**, 6-month horizon →
₹3.27 Cr projected. Evaluated **out-of-sample** (MAPE ≈ 32% on a 3-month
holdout — disclosed openly) with a **residual-bootstrap 95% confidence
interval** instead of an assumed error band.

### Statistical Validation (SciPy)
Four hypothesis tests with effect sizes (Welch's t-test, ANOVA +
Kruskal-Wallis, chi-square, IQR outliers). On this synthetic data they
correctly return **non-significant** results — reported honestly.
📄 [`reports/statistical_analysis.md`](reports/statistical_analysis.md)

### Grounded AI Layer
An LLM narrates a **verified fact sheet** computed from the CSVs — it can
never invent a number. Works with or without an API key.
📄 [`reports/weekly_brief.md`](reports/weekly_brief.md)

### Trust Layer (how you know it's real)
31 automated tests in CI: primary/foreign-key integrity, business-logic
constraints, **and dashboard-vs-pipeline consistency checks** that parse the
dashboard's data and assert it equals the pipeline output.
📄 [`reports/methodology.md`](reports/methodology.md)

---

## 8. 💡 Key Insights

### Insight 1 — Revenue is concentrated; retention is risk management
Top RFM segments (Champions + Loyal, 812 customers) hold ₹3.15 Cr of spend;
the top CLV decile alone holds ≈ 42% of projected future value.
**Impact:** losing a small group = losing a large share of revenue.
**Action:** loyalty program for Champions/Loyal; measure uplift vs. a control group.
*Owner: Marketing · KPI: frequency & AOV lift, enrolled vs. unenrolled.*

### Insight 2 — 448 customers are cooling off with ₹1.24 Cr of historical spend
The leakage-free churn model flags a 25.3% churn rate on the forward 180-day window.
**Impact:** these relationships are drifting toward permanent loss.
**Action:** tiered win-back with a **20% randomized holdout** — recovery rate
must be *measured*, never assumed.
*Owner: CRM Lead · KPI: 90-day incremental reactivation revenue (treated − control).*

### Insight 3 — Margin quality differs sharply by category
Category margins range from 47.3% (Beauty) to 56.5% (Sports); 37 SKUs are
low-volume/low-margin Dogs.
**Impact:** even mix shifts move blended margin meaningfully.
**Action:** shift paid-media weight toward Stars/Cash Cows; review Dogs for
repricing or delisting.
*Owner: Category Manager · KPI: blended gross margin % per category.*

### Insight 4 — Forecast honesty changes the conversation
The 6-month projection is ₹3.27 Cr, but the out-of-sample MAPE is ~32% —
the plan needs buffers, not false precision.
**Action:** use forecast ranges (bootstrap CI) in planning; re-evaluate
against actuals monthly.
*Owner: FP&A · KPI: forecast error tracked over time.*

---

## 9. 📸 Dashboard Preview

**[➡ Open the live dashboard](https://ecomanalytics-dashboard.vercel.app/)**

![Dashboard Preview](https://github.com/user-attachments/assets/3d0e9190-0a73-41d9-9ece-00a31f4318e8)

*6-page interactive dashboard: Executive Overview · Sales · Customer RFM ·
Churn · Product Profitability (BCG) · Forecast — built with vanilla
HTML/CSS/JS + Chart.js, mobile-responsive, no server required.*

Additional auto-generated analysis charts (Matplotlib/Seaborn) are in
[`docs/figures/`](docs/figures/) — 20 charts covering every module above.

---

## 10. 🏗 Project Architecture

```
E_commerce-Sales-and-Data-Analytics/
│
├── run_pipeline.py              # one-command orchestration + logging (8 steps)
├── requirements.txt             # pinned dependencies
│
├── data/
│   ├── DATA_DICTIONARY.md       # every table & column documented
│   ├── raw/                     # generate_data.py + 4 source CSVs (seeded)
│   └── processed/               # 6 analytical outputs (incl. clv.csv)
│
├── sql/                         # 🔑 the SQL layer (8 scripts + README)
│   ├── 01_database_schema.sql
│   ├── 02_data_cleaning.sql
│   ├── 03_kpi_analysis.sql
│   ├── 04_sales_analysis.sql
│   ├── 05_customer_analysis.sql
│   ├── 06_product_analysis.sql
│   ├── 07_regional_analysis.sql
│   ├── 08_return_analysis.sql
│   └── README.md
│
├── python/                      # the Python layer (cross-validates SQL)
│   ├── eda/                     #   preprocessing + product profitability
│   ├── segmentation/            #   RFM + K-Means (silhouette k)
│   ├── churn/                   #   leakage-free model + gains/lift chart
│   ├── forecasting/             #   statsmodels HW + bootstrap CI
│   ├── stats/                   #   hypothesis testing (SciPy)
│   └── clv/                     #   historical + predictive CLV
│
├── scripts/                     # grounded AI layer
│   ├── build_context.py         #   verified fact sheet from CSVs
│   └── weekly_brief.py          #   LLM narrates facts (no hallucination)
│
├── tests/                       # 31 tests: data quality + dashboard consistency
├── reports/                     # decision-support documents (see below)
├── dashboard/                   # Chart.js dashboard (deployed to Vercel)
└── docs/figures/                # 20 auto-generated charts
```

**Reports** (the layer that makes this a business deliverable):
[`executive_summary.md`](reports/executive_summary.md) ·
[`decision_log.md`](reports/decision_log.md) ·
[`methodology.md`](reports/methodology.md) ·
[`assumptions_and_limitations.md`](reports/assumptions_and_limitations.md) ·
[`statistical_analysis.md`](reports/statistical_analysis.md)

---

## 11. ▶️ How to Run

```bash
# 1. Clone
git clone https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics.git
cd E_commerce-Sales-and-Data-Analytics

# 2. Install dependencies (Python 3.9+)
pip install -r requirements.txt

# 3. Run the full pipeline (8 steps: data → EDA → RFM → churn →
#    forecast → profitability → statistics → CLV)
python run_pipeline.py

# 4. Validate (31 tests: data quality + dashboard consistency)
python -m pytest tests/ -v

# 5. Generate the grounded AI weekly brief
python scripts/build_context.py
python scripts/weekly_brief.py

# 6. Open the dashboard (no server needed)
open dashboard/dashboard.html        # macOS   (or just double-click it)
```

**Optional — run the SQL layer in PostgreSQL:**

```bash
createdb ecommerce_db
psql -d ecommerce_db -f sql/01_database_schema.sql
psql -d ecommerce_db -c "\COPY customers   FROM 'data/raw/customers.csv'   CSV HEADER;"
psql -d ecommerce_db -c "\COPY products    FROM 'data/raw/products.csv'    CSV HEADER;"
psql -d ecommerce_db -c "\COPY orders      FROM 'data/raw/orders.csv'      CSV HEADER;"
psql -d ecommerce_db -c "\COPY order_items FROM 'data/raw/order_items.csv' CSV HEADER;"

psql -d ecommerce_db -f sql/03_kpi_analysis.sql      # then 04–08 in any order
```

CI (`.github/workflows/ci.yml`) runs lint → pipeline → all 31 tests on every push.

---

## 12. 🎓 Key Learnings

- **Translating business questions into SQL** — every query starts from a
  question a manager would ask, not a column that happens to exist.
- **Cross-validating two implementations** (PostgreSQL + pandas) caught real
  inconsistencies and made every number defensible.
- **Evaluating predictive models responsibly** — finding and fixing target
  leakage (AUC 1.0 → 0.649) and in-sample forecast evaluation (MAPE 2.3% →
  31.6%) taught me that a suspicious metric is a debugging signal, not a trophy.
- **Communicating analysis to non-technical stakeholders** — the executive
  summary, decision log, and dashboard all say the same thing in three registers.
- **Building reproducible analytics** — seeded data, one-command pipeline,
  31 CI tests, and dashboard-consistency checks.
- **Grounding LLMs in verified data** — narrating a fact sheet instead of
  letting a model invent numbers.

---

## 13. 🔮 Future Improvements

- **Real dataset integration** (e.g., Olist Brazilian e-commerce) as a second
  case study to demonstrate the pipeline on messy, real-world data.
- **Automated refresh** — scheduled pipeline runs with drift detection on
  data-quality checks.
- **Cloud database deployment** (PostgreSQL on AWS/GCP) with the SQL layer
  as the serving interface.
- **Model monitoring** — track churn-model calibration and forecast error
  against actuals over time; alert when performance decays.
- **Improved churn modeling** — behavioural features (session data,
  support tickets) and probability calibration curves.

---

## 📄 License

MIT — free to use, adapt, and learn from.

<div align="center">

**⭐ Star this repo if it helped you ·
[🚀 Open the Live Dashboard](https://ecomanalytics-dashboard.vercel.app/) ⭐**

</div>
