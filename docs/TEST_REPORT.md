# TEST REPORT — E-Commerce
### Last full local run: 2026-11-20 — 273/273 passed (131.71s, Python 3.12 venv, `pytest tests/ -q`)

The run was executed on a CI-equivalent copy (tracked files only, no `.env`, no `.venv`)
after regenerating the dataset and every analytics artifact from source, mirroring the
GitHub Actions step order. Collection independently re-confirmed: `273 tests collected`.

## Suites

| Suite | File | Pins |
|---|---|---|
| Data quality | test_data_quality.py | schema, ranges, referential integrity |
| Dashboard consistency | test_dashboard_consistency.py | every displayed figure == pipeline output |
| Claims registry | test_claims_registry.py | `data/claims.json` == source artifacts + raw-CSV revenue; test-count agreement across README / RESUME_EVIDENCE / claims.json |
| Pricing dashboard | test_pricing_dashboard.py | injector idempotency, 4 dashboard copies byte-identical, embedded `DATA` block |
| Churn calibration | test_churn_calibration.py | AUC, PR-AUC, Brier, slope, threshold, profits |
| Churn model metrics | test_churn_model_metrics.py | holdout vs CV metric separation, label horizon |
| Forecast backtest | test_forecast_backtest.py | MASE values, coverage, verdict flags |
| Forecast challenger | test_forecast_challenger.py | holt_linear vs drift under identical rolling-origin protocol |
| Decision layer | test_decision_layer.py | decision_layer.json contents |
| Discount engine | test_discount_engine.py | break-even band |
| Win-back economics | test_winback_economics.py | eligible audience, EV per contact, budget sensitivity |
| Revenue PVM | test_revenue_pvm.py | price/volume/mix decomposition |
| NL-to-SQL | test_nl_to_sql.py | eval harness invariants |
| AI eval | test_ai_eval.py | benchmark results (100%, 0 fabricated) |
| AI service + API | test_analytics_ai_service.py | analyst endpoint, honest no-key fallback, CORS regression (unlisted origin gets no `Access-Control-Allow-Origin`) |
| API NL accuracy | tests/api/test_nl_query_accuracy.py | aggregate definitions, refusal of off-scope questions |
| API SQL guard | tests/api/test_security_nl_query.py | AST whitelist, read-only, LIMIT cap |
| API surface | tests/api/test_health.py, test_analytics.py, test_orders.py, test_idempotency.py | health, analytics responses, order pagination/validation, create-order idempotency |
| Reporting artifacts | test_business_reporting_workbook.py, test_excel_companion.py, test_business_value_engine.py | workbook/Excel outputs, business-value decision record |

## Live browser suite (separate from the 273)

`tests/test_live_vercel.py` is a **standalone script** (`python tests/test_live_vercel.py`,
optionally `VERCEL_URL=...`). It contains no `test_*` functions, so pytest collects 0 tests
from it by design; it is not part of the 273 and must not be counted as such.

Latest result against production (2026-11-19): **96 passed / 0 failed** across
Chromium, Firefox and WebKit — 12 nav pages, 0 console errors, no horizontal overflow at
390×844 / 768×1024 / 1366×768 / 1920×1080.

## How numbers are pinned
Each analysis writes `reports/*_metrics.json`; tests assert values against those
artifacts with tolerances chosen for cross-version stability (exact for structural
properties, ~rel 5% for profit figures, wider bins for ECE). Directional
invariants (calibration improves Brier; t* policy beats contact-all) are separate
tests, so a drifting float cannot silently pass a changed conclusion.
`test_claims_registry.py` additionally recomputes headline revenue from the raw CSVs,
so the registry cannot drift from the data while staying internally consistent.

## CI
GitHub Actions (`.github/workflows/ci.yml`, ubuntu-latest, Python 3.11):
flake8 → generate_data → run_pipeline → churn_calibration + forecast_backtest →
pricing/win-back/eval/challenger/injector → `node --check` → init DB → `pytest tests/ -v`.
Run status for the audit commit is recorded with evidence in
`docs/COMPLETE_PROJECT_QA_REPORT.md` (GitHub and release information); no status is
claimed here without a observed run.

## Not covered (disclosed)
- **PostgreSQL execution** of `sql/`: local server requires `scram-sha-256` and no
  credential is available. Static audit only (12 files / 75 statements parse under the
  PostgreSQL dialect, all relations/columns resolve). Execution: NOT VERIFIED.
- **Power BI Desktop** runtime: unavailable on this machine; `.pbix`/`.pbip` inspected at
  source level only.
- **Real Gemini provider calls**: no `GEMINI_API_KEY` locally and none configured on the
  Vercel project; the honest deterministic fallback is what is tested.
- **Concurrent load testing** of FastAPI: latency was measured single-client (p95 < 160 ms
  on all audited endpoints); no multi-client soak test.
- **Vercel private runtime logs** beyond CLI-visible metadata.
