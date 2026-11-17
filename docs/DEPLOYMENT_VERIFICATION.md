# DEPLOYMENT VERIFICATION — E-Commerce
### Verified 2026-10-18

## Targets
| Component | Where | URL |
|---|---|---|
| Dashboard (static HTML/Chart.js) | Vercel | https://ecomanalytics-dashboard.vercel.app/ |
| Repository + CI | GitHub Actions | rishi-1603/E_commerce-Sales-and-Data-Analytics |

## Machine-verified (2026-10-18)
- HTTP check on the dashboard URL: **200 OK**.
- CI latest run: **success** (pipeline -> eval scripts -> pytest, 196 tests).
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

---

# Fresh verification — 2026-11-17 (full browser session)

Supersedes the 2026-10-18 HTTP-200-only check above. Independent audit pass
(documented in `docs/PORTFOLIO_FINAL_AUDIT_2026-11-17.md`).

## Machine-verified (2026-11-17, real Chromium against the live URL)
- Page loads, title "EcomAnalytics — E-Commerce Sales & Customer Intelligence".
- **Console: 0 errors, 0 warnings.** Network: 10 requests, 0 failed / 4xx / 5xx.
- Hero KPIs match canonical: ₹5.93 Cr revenue · ₹3.20 Cr profit · 54.0% margin ·
  9,933 orders · 1,991 customers · ₹5,968 AOV · 448 cooling-off · return rate 10.2%
  (1,223 of 12,000 placed).
- Navigation: all 12 page sections present; Sales Performance activates and renders
  9,312 Delivered · 77.6%, 844 Cancellations · 7.0%, best category Sports and top
  region West (both match `reports/fact_sheet.json`).
- Responsive: viewport meta present; `@media` rules for hamburger (≤900px), KPI
  grid collapse (≤1080/560px), `prefers-reduced-motion`.
- Genuine screenshot: `docs/screenshots/live_deployment_2026-11-17.png`.
- CI green on audited commit `a8bf7e9` (run #88, plus Pages deploy success).

## Limitation of this check
Viewport-resize was unavailable in the audit browser, so no rendered ~390px
screenshot; responsiveness was verified via live-CSS inspection. Audit-harness
synthetic clicks did not trigger inline `onclick` handlers; navigation was verified
by executing the page's own `nav()` handler in the live DOM (environment
observation, not a product defect).
