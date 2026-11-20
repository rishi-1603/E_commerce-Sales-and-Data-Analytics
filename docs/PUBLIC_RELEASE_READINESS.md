# Public Release Readiness

**Date:** 2026-11-20<br>
**Overall verdict:** **RELEASE-READY WITH DISCLOSURES** for the public synthetic-data portfolio scope<br>
**Known unresolved P0/P1:** **none**<br>
**Code evidence SHA:** `890f66f` plus the A13 fix committed after it<br>
**Production:** https://ecomanalytics-dashboard.vercel.app/

The follow-up commit SHA is intentionally not guessed: identify it with `git log` after the commit. CI/deployment results below attach to code SHA `890f66f` unless a newer run is cited.

**Status terms:** **VERIFIED** = supported by the named source, test, live, or deployment evidence; **FAILED-UNRESOLVED** = a reproduced failure remains; **NOT VERIFIED** = execution or access evidence is insufficient. Source inspection, tests, live browser checks, and deployment evidence are not interchangeable.

## 1. Release decision and evidence

| Gate | Status | Evidence and scope |
|---|---|---|
| Source and local regression | **VERIFIED** — test | **273 pytest tests passed** on the final local run after the A13 fix. See [TEST_REPORT.md](TEST_REPORT.md) and [COMPLETE_PROJECT_QA_REPORT.md](COMPLETE_PROJECT_QA_REPORT.md). |
| Real CI gate | **VERIFIED** — test/deployment API evidence | GitHub Actions `test` succeeded on Python 3.11 at code SHA `890f66f` (run `44496785646`, job `135465903572`). This is real CI evidence, not a claimed local Linux reproduction. |
| Four check runs | **VERIFIED** — deployment/check-runs evidence | At code SHA `890f66f`: GitHub `test` plus Vercel `build`, `deploy`, and `report-build-status` all concluded `success`. These are four check runs, not four repetitions of pytest. |
| Public dashboard behavior | **VERIFIED** — live | **96/96 standalone live checks passed** across the recorded browser run: 12 pages, 15 charts, zero console errors, and responsive checks. The 96 checks are separate from the 273 pytest tests. |
| Chart data | **VERIFIED** — live + independent recomputation | **22/22 chart series reconcile** with independently recomputed values. This is a series count, not a claim that only 22 charts exist. |
| Deployment identity/content | **VERIFIED** — deployment | Deployment `dpl_5kbUkqNcA2KFovP8hgpKrY7Zjedg` is Ready and serves `890f66f`. Canonical live responses exactly equal the LF-normalized local canonical dashboard bytes (127,506 bytes). |
| Security/dependency audit | **VERIFIED** within recorded scan/test scope | CORS wildcard-with-credentials was removed and regression-tested; secret scan reported zero findings; requirements audit reported no known vulnerabilities. No credentials are exposed in these reports. |
| Public AI analyst | **VERIFIED** as a bounded deterministic feature — source + live + deployment | Six curated grounded answers, visible SQL, and refusal of arbitrary prompts. It is not Gemini and does not call FastAPI. See [AI_ANALYST_EVALUATION.md](AI_ANALYST_EVALUATION.md). |
| Offline AI fallback quality | **VERIFIED** — test | Fallback scores **37/37 (100%)** on benchmark v1.1 after the A13 fix, with 100% refusal correctness and zero fabricated numbers. A regression test pins the category-margin answer. This is not a live Gemini score. |
| Real Gemini provider | **NOT VERIFIED** — credential/deployment limit | FastAPI Gemini source and mocked tests exist, but no local `GEMINI_API_KEY` or Vercel production environment variables were available. The FastAPI backend is not deployed to Vercel. |

The release verdict means the audited static portfolio and its documented source/test evidence are suitable to publish with these caveats. It is not a guarantee of production business impact, provider quality, real campaign returns, or every unexecuted runtime.

## 2. Issue register reconciliation — exactly 25 entries

Authoritative defect details and regression evidence: [QA_REMEDIATION_LOG.md](QA_REMEDIATION_LOG.md). Investigated non-defects are separate and are not counted in these 25 entries.

| Severity | Fixed | Documented limitation | Open | Total |
|---|---:|---:|---:|---:|
| P0 | 1 | 0 | 0 | **1** |
| P1 | 6 | 0 | 0 | **6** |
| P2 | 8 | 1 (AN-01) | 0 | **9** |
| P3 | 7 | 0 | 2 | **9** |
| **Total** | **22** | **1** | **2** | **25** |

| # | ID | Severity | Disposition | Evidence layer / concise outcome |
|---:|---|---|---|---|
| 1 | DOC-04 | P0 | Fixed | `README.md:285`, `reports/assumptions_and_limitations.md`, `docs/AUDIT_2026-11-18.md`: raw-CSV recomputation + read-back; total revenue ₹59,283,619.32 = ₹5.928361932 Cr → ₹5.93 Cr; Delivered-only ₹55,492,687.66 = ₹5.549268766 Cr → ₹5.55 Cr |
| 2 | DASH-01 | P1 | Fixed | Live production DOM verification; five pages restored inside layout |
| 3 | DASH-02 | P1 | Fixed | Live resize/responsive verification; chart overflow removed |
| 4 | SEC-01 | P1 | Fixed | Source + regression tests; unsafe CORS reflection removed |
| 5 | DATA-01 | P1 | Fixed | Source artifacts + registry tests + live value; win-back claims reconciled |
| 6 | DATA-02 | P1 | Fixed | Source artifacts + tests + live answer; holdout/CV and split wording corrected |
| 7 | AI-01 | P1 | Fixed | Source fix + regression test; A13 returns category percentage margin; 37/37 eval, 0 fabricated |
| 8 | DASH-03 | P2 | Fixed | Live Chart.js configuration; margin axis starts at zero |
| 9 | DASH-04 | P2 | Fixed | Live DOM; model card names cross-validation protocol |
| 10 | DASH-05 | P2 | Fixed | Live DOM; churn horizon separated from model-selection protocol |
| 11 | DASH-06 | P2 | Fixed | Live DOM; forecast band labeled indicative with 9.5% coverage |
| 12 | DOC-01 | P2 | Fixed | Documentation aligned to observed test and 96-live-check evidence |
| 13 | DOC-02 | P2 | Fixed | Collection + registry agreement; public test count aligned |
| 14 | DOC-03 | P2 | Fixed | Local-only audit guidance reconciled with artifacts and canonical dashboard input |
| 15 | SEC-02 | P2 | Fixed | Placeholder credentials removed; secret scan reports zero findings |
| 16 | AN-01 | P2 | **Documented limitation** | Forecast uncertainty remains under-covered and honestly labeled; not re-engineered |
| 17 | REPO-01 | P3 | Fixed | Source references checked; debris removed and regression run passed |
| 18 | REPO-02 | P3 | Fixed | Duplicate weaker live suite removed; single 96-check suite retained |
| 19 | TECH-02 | P3 | Fixed (local environment) | Installer upgraded; local and requirements audits clean |
| 20 | VERCEL-01 | P3 | **Open** | Two auto-generated hosts return non-app responses; canonical app unaffected |
| 21 | VERCEL-02 | P3 | **Open** | Four Vercel projects point at the same repository |
| 22 | TECH-01 | P3 | Fixed | Source/mock tests; `google-genai` client + config; real provider still NOT VERIFIED |
| 23 | CI-01 | P3 | Fixed | `checkout@v7` / `setup-python@v7`; the next CI run is the confirming gate |
| 24 | SQL-01 | P3 | Fixed | Static audit; all 12 analysis scripts use the canonical header trio |
| 25 | API-01 | P3 | Fixed | API tests; explicit `refused` flag on refusal responses |

AI-01 records the former fallback A13 failure and its verified repair; the benchmark question and ground truth were unchanged. Details: [AI_ANALYST_EVALUATION.md](AI_ANALYST_EVALUATION.md).

### Six open P3 items — complete enumeration

| ID | Current evidence and required disclosure |
|---|---|
| **VERCEL-01** | `ecom-rishi-1603.vercel.app` and `ecom-git-main-rishi-1603.vercel.app` return **HTTP 200 non-application `Login – Vercel` HTML (~334 KB)**; body sizes vary slightly per request. This does not prove the exact protection configuration: settings were not inspected or changed. The canonical public URL is unaffected and its live bytes match the audited canonical source. |
| **VERCEL-02** | Four projects — `ecomanalytics-dashboard`, `e-commerce-sales-and-data-analytics`, `ecom`, and `dashboard` — deploy this repository. This is account housekeeping; no project was deleted or reconfigured. |
| **TECH-01** | FastAPI uses deprecated `google.generativeai`; migrate to `google.genai`. Real provider behavior after migration is **NOT VERIFIED** without a key. The deterministic public analyst is unaffected. |
| **CI-01** | `actions/checkout@v4` and `actions/setup-python@v5` emit the Node.js 20 deprecation warning/Node 24 forced-runtime annotation. The recorded run still succeeds; this is cosmetic technical debt, not a failed gate. |
| **SQL-01** | SQL scripts 09–12 use `Purpose` / `Why` / `Verified` instead of `Business Question` / `Why It Matters` / `Key Insight`. Static audit found eight canonical and four alternate headers with none missing; wording consistency only. |
| **API-01** | NL-to-SQL refusals return `is_safe=True`, empty SQL, zero rows, and explicit refusal text. Nothing executes, but the flag describes query safety rather than answer success; semantics remain open and documented. |

**No known unresolved P0/P1 remains. Two P3 Vercel account items remain open pending authorization; all code-level P3 items are fixed. No settings were changed.**

## 3. Analytical limitations that ship with the release

### AN-01 — forecast performance and uncertainty

**VERIFIED as a documented limitation — source + test + live disclosure.**

- The shipped ensemble has rolling-origin **MASE 0.680**, losing to the **drift baseline at 0.468** (lower is better). Evidence: [`reports/forecast_backtest.md`](../reports/forecast_backtest.md).
- The `holt_linear` challenger records **MASE 0.3752** under the identical protocol and beats drift, but it is a challenger result, not the currently shipped ensemble. Evidence: [`reports/forecast_challenger_metrics.json`](../reports/forecast_challenger_metrics.json).
- The nominal **95%** bootstrap band has only **9.5% empirical coverage** (21 evaluated points; h1 28.6%, h2/h3 0%). It is **indicative only**, not a calibrated 95% interval. The report attributes the weakness to estimating variance from three holdout residuals and recommends rolling-origin residual history.
- Jan–Jun 2025 is a historical holdout/backtest horizon, not a live forecast. Operational guidance should prefer the simpler drift/holt_linear evidence over claiming that ensemble complexity helps.

AN-01 is not claimed fixed. The release-safe action was disclosure at the report, metrics, README, and live dashboard card levels.

### Churn model — modest, non-causal evidence

**VERIFIED for recorded metrics — source + tests; operational uplift NOT VERIFIED.**

[`reports/churn_model_metrics.json`](../reports/churn_model_metrics.json) reports a stratified 64/16/20 protocol on 1,597 scored customers, with a 320-customer holdout:

| Metric | Value |
|---|---:|
| Holdout ROC-AUC | **0.6621** |
| Holdout PR-AUC | **0.3322** |
| Calibrated holdout Brier score | **0.1715** |
| Calibrated expected calibration error (ECE) | **0.0352** |
| Model-label prevalence | **23.54%** |

This is a modest model, not a causal targeting guarantee and not proof of campaign uplift. The split is not described as temporal; threshold economics are expected-value calculations under assumptions, not observed profit.

### Win-back economics — assumptions, not realized returns

**VERIFIED as scenario arithmetic — source + tests + live; campaign outcome NOT VERIFIED.**

[`reports/winback_economics.json`](../reports/winback_economics.json) uses an illustrative **₹250 cost per contact**, **15% recovery rate**, and **₹13,292.20 retained value**, applied to **441 Medium Risk customers**. Baseline expected-value outputs are ₹522.55 per contact and ₹230,443.56 total before COGS despite the artifact’s `expected_profit*` field names; they are not measured net profit.

No win-back campaign has been run. Sensitivity cases disclose how results change with contact cost and recovery rate; they do not establish causality, realized savings, or future revenue.

## 4. AI and deployment disclosure

The public Vercel analyst is a deterministic in-browser template router with visible SQL and curated grounded answers. It is **not real Gemini** and **not the FastAPI provider**. Real Gemini-backed interpretation and database-executing NL-to-SQL remain source-side capabilities outside the static Vercel deployment.

The committed offline fallback eval from **2026-11-20T03:20:20+00:00** is **37/37 = 100.0%**, with 13/13 simple aggregation, 10/10 segment breakdown, 9/9 time intelligence, 5/5 refusal, zero fabricated numbers, p50 632.0 ms and p95 699.0 ms. Baseline was 18/37 = 48.6%, with 80% refusal correctness and one fabricated answer. A13 was fixed at the routing level and is pinned by a regression test; the benchmark question and ground truth were unchanged. These figures evaluate the fallback harness only; they do not certify live Gemini quality or security. Full evidence and safety boundaries: [AI_ANALYST_EVALUATION.md](AI_ANALYST_EVALUATION.md).

## 5. Explicitly NOT VERIFIED

| Area | Status and precise boundary |
|---|---|
| PostgreSQL execution of `sql/` | **NOT VERIFIED.** Static PostgreSQL-dialect audit passed, but local PG 17 required credentials unavailable to the audit (`psql -w` / `fe_sendauth`). No credential was guessed and no server configuration changed. |
| Real Gemini provider execution | **NOT VERIFIED.** No local `GEMINI_API_KEY`; zero Vercel production environment variables. Mocked tests and fallback mode do not execute a real provider. |
| Power BI Desktop execution | **NOT VERIFIED.** Desktop was unavailable; `.pbix`/`.pbip` evidence is source-level inspection, not a fresh Desktop run. |
| Private Vercel runtime logs and raw GitHub job logs | **NOT VERIFIED.** Vercel conclusions rely on CLI-visible metadata; GitHub conclusions rely on the check-runs API. Raw job logs returned 403 unauthenticated and `gh` was unavailable. |
| Exact local Linux/Python 3.11 reproduction | **NOT VERIFIED.** No WSL/Docker reproduction was performed. The real GitHub Actions Python 3.11 run covers the CI gate and is reported separately. |
| Concurrent multi-client FastAPI load | **NOT VERIFIED.** Recorded API latency is single-client only; no production capacity or soak-test claim is made. |

## 6. Seven audit deliverables

1. [docs/COMPLETE_PROJECT_QA_REPORT.md](COMPLETE_PROJECT_QA_REPORT.md)
2. [docs/QA_REMEDIATION_LOG.md](QA_REMEDIATION_LOG.md)
3. [docs/METRIC_RECONCILIATION_REPORT.md](METRIC_RECONCILIATION_REPORT.md)
4. [docs/DASHBOARD_TEST_REPORT.md](DASHBOARD_TEST_REPORT.md)
5. [docs/VERCEL_DEPLOYMENT_AUDIT.md](VERCEL_DEPLOYMENT_AUDIT.md)
6. [docs/AI_ANALYST_EVALUATION.md](AI_ANALYST_EVALUATION.md)
7. [docs/PUBLIC_RELEASE_READINESS.md](PUBLIC_RELEASE_READINESS.md)

**Commit mapping:** DOC-04 corrections in `README.md`, `reports/assumptions_and_limitations.md`, and `docs/AUDIT_2026-11-18.md`, plus the seven audit reports above. Identify the resulting commit SHA with `git log` after commit; no commit SHA is invented here.

## 7. Final statement

**RELEASE-READY WITH DISCLOSURES.** The code at `890f66f` plus the A13 fix has recorded local regression evidence and matching live deployment evidence; no known unresolved P0/P1 remains. Open P3 items, AN-01, modest churn performance, assumption-driven win-back economics, and every NOT VERIFIED boundary remain visible. The fallback benchmark is now 37/37 with zero fabricated answers.

No settings were changed, no credentials are exposed, and no commit SHA for the follow-up documentation commit is invented; use `git log` after commit to identify it.
