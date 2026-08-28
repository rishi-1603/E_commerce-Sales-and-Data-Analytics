# 🗄️ SQL Layer — E-Commerce Analytics

**SQL is not a keyword in this project — it's the foundation.** The same
business logic exists twice on purpose: once in PostgreSQL (this folder) and
once in Python (`python/`), so results are cross-validated across two
independent implementations.

---

## Schema at a glance

```
customers (2,000)          products (150)
   customer_id ──┐             product_id ──┐
                 │                           │
              orders (12,000) ── order_items (~21,000)
                 order_id ────────┘  (line grain — the money table)
```

| Table | Grain | Key columns |
|---|---|---|
| `customers` | 1 row / customer | region, segment, acquisition_channel, registration_date |
| `products` | 1 row / SKU | category, cost_price, selling_price, stock_qty, rating |
| `orders` | 1 row / order | customer_id (FK), order_date, status, discount_pct |
| `order_items` | 1 row / line item | order_id (FK), product_id (FK), line_total, cost_total |

**Canonical business rule** (applied identically in SQL, Python and the
dashboard): revenue/profit metrics count only `Delivered` + `Processing`
orders — `Cancelled` and `Returned` are excluded. The `valid_orders` view in
`01_database_schema.sql` encodes this once.

## Scripts & the business questions they answer

| Script | Answers |
|---|---|
| `01_database_schema.sql` | How is the warehouse structured? (tables, FKs, indexes, load) |
| `02_data_cleaning.sql` | Is the data trustworthy? (duplicates, orphans, impossible values, line-math) |
| `03_kpi_analysis.sql` | What is business health? (revenue, profit, margin, AOV, MoM/YoY growth, Pareto) |
| `04_sales_analysis.sql` | Where does revenue come from? (trend, category, top SKUs, channel, payment mix) |
| `05_customer_analysis.sql` | Who are the customers? (RFM, CLV, cohorts, repeat behaviour, churn watchlist) |
| `06_product_analysis.sql` | What makes money? (product P&L, BCG matrix, discount impact, stock risk) |
| `07_regional_analysis.sql` | Where does it work? (regions, per-customer value, regional YoY growth) |
| `08_return_analysis.sql` | What leaks? (return rates, value at risk, most-returned SKUs, repeat returners) |

Every query carries a three-line contract: **Business Question → Why It
Matters → Key Insight Generated**. If a query can't answer all three, it
doesn't belong here.

## SQL techniques used (each earns its place)

| Technique | Where it's used | Why |
|---|---|---|
| **CTEs (`WITH`)** | nearly every script | readable multi-step analysis |
| **Window functions (`NTILE`, `RANK`, `DENSE_RANK`, `LAG`)** | 03, 04, 05, 06, 07 | RFM quintiles, rankings, MoM/YoY growth, purchase gaps |
| **`PERCENTILE_CONT ... OVER ()`** | 06 | median-split BCG classification |
| **`CASE WHEN` conditional aggregation** | 04, 05, 07, 08 | pivots, new-vs-returning, status filters |
| **`FILTER (WHERE ...)`** | 02, 08 | clean rate calculations |
| **Moving average (`ROWS BETWEEN 6 PRECEDING`)** | 04 | 7-day revenue smoothing |
| **Correlated subqueries** | 05 | snapshot-date recency without variables |
| **Multi-table JOINs (star schema)** | everywhere | fact-dimension analysis |

## How to run

```bash
# 1. Create the database and schema
createdb ecommerce_db
psql -d ecommerce_db -f sql/01_database_schema.sql

# 2. Load the CSVs (from the repo root)
psql -d ecommerce_db -c "\COPY customers   FROM 'data/raw/customers.csv'   CSV HEADER;"
psql -d ecommerce_db -c "\COPY products    FROM 'data/raw/products.csv'    CSV HEADER;"
psql -d ecommerce_db -c "\COPY orders      FROM 'data/raw/orders.csv'      CSV HEADER;"
psql -d ecommerce_db -c "\COPY order_items FROM 'data/raw/order_items.csv' CSV HEADER;"

# 3. Run any analysis script
psql -d ecommerce_db -f sql/03_kpi_analysis.sql
```

> **Note:** scripts 02–08 are read-only SELECTs (+ two `CREATE OR REPLACE
> VIEW` statements) — safe to run in any order after the schema is loaded.
> The Python pipeline (`python run_pipeline.py`) performs the equivalent
> analysis in pandas; the outputs are cross-checked by
> `tests/test_dashboard_consistency.py`.

## Data flow

```
data/raw/*.csv  →  sql/01 schema  →  sql/02 quality audit
                →  sql/03–08 business analysis (read-only)
                →  python pipeline (same logic, cross-validated)
                →  data/processed/*.csv  →  dashboard + reports
```
