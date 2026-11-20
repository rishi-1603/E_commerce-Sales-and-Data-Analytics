# Commerce Intelligence API Documentation
**Framework:** FastAPI & Uvicorn  
**Base URL:** `http://localhost:8000` (local or Docker; the Vercel deployment is the static dashboard)

All endpoints are versioned under `/api/v1`.

---

## 1. Analytics Endpoints (`/api/v1/analytics`)
- `GET /api/v1/analytics/overview`: Retrieves executive headline metrics (Total Revenue, AOV, Gross Margin %, Orders, Active Customers) with optional `start_date`/`end_date` filters.
- `GET /api/v1/analytics/top-products`: Returns top-performing products ranked by total revenue, including profit margins (optional `limit` param, max 50).
- `GET /api/v1/analytics/trends`: Returns monthly revenue, order volume, and average order value trends.

## 2. Resource Endpoints (`/api/v1`)
- `GET /api/v1/orders`: List orders with pagination and optional `status` filter.
- `GET /api/v1/orders/{order_id}`: Retrieve a single order by ID.
- `POST /api/v1/orders`: Create a new order (idempotent via `Idempotency-Key` header).
- `GET /api/v1/products`: List all products.
- `GET /api/v1/products/{product_id}`: Retrieve a single product by ID.
- `GET /api/v1/customers`: List all customers.
- `GET /api/v1/customers/{customer_id}`: Retrieve a single customer by ID.
- `GET /api/v1/health`: Health check with database connectivity verification.

## 3. Natural Language to SQL Copilot (`/api/v1/query`)
- `POST /api/v1/query/nl-to-sql`:
  - **Input:** JSON payload `{"question": "What is total revenue?"}`
  - **Supported scope:** total revenue, profit and margin; revenue and margin by category; revenue by region; top products by revenue; average order value; order and customer counts; cancellations; order-status distribution.
  - **Refusal:** a question outside that scope returns `generated_sql: ""`, `row_count: 0`, `data: []` and an explanation beginning `Refused:`. No SQL is generated or executed.
  - **Security & Guardrails:** read-only SELECT only, sqlglot AST validation, whitelisted analytical tables, and `LIMIT` capped at 100.
  - **Tests:** `tests/api/test_nl_query_accuracy.py` pins the aggregate definitions and refusal behavior; `tests/api/test_security_nl_query.py` pins the AST guard.

The 100% execution-accuracy figure belongs to the evaluated engine in `scripts/nl_to_sql.py`
(37/37 on the 37-question benchmark, 100% refusal correctness, 0 fabricated answers). It is not a
claim about this endpoint, which uses a separate deterministic intent router.
