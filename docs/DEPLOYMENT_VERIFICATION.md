# DEPLOYMENT VERIFICATION — E-Commerce
### Verified 2026-10-18

## Targets
| Component | Where | URL |
|---|---|---|
| Dashboard (static HTML/Chart.js) | Vercel | https://ecomanalytics-dashboard.vercel.app/ |
| Repository + CI | GitHub Actions | rishi-1603/E_commerce-Sales-and-Data-Analytics |

## Machine-verified (2026-10-18)
- HTTP check on the dashboard URL: **200 OK**.
- CI latest run: **success** (pipeline -> eval scripts -> pytest, 182 tests).
- Regeneration chain: metrics artifacts rebuild from scripts on every CI run.

## Manual checks the owner should do before sharing the link (click-through)
1. Open all 6 dashboard pages; spot-check one number per page against reports/.
2. Confirm charts render on mobile width.
3. Re-run `python run_pipeline.py && python -m pytest tests/` locally after any change.

## Redeployment
Vercel redeploys on push to main (static build). No secrets or env vars required
for the dashboard itself.

## Rollback
Git revert on main -> Vercel rebuilds previous state. Dashboard reads precomputed
JSON, so a broken pipeline cannot corrupt an already-deployed page.
