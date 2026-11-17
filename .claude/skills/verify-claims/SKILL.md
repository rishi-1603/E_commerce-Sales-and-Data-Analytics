---
name: verify-claims
description: Recompute and reconcile this repo's pinned KPIs and claims from raw CSVs against data/metrics.json, RESUME_EVIDENCE.md, data/claims.json and the dashboards. Use before publishing anything, after any data or pipeline change, when a displayed number is questioned, or when the user says 'verify claims', 'reconcile KPIs', 'audit the numbers', 'check the figures'.
---

# Verify Claims — pinned KPI reconciliation for this repo

This repo's promise: **every displayed figure reconciles from raw CSVs to README to dashboards.**
The pinned reference is `data/metrics.json` (+ `RESUME_EVIDENCE.md`, `data/claims.json`).

## Pinned values (as of 2026-11-17, commit a697d4e)

- Revenue (Delivered+Processing): **₹59,283,619.32** | COGS **₹27,286,277.68** | Profit **₹31,997,341.64** | Margin **53.97%**
- Funnel (mutually exclusive, of 12,000 placed): Delivered **9,312** (77.6%), Processing **621** (5.2%), Cancelled **844** (7.0%), Returned **1,223** (**10.19% of placed** — its own exit, NEVER subtracted from Delivered)
- Valid order base: **9,933** | AOV **₹5,968.35** (= revenue / 9,933)
- Active customers: **1,991** (distinct customers with ≥1 valid order; the other 8 of 1,999 placed only Cancelled/Returned orders) out of 2,000 records
- Dataset: 12,000 orders / 25,384 order lines / 2,000 customers / 150 products across **5 categories, 40 subcategories**; window Jan 2022 – Dec 2024; synthetic + seeded
- Forecast: ensemble MASE **0.68** vs drift baseline **0.468**; bootstrap CI coverage **9.5%**
- Churn: forward-time split ROC-AUC **≈0.65** (PR-AUC 0.36); isotonic Brier 0.197 → 0.184
- Discount: no significant quantity response (Kruskal-Wallis p = 0.305); break-even lift at 20% = +59.2%; 10% cap recovers ₹644,518 (2.0%)
- Win-back: 448 customers, ₹1.24 Cr historical spend, EV ₹541/contact, campaign EV ₹242,478, break-even 12.9%
- NL-to-SQL: 36/37 = 97.3%, refusals 100%, fabricated 0 (mode=fallback, benchmark v1.1)
- Tests: **227 passing** (CI: Python 3.11, `.github/workflows/ci.yml`)

## Procedure

1. Recompute from raw (never trust cached outputs):
   ```python
   import pandas as pd
   o  = pd.read_csv('data/raw/orders.csv')        # status column: Delivered/Processing/Cancelled/Returned
   oi = pd.read_csv('data/raw/order_items.csv')   # line_total, cost_total
   j  = oi.merge(o[['order_id','status']], on='order_id')
   v  = j[j.status.isin(['Delivered','Processing'])]
   revenue = v.line_total.sum(); cogs = v.cost_total.sum()
   aov = revenue / v.order_id.nunique()
   customers = o[o.status.isin(['Delivered','Processing'])].customer_id.nunique()
   ```
2. Compare each value to the pinned list + `data/metrics.json`; flag ANY mismatch.
3. Cross-check surfaces a reviewer reads: `README.md`, `RESUME_EVIDENCE.md`, `data/claims.json`,
   dashboard DATA block, `powerbi/dax_measures.md`, Vercel live URL.
4. Known benign artifacts (NOT errors): float last-ulp diffs in regenerated `data/processed` CSVs;
   ₹→Rs./em-dash→-- console fallbacks on Windows; PNG metadata. Restore with `git checkout -- .`
   — never commit regenerated noise.
5. Report: table of metric | recomputed | pinned | verdict. Fix any drifting doc in place, commit.
