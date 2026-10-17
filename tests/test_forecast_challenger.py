"""
test_forecast_challenger.py — the challenger evaluation must be fair and honest.
==============================================================================
Pins:
  1. PROTOCOL PARITY — the challengers are scored with the same constants and
     baseline functions as forecast_backtest.py. If someone re-implements the
     loop, this test fails before a misleading leaderboard ships.
  2. COMPLETENESS    — every model must run at every origin. A silently excluded
     model (a crashed statsmodels fit, for example) would make the leaderboard
     look better than it is, so exclusion is a test failure.
  3. THE FINDING     — holt_linear beating drift is pinned in both directions:
     the winner, and the fact that the seasonality-free model wins. If the data
     or the models change, this must fail loudly so the recommendation moves
     with it.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import forecast_backtest as fb  # noqa: E402
import forecast_challenger as fc  # noqa: E402


@pytest.fixture(scope="module")
def metrics():
    return fc.run()


class TestProtocolParity:
    """Challengers must be judged by the same ruler as the baselines."""

    def test_constants_are_imported_not_redefined(self):
        assert fc.HORIZONS is fb.HORIZONS
        assert fc.MIN_TRAIN == fb.MIN_TRAIN

    def test_baseline_functions_are_the_same_objects(self):
        assert fc.f_drift is fb.f_drift
        assert fc.f_naive_last is fb.f_naive_last
        assert fc.f_seasonal_naive is fb.f_seasonal_naive
        assert fc.f_linear is fb.f_linear
        assert fc.f_holt_winters is fb.f_holt_winters
        assert fc.f_ensemble is fb.f_ensemble

    def test_mase_scale_is_the_same_function(self):
        assert fc.mase_scale is fb.mase_scale

    def test_drift_score_matches_the_original_backtest(self):
        """The imported baseline must reproduce its published MASE exactly.

        If this drifts, the whole leaderboard is incomparable to
        reports/forecast_backtest_metrics.json.
        """
        original = json.loads(
            (ROOT / "reports" / "forecast_backtest_metrics.json").read_text())
        m = fc.run()
        assert m["models"]["drift"]["overall_mase"] == pytest.approx(
            original["models"]["drift"]["overall_mase"], abs=1e-3)


class TestCompleteness:
    """No model may silently drop out of the leaderboard."""

    def test_every_model_ran_at_every_origin(self, metrics):
        broken = {k: v for k, v in metrics["models"].items() if v["status"] != "ok"}
        assert broken == {}, f"models that did not run cleanly: {broken}"

    def test_all_expected_models_present(self, metrics):
        expected = set(fc.BASELINES) | set(fc.CHALLENGERS)
        assert set(metrics["models"]) == expected

    def test_leaderboard_covers_every_model(self, metrics):
        assert len(metrics["leaderboard"]) == len(metrics["models"])

    def test_no_nan_scores(self, metrics):
        for name, v in metrics["models"].items():
            assert v["overall_mase"] is not None, name
            assert v["overall_mase"] > 0, name


class TestVerdictConsistency:
    """The verdict must follow from the numbers, not sit beside them."""

    def test_winner_is_the_minimum_mase(self, metrics):
        ranked = sorted(
            ((k, v["overall_mase"]) for k, v in metrics["models"].items()),
            key=lambda kv: kv[1])
        assert metrics["verdict"]["winner"] == ranked[0][0]
        assert metrics["verdict"]["winner_mase"] == pytest.approx(ranked[0][1])

    def test_beats_drift_flag_matches_the_numbers(self, metrics):
        v = metrics["verdict"]
        assert v["challenger_beats_drift"] == (
            v["best_challenger_mase"] < v["drift_mase"])

    def test_recommendation_matches_the_direction(self, metrics):
        v = metrics["verdict"]
        if v["challenger_beats_drift"]:
            assert "Promote it" in v["recommendation"]
            assert v["winner"] in v["recommendation"]
        else:
            assert "ceiling" in v["recommendation"]


class TestTheFinding:
    """The published result — pinned so a change must move the recommendation."""

    def test_holt_linear_beats_drift(self, metrics):
        hl = metrics["models"]["holt_linear"]["overall_mase"]
        drift = metrics["models"]["drift"]["overall_mase"]
        assert hl < drift, (
            "holt_linear no longer beats drift — the README and dashboard "
            "recommendation must be updated with this run's verdict"
        )
        assert hl == pytest.approx(0.3752, abs=2e-3)
        assert drift == pytest.approx(0.4681, abs=2e-3)

    def test_improvement_is_material(self, metrics):
        """The win must be large enough to justify the swap (~20% better)."""
        hl = metrics["models"]["holt_linear"]["overall_mase"]
        drift = metrics["models"]["drift"]["overall_mase"]
        assert (drift - hl) / drift > 0.10, "improvement under 10% — not worth swapping"

    def test_seasonality_hurts_on_this_data(self, metrics):
        """The insight behind the win: seasonal models do worse, not better.

        seasonal_naive and holt_winters (multiplicative seasonality) both lose
        to the seasonality-free trend models. That is why holt_linear wins.
        """
        hl = metrics["models"]["holt_linear"]["overall_mase"]
        assert metrics["models"]["seasonal_naive"]["overall_mase"] > 2.0
        assert metrics["models"]["holt_winters"]["overall_mase"] > hl

    def test_shipped_ensemble_still_loses_to_drift(self, metrics):
        """The original honest verdict stands — this is why the challenger work existed."""
        assert metrics["models"]["ensemble_shipped"]["overall_mase"] > \
               metrics["models"]["drift"]["overall_mase"]


class TestCommittedArtifact:
    def test_report_json_matches_a_fresh_run(self):
        p = ROOT / "reports" / "forecast_challenger_metrics.json"
        assert p.exists(), "run scripts/forecast_challenger.py to regenerate"
        committed = json.loads(p.read_text())
        fresh = fc.run()
        assert committed["verdict"]["winner"] == fresh["verdict"]["winner"]
        assert committed["models"]["holt_linear"]["overall_mase"] == pytest.approx(
            fresh["models"]["holt_linear"]["overall_mase"], abs=1e-3)

    def test_markdown_report_exists(self):
        assert (ROOT / "reports" / "forecast_challenger.md").exists()
