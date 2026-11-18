# Commerce Intelligence API Documentation
**Framework:** FastAPI & Uvicorn  
**Base URL:** `http://localhost:8000` (local or Docker; the Vercel deployment is the static dashboard)

All endpoints are versioned under `/api/v1`.

---

## 1. Analytics Endpoints (`/api/v1/analytics`)
- `GET /api/v1/analytics/kpis`: Retrieves executive headline metrics (Total Revenue, AOV, Gross Margin %, Orders, Active Customers).
- `GET /api/v1/analytics/cohorts`: Returns customer retention cohort matrices grouped by acquisition month.
- `GET /api/v1/analytics/pricing-elasticity`: Provides SKU-level price elasticity coefficients and discount margin impact.

## 2. Natural Language to SQL Copilot (`/api/v1/query`)
- `POST /api/v1/query/nl-to-sql`:
  - **Input:** JSON payload `{"question": "What is total revenue?"}`
  - **Supported scope:** total revenue, profit and margin; revenue and margin by category; revenue by region; top products by revenue; average order value; order and customer counts; cancellations; order-status distribution.
  - **Refusal:** a question outside that scope returns `generated_sql: ""`, `row_count: 0`, `data: []` and an explanation beginning `Refused:`. No SQL is generated or executed.
  - **Security & Guardrails:** read-only SELECT only, sqlglot AST validation, whitelisted analytical tables, and `LIMIT` capped at 100.
  - **Tests:** `tests/api/test_nl_query_accuracy.py` pins the aggregate definitions and refusal behavior; `tests/api/test_security_nl_query.py` pins the AST guard.

The 97.3% execution-accuracy figure belongs to the evaluated engine in `scripts/nl_to_sql.py`
(36/37 on the 37-question benchmark, 100% refusal correctness, 0 fabricated answers). It is not a
claim about this endpoint, which uses a separate deterministic intent router.
