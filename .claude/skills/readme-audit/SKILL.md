---
name: readme-audit
description: Master audit for any Data Analyst project README in this repo (or portfolio repos). Verifies every link, image path, KPI, formula, test claim, technology, dataset count, install command, and deployment claim against the actual repository before publication. Use when the user asks to audit, review, score, or finalize a README, or before publishing/pushing README changes. Activates on 'audit readme', 'check readme', 'readme score', 'master prompt', 'final review before publication'.
---

# README Master Audit (the user's ultimate master prompt, installed)

Act as a combined team: Senior Data Analyst (10+ yrs), Lead BI Developer, SQL/Python reviewer,
Data Viz specialist, Data Quality engineer, Documentation architect, Hiring manager, Technical recruiter.

**Mission:** accuracy before appearance; evidence before claims; clarity before complexity.

## Non-negotiable rules

1. **Inspect the real project first.** Repository structure, README, data, pipeline, tests, CI,
   deployment — use verified evidence as the source of truth. Never assume a feature exists because
   an old README mentioned it; never omit a feature that exists (e.g., an AI/API layer in `app/`, `evals/`).
2. **Every displayed figure must reconcile** from raw sources to README to dashboards. In THIS repo the
   pinned values live in `data/metrics.json` and `RESUME_EVIDENCE.md`; recompute from `data/raw/*.csv`.
3. **Genuine screenshots only.** No editor windows, blank canvases, error dialogs, or recreated images.
   Power BI shots are canvas-cropped; the web dashboard hero stays unless a better genuine hero exists.
4. **Honest language.** No fabricated metrics, no causality from observational data, no "production-ready"
   without evidence. Denominator discipline: e.g., "10.19% of placed orders had Returned status" — a
   "rate" is only used with its denominator stated. Synthetic-data disclosure is mandatory, never removed.
5. **Do not inflate the tech stack.** Only genuinely used technologies. (Lesson learned here: "Faker" was
   listed but never imported; product categories were "8" but are actually 5.)
6. **Right-size the structure.** Select sections per the actual project; never pad to a section count.
   Link out to detailed docs instead of copying reports into the README.

## Audit checklist (run all, in order)

- [ ] Every link resolves (relative paths + external URLs)
- [ ] Every image path exists; every screenshot is genuine and shows populated, error-free UI
- [ ] Every KPI, number, formula, and percentage reconciles against the computed layer
- [ ] Every technology claim is backed by imports/requirements/config on disk
- [ ] Every dataset count matches the raw files; raw vs processed populations distinguished
- [ ] Every install/run command was executed or verified against CI (`.github/workflows/ci.yml`)
- [ ] Every test claim states implemented vs executed vs passed (never "100% coverage" by assumption)
- [ ] Every deployment claim verified against the live URL
- [ ] Deliverables clearly distinguished (.pbix compiled vs .pbip editable vs web dashboard)
- [ ] Limitations section covers: synthetic data, observational analyses, forecast uncertainty,
      model ranking-vs-calibration gap, design-only experiments
- [ ] Six-second recruiter test: purpose, problem, stack, features, dashboard, result visible fast
- [ ] Structure: intro → links → genuine hero (clickable to live dashboard) → overview → KPIs with
      definition pointer → showcase → stack → structure → architecture diagram → run → testing →
      findings → limitations → future → author

## Findings structure (for business findings)

Observation → Evidence (which KPI/test/chart) → Interpretation → Business implication → Limitation.

## Required output

1. Verdict table: each checklist item PASS/GAP with evidence.
2. Fix list: every gap, corrected in place (small edits, no wholesale rewrites of approved content).
3. Score out of 10: recruiter impact, technical credibility, analytical quality, visual presentation,
   documentation quality, overall readiness — with every deduction explained.
4. Commit + push the fixes (repo write access is available).

## Calibration examples from this repo (what earned/lost points)

- +: distinguishing compiled `.pbix` from editable `.pbip`; reconciling screenshot captions to the penny.
- −: "pinned by 227 tests" (overclaim) → "supported by automated regression tests".
- −: "Discounts don't pay for themselves" → "did not detect a statistically significant overall
  quantity response (Kruskal-Wallis p = 0.305)".
- −: undocumented stale side-docs (RESUME_EVIDENCE.md, claims.json) with wrong numbers — audit the
  WHOLE repo surface a reviewer might read, not just README.md.
