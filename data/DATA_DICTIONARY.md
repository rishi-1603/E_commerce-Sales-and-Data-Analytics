# Data Dictionary
### Source tables (`data/raw/`) and analytical outputs (`data/processed/`)
> Generated dataset, INR. See `reports/assumptions_and_limitations.md` for
> what the data can and cannot support.

## Source tables

### `customers.csv` — 2,000 rows
| Column | Type | Description |
|--------|------|-------------|
| customer_id | string (PK) | `CUST00001` … unique customer key |
| first_name, last_name | string | Name parts |
| email | string (unique) | Synthetic email |
| region | string | North / South / East / West / Central |
| segment | string | B2C / B2B / Enterprise |
| acquisition_channel | string | Organic/Paid/Social/Email/Direct/Referral/Affiliate |
| registration_date | date | Account creation date |
| age | int | 18–65 |
| gender | string | Male / Female / Other |

### `products.csv` — 150 rows
| Column | Type | Description |
|--------|------|-------------|
| product_id | string (PK) | `PROD0001` … |
| product_name | string | e.g. "Smartphone Pro" |
| category | string | Electronics / Clothing / Home & Garden / Sports / Beauty |
| subcategory | string | Item type |
| cost_price | float | Unit cost (INR) |
| selling_price | float | Unit list price (INR) |
| stock_qty | int | Inventory units |
| rating | float | 2.5–5.0 |
| launch_date | date | Product launch |

### `orders.csv` — 12,000 rows
| Column | Type | Description |
|--------|------|-------------|
| order_id | string (PK) | `ORD0000001` … |
| customer_id | string (FK) | → customers |
| order_date | date | Order placement |
| status | string | Delivered / Returned / Cancelled / Processing |
| payment_method | string | Credit Card / Debit Card / PayPal / UPI / Net Banking / Wallet |
| discount_pct | float | 0 / 0.05 / 0.10 / 0.15 / 0.20 |
| shipping_cost | float | INR |

### `order_items.csv` — ~25,000 rows
| Column | Type | Description |
|--------|------|-------------|
| item_id | string (PK) | Line-item key |
| order_id | string (FK) | → orders |
| product_id | string (FK) | → products |
| quantity | int | Units |
| unit_price | float | Pre-discount unit price |
| discount_pct | float | Order-level discount applied |
| final_price | float | Unit price after discount |
| line_total | float | `final_price × quantity` |
| cost_total | float | `cost_price × quantity` |

## Analytical outputs (`data/processed/`)

| File | Grain | Key columns | Use for |
|------|-------|-------------|---------|
| `master_orders.csv` | order-item | line_total, profit, category, region, month/quarter | Sales performance, revenue trends |
| `rfm_segments.csv` | customer | R, F, M, rfm_total, segment, cluster | Segmentation map |
| `churn_features.csv` | customer | churn_probability, churn_risk, churned | Churn risk targeting |
| `product_profitability.csv` | product | gross_profit, margin, bcg_bucket | BCG matrix, margin |
| `revenue_forecast.csv` | month | lr/hw/ensemble forecast | Forecast vs actuals |
