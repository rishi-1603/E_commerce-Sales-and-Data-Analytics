# AI Evaluation Report — NL-to-SQL Assistant

**Mode:** `fallback` · **Run:** 2026-10-16T18:55:18+00:00 · **Benchmark:** `evals/nl2sql_benchmark.json` (v1.1, 37 questions, 4 classes)

> Ground truth is computed independently by the harness (pandas, from the raw processed table) — never from the system under test. Checks are alias-agnostic. Failures are listed below in full.

## Headline

| Metric | Value |
|---|---|
| **Execution accuracy** | **36/37 = 97.3%** |
| Refusal correctness | 100.0% |
| Fabricated numbers on unanswerable questions | **0** |
| Latency p50 / p95 | 179.1 ms / 215.9 ms |

## Before / after — measured improvement

The benchmark was first run against the **unmodified** system and that run is committed as `evals/results_fallback_baseline.json`. It is the evidence for every claim below.

| Metric | Baseline (before) | Current (after) |
|---|---|---|
| Execution accuracy | 18/37 = 48.6% | **36/37 = 97.3%** (+48.7%) |
| Fabricated answers on unanswerable questions | **1** | **0** |
| Refusal correctness | 80% | 100% |

### What the baseline run found — real bugs, now fixed

1. **A fabricated answer.** Asking *"What will total revenue be next year?"* returned ₹5.93 Cr — all-time historical revenue — as if it were a forecast. A confident number for an unanswerable question is the most damaging failure mode an analytics assistant can have. Fixed with an explicit forecast guard: this SQL layer now refuses future/forecast questions instead of guessing.
2. **A silently wrong answer.** *"What is total revenue in 2024?"* returned all-time revenue (₹5.93 Cr) instead of 2024 revenue (₹4.09 Cr) — the pattern matcher dropped the year filter. Filter-aware patterns now run before their all-time equivalents. This bug class is invisible without an eval harness.
3. **16 false refusals** — answerable questions the matcher did not recognise (quantity, discount, subcategory, segment, year/quarter/MoM logic).
4. **1 wrong metric** — *"orders by month"* returned revenue by month.

**A benchmark error caught by running it:** question B06 originally expected 2 customer segments. The data has three (B2C / B2B / Enterprise — see `data/DATA_DICTIONARY.md`). The **system was right and the benchmark was wrong**; the expectation was corrected and the correction left visible rather than quietly patched.

## Accuracy by question class

| Class | Passed | N | Accuracy |
|---|---|---|---|
| refusal | 5 | 5 | 100.0% |
| segment_breakdown | 10 | 10 | 100.0% |
| simple_aggregation | 12 | 13 | 92.3% |
| time_intelligence | 9 | 9 | 100.0% |

## Failure log (published in full — no cherry-picking)

1 failure(s) of 37. Each is classified below.

| ID | Class | Variant | Question | What happened |
|---|---|---|---|---|
| A13 | simple_aggregation | paraphrase | Which product line gives us the best percentage profit? | no column matching ['category'] in ['product_name', 'profit'] |

### Failure class #1 — paraphrase not covered by the pattern matcher

1 of 1 failures are natural re-wordings (`variant=paraphrase`) of questions the system answers correctly in canonical form. The deterministic fallback matches literal patterns, so it cannot generalise wording. This is the structural reason the LLM path exists; the fallback is a floor, not the ceiling.

**Fix path:** (a) score the LLM path on the same benchmark (`--mode llm`) and report it separately; (b) add synonym groups to the highest-value patterns; (c) keep paraphrase accuracy pinned in CI so the floor is enforced, not assumed.

## Method notes (what a reviewer should verify)

1. **Independent ground truth** — every expected value is computed in `evals/run_eval.py::ground_truth_registry` with pandas from `data/processed/master_orders.csv`. The system under test never provides its own answer key.
2. **Alias-agnostic scoring** — `SELECT SUM(line_total) AS revenue` and `SELECT SUM(line_total) AS total_sales` score identically. Correctness is the value, not the naming.
3. **Unit ambiguity is forgiven, wrong magnitudes are not** — for the average-discount question, `0.0997` and `9.97` both pass; `0.997` fails.
4. **Refusals scored separately** — a fabricated number on an unanswerable question is the most costly failure mode, so it gets its own metric (target: 0).
5. **CI-enforced floor** — `tests/test_ai_eval.py` pins the fallback-mode accuracy and refusal correctness thresholds, so this score cannot silently regress.
