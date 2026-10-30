# Commerce Intelligence API Documentation
**Framework:** FastAPI & Uvicorn  
**Base URL:** `http://localhost:8000` / `https://ecomanalytics-dashboard.vercel.app/api`

---

## 1. Analytics Endpoints (`/api/analytics`)
- `GET /api/analytics/kpis`: Retrieves executive headline metrics (Total Revenue, AOV, Gross Margin %, Orders, Active Customers).
- `GET /api/analytics/cohorts`: Returns customer retention cohort matrices grouped by acquisition month.
- `GET /api/analytics/pricing-elasticity`: Provides SKU-level price elasticity coefficients and discount margin impact.

## 2. Natural Language to SQL Copilot (`/api/nl-to-sql`)
- `POST /api/nl-to-sql/query`:
  - **Input:** JSON payload `{"prompt": "What were top 5 products by gross margin last month?"}`
  - **Security & Guardrails:** Strict read-only SQL parser, deterministic schema validation, prevents write/drop operations.
  - **Performance:** 97.3% execution accuracy across 37 benchmark retail questions with offline template fallback.
