# Final publication audit — E-Commerce Sales & Customer Analytics

Audit date: 2026-10-30. Scope: targeted publication repair, not a certification of literal perfection.
Baseline GitHub main: `99648ff2361e7870e001397d5b07c645e4b0993c`. Recoverable branch: `audit/publication-review`.

## Execution and ownership
No autonomous subagents were available. One assistant performed sequential data/SQL, code, QA, security, browser and documentation workstreams. Tests and tool checks are evidence; there was no independent human or separately spawned QA agent.

## Changes and issue register
| Severity | File/screen | Evidence | Root cause | Repair | Verification |
|---|---|---|---|---|---|
| HIGH | scripts/inject_pricing_dashboard.py; four dashboard HTML copies | Live Win-Back navigation throws TypeError at titles[id][0]. | Generator added the page but not its title. | Generate both titles idempotently; add all-navigation-title regression test. | FIXED: 26 dashboard tests; nine local navigation pages, no page errors. |
| LOW | README.md | Footer claimed 182 while current baseline suite contained 195. | Stale documentation. | Record actual new suite total 196 and avoid claiming tests prove every production interaction. | FIXED; full suite 196 passes. |
| MEDIUM | Forecast evaluation | 40 optimizer convergence warnings. | Some Holt-Winters fits do not converge cleanly. | Keep warnings visible; do not sell model performance as production certainty. | OPEN/DISCLOSED; forecasts remain demonstration-only. |

## Data and metric verification
Full seeded generation/pipeline and evaluation commands executed. A cross-project environment initially used scikit-learn 1.9.0 and failed a calibration pin; reinstalling the project-pinned 1.6.1 restored the expected result. Final full regression: 196 pass. Monetary SQL and funnel assertions run in the suite.

PARTIAL — executable SQLite/NL-to-SQL accuracy and safety tests passed. PostgreSQL scripts were not all executed against a PostgreSQL server.

## Feature verification matrix
Production: nine navigation actions exercised; Win-Back crash reproduced before repair. Local repaired HTML: nine pages exercised, no JavaScript page errors. Four requested viewports captured. Filter combinations, all exports and external LLM/API paths are not exhaustively verified.

- Production browser checks were separate from local tests.
- Initial Streamlit sleep screens were not counted as application success; apps were woken and actual embedded app frames inspected.
- Screenshot captures were genuine browser images, not generated mockups. Baseline production captures are retained in the external audit evidence pack, not represented as post-repair screenshots.
- No independent LLM provider test, exhaustive state-space check, accessibility-tool audit or production load test was completed.

## Source, structure and security checks
- 192 tracked files inventoried; 140 relevant text files pattern-scanned. This is not a claim of exhaustive semantic line-by-line review.
- Fatal syntax/undefined-name static check: `ruff check . --select E9,F63,F7,F82` passed. Broad style/type cleanup was not performed.
- README local link/image paths: no missing targets detected at baseline.
- Known GitHub token, Google-key and private-key signature scan over selected current text files and reachable historical text blobs: no matches. Heuristic only; screenshots/binary secrets and all possible credential formats are unverified.
- No tracked .env, credentials.json or secrets.toml found by the targeted filename check.
- pip-audit requirements resolution: no known vulnerabilities reported at scan time. This is not a guarantee of secure deployment or a replacement for a lockfile.
- The token supplied in chat is exposed and should be revoked/rotated. It must never enter repository content.

## Release scorecard
| Area | Status | Evidence / boundary |
|---|---|---|
| Repository structure | PARTIAL | Targeted evidence above; comprehensive requirement coverage not established. |
| Code quality | PARTIAL | Targeted evidence above; comprehensive requirement coverage not established. |
| Data cleaning | PARTIAL | Targeted evidence above; comprehensive requirement coverage not established. |
| Metric correctness | PARTIAL | Executed reconciliation/tests for covered metrics; not every displayed calculation independently re-derived. |
| SQL validation | PARTIAL | PARTIAL — executable SQLite/NL-to-SQL accuracy and safety tests passed. PostgreSQL scripts were not all executed against a PostgreSQL server. |
| Feature functionality | PARTIAL | Targeted evidence above; comprehensive requirement coverage not established. |
| UI/UX | PARTIAL | Four viewports captured; tab/navigation smoke checks only. |
| Accessibility | BLOCKED | No complete keyboard/screen-reader/contrast audit; viewport checks do not establish accessibility. |
| Security | PARTIAL | Requirements scan and selected secret signatures only. |
| Performance | PARTIAL | Targeted evidence above; comprehensive requirement coverage not established. |
| Automated tests | PASS | 196 passed; see external final test log. |
| Build and CI | PARTIAL | Local checks recorded; pushed-commit CI is verified separately in the delivery report. |
| README and documentation | PARTIAL | Targeted evidence above; comprehensive requirement coverage not established. |
| GitHub presentation | PARTIAL | Targeted evidence above; comprehensive requirement coverage not established. |
| Live deployment | PARTIAL | Baseline production rendered; repaired-commit deployment must be confirmed separately. |
| Recruiter readiness | PARTIAL | Targeted evidence above; comprehensive requirement coverage not established. |

## Recruiter notes
### 15-second summary
Commercial analytics case study linking sales, customer retention and pricing questions to reproducible SQL/Python outputs and a dashboard.

### One-minute technical overview
Commercial analytics case study linking sales, customer retention and pricing questions to reproducible SQL/Python outputs and a dashboard. The workflow defines entities and denominators, validates selected calculations independently, and presents findings with reproducible Python/SQL evidence. Statistical results are framed as descriptive or scenario-based where causal evidence is absent. Review the limitations before interpreting any model, risk score or financial estimate. Tests support reproducibility but do not prove production performance.

### Three analytical achievements
- Revenue and margin use explicit order-status and line-item definitions; tests reconcile analytical outputs.
- Discount scenarios quantify required volume lift rather than claiming causal promotion impact.
- Forecast challengers are compared with shared rolling-origin baselines; losing models remain documented.

### Three technical challenges
- Maintaining four identical deployment HTML copies.
- Avoiding leakage and denominator drift in retention/churn metrics.
- Distinguishing modeled campaign economics from measured uplift.

### Five interview questions
- Which order statuses count as revenue, and why?
- What is the difference between an order and a line item?
- Why can observational discounts not establish demand elasticity?
- How is the forecast baseline evaluated?
- What would validate a win-back campaign in practice?

## Release checklist
- [x] Fresh public clone; old workspaces left untouched.
- [x] Recoverable branch and scoped diff.
- [x] Targeted fixes tested; no test weakened or deleted.
- [x] Selected SQL/data, security and browser evidence recorded.
- [ ] Pushed commit CI and repaired deployment verified (see delivery report).
- [ ] Complete accessibility, filter/export/provider and performance coverage.

## Remaining verification
Recheck production after deployment of this repair. Full PostgreSQL execution, keyboard/screen-reader audit, every filter/export/AI-provider path, and performance load testing remain incomplete.

## Verdict
**NOT READY for an unconditional all-features final-release claim.** Targeted source repairs pass their local acceptance tests. Publication as an analytics demonstration must retain the listed limitations; release completion depends on the pushed-commit CI and deployment follow-up.

## 2026-10-30 Second-pass publication audit (independent)

Baseline main: `85bcbf5`. Recoverable branch: `audit/publication-review-2`. All work on a branch; nothing pushed to `main` directly.

### Verified in this pass
- Dependency install from `requirements.txt`: exit 0.
- Full automated suite executed on Python 3.13: **196 passed**.
- Static fatal-error scan (`ruff check --select E9,F63,F7,F82`): **All checks passed**.
- CI on the current `main` head: **success** (GitHub Actions API).
- README internal links and local image paths: no missing targets.

### Fixes applied
- Repaired three malformed Markdown code fences in `README.md` (single-backtick lines opened/closed architecture and quickstart blocks).
- Corrected stale test counts in `README.md` (119 -> 196) and in `docs/RELEASE_GATES.md`, `docs/DEPLOYMENT_VERIFICATION.md`, `docs/MASTER_PLAN.md`, `reports/interview_prep.md` (182 -> 196).
- Removed unreferenced debug artifact `_debug_parse.py`.
- Security: removed the hardcoded `SECRET_KEY` default in `app/core/config.py` (now reads `SECRET_KEY` or generates an ephemeral key); parameterized `docker-compose.yml` (`POSTGRES_PASSWORD`, `SECRET_KEY`) with fail-fast Compose interpolation; documented `POSTGRES_PASSWORD` in `.env.example`.
- Added a verified 'public - no login' note to the live dashboard link.

### Blocked / manual action required
- Repository homepage field: **set** via the GitHub API (HTTP 200) to the live app URL.
- Full PostgreSQL execution, keyboard/screen-reader accessibility audit, every filter/export path, and load testing remain unverified.
