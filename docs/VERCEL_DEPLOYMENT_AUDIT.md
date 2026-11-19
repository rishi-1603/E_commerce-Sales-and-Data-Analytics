# Vercel Deployment Audit — EcomAnalytics

**Audit date:** 2026-11-19<br>
**Code commit:** `890f66ffd21e5cfb7cf64358a9b56f01a3659747`<br>
**Branch:** `main`; commit pushed to `origin/main`<br>
**Canonical public URLs:** https://ecomanalytics-dashboard.vercel.app/ and https://ecom-zeta-one.vercel.app/

## Release verdict

**VERIFIED — the canonical public static-dashboard release is supported by the evidence.** The audited commit was pushed, all four recorded GitHub check runs completed successfully, the Vercel production deployment is `READY`, and both canonical live responses exactly match the canonical local dashboard after CRLF→LF normalization.

No **FAILED-UNRESOLVED** P0/P1/P2 deployment defect is evidenced for the canonical static app. Open P3 findings remain for noncanonical hostnames, duplicate projects, and a CI action-runtime warning. Project-inspect metadata is recorded separately as an observation whose cause is not established. Private runtime logs are **NOT VERIFIED**. This verdict does not deploy or certify FastAPI or a real Gemini analyst. **No Vercel settings were changed.**

## Status meanings

- **VERIFIED** — directly supported by the cited captured CLI/API/live-response evidence or a fresh read-only local check.
- **FAILED-UNRESOLVED** — an observed issue or inconsistency remains open; severity and release impact are stated separately.
- **NOT VERIFIED** — not established by the available evidence; this is not a claim of failure.

## 1. Source control and GitHub checks

**VERIFIED:** commit `890f66ffd21e5cfb7cf64358a9b56f01a3659747` was pushed to `origin/main`.

| Check run | Check-run ID | Recorded state | Status |
|---|---:|---|---|
| `test` | `135465903572` | Completed, `success` | **VERIFIED** |
| `build` | `135465907293` | Completed, `success` | **VERIFIED** |
| `deploy` | `135466119938` | Completed, `success` | **VERIFIED** |
| `report-build-status` | `135466120120` | Completed, `success` | **VERIFIED** |

One build annotation was recorded: the Node.js 20 deprecation warning affecting the current GitHub Actions runtime usage. It did not fail the run and remains an open P3 maintenance item — **FAILED-UNRESOLVED**, non-blocking.

The successful `test` check corresponds to the **272 pytest tests**. The separate **96-check standalone live browser script** is not part of that pytest count, and the two totals are never added together.

## 2. Production deployment identity

| Field | Audited value | Status |
|---|---|---|
| Deployment ID | `dpl_5kbUkqNcA2KFovP8hgpKrY7Zjedg` | **VERIFIED** |
| State / target | `READY` / production | **VERIFIED** |
| Deployment URL | `ecom-e6jv49zlv-rishi-1603.vercel.app` | **VERIFIED** |
| Time to ready | **3329 ms** | **VERIFIED** |
| Aliases | `ecom-zeta-one`, `ecom-rishi-1603`, `ecom-git-main-rishi-1603` | **VERIFIED** as deployment metadata |

Alias association is not treated as proof that every alias serves the application; actual hostname responses are assessed in §6.

## 3. Static deployment configuration

`vercel.json` was inspected directly:

```json
{
  "buildCommand": "echo 'Static site - no build needed'",
  "devCommand": "python -m http.server 8080",
  "installCommand": "echo 'No install needed'",
  "framework": null,
  "outputDirectory": "dashboard"
}
```

| Check | Result | Status |
|---|---|---|
| Served output | Static `dashboard/` output | **VERIFIED** |
| Application build/install | None; the configured commands only echo static-site messages | **VERIFIED** |
| Production environment variables | `vercel env ls production`: no environment variables | **VERIFIED** for the inspected project at audit time |
| Public backend | Static HTML/JavaScript application; no FastAPI service or real Gemini provider deployed | **VERIFIED** for the deployment architecture |
| Public AI behavior | Deterministic SQL and grounded built-in answers, including refusals | **VERIFIED**; see `docs/DASHBOARD_TEST_REPORT.md` |

The empty production environment-variable list is consistent with this self-contained static app. It is not an account-wide claim and does not describe other projects or non-production environments.

### Project-inspect metadata mismatch

Vercel project inspect metadata reports **framework `fastapi` and Node `26.x`**, despite the static `framework: null` configuration and static output described above.

**VERIFIED as a metadata observation; cause NOT VERIFIED.** This is not counted as an additional defect-register item: the effective static deployment and served content are independently verified. These metadata labels are not evidence that a FastAPI server or Node runtime serves the public app. No framework, Node, build, install, or output setting was changed.

## 4. Canonical content integrity

A fresh read-only local check confirmed that all four local dashboard copies are byte-identical. Normalizing the canonical local file from CRLF to LF produced exactly the same bytes and hash recorded for both canonical live responses.

| Artifact | Bytes | SHA256 | Status |
|---|---:|---|---|
| Each local copy: `dashboard.html`, `index.html`, `dashboard/dashboard.html`, `dashboard/index.html` | 129,765 | `e82fe755083c1703f26873b666480d23947d93608996cf100b97c20a7d184f6c` | **VERIFIED** |
| Canonical local `dashboard/dashboard.html`, CRLF→LF normalized | 127,506 | `5aafd17688e5ed71f6ee54acaaae3552d971a394248efdb5d7e019fa1fdd4a1d` | **VERIFIED** |
| `https://ecomanalytics-dashboard.vercel.app/`, CRLF→LF normalized | 127,506 | `5aafd17688e5ed71f6ee54acaaae3552d971a394248efdb5d7e019fa1fdd4a1d` | **VERIFIED** |
| `https://ecom-zeta-one.vercel.app/`, CRLF→LF normalized | 127,506 | `5aafd17688e5ed71f6ee54acaaae3552d971a394248efdb5d7e019fa1fdd4a1d` | **VERIFIED** |

**Both canonical live responses equal local after CRLF→LF normalization.** Raw local working-tree bytes and normalized live bytes are not expected to have identical sizes or hashes because line-ending normalization changes the byte representation. Under the same normalization, the comparison is exact. Live browser checks independently verify application behavior, so the release conclusion does not rest on hashes alone.

## 5. Build and deployment interpretation

The recorded `timeToReady` of **3329 ms** applies to this static deployment; it is not presented as a backend build or cold-start benchmark. There is no application dependency-install or compilation step in the audited static configuration.

The following are outside this deployment and are **NOT VERIFIED** as production services:

- FastAPI endpoints and their runtime behavior on Vercel;
- real Gemini provider calls;
- server-side environment configuration for such services.

The public static AI analyst must therefore not be described as a deployed Gemini/FastAPI service.

## 6. Hostname response audit

| Hostname | Observed response | Assessment |
|---|---|---|
| `ecomanalytics-dashboard.vercel.app` | Canonical EcomAnalytics application bytes; exact normalized local/live match | **VERIFIED** |
| `ecom-zeta-one.vercel.app` | Identical canonical EcomAnalytics application bytes; exact normalized local/live match | **VERIFIED** |
| `ecom-rishi-1603.vercel.app` | **HTTP 200 non-application `Login – Vercel` HTML (~334 KB)** | **FAILED-UNRESOLVED — open P3 hostname protection/housekeeping finding** |
| `ecom-git-main-rishi-1603.vercel.app` | **HTTP 200 non-application `Login – Vercel` HTML (~334 KB)** | **FAILED-UNRESOLVED — open P3 hostname protection/housekeeping finding** |

Fresh title extraction on both auto-generated hosts returned **`Login – Vercel`**. Their response bodies are approximately 334 KB and byte counts vary slightly between requests, so no single exact response size is claimed. HTTP 200 on these hosts is not application availability.

The exact Vercel protection setting was **NOT VERIFIED** and is not asserted to have been inspected. The finding is limited to the observed title/body classification and its open housekeeping impact; the two canonical public URLs are unaffected by the observed non-application responses.

## 7. Duplicate Vercel projects

Four Vercel projects point at this repository:

1. `ecomanalytics-dashboard`
2. `e-commerce-sales-and-data-analytics`
3. `ecom`
4. `dashboard`

**FAILED-UNRESOLVED — open P3 account housekeeping.** No project was deleted, renamed, unlinked, or otherwise changed. Duplication is not treated as a functional defect in the canonical static app, but ownership and ongoing maintenance of the duplicates remain unresolved.

## 8. Open findings and limitations

| Item | Status | Release impact |
|---|---|---|
| Two auto-generated hosts return `Login – Vercel` HTML rather than the app | **FAILED-UNRESOLVED — P3** | Noncanonical-host protection/housekeeping; canonical URLs verified separately |
| Four duplicate Vercel projects | **FAILED-UNRESOLVED — P3** | Account housekeeping; no canonical-app functional failure established |
| Inspect metadata says `fastapi` / Node `26.x` despite static config | Metadata values **VERIFIED**; cause **NOT VERIFIED** | Observation only, not an additional defect-register item; effective static deployment and content verified; no settings changed |
| Node.js 20 deprecation annotation in CI | **FAILED-UNRESOLVED — P3** | Warning only; all four checks succeeded |
| Exact auto-host protection configuration | **NOT VERIFIED** | No configuration cause is invented |
| Vercel private runtime logs | **NOT VERIFIED** | Audit is limited to CLI-visible metadata and public responses |
| Real Gemini provider execution | **NOT VERIFIED** | Not deployed to the public static app |
| FastAPI production runtime on Vercel | **NOT VERIFIED** | Not part of this static deployment |
| Concurrent load and real-user performance | **NOT VERIFIED** | Local browser timings are not a load test or field/RUM data |

Additional limitations:

- This is a point-in-time audit dated 2026-11-19, not continuous deployment monitoring.
- No settings, environment variables, aliases, protection controls, or project ownership were changed.
- Public response evidence establishes the returned content, not private infrastructure behavior.
- No real Gemini or FastAPI backend is deployed to the public static application.

## Final assessment

**VERIFIED for release of the audited static dashboard on the two canonical public URLs**, with the open P3 items listed above. The successful checks, `READY` production deployment, exact normalized canonical-byte match, and independent live browser evidence support that verdict. The audit does not claim a verified FastAPI/Gemini deployment, private-log review, exact auto-host protection configuration, or resolution of the P3 housekeeping findings.
