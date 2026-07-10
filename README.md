# 📊 E-Commerce Sales & Customer Analytics

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Pytest](https://img.shields.io/badge/Tests-21%20passed-brightgreen?logo=pytest)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Pipeline](https://img.shields.io/badge/Pipeline-Automated-informational)

> End-to-end analytics pipeline covering sales performance, customer segmentation, churn prediction, product profitability, and revenue forecasting — built with Python, SQL, and an interactive 6-dashboard HTML interface.

---

## 🎯 Project Summary

**Situation:** An e-commerce business needed to identify revenue drivers, understand customer behaviour, and reduce churn across 3 years of transaction data.

**Task:** Design and build a fully automated analytics pipeline — from raw data generation through to an interactive business dashboard.

**Action:** Built a modular Python pipeline with SQL-backed data modelling, RFM segmentation, 3 ML churn models, BCG profitability analysis, and ensemble revenue forecasting. Added 21 data quality tests and structured logging with timestamps.

**Result:** Identified **₹1.97 Cr in at-risk revenue** across 708 customers, segmented 1,991 customers into 8 actionable groups, achieved AUC of 1.0 across all churn models, and projected ₹2.92 Cr in revenue over the next 6 months.

---

## 💡 Key Business Findings

**1. ₹1.97 Cr at-risk revenue — act now**
708 customers across At Risk, About To Sleep, and Lost segments hold ₹1.97 Cr in historical spend. A targeted win-back campaign at 15% recovery rate would recover ~₹29.6L before Q3.

**2. Customer Segmentation — where to focus**
| Segment | Customers | Strategy |
|---------|-----------|----------|
| Champions (317) | ₹1.55 Cr spend | Upsell, request reviews |
| Loyal Customers (495) | ₹1.60 Cr spend | Loyalty programme |
| At Risk (221) | ₹92.5L spend | Re-engagement drip immediately |
| Lost Customers (133) | ₹15.9L spend | Last-chance survey or write-off |

**3. Revenue Forecast — ₹2.92 Cr projected**
Ensemble model (Holt-Winters + Linear) projects ₹2.92 Cr over Jan–Jun 2025. February shows a seasonal dip — monitor closely as a leading indicator for Q2 planning.

**4. Data Quality — 21/21 checks passing**
Automated tests validate primary keys, foreign key integrity, and business-logic constraints across all 4 tables and 2 processed outputs. Zero failures on latest run.

---

## 📸 Dashboard Preview

<img width="1920" height="1024" alt="ecom_project_1" src="https://github.com/user-attachments/assets/3d0e9190-0a73-41d9-9ece-00a31f4318e8" />


> 6-page interactive dashboard — Executive Overview · Sales · Customer RFM · Churn · Profitability · Forecast

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
start dashboard/dashboard.html      # Windows
open dashboard/dashboard.html       # Mac/Linux
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

| Table | Rows | Description |
|-------|------|-------------|
| customers | 2,000 | Demographics, region, channel |
| products | 150 | 5 categories, cost/selling price |
| orders | 12,000 | 3 years, 4 statuses, discount levels |
| order_items | ~25,000 | Line items with cost tracking |

---

## 📄 License

MIT — free to use, adapt, and include in your portfolio.
