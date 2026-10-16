"""
test_forecast_backtest.py — the backtest leaderboard cannot drift.
==================================================================
Pins reports/forecast_backtest_metrics.json (written by
scripts/forecast_backtest.py) and enforces the invariants behind the
Day-3 verdict: the ensemble does NOT beat the drift baseline, and the
shipped bootstrap-95% CI under-covers badly.

Run:  python -m pytest tests/test_forecast_backtest.py -v
"""
import json
import os
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

METRICS_PATH = os.path.join(BASE, "reports", "forecast_backtest_metrics.json")


@pytest.fixture(scope="module")
def metrics():
    assert os.path.exists(METRICS_PATH), \
        "reports/forecast_backtest_metrics.json missing — run scripts/forecast_backtest.py"
    with open(METRICS_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def recomputed(metrics):
    import forecast_backtest as fb
    m, _ = fb.run_backtest()
    return m


# ── Reproducibility (tolerances absorb cross-version float drift) ─────
def test_recomputation_matches_committed_json(metrics, recomputed):
    for name in metrics["models"]:
        assert recomputed["models"][name]["overall_mase"] == pytest.approx(
            metrics["models"][name]["overall_mase"], abs=0.03)
    assert recomputed["verdict"]["best_baseline"] == metrics["verdict"]["best_baseline"]
    assert recomputed["coverage_95ci"]["empirical_coverage"] == pytest.approx(
        metrics["coverage_95ci"]["empirical_coverage"], abs=0.05)


# ── Pinned values (Day-3 release, seeded data) ────────────────────────
def test_pinned_leaderboard(metrics):
    m = metrics["models"]
    assert m["ensemble"]["overall_mase"] == pytest.approx(0.680, abs=0.03)
    assert m["drift"]["overall_mase"] == pytest.approx(0.468, abs=0.03)
    assert m["holt_winters"]["overall_mase"] == pytest.approx(0.561, abs=0.03)
    assert m["naive_last"]["overall_mase"] == pytest.approx(0.631, abs=0.03)
    assert m["seasonal_naive"]["overall_mase"] == pytest.approx(2.054, abs=0.05)


def test_pinned_coverage(metrics):
    cov = metrics["coverage_95ci"]
    assert cov["empirical_coverage"] == pytest.approx(0.095, abs=0.05)
    assert cov["n_checked"] == 21


# ── The verdict is the finding — lock it ──────────────────────────────
def test_verdict_ensemble_loses_to_drift(metrics):
    v = metrics["verdict"]
    assert v["best_baseline"] == "drift"
    assert v["ensemble_beats_best_baseline"] is False
    assert "NOT the strongest baseline" in v["recommendation"]


def test_shipped_ci_under_covers(metrics):
    # nominal is 95%; measured coverage must be flagged as under-covering
    assert metrics["coverage_95ci"]["empirical_coverage"] < 0.85


# ── Statistical invariants ────────────────────────────────────────────
def test_ensemble_beats_seasonal_naive_scale(metrics):
    assert metrics["models"]["ensemble"]["overall_mase"] < 1.0
    assert metrics["models"]["seasonal_naive"]["overall_mase"] > 1.0


def test_all_models_have_horizon_breakdown(metrics):
    for name, m in metrics["models"].items():
        for h in ("h1", "h2", "h3"):
            assert m["by_horizon"][h]["mase"] > 0
        assert m["overall_mae"] > 0 and m["overall_rmse"] >= m["overall_mae"] * 0.99


def test_origin_count_and_months(metrics):
    assert metrics["n_months"] == 36
    assert metrics["n_origins"] == 10


def test_coverage_worsens_with_horizon(metrics):
    # documented pattern: h=1 covers more than h=2/h=3
    cov = metrics["coverage_95ci"]["by_horizon"]
    assert cov["h1"] >= cov["h3"]
