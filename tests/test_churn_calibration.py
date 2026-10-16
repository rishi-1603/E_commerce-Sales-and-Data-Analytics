"""
test_churn_calibration.py — the calibration/threshold report cannot drift.
=========================================================================
Pins the numbers in reports/churn_calibration_metrics.json (written by
scripts/churn_calibration.py) and enforces the statistical invariants that
make the report's claims defensible.

Run:  python -m pytest tests/test_churn_calibration.py -v
"""
import json
import os
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

METRICS_PATH = os.path.join(BASE, "reports", "churn_calibration_metrics.json")


@pytest.fixture(scope="module")
def metrics():
    assert os.path.exists(METRICS_PATH), \
        "reports/churn_calibration_metrics.json missing — run scripts/churn_calibration.py"
    with open(METRICS_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def recomputed(metrics):
    """Recompute the analysis and require it to reproduce the committed JSON."""
    import churn_calibration as cc
    m, _ = cc.run_analysis()
    return m


# ── Reproducibility: recomputation must match the committed JSON ──────
# Tolerances absorb cross-version float drift (sklearn 1.6.x vs 1.9.x give
# differences ~1e-3); anything larger means the analysis silently changed.
def test_recomputation_matches_committed_json(metrics, recomputed):
    assert recomputed["roc_auc"] == pytest.approx(metrics["roc_auc"], abs=5e-3)
    assert recomputed["pr_auc"] == pytest.approx(metrics["pr_auc"], abs=5e-3)
    assert recomputed["calibration"]["isotonic"]["brier"] == pytest.approx(
        metrics["calibration"]["isotonic"]["brier"], abs=5e-3)
    assert recomputed["cost_model"]["t_star_selected_on_cal"] == pytest.approx(
        metrics["cost_model"]["t_star_selected_on_cal"], abs=0.02)
    pol_new = recomputed["policies_on_test"]
    pol_old = metrics["policies_on_test"]
    key = [k for k in pol_old if k.startswith("data_driven")][0]
    key_new = [k for k in pol_new if k.startswith("data_driven")][0]
    assert pol_new[key_new]["expected_profit"] == pytest.approx(pol_old[key]["expected_profit"], rel=5e-2)
    assert pol_new[key_new]["contacts"] == pytest.approx(pol_old[key]["contacts"], abs=15)


# ── Pinned values (Day-2 release, seeded data) ────────────────────────
def test_pinned_headline_metrics(metrics):
    assert metrics["roc_auc"] == pytest.approx(0.6489, abs=5e-3)
    assert metrics["pr_auc"] == pytest.approx(0.3664, abs=5e-3)
    assert metrics["prevalence"] == pytest.approx(0.2535, abs=5e-3)


def test_pinned_calibration(metrics):
    cal = metrics["calibration"]
    assert cal["raw"]["brier"] == pytest.approx(0.1952, abs=5e-3)
    assert cal["isotonic"]["brier"] == pytest.approx(0.1811, abs=5e-3)
    # ECE is bin-sensitive across sklearn builds (isotonic tie-handling drifts
    # slightly): pin with a looser band but assert the meaningful bound —
    # isotonic ECE must stay far below the raw 0.0966 (direction tested separately).
    assert cal["isotonic"]["ece_10bin"] == pytest.approx(0.034, abs=1.5e-2)
    assert cal["isotonic"]["ece_10bin"] < 0.5 * cal["raw"]["ece_10bin"]


def test_pinned_threshold_and_profits(metrics):
    cm = metrics["cost_model"]
    assert cm["bayes_threshold"] == pytest.approx(0.1289, abs=5e-3)
    assert cm["t_star_selected_on_cal"] == pytest.approx(0.10, abs=5e-3)
    pol = metrics["policies_on_test"]
    assert pol["data_driven_t_star (p>=0.1)"]["expected_profit"] == pytest.approx(81279, rel=5e-2)
    assert pol["contact_all"]["expected_profit"] == pytest.approx(77615, rel=5e-2)


# ── Statistical invariants (the report's claims depend on these) ──────
def test_model_beats_prevalence_reference_on_brier(metrics):
    iso = metrics["calibration"]["isotonic"]["brier"]
    ref = metrics["brier_prevalence_reference"]
    assert iso < ref, "model must beat the always-predict-base-rate Brier score"


def test_pr_auc_beats_random_ranking(metrics):
    # random ranking scores ≈ prevalence on PR-AUC
    assert metrics["pr_auc"] > metrics["prevalence"]


def test_calibration_improves_with_isotonic(metrics):
    cal = metrics["calibration"]
    assert cal["isotonic"]["brier"] < cal["raw"]["brier"]
    assert cal["isotonic"]["ece_10bin"] < cal["raw"]["ece_10bin"]


def test_raw_model_is_overconfident(metrics):
    # slope < 1 => predictions too extreme; this is the documented finding
    assert metrics["calibration"]["raw"]["calibration_slope"] < 1.0


def test_t_star_policy_beats_contact_all(metrics):
    pol = metrics["policies_on_test"]
    tstar_key = [k for k in pol if k.startswith("data_driven")][0]
    assert pol[tstar_key]["expected_profit"] >= pol["contact_all"]["expected_profit"]
    assert pol[tstar_key]["contacts"] < pol["contact_all"]["contacts"]


def test_current_bands_leave_value_on_the_table(metrics):
    pol = metrics["policies_on_test"]
    tstar_key = [k for k in pol if k.startswith("data_driven")][0]
    band = pol["current_band_medium_plus (p>=0.33)"]
    assert pol[tstar_key]["expected_profit"] > band["expected_profit"] * 2


def test_reliability_table_has_10_bins(metrics):
    assert len(metrics["reliability_table_isotonic"]) == 10


def test_capacity_curve_monotone_capture(metrics):
    caps = metrics["capacity_curve"]
    captures = [c["capture_rate"] for c in caps]
    assert captures == sorted(captures), "capture rate must rise with campaign size"


def test_sensitivity_covers_3x3_grid(metrics):
    assert len(metrics["sensitivity"]) == 9
    # higher recovery rate -> higher profit at fixed cost
    r105 = [s for s in metrics["sensitivity"] if s["recovery_rate"] == 0.105 and s["contact_cost"] == 250.0][0]
    r195 = [s for s in metrics["sensitivity"] if s["recovery_rate"] == 0.195 and s["contact_cost"] == 250.0][0]
    assert r195["expected_profit"] > r105["expected_profit"]


def test_error_analysis_covers_all_bands(metrics):
    ea = metrics["error_analysis"]
    for key in ("by_recency", "by_frequency", "by_tenure"):
        assert len(ea[key]) == 3
        for row in ea[key]:
            assert row["n"] > 0


def test_protocol_is_temporal_honest(metrics):
    assert "calibration 16%" in metrics["protocol"]
    assert "test 20%" in metrics["protocol"]
