# AGENTS.md — operating contract for every AI agent working in this repo

Applies to Claude Code, OpenCode, Codex, Cursor, and any other harness. Read this before doing anything.

## Project

E-Commerce Sales & Customer Analytics — synthetic, seeded INR dataset (12,000 orders / 25,384 lines /
2,000 customers / 150 products, 5 categories, Jan 2022 – Dec 2024). Python pipeline + 11 SQL scripts +
Power BI (.pbix compiled / .pbip editable) + Chart.js dashboard on Vercel + FastAPI app with a grounded
NL-to-SQL assistant. 227 pytest tests pin the KPIs; definitions live in `data/metrics.json`.

## Non-negotiable rules

1. **Never fabricate** a number, screenshot, score, or capability. Evidence before claims.
2. **Every displayed figure must reconcile** — see the pinned values and procedure in
   `.claude/skills/verify-claims/SKILL.md` before publishing any number.
3. **Funnel semantics:** statuses are mutually exclusive; Returned (1,223 = 10.19% of placed) is its
   own exit — never subtract it from Delivered (9,312). State denominators explicitly.
4. **Synthetic-data disclosure stays** in README, metrics.json, docs. Never remove it.
5. **Dashboard copies stay byte-identical** (dashboard.html, index.html, dashboard/dashboard.html,
   dashboard/index.html). Edit `dashboard.html`, then copy to the other three (or run
   `scripts/inject_pricing_dashboard.py`), and confirm identical SHA256 before committing.
6. **Pipeline reruns regenerate benign noise** (float last-ulp diffs in `data/processed`, ₹→Rs./
   em-dash→-- console fallback, PNG metadata). Restore with `git checkout -- .` — never commit it.
7. **Power BI:** `.pbix` = compiled with embedded data (opens, no refresh); `.pbip` = editable source
   of truth (needs "Refresh now"). Screenshots must be genuine canvas captures — no editor chrome,
   no error dialogs. `.pbi/` local state is gitignored.
8. **Commits:** Conventional Commits style, concise subject; push to `main`. `git push` stderr
   NativeCommandError on Windows PowerShell is cosmetic — verify with `git log origin/main`.

## Environment quirks (Windows)

- PowerShell: no `&&` (use `;`), no `head`/`tail`/`grep` (use `Select-Object`/`Select-String`),
  no `rm -f` (use `Remove-Item -Force`).
- Always run Python via the venv: `.venv\Scripts\python.exe` (global 3.14 lacks deps). Set
  `$env:PYTHONUTF8='1'; $env:PYTHONPATH='.'` for tests/pipeline/scripts.
- flake8 (CI command): `.venv\Scripts\python.exe -m flake8 python/ run_pipeline.py app/ --max-line-length=120 --ignore=E501,W503,E302,E303,E305,E401,E402,E226,E231,E241,E251,E221,E127,E128,E272,E701,E702,E704,W292,W504,F401,E741`

## Verified commands

```bash
python data/raw/generate_data.py   # seeded, byte-identical regeneration
python run_pipeline.py             # 8-step pipeline
python -m pytest tests/ -q         # 227 tests
python scripts/inject_pricing_dashboard.py        # re-sync 4 dashboard copies
python evals/run_eval.py --min-accuracy 0.90      # AI eval gate (exit 0 required)
```

## Skills installed in this repo (.claude/skills/)

| Skill | Use when |
|---|---|
| `verify-claims` | Any number is displayed, changed, or questioned |
| `readme-audit` | README changes, publication readiness, scoring |
| `verification-loop` | Formal pre-merge/pre-push verification report |
| `python-patterns`, `python-testing` | Writing or reviewing pipeline/test code |
| `fastapi-patterns` | Working in `app/` (FastAPI service) |
| `postgres-patterns` | Working in `sql/` |
| `coding-standards` | General code-quality review |
| `codebase-onboarding` | Onboarding a new agent/human to this repo |
| `conventional-commit-review` | Drafting/reviewing commit messages |
| `documentation-lookup` | Verifying library usage against official docs |

## Agents installed in this repo (.claude/agents/)

| Agent | Delegates |
|---|---|
| `kpi-auditor` | Independent KPI reconciliation from raw CSVs |
| `readme-reviewer` | Senior-analyst + recruiter README scoring per the master prompt |
| `code-reviewer`, `commit-reviewer`, `architect`, `code-explorer`, `code-simplifier`, `build-error-resolver` | General review/build roles |

Working agreement: route work through the matching skill/agent first; do the work; verify; commit.
