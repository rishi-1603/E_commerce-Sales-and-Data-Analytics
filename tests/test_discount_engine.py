"""
test_discount_engine.py — the discount/margin engine must stay correct and honest.
==============================================================================
Pins three kinds of thing:

  1. MATH      — margin curves, break-even lifts and re-pricing arithmetic must be
                 reproducible and internally consistent (recomputed by hand here).
  2. FINDINGS  — the measured result (no significant volume response to discount
                 depth in this dataset; break-even lift at 20% ≈ +59%) is pinned
                 so that if the data or the engine changes, the change is loud.
  3. BOUNDARIES— edge cases: capping at/above the max depth affects nothing;
                 the simulator's break-even flag flips at the right threshold.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from pricing.elasticity import (  # noqa: E402
    DISCOUNT_LEVELS,
    break_even_table,
    discount_response,
    load,
    margin_curve,
    repricing_scenario,
    simulate,
)


@pytest.fixture(scope="module")
def df():
    return load()


@pytest.fixture(scope="module")
def curve(df):
    return margin_curve(df)


@pytest.fixture(scope="module")
def be(df):
    return break_even_table(df)


class TestMarginCurve:
    """The cost side of discounting must be computed correctly."""

    def test_one_row_per_depth_present(self, curve, df):
        expected = sorted(df.discount_pct_y.unique())
        assert sorted(curve.discount.tolist()) == pytest.approx(expected)

    def test_margin_as_pct_of_list_is_definitionally_correct(self, df):
        """margin_pct_of_list = margin_rate * (1 - discount), row by row."""
        sample = df.sample(200, random_state=42)
        expected = sample.margin_rate * (1 - sample.discount_pct_y)
        assert np.allclose(sample.margin_pct_of_list, expected)

    def test_margin_erodes_monotonically_with_depth(self, curve):
        """Deeper discounts must never show *more* margin as a share of list."""
        seq = curve.sort_values("discount").margin_pct_of_list.tolist()
        assert all(a > b for a, b in zip(seq, seq[1:])), seq

    def test_no_discount_row_is_the_reference(self, curve):
        row = curve[curve.discount == 0.0].iloc[0]
        assert row.margin_loss_vs_no_discount == pytest.approx(0.0)
        assert row.margin_rate == pytest.approx(0.5379, abs=0.01)


class TestBreakEven:
    """Break-even lift is the decision number — it must be right."""

    def test_zero_discount_needs_no_lift(self, be):
        assert be.loc[be.discount == 0.0, "break_even_volume_lift"].iloc[0] == \
            pytest.approx(0.0)

    def test_lift_increases_with_depth(self, be):
        seq = be.sort_values("discount").break_even_volume_lift.tolist()
        assert all(a < b for a, b in zip(seq, seq[1:])), seq

    def test_lift_at_20pct_matches_hand_calculation(self, be, df):
        """Hand-check: base margin/list ÷ 20%-discount margin/list − 1."""
        base = df.loc[df.discount_pct_y == 0.0].margin_pct_of_list.mean()
        at20 = df.loc[df.discount_pct_y == 0.20].margin_pct_of_list.mean()
        expected = base / at20 - 1
        got = be.loc[be.discount == 0.20, "break_even_volume_lift"].iloc[0]
        # engine rounds to 4dp for display; compare at that resolution
        assert got == pytest.approx(expected, abs=1e-4)
        assert got == pytest.approx(0.592, abs=0.01)  # the published figure

    def test_all_break_even_values_are_positive(self, be):
        assert (be[be.discount > 0].break_even_volume_lift > 0).all()


class TestMeasuredResponseIsPublished:
    """The honest finding is pinned — if it changes, it must change loudly."""

    def test_no_significant_volume_response_detected(self, df):
        resp = discount_response(df)
        assert resp["volume_response_detected"] is False
        assert resp["kruskal_wallis_p"] > 0.05

    def test_the_one_significant_category_is_negative_and_pinned(self, df):
        """Significance ≠ materiality: Sports is the only p<0.05 category.

        With n≈4,300 line items, a −7% effect at 20pp reaches p=0.003. The
        finding is pinned in BOTH dimensions: the p-value AND the magnitude,
        and the magnitude is reported against the break-even requirement.
        """
        resp = discount_response(df)
        sig = {c: v for c, v in resp["per_category"].items() if v["significant_at_5pct"]}
        assert set(sig) == {"Sports"}
        assert sig["Sports"]["p_value"] == pytest.approx(0.003, abs=0.002)
        assert sig["Sports"]["qty_change_pct_at_20pp"] < 0

    def test_no_category_response_comes_near_break_even(self, df):
        """Even the largest measured response is far below what a discount needs."""
        resp = discount_response(df)
        be = break_even_table(df)
        required = float(be.loc[be.discount == 0.20, "break_even_volume_lift"].iloc[0])
        for cat, v in resp["per_category"].items():
            assert v["qty_change_pct_at_20pp"] < required, (
                f"{cat} shows {v['qty_change_pct_at_20pp']:+.1%} at 20pp, which would "
                f"justify the discount (needs {required:.1%}) — re-examine the engine"
            )

    def test_mean_quantity_is_flat_across_depths(self, df):
        """The published finding: quantity barely moves with discount depth."""
        means = df.groupby("discount_pct_y").quantity.mean()
        assert (means.max() - means.min()) < 0.10


class TestRepricingScenario:
    """Static re-pricing arithmetic must be exact."""

    def test_cap_above_max_depth_affects_nothing(self, df):
        s = repricing_scenario(df, cap=0.20)
        assert s["lines_affected"] == 0
        assert s["margin_recovered"] == 0.0

    def test_row_level_repricing_math(self, df):
        """Recompute one affected line by hand and compare with the engine."""
        cap = 0.10
        affected = df[df.discount_pct_y > cap]
        row = affected.iloc[0]
        new_line_total = row.line_total * (1 - cap) / (1 - row.discount_pct_y)
        manual = (new_line_total - row.cost_total) - row.profit
        assert manual > 0  # less discount ⇒ more margin, always

    def test_cap_10_recovers_the_published_amount(self, df):
        s = repricing_scenario(df, cap=0.10)
        assert s["lines_affected"] == 3294
        assert s["margin_recovered"] == pytest.approx(644_518, rel=0.02)
        assert 0 < s["margin_recovered_pct_of_total"] < 0.10

    def test_deeper_cap_recovers_less_than_shallower_cap(self, df):
        """A tighter cap forces more lines to re-price ⇒ more recovery."""
        assert repricing_scenario(df, 0.10)["margin_recovered"] > \
               repricing_scenario(df, 0.15)["margin_recovered"]

    def test_no_nan_anywhere(self, df, curve, be):
        assert not curve.isna().any().any()
        assert not be.isna().any().any()
        for k, v in repricing_scenario(df, 0.10).items():
            if isinstance(v, float):
                assert not np.isnan(v), k


class TestDiscountLabSimulator:
    """The lab's job is to show the break-even line, not to pretend to predict."""

    def test_zero_depth_zero_lift_reproduces_baseline(self, df):
        s = simulate(depth=0.0, assumed_volume_lift=0.0, df=df)
        assert s["margin_change_pct"] == pytest.approx(0.0, abs=1e-6)
        assert s["revenue_change_pct"] == pytest.approx(0.0, abs=1e-6)

    def test_lift_above_break_even_beats_it(self, df):
        s = simulate(depth=0.20, assumed_volume_lift=0.70, df=df)
        assert s["beats_break_even"] is True
        assert s["margin_change_pct"] > 0

    def test_lift_below_break_even_loses(self, df):
        s = simulate(depth=0.20, assumed_volume_lift=0.10, df=df)
        assert s["beats_break_even"] is False
        assert s["margin_change_pct"] < 0

    def test_break_even_flag_flips_at_the_threshold(self, df):
        be = break_even_table(df)
        threshold = float(be.loc[be.discount == 0.20, "break_even_volume_lift"].iloc[0])
        just_below = simulate(0.20, threshold - 0.01, df=df)
        just_above = simulate(0.20, threshold + 0.01, df=df)
        assert just_below["beats_break_even"] is False
        assert just_above["beats_break_even"] is True

    def test_break_even_reported_for_every_supported_depth(self, df):
        for d in DISCOUNT_LEVELS:
            s = simulate(depth=d, assumed_volume_lift=0.0, df=df)
            assert s["break_even_volume_lift"] is not None


class TestCommittedArtifact:
    """The report the dashboard and README quote must exist and be well-formed."""

    def test_report_json_exists_with_headline_keys(self):
        import json
        p = ROOT / "reports" / "discount_analysis.json"
        assert p.exists(), "run python/pricing/elasticity.py to regenerate"
        payload = json.loads(p.read_text())
        for key in ("discount_response", "margin_curve", "break_even",
                    "repricing_scenarios", "headline"):
            assert key in payload, f"missing {key}"
        assert payload["headline"]["volume_response_detected"] is False
        assert payload["headline"]["break_even_lift_at_20pct"] == \
            pytest.approx(0.592, abs=0.01)
