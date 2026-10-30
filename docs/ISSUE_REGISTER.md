# Issue register

2026-10-30 follow-up. All listed repairs require full regression; deployment checks are separate.

| Severity | Exact location | Evidence | Root cause | Repair | Verification |
|---|---|---|---|---|---|
| Medium | index.html; dashboard.html; dashboard/index.html; dashboard/dashboard.html | axe identified mobile scrollable-region-focusable. | Content scroller was not keyboard-focusable. | Add tabindex, region role and accessible name. | Browser patch scan clears violation; regression and post-release scan. |
| High | tests/api/conftest.py | API tests added five records to the default developer database. | Fixture initialized the configured application database. | Override URLs with a temporary SQLite path before importing settings/engines. | Full suite passes; developer DB SHA256 unchanged after test run. |
| Medium | app/services/query_service.py | LIMIT 1000000 and LIMIT -1 bypassed the documented bound. | Only absent limits were capped. | Cap oversized integer limits; reject negative/dynamic limits and qualified external tables. | Strict new security regression and full suite pass. |
| High | app/core/config.py; docker-compose.yml; .env.example | Reviewed audit PR contained fixes for shipped default secrets/passwords. | Unsafe demonstration defaults could be mistaken for deployable credentials. | Merge reviewed PR: ephemeral local key, required Compose secret variables and example placeholders. | API tests/startup pass; Docker build not executed because Docker is unavailable. |
| Low | Python analysis and test modules; migrations | 38 selected lint findings at baseline. | Unused bindings and intentional model-registration imports. | Remove unused imports/locals; retain and explain registration side effects. | Ruff E9/F63/F7/F82/F401/F541/F841 clean; no assertion removed. |

## Remaining boundaries
- No real parallel subagent facility was available; sequential specialist workstreams were used.
- Optional external LLM providers require separate credentials and evaluation; deterministic tests are not unrestricted narration tests.
- No complete manual screen-reader/contrast review or production stress certification.
- Revoke any credential exposed in chat or elsewhere. Repository cleanup cannot revoke that credential.
