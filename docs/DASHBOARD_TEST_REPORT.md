# Dashboard Test Report — EcomAnalytics

> **Historical snapshot (2026-11-19).** The 273-test count below describes that audit
> commit. Current suite: **284 tests** (see `docs/TEST_REPORT.md`).

**Audit date:** 2026-11-19<br>
**Production URL:** https://ecomanalytics-dashboard.vercel.app/<br>
**Audited code commit:** `890f66ffd21e5cfb7cf64358a9b56f01a3659747`<br>
**Overall result:** **VERIFIED** for the static-dashboard scope described below. The captured standalone run passed **96/96 live checks**, all 12 pages were present, 22/22 independently reconciled chart series passed, and no console errors were captured. No **FAILED-UNRESOLVED** functional dashboard defect appears in that evidence. Items outside the evidence are explicitly **NOT VERIFIED**.

## Status meanings

- **VERIFIED** — supported by a cited captured run/artifact or by the fresh read-only reconciliation performed for this report.
- **FAILED-UNRESOLVED** — an observed failure or finding remains open; this is not used for unobserved behavior.
- **NOT VERIFIED** — available evidence does not establish the claim. This does not mean the claim failed.

## 1. Evidence and test-count boundaries

Evidence reviewed: `tests/test_live_vercel.py`, `docs/TEST_REPORT.md`, `docs/COMPLETE_PROJECT_QA_REPORT.md`, `docs/QA_REMEDIATION_LOG.md`, the captured `dashboard_audit.json`, `perf_live.json`, and `chart_reconcile.py`. The reconciliation script was also executed read-only for this report and returned `22/22 series reconcile; 0 FAIL`.

| Evidence stream | Result | Boundary |
|---|---:|---|
| Repository pytest suite | **VERIFIED — 273/273 passed** | `python -m pytest tests/ -q`; 273 tests collected. Local and GitHub Actions results are recorded in `docs/TEST_REPORT.md`. |
| Standalone live browser script | **VERIFIED — 96/96 checks passed** | `python tests/test_live_vercel.py`; a standalone script with no `test_*` functions. Pytest collects zero tests from it. |
| Independent series reconciliation | **VERIFIED — 22/22 passed** | A separate source-artifact/raw-data reconciliation, not an additional pytest or browser-test count. |

The **96 browser checks and 273 pytest tests are separate and are never added together**. The 22 reconciled series are likewise not added to either total.

The 96-check total decomposes as three browsers × 32 counted checks: one page load, 15 KPI content checks, four initially visible Overview chart checks, and 12 navigation checks per browser. Responsive observations and hidden-canvas warnings do not increment that script's pass counter.

## 2. Cross-browser, navigation, and console evidence

| Area | Status | Evidence |
|---|---|---|
| Chromium, Firefox, WebKit | **VERIFIED** | 96/96 standalone live checks passed across the three browser engines. |
| Navigation | **VERIFIED** | All 12 navigation targets were present and opened their corresponding pages. |
| Canvas inventory | **VERIFIED** | 15 canvases/Chart.js instances across the SPA; per-page counts below sum to 15. |
| Initial Overview visibility | **VERIFIED** | Four Overview charts are visible on the initial page. The other page sections are hidden by SPA design until selected; the 15-canvas total is not a claim of 15 simultaneously visible Overview charts. |
| Console/runtime capture | **VERIFIED** | Zero console errors or page errors were captured in the audited flows. This is scoped to those flows, not a proof that no error can ever occur. |

## 3. Per-page chart audit

| Page | Navigation ID | Charts | Canvas IDs | Status |
|---|---|---:|---|---|
| Executive Overview | `overview` | 4 | `ch_revtrend`, `ch_catrev`, `ch_status`, `ch_rfm_ovr` | **VERIFIED** |
| Sales Performance | `sales` | 2 | `ch_catcomp`, `ch_region` | **VERIFIED** |
| Customer RFM | `customers` | 1 | `ch_rfm` | **VERIFIED** |
| Retention & Cohorts | `cohorts` | 1 | `ch_cohort` | **VERIFIED** |
| Churn Analysis | `churn` | 2 | `ch_churnpie`, `ch_models` | **VERIFIED** |
| Product Profitability | `products` | 2 | `ch_bcg`, `ch_margin` | **VERIFIED** |
| Revenue Forecast | `forecast` | 1 | `ch_forecast` | **VERIFIED** |
| Data Quality | `quality` | 0 | Content/table page; no chart required | **VERIFIED** |
| Business Insights | `insights` | 0 | Content page; no chart required | **VERIFIED** |
| AI Analyst | `ai` | 0 | Deterministic question/answer interface; no chart required | **VERIFIED** |
| Pricing Lab | `pricing` | 1 | `ch_pricing_margin` | **VERIFIED** |
| Win-Back Economics | `winback` | 1 | `ch_winback_sens` | **VERIFIED** |
| **Total** | **12 pages** | **15** | | **VERIFIED** |

## 4. Independent chart-series reconciliation

**VERIFIED — 22/22 series reconciled, 0 failures.** `chart_reconcile.py` derives expectations independently from raw CSVs, processed data, and reports rather than accepting dashboard self-reported KPI text. Its checks cover:

- order-status counts, monthly revenue, category revenue/profit/margin, and regional revenue;
- top-10 product revenue/profit/units, RFM segments, churn-risk bands, and the 156-cell cohort matrix;
- forecast and historical revenue, churn-model cross-validated AUC/F1, and BCG counts;
- pricing depth/margin/break-even/share series and win-back sensitivity.

The script reads the audited local dashboard data and independently recomputes expected values. Applying that reconciliation to production is supported by the exact CRLF→LF byte equivalence documented in §7, together with the live browser evidence. Merely displaying a value in the UI is not treated as independent proof.

## 5. Responsive behavior

**VERIFIED — zero horizontal overflow** at each audited width:

| Viewport width | Horizontal overflow |
|---:|---|
| 1920 px | 0 |
| 1366 px | 0 |
| 768 px | 0 |
| 375 px | 0 |

The checked-in standalone script separately contains a 390×844 mobile responsive observation. That script observation and the 375 px audit evidence are not conflated, and responsive probes are not added to the 96-check total.

## 6. Interaction and public-AI evidence

| Interaction | Observed result | Status |
|---|---|---|
| Pricing Lab: discount `20%`, assumed volume lift `20%` | Margin vs no discount **−24.6%**; revenue vs no discount **−4.0%**; break-even lift needed **+59.2%**; verdict “Below break-even” | **VERIFIED** |
| Win-Back Economics: budget `Rs 50,000` | 200 calls affordable and 200 customers contacted; expected net revenue **Rs 1.05 L**; return per unit spent **2.09×** | **VERIFIED** |
| Public AI built-in questions | Deterministic SQL text and grounded answers were exposed for the supported question set | **VERIFIED** for the deterministic public implementation |
| SQL-injection-shaped input | Refused by the public interface | **VERIFIED** for observed refusal behavior |
| Arbitrary/off-topic question | Refused by the public interface | **VERIFIED** for observed refusal behavior |
| Real Gemini provider calls | No real Gemini backend is deployed to the public static app | **NOT VERIFIED** |
| FastAPI-backed public AI execution | FastAPI is not part of this static deployment | **NOT VERIFIED** |

Pricing and win-back results are scenario/model outputs, not realized campaign outcomes. SQL shown by the static UI is explanatory deterministic content; its presence is not independent evidence that a production database query executed. Likewise, a UI refusal verifies the public interaction, not the separately hosted FastAPI service's database behavior.

## 7. Local/live byte integrity

**VERIFIED** by a fresh read-only local hash check and the captured live-response comparison:

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Each of four local copies: `dashboard.html`, `index.html`, `dashboard/dashboard.html`, `dashboard/index.html` | 129,765 | `e82fe755083c1703f26873b666480d23947d93608996cf100b97c20a7d184f6c` |
| Canonical local `dashboard/dashboard.html` after CRLF→LF normalization | 127,506 | `5aafd17688e5ed71f6ee54acaaae3552d971a394248efdb5d7e019fa1fdd4a1d` |
| Live `https://ecomanalytics-dashboard.vercel.app/` after CRLF→LF normalization | 127,506 | `5aafd17688e5ed71f6ee54acaaae3552d971a394248efdb5d7e019fa1fdd4a1d` |
| Live `https://ecom-zeta-one.vercel.app/` after CRLF→LF normalization | 127,506 | `5aafd17688e5ed71f6ee54acaaae3552d971a394248efdb5d7e019fa1fdd4a1d` |

Both canonical live responses equal the canonical local file after CRLF→LF normalization. Raw local working-tree bytes and LF-normalized live bytes therefore need not have matching sizes or hashes; line-ending normalization changes both. After the same normalization, the live and local bytes match exactly. The browser runs separately verify live behavior rather than relying only on file identity.

## 8. Performance observations

Median of three local browser runs per engine against the live URL. All timing values are milliseconds; CLS is unitless.

| Browser | TTFB | DOMContentLoaded | Load | LCP | CLS | Charts reported |
|---|---:|---:|---:|---:|---:|---:|
| Chromium | 86 | 923.9 | 1203.9 | 1280 | 0.0003745 | 15 |
| Firefox | 138 | 798 | 1190 | 859 | 0 | 15 |
| WebKit | 24 | 628 | 775 | 933 | 0 | 15 |

**VERIFIED** only as the recorded local measurements from `perf_live.json`. These are local measurements against the live URL, **not field/RUM data, not a controlled lab benchmark, and not a load test**. They do not establish performance under concurrent traffic or across user devices and networks. The 15-chart performance count denotes instantiated charts, not 15 simultaneously visible Overview charts.

## 9. Limitations and final dashboard verdict

- **NOT VERIFIED:** real Gemini provider calls and FastAPI-backed public AI; neither is deployed to the public static app.
- **NOT VERIFIED:** concurrent load behavior, real-user field performance, and errors outside the exercised flows.
- Zero captured console errors is scoped evidence, not an absolute guarantee.
- UI text alone was not accepted as analytical proof; independent reconciliation supplied the numerical evidence where available.
- Deployment-only findings and noncanonical hostname behavior are tracked in `docs/VERCEL_DEPLOYMENT_AUDIT.md`.

**Release verdict: VERIFIED for the canonical static dashboard.** The evidence supports the audited navigation, charts, responsive layout, deterministic interactions, and canonical live content. It does not certify an undeployed FastAPI/Gemini service or provide field/load-test assurance.
