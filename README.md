# 📊 E-Commerce Sales & Customer Analytics

> End-to-end analytics pipeline covering sales performance, customer segmentation, churn prediction, product profitability, and revenue forecasting — built with Python, SQL, and an interactive 6-dashboard HTML interface.

---

## 🎯 Project Summary

**Situation:** An e-commerce business needed to identify revenue drivers, understand customer behaviour, and reduce churn across 3 years of transaction data.

**Task:** Design and build a fully automated analytics pipeline — from raw data generation through to an interactive business dashboard.

**Action:** Built a modular Python pipeline with SQL-backed data modelling, RFM segmentation, 3 ML churn models, BCG profitability analysis, and ensemble revenue forecasting. Added data quality tests (21 checks) and structured logging with timestamps.

**Result:** Identified 375 high-risk customers representing at-risk revenue, segmented 1,991 customers into 8 actionable groups, achieved AUC of 1.0 across all churn models, and projected ₹29.15M in revenue over the next 6 months.

---

## 💡 Key Business Findings

**1. Churn Risk — ₹ at stake**
375 customers are flagged as High Risk (180-day inactivity threshold). A targeted win-back campaign with a 20% discount voucher at a 15% recovery rate would recover significant at-risk revenue before Q3.

**2. Customer Segmentation — where to focus**
- **Champions (317)** — highest RFM scores; prioritise upsell and review requests
- **Loyal Customers (495)** — largest segment; loyalty programme candidates
- **At Risk (221)** — re-engagement drip sequence needed immediately
- **Lost Customers (133)** — last-chance survey or write-off decision required

**3. Revenue Forecast**
Ensemble model (Holt-Winters + Linear) projects ₹29.15M over Jan–Jun 2025. February dips negative due to seasonal smoothing — investigate whether this reflects a real seasonal pattern or a data distribution artefact in the synthetic set.

**4. Data Quality**
21 automated tests validate primary keys, foreign key integrity, business-logic constraints (no negative prices, valid order statuses, probability scores in 0–1 range) across all 4 tables and 2 processed outputs. Zero failures on latest run.

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics.git
cd E_commerce-Sales-and-Data-Analytics
pip install -r requirements.txt
```

### 2. Run Pipeline
```bash
python run_pipeline.py
```
Logs are written to console and `pipeline.log` with timestamps and step durations.

### 3. Run Data Quality Tests
```bash
python -m pytest tests/test_data_quality.py -v
```

### 4. Open Dashboard
```bash
# Windows
start dashboard/dashboard.html
# Mac/Linux
open dashboard/dashboard.html
```

---

## 🗂 Project Structure

```
ecommerce-analytics/
├── data/
│   ├── raw/                   # Generated CSV datasets
│   └── processed/             # Pipeline outputs
├── sql/
│   ├── 01_schema.sql
│   ├── 02_sales_performance.sql
│   ├── 03_customer_analytics.sql
│   └── 04_product_profitability.sql
├── python/
│   ├── eda/
│   ├── segmentation/
│   ├── churn/
│   └── forecasting/
├── tests/
│   └── test_data_quality.py   # 21 data quality checks
├── dashboard/
│   └── dashboard.html         # Standalone, no server needed
├── docs/figures/              # Auto-generated charts (17 PNGs)
├── run_pipeline.py            # One-command runner with logging
└── requirements.txt
```

---

## 📋 What's Included

### 📈 Sales Performance
- Monthly revenue trend (2022–2024), YoY comparison, 7-day moving averages
- Revenue & profit by category, region, channel
- Top 20 products by revenue and profit, order status distribution

### 👥 Customer RFM Segmentation
- Recency / Frequency / Monetary scoring (1–5 scale), 8 actionable segments
- K-Means clustering (k=5, elbow curve), PCA 2D visualisation
- Segment-level revenue contribution

### ⚠️ Churn Prediction
- 180-day churn definition, 3 ML models (Logistic Regression, Random Forest, Gradient Boosting)
- AUC / F1 / Precision / Recall comparison, feature importance ranking
- Per-customer churn probability scores, risk band segmentation (Low / Medium / High)

### 💰 Product Profitability
- Gross profit and margin per product, BCG Matrix (Stars / Cash Cows / Question Marks / Dogs)
- Category-level profitability, discount band impact on margin, return rate by product

### 🔮 Revenue Forecasting
- Holt-Winters triple exponential smoothing + linear trend baseline + ensemble average
- 6-month forward projection with confidence intervals, monthly heatmap by year

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| Data Generation | Python (Pandas, NumPy) |
| Data Storage | CSV + PostgreSQL |
| Analysis | Python (Pandas, scikit-learn) |
| ML Models | Random Forest, Logistic Regression, Gradient Boosting |
| Forecasting | Holt-Winters, Linear Regression, Ensemble |
| Visualisation | Matplotlib, Seaborn |
| Dashboard | HTML5, Chart.js, Vanilla JS |
| Data Quality | pytest (21 checks) |
| Logging | Python logging (file + console) |
| BI Tool | Power BI / Tableau (optional, CSVs ready) |

---

## 🗄️ Database Setup (PostgreSQL)

```bash
createdb ecommerce_db
psql -d ecommerce_db -f sql/01_schema.sql
psql -d ecommerce_db -c "\COPY customers FROM 'data/raw/customers.csv' CSV HEADER;"
psql -d ecommerce_db -c "\COPY products FROM 'data/raw/products.csv' CSV HEADER;"
psql -d ecommerce_db -c "\COPY orders FROM 'data/raw/orders.csv' CSV HEADER;"
psql -d ecommerce_db -c "\COPY order_items FROM 'data/raw/order_items.csv' CSV HEADER;"
psql -d ecommerce_db -f sql/02_sales_performance.sql
psql -d ecommerce_db -f sql/03_customer_analytics.sql
psql -d ecommerce_db -f sql/04_product_profitability.sql
```

---

## 📊 Power BI / Tableau

Connect directly to `data/processed/`:

| File | Use For |
|------|---------|
| `master_orders.csv` | Sales performance, revenue trends |
| `rfm_segments.csv` | Customer segmentation map |
| `churn_features.csv` | Churn risk scoring |
| `product_profitability.csv` | BCG matrix, margin analysis |
| `revenue_forecast.csv` | Forecast vs actuals |

**Power BI:** Home → Get Data → Text/CSV → load each file → relate on `customer_id`, `order_id`, `product_id`.

**Tableau:** Connect → Text File → load CSVs → drag relationships in Data Source view.

---

## 📦 Dataset

Synthetically generated realistic e-commerce data:

| Table | Rows | Description |
|-------|------|-------------|
| customers | 2,000 | Demographics, region, channel |
| products | 150 | 5 categories, cost/selling price |
| orders | 12,000 | 3 years, 4 statuses, discount levels |
| order_items | ~25,000 | Line items with cost tracking |

---

## 📄 License

MIT — free to use, adapt, and include in your portfolio.
