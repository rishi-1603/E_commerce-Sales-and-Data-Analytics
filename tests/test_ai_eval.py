"""
test_ai_eval.py — the AI evaluation floor is enforced, not assumed.
==============================================================================
Runs the NL-to-SQL evaluation harness (evals/run_eval.py) against the
committed benchmark and pins the measured floor:

    - overall execution accuracy  >= 90%   (measured 97.3% at v2.0)
    - refusal correctness         == 100%  (a fabricated answer fails CI)
    - fabricated answers          == 0
    - per-class accuracy floors

These thresholds exist so a future change to scripts/nl_to_sql.py cannot
silently make the assistant worse. They were set AFTER measuring, never to
fit the current score: the baseline run (committed as
evals/results_fallback_baseline.json) scored 48.6% overall with 1 fabricated
answer — proof the floor was genuinely low before this work.

Also pins the two specific defects the first harness run uncovered, so they
can never come back:
    - "total revenue in 2024" must not return all-time revenue
    - "what will revenue be next year" must refuse, not answer
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_eval import BENCHMARK, run_benchmark  # noqa: E402
from nl_to_sql import answer_question  # noqa: E402

import json  # noqa: E402

# Floors measured on the deterministic fallback path (CI-safe, no API key).
MIN_OVERALL = 0.90
MIN_PER_CLASS = {
    "simple_aggregation": 0.85,
    "segment_breakdown": 0.85,
    "time_intelligence": 0.85,
    "refusal": 1.00,
}


@pytest.fixture(scope="module")
def metrics():
    """Run the benchmark once for the whole module."""
    return run_benchmark(mode="fallback")


class TestBenchmarkIntegrity:
    """The benchmark itself must be well-formed."""

    def test_benchmark_loads_and_has_expected_shape(self):
        bench = json.loads(BENCHMARK.read_text())
        qs = bench["questions"]
        assert len(qs) == 37
        ids = [q["id"] for q in qs]
        assert len(ids) == len(set(ids)), "duplicate question ids"
        classes = {q["class"] for q in qs}
        assert classes == {
            "simple_aggregation", "segment_breakdown",
            "time_intelligence", "refusal",
        }

    def test_every_question_has_a_check(self):
        bench = json.loads(BENCHMARK.read_text())
        for q in bench["questions"]:
            assert "check" in q and "type" in q["check"], q["id"]


class TestEnforcedFloor:
    """Measured scores must stay above the committed floor."""

    def test_overall_accuracy_meets_floor(self, metrics):
        assert metrics["overall_accuracy"] >= MIN_OVERALL, (
            f"execution accuracy {metrics['overall_accuracy']:.1%} "
            f"fell below the {MIN_OVERALL:.0%} floor — did nl_to_sql change?"
        )

    def test_no_fabricated_answers(self, metrics):
        """A number produced for an unanswerable question fails CI outright."""
        assert metrics["fabricated_numbers"] == 0, (
            "the assistant answered an unanswerable question with a number"
        )

    def test_refusal_correctness_is_perfect(self, metrics):
        assert metrics["refusal_correctness"] == 1.0

    @pytest.mark.parametrize("qclass", sorted(MIN_PER_CLASS))
    def test_per_class_floor(self, metrics, qclass):
        got = metrics["by_class"][qclass]["accuracy"]
        assert got >= MIN_PER_CLASS[qclass], (
            f"{qclass}: {got:.1%} below floor {MIN_PER_CLASS[qclass]:.0%}"
        )

    def test_latency_stays_sane(self, metrics):
        """Deterministic path must stay interactive (no pathological regression)."""
        assert metrics["latency_p95_ms"] < 2000


class TestRegressionGuards:
    """The two defects found by the first harness run can never return."""

    def test_year_filter_is_respected(self):
        """BUG #1: 'in 2024' must not return all-time revenue."""
        r = answer_question("What is total revenue in 2024?", use_llm=False)
        assert r["ok"]
        got = r["result"][0]["total_revenue"]
        # 2024 revenue, NOT the all-time 59.28M figure
        assert got == pytest.approx(40901640.96, rel=0.01)
        assert got < 50_000_000, "year filter was dropped — all-time revenue returned"

    def test_forecast_questions_are_refused(self):
        """BUG #2: a question this layer cannot answer must refuse, not guess."""
        for q in [
            "What will total revenue be next year?",
            "Predict next month's sales",
            "Give me a forecast for 2026",
        ]:
            r = answer_question(q, use_llm=False)
            assert not r["ok"] or r.get("result") in (None, []), (
                f"'{q}' produced an answer — this layer has no forecasting ability"
            )
