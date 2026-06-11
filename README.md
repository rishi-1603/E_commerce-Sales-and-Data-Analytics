# 📊 E-Commerce Sales & Customer Analytics

> A full-stack analytics project covering sales performance, customer segmentation (RFM), churn prediction, product profitability, and revenue forecasting — built with Python, SQL, and an interactive HTML/JS dashboard.

---

## 🗂 Project Structure

```
ecommerce-analytics/
├── data/
│   ├── raw/                   # Generated CSV datasets
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   ├── orders.csv
│   │   ├── order_items.csv
│   │   └── generate_data.py   # Data generator script
│   └── processed/             # Pipeline outputs
│       ├── master_orders.csv
│       ├── rfm_segments.csv
│       ├── churn_features.csv
│       ├── product_profitability.csv
│       └── revenue_forecast.csv
├── sql/
│   ├── 01_schema.sql          # DB schema + indexes
│   ├── 02_sales_performance.sql
│   ├── 03_customer_analytics.sql
│   └── 04_product_profitability.sql
├── python/
│   ├── eda/
│   │   ├── 01_eda_preprocessing.py
│   │   └── 05_product_profitability.py
│   ├── segmentation/
│   │   └── 02_rfm_segmentation.py
│   ├── churn/
│   │   └── 03_churn_analysis.py
│   └── forecasting/
│       └── 04_revenue_forecasting.py
├── dashboard/
│   └── dashboard.html         # Standalone interactive dashboard
├── docs/
│   └── figures/               # Auto-generated charts (17 PNGs)
├── run_pipeline.py            # One-command pipeline runner
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/YOUR_USERNAME/ecommerce-analytics.git
cd ecommerce-analytics
pip install pandas numpy scikit-learn matplotlib seaborn
```

### 2. Run Full Pipeline
```bash
# Generates data + runs all analysis in order
python run_pipeline.py
```

### 3. Open Dashboard
```bash
# Just open in any browser — no server needed
open dashboard/dashboard.html
# or on Windows:
start dashboard/dashboard.html
```

---

## 📋 What's Included

### 📈 Sales Performance
- Monthly revenue trend (2022–2024)
- Revenue & profit by category, region, channel
- Top 20 products by revenue and profit
- Order status distribution, payment method analysis
- YoY comparison and 7-day moving averages

### 👥 Customer RFM Segmentation
- Recency / Frequency / Monetary scoring (1–5 scale)
- 8 actionable segments: Champions, Loyal, At Risk, etc.
- K-Means clustering (k=5, elbow curve)
- PCA 2D cluster visualisation
- Segment-level revenue contribution

### ⚠️ Churn Analysis
- 180-day churn definition
- 3 ML models: Logistic Regression, Random Forest, Gradient Boosting
- AUC / F1 / Precision / Recall metrics
- Feature importance ranking
- Per-customer churn probability scores
- Risk band segmentation (Low / Medium / High)

### 💰 Product Profitability
- Gross profit and actual margin per product
- BCG Matrix (Stars / Cash Cows / Question Marks / Dogs)
- Category-level profitability comparison
- Discount band impact on margin
- Return rate by product

### 🔮 Revenue Forecasting
- Holt-Winters triple exponential smoothing
- Linear trend baseline
- Ensemble average (Linear + Holt-Winters)
- 6-month forward projection with confidence intervals
- Monthly heatmap by year

---

## 🗄️ Database Setup (PostgreSQL)

```bash
# Create database
createdb ecommerce_db

# Run schema
psql -d ecommerce_db -f sql/01_schema.sql

# Load data
psql -d ecommerce_db -c "\COPY customers FROM 'data/raw/customers.csv' CSV HEADER;"
psql -d ecommerce_db -c "\COPY products FROM 'data/raw/products.csv' CSV HEADER;"
psql -d ecommerce_db -c "\COPY orders FROM 'data/raw/orders.csv' CSV HEADER;"
psql -d ecommerce_db -c "\COPY order_items FROM 'data/raw/order_items.csv' CSV HEADER;"

# Run analytics queries
psql -d ecommerce_db -f sql/02_sales_performance.sql
psql -d ecommerce_db -f sql/03_customer_analytics.sql
psql -d ecommerce_db -f sql/04_product_profitability.sql
```

---

## 📊 Dashboard

The dashboard (`dashboard/dashboard.html`) is a **fully standalone HTML file** — no server, no npm, no dependencies to install. Just open it in Chrome/Firefox/Edge.

**6 pages:**
| Page | Content |
|------|---------|
| Executive Overview | KPIs, revenue trend, category split, order status |
| Sales Performance | Category/region comparison, top 10 products table |
| Customer RFM | Segment distribution, progress bars, segment guide |
| Churn Analysis | Risk bands, ML model comparison, action plan |
| Product Profitability | BCG matrix, margin by category, strategy guide |
| Revenue Forecast | Chart + monthly breakdown table |

---

## 📊 Power BI / Tableau

Connect directly to the processed CSVs in `data/processed/`:

| File | Use For |
|------|---------|
| `master_orders.csv` | Sales performance, revenue trends |
| `rfm_segments.csv` | Customer segmentation map |
| `churn_features.csv` | Churn risk scoring |
| `product_profitability.csv` | BCG matrix, margin analysis |
| `revenue_forecast.csv` | Forecast vs actuals |

**Power BI:** Home → Get Data → Text/CSV → load each file → use Data Model relationships on `customer_id`, `order_id`, `product_id`.

**Tableau:** Connect → Text File → load CSVs → drag relationships in Data Source view.

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| Data Generation | Python (Pandas, NumPy, random) |
| Data Storage | CSV + PostgreSQL |
| Analysis | Python (Pandas, scikit-learn) |
| ML Models | Random Forest, Logistic Regression, Gradient Boosting |
| Forecasting | Holt-Winters, Linear Regression |
| Visualisation | Matplotlib, Seaborn |
| Dashboard | HTML5, Chart.js, Vanilla JS |
| BI Tool | Power BI / Tableau (optional) |

---

## 📦 Dataset

Synthetically generated, realistic e-commerce data:

| Table | Rows | Description |
|-------|------|-------------|
| customers | 2,000 | Demographics, region, channel |
| products | 150 | 5 categories, cost/selling price |
| orders | 12,000 | 3 years, 4 statuses, discount levels |
| order_items | ~25,000 | Line items with cost tracking |

---

## 📄 License

MIT — free to use, adapt, and include in your portfolio.
