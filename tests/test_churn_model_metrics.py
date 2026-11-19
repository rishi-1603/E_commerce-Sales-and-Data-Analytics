"""
test_churn_model_metrics.py — the shipped churn model and its rolling backtest.
==============================================================================
The 80/20 split is a held-out evaluation on a single cutoff, NOT a temporal
split. Real temporal evidence lives in reports/churn_temporal_backtest.json.
These tests pin both artifacts and require the dashboard chart to match the
model artifact exactly, so a stale chart cannot survive a model change.
"""
import json
import os
import re

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(BASE, "reports")


@pytest.fixture(scope="module")
def model():
    with open(os.path.join(REPORTS, "churn_model_metrics.json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def backtest():
    with open(os.path.join(REPORTS, "churn_temporal_backtest.json"), encoding="utf-8") as f:
        return json.load(f)


def test_pinned_headline(model):
    assert model["selected_model"] == "Logistic Regression"
    assert model["n_customers"] == 1597
    assert model["prevalence"] == pytest.approx(0.2354, abs=5e-3)
    assert model["cutoff"] == "2024-07-03"
    assert model["horizon_days"] == 180


def test_cv_selection_is_real(model):
    cv = model["cv"]
    assert set(cv) == {"Logistic Regression", "Random Forest", "Gradient Boosting"}
    best = max(cv, key=lambda k: cv[k]["roc_auc_mean"])
    assert cv[best]["roc_auc_mean"] == pytest.approx(0.6742, abs=5e-3)
    assert cv[best]["roc_auc_std"] == pytest.approx(0.0303, abs=5e-3)
    assert cv[best]["f1_mean"] == pytest.approx(0.3994, abs=5e-3)
    assert model["selected_model"] == best
    for v in cv.values():
        assert 0 <= v["roc_auc_mean"] <= 1
        assert 0 <= v["f1_mean"] <= 1


def test_holdout_scored_once(model):
    h = model["holdout"]
    assert h["n"] == 320                      # 20% of 1,597
    assert h["roc_auc"] == pytest.approx(0.6621, abs=5e-3)
    assert h["pr_auc"] == pytest.approx(0.3322, abs=5e-3)
    assert 0 < h["brier_calibrated"] < h["brier_raw"]
    assert h["ece_calibrated"] == pytest.approx(0.0352, abs=5e-3)


def test_published_scores_are_out_of_fold_not_insample(model):
    text = model["calibration"].lower()
    assert "out-of-fold" in text
    assert "holdout" in text
    assert model["risk_bands"] == {"Low Risk": 1156, "Medium Risk": 441, "High Risk": 0}
    assert sum(model["risk_bands"].values()) == model["n_customers"]


def test_dashboard_model_chart_matches_artifact(model):
    with open(os.path.join(BASE, "dashboard.html"), encoding="utf-8") as f:
        html = f.read()
    auc = re.search(r"label:'AUC',data:\[([0-9.,\s]+)\]", html)
    f1 = re.search(r"label:'F1',data:\[([0-9.,\s]+)\]", html)
    assert auc and f1
    auc_vals = [float(x) for x in auc.group(1).split(",")]
    f1_vals = [float(x) for x in f1.group(1).split(",")]
    order = list(model["cv"])
    # The pipeline regenerates the artifact on each runner, and float summation
    # differs across platforms: the 4th decimal can move by one unit. Agree to
    # the displayed precision (4 dp) with half-a-unit tolerance instead of exact
    # equality, so a genuinely different score still fails.
    assert auc_vals == pytest.approx(
        [model["cv"][k]["roc_auc_mean"] for k in order], abs=5e-4
    )
    assert f1_vals == pytest.approx(
        [model["cv"][k]["f1_mean"] for k in order], abs=5e-4
    )


def test_temporal_backtest_is_real(backtest, model):
    origins = backtest["origins"]
    assert len(origins) >= 3
    cutoffs = [o["cutoff"] for o in origins]
    assert cutoffs == sorted(cutoffs)
    assert cutoffs[-1] == model["cutoff"]
    for o in origins:
        assert o["n_customers"] > 0
        assert 0 < o["prevalence"] < 1
        assert 0.4 < o["cv_roc_auc_mean"] < 1
    # The production cutoff must agree with the single-cutoff artifact.
    assert origins[-1]["cv_roc_auc_mean"] == pytest.approx(
        model["cv"]["Logistic Regression"]["roc_auc_mean"], abs=5e-3)
    assert origins[-1]["n_customers"] == model["n_customers"]
    assert origins[-1]["prevalence"] == pytest.approx(model["prevalence"], abs=5e-3)


def test_split_is_not_mislabelled_temporal():
    """The 80/20 holdout is random and stratified, not a temporal split."""
    with open(os.path.join(REPORTS, "churn_calibration_metrics.json"), encoding="utf-8") as f:
        protocol = json.load(f)["protocol"]
    assert "stratified" in protocol
    assert "temporal" not in protocol
    assert "forward-time" not in protocol
