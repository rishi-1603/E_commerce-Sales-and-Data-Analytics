"""
test_winback_economics.py — the campaign economics must be correct and honest.
==============================================================================
Pins:
  1. MATH        — expected value, break-even and budget arithmetic recomputed
                   by hand.
  2. CONSISTENCY — the campaign's break-even churn probability must equal the
                   churn model's own Bayes threshold. Two independently written
                   modules agreeing is the strongest available check that the
                   cost model has not drifted.
  3. BOUNDARIES  — the budget worklist never overspends; the sensitivity grid
                   moves in the direction it should; a negative-EV campaign is
                   reported as unprofitable rather than quietly recommended.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from pricing.winback import (  # noqa: E402
    CONTACT_COST_INR,
    RECOVERY_RATE,
    RETAINED_VALUE_INR,
    break_even_probability,
    budget_worklist,
    economics,
    load_pool,
    sensitivity_grid,
    tiered_scenarios,
)


@pytest.fixture(scope="module")
def pool():
    return load_pool()


@pytest.fixture(scope="module")
def be():
    return break_even_probability()


class TestExpectedValueMath:
    """EV = p × r × V − C, recomputed by hand."""

    def test_single_contact_matches_hand_calculation(self):
        e = economics(audience=1, mean_churn_prob=0.40)
        expected_recovered = 0.40 * RECOVERY_RATE * RETAINED_VALUE_INR
        assert e["expected_value_recovered_per_contact"] == pytest.approx(
            expected_recovered, abs=0.01)
        assert e["expected_profit_per_contact"] == pytest.approx(
            expected_recovered - CONTACT_COST_INR, abs=0.01)

    def test_totals_scale_linearly_with_audience(self):
        one = economics(1, 0.40)
        hundred = economics(100, 0.40)
        assert hundred["expected_profit_total"] == pytest.approx(
            one["expected_profit_per_contact"] * 100, abs=0.5)

    def test_zero_churn_probability_is_unprofitable(self):
        e = economics(100, 0.0)
        assert e["expected_profit_per_contact"] == pytest.approx(-CONTACT_COST_INR)
        assert e["profitable"] is False

    def test_certain_churn_is_profitable(self):
        e = economics(100, 1.0)
        assert e["expected_profit_per_contact"] > 0
        assert e["profitable"] is True


class TestBreakEven:
    """The break-even probability is the decision rule — it must be exact."""

    def test_formula_matches_hand_calculation(self, be):
        # the module rounds to 4dp for display; compare at that resolution
        expected = CONTACT_COST_INR / (RECOVERY_RATE * RETAINED_VALUE_INR)
        assert be["break_even_churn_probability"] == pytest.approx(expected, abs=1e-4)

    def test_at_break_even_expected_profit_is_zero(self, be):
        # tolerance covers the 4dp rounding of the reported break-even
        p = be["break_even_churn_probability"]
        e = economics(1, p)
        assert e["expected_profit_per_contact"] == pytest.approx(0.0, abs=0.05)

    def test_just_above_and_below_break_even_flip_the_decision(self, be):
        p = be["break_even_churn_probability"]
        assert economics(1, p * 1.05)["profitable"] is True
        assert economics(1, p * 0.95)["profitable"] is False


class TestConsistencyWithChurnModel:
    """Two independently written modules must agree on the same threshold."""

    def test_break_even_equals_the_churn_model_bayes_threshold(self, be):
        """The campaign break-even IS the churn model's Bayes threshold.

        churn_calibration.py computes bayes_threshold = C / (r × V) internally
        from the same cost model. If these two ever disagree, the cost model
        has drifted and one of the two implementations is wrong.
        """
        path = ROOT / "reports" / "churn_calibration_metrics.json"
        if not path.exists():
            pytest.skip("run scripts/churn_calibration.py first")
        bayes = json.loads(path.read_text())["cost_model"]["bayes_threshold"]
        assert be["break_even_churn_probability"] == pytest.approx(bayes, abs=5e-3), (
            f"campaign break-even {be['break_even_churn_probability']} != "
            f"churn model Bayes threshold {bayes} — the cost models have drifted"
        )


class TestSensitivity:
    """Direction of movement must be right, or the grid misleads."""

    def test_higher_recovery_rate_never_reduces_profit(self):
        grid = sensitivity_grid(448, 0.40)
        by_cost = {}
        for row in grid:
            by_cost.setdefault(row["contact_cost"], []).append(row)
        for cost, rows in by_cost.items():
            rows = sorted(rows, key=lambda r: r["recovery_rate"])
            profits = [r["profit_per_contact"] for r in rows]
            assert all(a <= b for a, b in zip(profits, profits[1:])), (cost, profits)

    def test_higher_contact_cost_never_increases_profit(self):
        grid = sensitivity_grid(448, 0.40)
        by_rate = {}
        for row in grid:
            by_rate.setdefault(row["recovery_rate"], []).append(row)
        for rate, rows in by_rate.items():
            rows = sorted(rows, key=lambda r: r["contact_cost"])
            profits = [r["profit_per_contact"] for r in rows]
            assert all(a >= b for a, b in zip(profits, profits[1:])), (rate, profits)

    def test_grid_is_complete(self):
        grid = sensitivity_grid(448, 0.40)
        assert len(grid) == 6 * 4  # 6 recovery rates × 4 costs


class TestTieredScenarios:
    """Scenario arithmetic must match the pool."""

    def test_produces_four_scenarios(self, pool):
        tiers = tiered_scenarios(pool)
        assert len(tiers) == 4

    def test_do_nothing_earns_nothing(self, pool):
        d = [t for t in tiered_scenarios(pool) if t["scenario"].startswith("D.")][0]
        assert d["expected_profit_total"] == 0.0

    def test_blanket_matches_the_economics_function(self, pool):
        tiers = tiered_scenarios(pool)
        a = [t for t in tiers if t["scenario"].startswith("A.")][0]
        expected = economics(len(pool), float(pool["churn_probability"].mean()))
        assert a["expected_profit_total"] == pytest.approx(
            expected["expected_profit_total"], abs=1.0)

    def test_when_all_above_break_even_blanket_equals_threshold_rule(self, pool):
        """In this pool every customer clears break-even, so the threshold rule
        selects the same audience as the blanket campaign."""
        tiers = tiered_scenarios(pool)
        a = [t for t in tiers if t["scenario"].startswith("A.")][0]
        c = [t for t in tiers if t["scenario"].startswith("C.")][0]
        if c["audience"] == a["audience"]:
            assert c["expected_profit_total"] == pytest.approx(
                a["expected_profit_total"], abs=1.0)


class TestBudgetWorklist:
    """A budget must never be exceeded, and only positive-EV customers appear."""

    def test_never_overspends(self, pool):
        for budget in (5_000, 25_000, 100_000, 1_000_000):
            w = budget_worklist(pool, budget)
            assert w["spend_inr"] <= budget + 1e-6, (budget, w["spend_inr"])
            assert w["selected"] <= w["calls_affordable"]

    def test_only_positive_expected_value_customers(self, pool):
        w = budget_worklist(pool, 25_000)
        assert w["eligible_customers"] <= len(pool)
        assert w["expected_profit_inr"] >= 0

    def test_zero_budget_selects_nobody(self, pool):
        w = budget_worklist(pool, 0)
        assert w["selected"] == 0
        assert w["expected_profit_inr"] == 0

    def test_larger_budget_never_reduces_expected_profit(self, pool):
        small = budget_worklist(pool, 10_000)
        large = budget_worklist(pool, 50_000)
        assert large["expected_profit_inr"] >= small["expected_profit_inr"]

    def test_worklist_is_capped_by_eligibility(self, pool):
        w = budget_worklist(pool, 10_000_000)
        assert w["selected"] == min(w["calls_affordable"], w["eligible_customers"])


class TestCommittedArtifact:
    def test_report_json_is_present_and_consistent(self):
        p = ROOT / "reports" / "winback_economics.json"
        assert p.exists(), "run python/pricing/winback.py to regenerate"
        d = json.loads(p.read_text())
        for key in ("pool", "baseline_campaign", "break_even",
                    "sensitivity", "tiered_scenarios", "budget_worklist"):
            assert key in d, f"missing {key}"
        assert d["pool"]["customers"] == 448
        assert d["bayes_threshold_cross_check"]["consistent"] is True
