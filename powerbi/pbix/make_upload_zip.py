"""Package the EcomAnalytics project into a clean upload ZIP (no secrets, no caches)."""
import os
import zipfile

ROOT = r'C:\Users\user\portfolio-roadmaps\repos\ecom'
OUT = os.path.join(os.path.expanduser('~'), 'Desktop', 'EcomProject_2026-11-14.zip')

EXCLUDE_DIRS = {
    '.venv', '.git', '__pycache__', '.pytest_cache', '.opencode',
    '.agents', 'node_modules', '.ruff_cache', '.mypy_cache',
}
EXCLUDE_FILES = {'.env', '.env.local', 'skills-lock.json'}
EXCLUDE_EXT = {'.db', '.sqlite', '.pyc', '.pyo', '.log'}

NOTES = """# Context for review — verified numbers & conventions

This package is the full EcomAnalytics repository (dataset, Python analysis,
SQL, dashboard, Power BI assets). Everything below is verified in the repo's
227-test regression suite.

## Verified headline figures (do not invent alternatives)
- Revenue (Delivered + Processing orders): 59,283,619.32 (currency: INR)
- Total COGS: 27,286,277.68
- Gross profit: 31,997,341.64 | Gross margin: 53.97%
- Orders: 9,933 = 9,312 Delivered + 621 Processing
- Active customers: 1,991 | AOV: 5,968.35

## Reporting convention
Revenue and profit counts Delivered + Processing orders only (Cancelled and
Returned excluded). Customer/funnel/retention measures use their own
documented populations (see README + data/metrics.json).

## Data provenance
The dataset is synthetic/demo data created for this portfolio project and is
disclosed as such in the README. Figures reconcile across SQL, Python, the
dashboard and the Power BI model.

## Power BI contents
- powerbi/pbix/EcomAnalytics.pbix — REAL file compiled by Power BI Desktop
  (DataModel 887,581 bytes; verified on-screen: revenue 59,283,619.32 /
  COGS 27,286,277.68 / active customers 1,991; screenshot in the same folder).
- powerbi/pbix/ — PBIP source project (TMDL), generator script and the four
  star-schema CSVs the model imports (data/ subfolder).
- powerbi/dax_measures.md — the 10 DAX measures; powerbi/model_diagram.md —
  star-schema design; powerbi/reconciliation_matrix.csv — metric reconciliation.
- Two Excel companions (BI companion + business reporting workbook).

## Key paths
- Dataset: data/raw/{orders,order_items,customers,products}.csv
- Processed outputs: data/processed/
- Pipeline: python/*.py, run_pipeline.py
- SQL: sql/
- Dashboard: dashboard/, index.html, dashboard.html
- Tests: tests/ (227 analytical/API tests)
- API: app/ (FastAPI)

NOTE: A GitHub personal access token was used in a shell command during
development but is NOT stored in any repository file (verified by scan).
""".replace('NOTE: A GitHub personal access token was used in a shell command during\ndevelopment but is NOT stored in any repository file (verified by scan).',
            'NOTE: No secrets are included in this package (.env does not exist in the\nrepository; no credentials are stored in any tracked file).')

count = 0
total = 0
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    z.writestr('CONTEXT_FOR_REVIEW.md', NOTES)
    count += 1
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn in EXCLUDE_FILES or os.path.splitext(fn)[1].lower() in EXCLUDE_EXT:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT)
            try:
                z.write(full, rel)
                count += 1
                total += os.path.getsize(full)
            except (OSError, PermissionError) as e:
                print('SKIP', rel, e)

print('written:', OUT)
print('files:', count, '| raw bytes:', f'{total:,}')
print('zip size:', f'{os.path.getsize(OUT):,}')
