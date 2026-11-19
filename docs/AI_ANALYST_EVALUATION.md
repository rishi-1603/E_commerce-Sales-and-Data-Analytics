# AI Analyst Evaluation

**Date:** 2026-11-19<br>
**Audited code:** `890f66f`<br>
**Public URL:** https://ecomanalytics-dashboard.vercel.app/<br>
**Status terms:** **VERIFIED** = supported by the evidence layer named; **FAILED-UNRESOLVED** = a reproduced failure remains; **NOT VERIFIED** = execution or access evidence is insufficient.

Evidence layers are kept distinct: **source** inspection, recorded **test** runs, **live** browser behavior, and **deployment** metadata/content. A mocked integration or a source safeguard is not treated as a live-provider result.

## 1. Verdict

| Surface / claim | Status | Evidence-based conclusion |
|---|---|---|
| Public Vercel AI Analyst | **VERIFIED** — source + live + deployment | A deterministic in-browser template router with six curated, dataset-grounded answers and visible SQL. It is **not real Gemini**, does not call the FastAPI provider, and does not execute the displayed SQL in the browser. |
| Offline fallback benchmark | **FAILED-UNRESOLVED** — test | The recorded fallback run scores 36/37, but A13 still returns product-level profit for a category-margin paraphrase. The CI floor passes; the failure is not hidden or claimed fixed. |
| FastAPI Gemini-backed analyst | **NOT VERIFIED** for real provider execution — source + mocked test only | Python computes KPIs and source code asks Gemini to interpret them. No local `GEMINI_API_KEY` was available, no Vercel production environment variables exist, and this backend is not deployed to Vercel. |
| FastAPI database-executing NL-to-SQL | **VERIFIED** within recorded local source/test scope; **NOT VERIFIED** as a deployed provider service | Deterministic query templates, AST validation and database execution exist in FastAPI source and have local tests. This is a separate path from the Gemini interpretation endpoint and is not part of the static Vercel deployment. |
| Credential exposure | **VERIFIED** — source/audit evidence | No credentials are reproduced here. The release audit records zero secret-scan findings; no API key was printed or configured during this evaluation. |

The seven-report release context and deployment separation are recorded in [COMPLETE_PROJECT_QA_REPORT.md](COMPLETE_PROJECT_QA_REPORT.md), especially §§B, F, G and K.

## 2. What each “AI” surface actually is

### 2.1 Public Vercel analyst — deterministic browser templates

**VERIFIED — source + live + deployment.**

- [`dashboard/dashboard.html`](../dashboard/dashboard.html), lines 2001–2054, defines `AI_ANSWERS` with exactly six keys: `revenue`, `top_category`, `churn`, `inactive`, `forecast`, and `margin`.
- `askAI(q)` performs an object lookup, renders the selected SQL string and curated answer, and returns “Question not supported” for an unknown key. There is no provider request, FastAPI request, general natural-language parser, or browser SQL execution in this path.
- The UI accurately says “Built-in questions only (deterministic, no API key)” and “No LLM key required.” Its SQL is the SQL the approved KPI definition **would run**, not proof that a query ran in the browser.
- The recorded live audit numerically reconciled all six answers and verified refusal. Arbitrary public prompts and SQL-injection-shaped prompts were refused by this bounded router. Because the browser has no SQL execution backend, that live result is **not** evidence for AST-based injection prevention.
- Deployment evidence says the canonical live response equals the LF-normalized local canonical dashboard bytes. Vercel serves the static `dashboard/` directory; [`vercel.json`](../vercel.json) declares no functions or backend.

**Boundary:** this verifies a useful, honest built-in demonstration. It does not establish open-ended NL-to-SQL quality, LLM quality, or provider-side prompt-injection resistance.

### 2.2 FastAPI Gemini analyst — source-only relative to Vercel

**Source presence: VERIFIED. Real provider execution: NOT VERIFIED.**

[`app/services/analytics_ai_service.py`](../app/services/analytics_ai_service.py) and [`app/api/v1/endpoints/ai_analyst.py`](../app/api/v1/endpoints/ai_analyst.py) implement `/api/v1/ai/ai-analyst`:

1. pandas calculates KPIs from processed data;
2. a prompt instructs Gemini to use only those supplied results and not calculate;
3. `google.generativeai.GenerativeModel.generate_content` returns the interpretation;
4. the response includes the underlying analysis and synthetic-data/model limitations.

This is genuine provider-backed source code, but it is not the public Vercel implementation. [`tests/test_analytics_ai_service.py`](../tests/test_analytics_ai_service.py) mocks `generate_content`; it does not prove a real Gemini request, model behavior, answer quality, or adversarial robustness. No local `GEMINI_API_KEY` and no Vercel production environment variables were available, so live provider execution remains **NOT VERIFIED**.

**Open P3 — TECH-01:** FastAPI imports deprecated `google.generativeai`. Migration to `google.genai` remains open because provider-backed migration behavior could not be tested without a key. The deterministic public analyst is unaffected. See [QA_REMEDIATION_LOG.md](QA_REMEDIATION_LOG.md).

### 2.3 FastAPI NL-to-SQL — deterministic server path, not Gemini generation

**Source/local tests: VERIFIED within scope. Production deployment: NOT VERIFIED.**

[`app/services/query_service.py`](../app/services/query_service.py) maps supported questions to fixed SQL templates and executes sanitized SQL through `/api/v1/query/nl-to-sql`. Unsupported questions return no SQL and execute nothing. This endpoint does **not** call Gemini; it must not be conflated with the Gemini interpretation service above.

The standalone [`scripts/nl_to_sql.py`](../scripts/nl_to_sql.py) evaluated below is a third surface. It has optional provider-backed SQL generation/explanation, but the recorded evaluation used only its deterministic fallback. None of these server/provider paths is wired into the public static Vercel analyst.

## 3. Fallback evaluation results

**Committed test evidence:** [`evals/results_fallback.json`](../evals/results_fallback.json), [`reports/ai_eval_report.md`](../reports/ai_eval_report.md), and [`evals/run_eval.py`](../evals/run_eval.py).<br>
**Committed run:** 2026-11-19T08:25:10+00:00 · **mode:** `fallback` · **benchmark:** v1.1, 37 questions, four classes.

The harness evaluates `scripts/nl_to_sql.py::answer_question`, not the six Vercel templates and not the FastAPI Gemini endpoint. Ground truth is independently computed with pandas from `data/processed/master_orders.csv`; it is not supplied by the system under test.

| Metric | Baseline | Current fallback | Status |
|---|---:|---:|---|
| Overall execution accuracy | 18/37 = 48.6% | **36/37 = 97.3%** | **FAILED-UNRESOLVED** overall because one case remains |
| Simple aggregation | — | **12/13 = 92.3%** | **FAILED-UNRESOLVED**: A13 |
| Segment breakdown | — | **10/10 = 100%** | **VERIFIED** in this harness |
| Time intelligence | — | **9/9 = 100%** | **VERIFIED** in this harness |
| Refusal correctness | 4/5 = 80% | **5/5 = 100%** | **VERIFIED** in this harness |
| Fabricated numbers on unanswerable questions | **1** | **0** | **VERIFIED** in this harness |
| Latency p50 / p95 | — | **511.4 ms / 532.0 ms** | **VERIFIED** for this committed local fallback run only |

The baseline’s fabricated next-year revenue answer reused historical all-time revenue; the current fallback refuses that unsupported forecast request. Latency is harness latency, not Gemini latency, public Vercel latency, or concurrent-load performance.

### Sole current regression failure — A13

**FAILED-UNRESOLVED — recorded test evidence.**

| Field | Evidence |
|---|---|
| Question | “Which product line gives us the best percentage profit?” |
| Variant / class | Paraphrase / `simple_aggregation` |
| Actual SQL grain | `product_name`, `SUM(profit)` — top product by total profit |
| Expected grain | `category`, percentage margin |
| Harness detail | `no column matching ['category'] in ['product_name', 'profit']` |
| Record | A13 in [`evals/results_fallback.json`](../evals/results_fallback.json) |

This is a wrong-grain answer to an uncovered paraphrase, not a passing result and not evidence of a resolved regression. A repair should add a focused A13 regression assertion for category percentage margin, preserve canonical category-margin cases, then rerun the 37-case evaluation and the project suite. Separately, `--mode llm` must be run and reported before making any provider-quality comparison.

**Do not overclaim:** 97.3% is the deterministic fallback harness score. It is not proof of live Gemini quality, open-ended language coverage, production security, or the behavior of the six-question public template router. The eval gate enforces a floor; it does not require 37/37.

## 4. Source safety review and its limits

| Surface | Controls established by source/test evidence | Status and boundary |
|---|---|---|
| Public browser router | Six-key answer allowlist; unsupported input returns a refusal; no SQL execution or provider call | **VERIFIED** for bounded live behavior, including refusal of arbitrary and injection-shaped public prompts. Not a general SQL-security test. |
| FastAPI `QueryService` | `sqlglot` AST parsing; root must be `Select`; mutation nodes blocked; table allowlist is `orders`, `order_items`, `customers`, `products`; qualified DB/catalog tables rejected; missing `LIMIT` becomes 100 and larger values are capped at 100; only sanitized SQL is executed | **VERIFIED** by source inspection and [`tests/api/test_security_nl_query.py`](../tests/api/test_security_nl_query.py) for malicious `DROP`, unauthorized `sqlite_master`, qualified tables, negative limits, multi-statement input, and the LIMIT cap. PostgreSQL execution is separately **NOT VERIFIED**. |
| FastAPI query columns | The router emits fixed column templates rather than accepting arbitrary user SQL. `QueryService` has a table allowlist but **no general standalone column allowlist**; benchmark answer-alias lists are scoring logic, not a security boundary | **VERIFIED** as a scope statement; no broader arbitrary-column protection is claimed. |
| Offline `scripts/nl_to_sql.py` | `validate_sql` permits `SELECT`/`WITH` and regex-blocks listed destructive keywords before in-memory SQLite execution | **VERIFIED** for those narrow checks only. This script does not use the FastAPI `sqlglot` AST validator and does not add equivalent table/column allowlists or a LIMIT cap; FastAPI controls must not be attributed to this eval harness. |

### Refusal semantics — open P3 (API-01)

FastAPI refusals return `is_safe=True`, empty SQL, zero rows, and explicit refusal text. Nothing is executed, so the behavior is functionally safe in the tested path, but `is_safe` describes the absence of unsafe SQL rather than whether the question was answered. That ambiguity remains **open P3**, documented in [QA_REMEDIATION_LOG.md](QA_REMEDIATION_LOG.md); it is not silently reclassified as resolved.

## 5. Final AI release statement

- **VERIFIED:** the public analyst is an honestly disclosed deterministic template experience with visible SQL and curated grounded answers.
- **FAILED-UNRESOLVED:** fallback A13 remains the sole failure in the recorded 37-case run.
- **NOT VERIFIED:** real Gemini provider execution/quality/security, provider-backed NL generation, and any deployed FastAPI AI service. Mocked tests and fallback scores are not substitutes for those checks.
- The real Gemini-backed interpretation and database-executing NL-to-SQL implementations remain source-side capabilities, not features of the public Vercel deployment.
