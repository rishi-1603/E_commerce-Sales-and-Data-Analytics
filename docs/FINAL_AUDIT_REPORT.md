# Final Portfolio Audit

**Repository:** E-Commerce Sales & Customer Analytics  
**Audit scope:** data, analytics, Power BI PBIP, Excel workbooks, web dashboard,
tests, deployment surface, documentation, accessibility and recruiter readiness.  
**Final commit:** `70988d8`  
**Decision:** **GO — resume-ready, with documented limitations**

## Evidence checked

- Full pytest suite: **227 passed**, 56 non-failing `statsmodels` convergence warnings.
- Excel validation: **10 passed** across both `.xlsx` workbooks.
- Dashboard consistency, decision-layer and pricing regression tests: **all passed**.
- Flake8 command used by CI: passed with the repository's configured exclusions.
- Raw data reconciliation: 12,000 orders, 25,384 order lines, 2,000 customer
  records, 150 products; no duplicate primary identifiers, nulls or orphan
  foreign keys in the raw tables.
- Order status reconciliation: Delivered 9,312; Processing 621; Returned 1,223;
  Cancelled 844.
- PBIP definition: version 4.0, BOM-free, four pages and 37 visuals.
- Power BI Desktop local verification: report opened, refreshed and rendered the
  Executive Overview with reconciled KPI values.
- Live dashboard: `https://ecomanalytics-dashboard.vercel.app/` loaded over HTTPS;
  no console errors; navigation to Sales Performance worked; Lighthouse reported
  Accessibility 100, Best Practices 100 and SEO 100 after the final deployment
  was cache-busted for verification.

## Issue and fix tracker

| Severity | Finding | Resolution | Status |
|---|---|---|---|
| High | Stale legacy `.pbix` binary conflicted with the complete PBIP report | Removed the stale binary; README and build specification identify PBIP as the source of truth | Fixed |
| High | Funnel previously subtracted Returned from Delivered | Corrected SQL, Python, metrics, dashboard, tests and interview documentation | Fixed |
| High | Power BI PBIR/TMDL load failures | Fixed PBIR version/location, page and visual identifiers, TMDL indentation, BOMs and auto-date references | Fixed |
| Medium | Dashboard header claimed 55,867 transactions | Corrected to 25,384 order lines and 1,991 active customers | Fixed |
| Medium | DAX dictionary described an obsolete 10-measure model and 0% return rate | Replaced with the current 18-measure dictionary and 10.19% return rate | Fixed |
| Medium | Public repository contained obsolete delivery/audit files claiming a missing `.pbix` and missing context file | Removed stale generated reports and audit scripts | Fixed |
| Medium | Live dashboard lacked a semantic `<main>` landmark | Converted the content container to `<main>` and verified Lighthouse | Fixed |
| Low | Forecast tests emit `statsmodels` convergence warnings | Results remain regression-tested; warnings are documented as non-blocking model-fit diagnostics | Accepted / documented |

## Data-quality results

| Check | Result |
|---|---|
| Order headers | 12,000 unique IDs; no nulls |
| Order lines | 25,384 unique item IDs; no nulls |
| Customers | 2,000 unique IDs; no nulls |
| Products | 150 unique IDs; no nulls |
| Orphan order references | 0 |
| Orphan product/customer references | 0 |
| Negative quantity or price | 0 |
| Revenue-eligible orders | 9,933 (Delivered + Processing) |
| Active revenue customers | 1,991 |

## Analytical validation

The main revenue population is explicitly `Delivered + Processing`:

- Revenue: ₹59,283,619.32
- COGS: ₹27,286,277.68
- Gross profit: ₹31,997,341.64
- Gross margin: 53.97%
- AOV: ₹5,968.35

The operational population is all 12,000 order headers. Returned orders are an
independent status category and are not subtracted from Delivered orders.

## Excel handover

Both workbooks are present and tested:

- `powerbi/EcomAnalytics_Business_Reporting.xlsx`: reporting workbook with Read
  Me, source data, customer data, executive KPIs, sales analysis, RFM, retention,
  forecast and reconciliation sheets.
- `powerbi/Ecommerce_BI_Companion.xlsx`: star-schema companion with fact sales,
  customer/product/date dimensions and monthly checks.

The Excel tests validate required sheets, row counts, formula/output structure and
reconciliation values. The workbooks are static generated artifacts and should be
regenerated when source data changes.

## Remaining boundaries

1. The repository intentionally ships PBIP/PBIR, not a legacy `.pbix` binary.
   A local Power BI Desktop user can save the PBIP as `.pbix` when a binary
   handoff is required.
2. The dataset is synthetic and all business findings are illustrative.
3. The Vercel deployment is a static dashboard; Power BI Desktop refresh is a
   local desktop operation, not a claimed Power BI Service deployment.
4. The forecast convergence warnings are non-fatal diagnostics, not hidden test
   failures. Forecast backtest results and limitations are documented.

## Final verdict

**GO — RESUME READY.** No known critical correctness, security, deployment,
dashboard or documentation blockers remain in the repository. The project is
credible for a fresher Data Analyst / BI portfolio provided the candidate can
explain the population definitions, synthetic-data limitation, order-line grain,
churn/forecast caveats and why the PBIP—not a legacy PBIX—is the Power BI source
artifact.
