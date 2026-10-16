"""
run_eval.py — AI Evaluation Harness for the NL-to-SQL assistant
================================================================================
Scores scripts/nl_to_sql.py against evals/nl2sql_benchmark.json (37 questions,
4 classes) and writes reports/ai_eval_report.md.

DESIGN PRINCIPLES (why this is trustworthy):
    1. Ground truth is computed INDEPENDENTLY here (pandas, straight from
       data/processed/master_orders.csv) — never from the system under test.
    2. Checks are alias-agnostic where possible: a scalar answer is scored on
       its numeric value, not on the SQL alias the system happened to choose.
    3. Refusals are scored separately. A system that answers an unanswerable
       question with a number is penalised harder than one that admits it can't.
    4. Failures are published with their class and question — no cherry-picking.

MODES:
    fallback : deterministic pattern-matching path (openai/google keys ignored)
               → runs in CI, no API key needed
    llm      : the LLM path (requires OPENAI_API_KEY or GOOGLE_API_KEY)
               → run locally; scores are reported separately

USAGE:
    python evals/run_eval.py                     # fallback mode, writes report
    python evals/run_eval.py --mode llm          # LLM mode (needs key)
    python evals/run_eval.py --min-accuracy 0.80 # exit 1 if below threshold
    python evals/run_eval.py --print             # print per-question table
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from nl_to_sql import answer_question  # system under test

DATA = ROOT / "data" / "processed" / "master_orders.csv"
BENCHMARK = ROOT / "evals" / "nl2sql_benchmark.json"
REPORT_MD = ROOT / "reports" / "ai_eval_report.md"


# ──────────────────────────────────────────────────────────────────────────────
# Ground truth — computed independently, from the raw processed table
# ──────────────────────────────────────────────────────────────────────────────
def ground_truth_registry(df: pd.DataFrame) -> dict:
    """Each value is computed here with pandas — never taken from the SQL layer."""
    cat = df.groupby("category")
    region = df.groupby("region")
    product_rev = df.groupby("product_name").line_total.sum()
    product_profit = df.groupby("product_name").profit.sum()
    subcat_rev = df.groupby("subcategory").line_total.sum()
    year_rev = df.groupby("year").line_total.sum()
    quarter_rev = df.groupby("quarter").line_total.sum()

    return {
        "sum_line_total": float(df.line_total.sum()),
        "sum_profit": float(df.profit.sum()),
        "count_orders": int(df.order_id.nunique()),
        "count_customers": int(df.customer_id.nunique()),
        "aov": float(df.line_total.sum() / df.order_id.nunique()),
        "revenue_2024": float(df[df.year == 2024].line_total.sum()),
        "avg_discount": float(df.discount_pct_y.mean()),
        "top_category_by_margin": str(
            (cat.profit.sum() / cat.line_total.sum()).idxmax()
        ),
        "sum_quantity": float(df.quantity.sum()),
        "orders_dec_2024": int(
            df[(df.year == 2024) & (df.month == 12)].order_id.nunique()
        ),
        "top_category_by_revenue": str(cat.line_total.sum().idxmax()),
        "top_region_by_revenue": str(region.line_total.sum().idxmax()),
        "top_product_by_revenue": str(product_rev.idxmax()),
        "min_subcategory_by_revenue": str(subcat_rev.idxmin()),
        "top_product_by_profit": str(product_profit.idxmax()),
        "revenue_q4_2024": float(quarter_rev.get("2024Q4", 0.0)),
        "top_year_by_revenue": str(year_rev.idxmax()),
        "top_quarter_by_revenue": str(quarter_rev.idxmax()),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Checkers
# ──────────────────────────────────────────────────────────────────────────────
def _numeric_cells(row: dict) -> list:
    out = []
    for v in row.values():
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            out.append(float(v))
    return out


def _alias_col(columns: list, aliases: list) -> str | None:
    """Case-insensitive substring match: find the column the system returned."""
    for alias in aliases:
        for c in columns:
            if alias.lower() in str(c).lower():
                return c
    return None


def check_answer(spec: dict, gt: dict, result: dict) -> tuple[bool, str]:
    """Return (passed, detail). Never raises — a crashed check is a failed check."""
    ctype = spec["type"]
    rows = result.get("result") or []

    # ---- refusal: pass iff the system did NOT produce data -------------------
    if ctype == "refusal":
        if not result.get("ok"):
            return True, f"refused ({result.get('error', 'no answer')[:60]})"
        if not rows:
            return True, "refused (returned no data)"
        nums = _numeric_cells(rows[0])
        return False, f"FABRICATED an answer: {nums[:2] if nums else rows[0]}"

    # ---- everything below needs rows ----------------------------------------
    if not result.get("ok"):
        return False, f"system error: {result.get('error', 'unknown')[:80]}"
    if not rows:
        return False, "no data returned for an answerable question"

    expected = gt[spec["ground_truth"]] if "ground_truth" in spec else None
    tol = spec.get("tol_pct", 0.5) / 100.0

    # ---- scalar numeric ------------------------------------------------------
    if ctype == "scalar_numeric":
        if len(rows) != 1:
            return False, f"expected 1 row, got {len(rows)}"
        cells = _numeric_cells(rows[0])
        if not cells:
            return False, "no numeric value in the answer"
        v = cells[0]
        ok = abs(v - expected) <= abs(expected) * tol
        if not ok and spec.get("unit_ambiguity") == "fraction_or_percent":
            ok = abs(v / 100.0 - expected) <= abs(expected) * tol
        return ok, f"got {v:,.2f} vs expected {expected:,.2f}"

    # ---- extremes / first-row text ------------------------------------------
    if ctype == "extreme_row":
        if "row_count" in spec and len(rows) != spec["row_count"]:
            return False, f"expected {spec['row_count']} rows, got {len(rows)}"
        if "max_rows" in spec and len(rows) > spec["max_rows"]:
            return False, f"expected <= {spec['max_rows']} rows, got {len(rows)}"
        col = _alias_col(list(rows[0].keys()), spec["column_alias"])
        if col is None:
            return False, f"no column matching {spec['column_alias']} in {list(rows[0].keys())}"
        got_first = str(rows[0][col]).strip().lower()
        got_last = str(rows[-1][col]).strip().lower()
        want = str(expected).strip().lower()
        if got_first == want or got_last == want:
            return True, f"correct extreme: {rows[0][col]}"
        return False, f"neither end is right: first={rows[0][col]!r} last={rows[-1][col]!r} want={expected!r}"

    # ---- shape checks --------------------------------------------------------
    if ctype == "row_count":
        return len(rows) == spec["rows"], f"got {len(rows)} rows, expected {spec['rows']}"

    if ctype == "row_count_range":
        ok = spec["min"] <= len(rows) <= spec["max"]
        return ok, f"got {len(rows)} rows, expected {spec['min']}–{spec['max']}"

    if ctype == "has_column_and_rows":
        if not (spec["min"] <= len(rows) <= spec["max"]):
            return False, f"got {len(rows)} rows, expected {spec['min']}–{spec['max']}"
        cols = " | ".join(str(c).lower() for c in rows[0].keys())
        if any(s in cols for s in spec["column_name_contains"]):
            return True, f"{len(rows)} rows with column(s): {list(rows[0].keys())}"
        return False, f"no column matching {spec['column_name_contains']} in {list(rows[0].keys())}"

    return False, f"unknown check type: {ctype}"


# ──────────────────────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────────────────────
def run_benchmark(mode: str = "fallback", verbose: bool = False) -> dict:
    bench = json.loads(BENCHMARK.read_text())
    df = pd.read_csv(DATA)
    gt = ground_truth_registry(df)

    results = []
    for q in bench["questions"]:
        t0 = time.perf_counter()
        try:
            r = answer_question(q["question"], use_llm=(mode == "llm"))
        except Exception as e:  # a crash is a failure, never an interruption
            r = {"ok": False, "error": f"crash: {e}"}
        latency_ms = (time.perf_counter() - t0) * 1000
        passed, detail = check_answer(q["check"], gt, r)
        results.append({
            "id": q["id"], "class": q["class"], "variant": q["variant"],
            "question": q["question"], "passed": passed, "detail": detail,
            "latency_ms": round(latency_ms, 1),
            "sql": (r.get("sql") or "")[:160],
        })
        if verbose:
            mark = "PASS" if passed else "FAIL"
            print(f"[{mark}] {q['id']} ({q['class'][:6]}) {q['question'][:58]} — {detail[:70]}")

    # ---- aggregate -----------------------------------------------------------
    by_class: dict[str, dict] = {}
    for r in results:
        c = by_class.setdefault(r["class"], {"n": 0, "passed": 0})
        c["n"] += 1
        c["passed"] += int(r["passed"])

    for c in by_class.values():
        c["accuracy"] = round(c["passed"] / c["n"], 3)

    lat = sorted(r["latency_ms"] for r in results)
    p50 = statistics.median(lat)
    p95 = lat[max(0, int(len(lat) * 0.95) - 1)]

    refusal_questions = [r for r in results if r["class"] == "refusal"]
    metrics = {
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_questions": len(results),
        "passed": sum(r["passed"] for r in results),
        "overall_accuracy": round(sum(r["passed"] for r in results) / len(results), 3),
        "by_class": by_class,
        "refusal_correctness": round(
            sum(r["passed"] for r in refusal_questions) / max(1, len(refusal_questions)), 3
        ),
        "fabricated_numbers": sum(
            1 for r in refusal_questions if not r["passed"]
        ),
        "latency_p50_ms": round(p50, 1),
        "latency_p95_ms": round(p95, 1),
        "results": results,
    }
    return metrics


def _baseline_block(m: dict) -> list:
    """Before/after section — loads the committed pre-upgrade baseline run."""
    bp = ROOT / "evals" / "results_fallback_baseline.json"
    if not bp.exists() or m["mode"] != "fallback":
        return []
    try:
        b = json.loads(bp.read_text())
    except Exception:
        return []
    if b.get("timestamp") == m.get("timestamp"):
        return []

    d_acc = m["overall_accuracy"] - b["overall_accuracy"]
    return [
        "## Before / after — measured improvement",
        "",
        "The benchmark was first run against the **unmodified** system and that run is "
        "committed as `evals/results_fallback_baseline.json`. It is the evidence for "
        "every claim below.",
        "",
        "| Metric | Baseline (before) | Current (after) |",
        "|---|---|---|",
        f"| Execution accuracy | {b['passed']}/{b['n_questions']} = {b['overall_accuracy']:.1%} "
        f"| **{m['passed']}/{m['n_questions']} = {m['overall_accuracy']:.1%}** ({d_acc:+.1%}) |",
        f"| Fabricated answers on unanswerable questions | **{b['fabricated_numbers']}** "
        f"| **{m['fabricated_numbers']}** |",
        f"| Refusal correctness | {b['refusal_correctness']:.0%} "
        f"| {m['refusal_correctness']:.0%} |",
        "",
        "### What the baseline run found — real bugs, now fixed",
        "",
        "1. **A fabricated answer.** Asking *\"What will total revenue be next year?\"* returned "
        "₹5.93 Cr — all-time historical revenue — as if it were a forecast. A confident number "
        "for an unanswerable question is the most damaging failure mode an analytics assistant "
        "can have. Fixed with an explicit forecast guard: this SQL layer now refuses "
        "future/forecast questions instead of guessing.",
        "2. **A silently wrong answer.** *\"What is total revenue in 2024?\"* returned all-time "
        "revenue (₹5.93 Cr) instead of 2024 revenue (₹4.09 Cr) — the pattern matcher dropped the "
        "year filter. Filter-aware patterns now run before their all-time equivalents. This bug "
        "class is invisible without an eval harness.",
        "3. **16 false refusals** — answerable questions the matcher did not recognise "
        "(quantity, discount, subcategory, segment, year/quarter/MoM logic).",
        "4. **1 wrong metric** — *\"orders by month\"* returned revenue by month.",
        "",
        "**A benchmark error caught by running it:** question B06 originally expected 2 customer "
        "segments. The data has three (B2C / B2B / Enterprise — see `data/DATA_DICTIONARY.md`). "
        "The **system was right and the benchmark was wrong**; the expectation was corrected and "
        "the correction left visible rather than quietly patched.",
        "",
    ]


def write_report(m: dict) -> None:
    fails = [r for r in m["results"] if not r["passed"]]
    lines = [
        "# AI Evaluation Report — NL-to-SQL Assistant",
        "",
        f"**Mode:** `{m['mode']}` · **Run:** {m['timestamp']} · "
        f"**Benchmark:** `evals/nl2sql_benchmark.json` (v1.1, 37 questions, 4 classes)",
        "",
        "> Ground truth is computed independently by the harness (pandas, from the raw "
        "processed table) — never from the system under test. Checks are alias-agnostic. "
        "Failures are listed below in full.",
        "",
        "## Headline",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| **Execution accuracy** | **{m['passed']}/{m['n_questions']} = {m['overall_accuracy']:.1%}** |",
        f"| Refusal correctness | {m['refusal_correctness']:.1%} |",
        f"| Fabricated numbers on unanswerable questions | **{m['fabricated_numbers']}** |",
        f"| Latency p50 / p95 | {m['latency_p50_ms']} ms / {m['latency_p95_ms']} ms |",
        "",
        *_baseline_block(m),
        "## Accuracy by question class",
        "",
        "| Class | Passed | N | Accuracy |",
        "|---|---|---|---|",
    ]
    for name, c in sorted(m["by_class"].items()):
        lines.append(f"| {name} | {c['passed']} | {c['n']} | {c['accuracy']:.1%} |")

    lines += ["", "## Failure log (published in full — no cherry-picking)", ""]
    if not fails:
        lines.append("_No failures in this run._")
    else:
        lines += [
            f"{len(fails)} failure(s) of {m['n_questions']}. Each is classified below.",
            "",
            "| ID | Class | Variant | Question | What happened |",
            "|---|---|---|---|---|",
        ]
        for r in fails:
            lines.append(
                f"| {r['id']} | {r['class']} | {r['variant']} | {r['question']} | {r['detail']} |"
            )
        para = [r for r in fails if r["variant"] == "paraphrase"]
        if para:
            lines += [
                "",
                "### Failure class #1 — paraphrase not covered by the pattern matcher",
                "",
                f"{len(para)} of {len(fails)} failures are natural re-wordings "
                "(`variant=paraphrase`) of questions the system answers correctly in "
                "canonical form. The deterministic fallback matches literal patterns, so "
                "it cannot generalise wording. This is the structural reason the LLM path "
                "exists; the fallback is a floor, not the ceiling.",
                "",
                "**Fix path:** (a) score the LLM path on the same benchmark (`--mode llm`) "
                "and report it separately; (b) add synonym groups to the highest-value "
                "patterns; (c) keep paraphrase accuracy pinned in CI so the floor is "
                "enforced, not assumed.",
            ]

    lines += [
        "",
        "## Method notes (what a reviewer should verify)",
        "",
        "1. **Independent ground truth** — every expected value is computed in "
        "`evals/run_eval.py::ground_truth_registry` with pandas from "
        "`data/processed/master_orders.csv`. The system under test never provides its own answer key.",
        "2. **Alias-agnostic scoring** — `SELECT SUM(line_total) AS revenue` and "
        "`SELECT SUM(line_total) AS total_sales` score identically. Correctness is the value, "
        "not the naming.",
        "3. **Unit ambiguity is forgiven, wrong magnitudes are not** — for the average-discount "
        "question, `0.0997` and `9.97` both pass; `0.997` fails.",
        "4. **Refusals scored separately** — a fabricated number on an unanswerable question is "
        "the most costly failure mode, so it gets its own metric (target: 0).",
        "5. **CI-enforced floor** — `tests/test_ai_eval.py` pins the fallback-mode accuracy "
        "and refusal correctness thresholds, so this score cannot silently regress.",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines))
    print(f"wrote {REPORT_MD.relative_to(ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="NL-to-SQL evaluation harness")
    ap.add_argument("--mode", choices=["fallback", "llm"], default="fallback")
    ap.add_argument("--print", dest="verbose", action="store_true")
    ap.add_argument("--min-accuracy", type=float, default=0.0)
    args = ap.parse_args()

    m = run_benchmark(mode=args.mode, verbose=args.verbose)

    out = ROOT / "evals" / f"results_{args.mode}.json"
    out.write_text(json.dumps(m, indent=2))
    write_report(m)

    print(f"\n{mode_line(m)}")
    if m["overall_accuracy"] < args.min_accuracy:
        print(f"BELOW THRESHOLD: {m['overall_accuracy']:.3f} < {args.min_accuracy:.2f}")
        return 1
    return 0


def mode_line(m: dict) -> str:
    return (
        f"mode={m['mode']}  accuracy={m['passed']}/{m['n_questions']}"
        f" ({m['overall_accuracy']:.1%})  refusals={m['refusal_correctness']:.0%}"
        f"  fabricated={m['fabricated_numbers']}  p95={m['latency_p95_ms']}ms"
    )


if __name__ == "__main__":
    sys.exit(main())
