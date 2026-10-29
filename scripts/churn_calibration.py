"""
churn_calibration.py -- probability calibration, cost-based thresholds, error analysis
===================================================================================
WHY THIS EXISTS: an AUC (0.65) says the model RANKS customers usefully. It does
NOT say the probabilities are trustworthy, nor which customers a campaign
should contact. This script answers the three questions a retention manager
actually asks:

  1. "If the model says 40% risk, do ~40% of those customers churn?"  (calibration)
  2. "Who should I contact with a limited budget?"                    (thresholds)
  3. "Who does the model systematically miss?"                        (error analysis)

Protocol (stricter than the pipeline's 80/20 split):
  fit 64% / calibration 16% / test 20%  -- stratified, random_state=42
  - base model fit on the fit slice
  - Platt (sigmoid) and isotonic calibrators fit on the calibration slice
  - operating threshold SELECTED on the calibration slice (expected profit)
  - everything reported on the untouched test slice

Cost model (ALL money figures are illustrative -- replace with business inputs):
  contacting one customer costs C (incentive + ops)
  contacting a churner retains them with probability r (recovery rate)
  a retained customer is worth V (proxy: mean historical spend in the data)
  -> expected profit of contacting a customer with churn probability p:
        E[profit] = p * r * V - C          ->  contact iff p > C / (r * V)

Outputs:
  reports/churn_calibration_metrics.json   (machine-readable; pinned by tests)
  reports/churn_calibration_and_thresholds.md  (the report)
  docs/figures/18_churn_calibration.png
  docs/figures/19_churn_threshold_profit.png

Run:  python scripts/churn_calibration.py
"""
import json
import os
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
RAW = os.path.join(BASE, "data", "raw")
FIGS = os.path.join(BASE, "docs", "figures")
REPORTS = os.path.join(BASE, "reports")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
PALETTE = ["#2563EB", "#DB2777", "#D97706", "#059669", "#7C3AED"]

# -- Illustrative cost assumptions (the report flags these loudly) -----
C_CONTACT = 250.0     # Rs. per customer contacted (incentive + ops)
R_RECOVERY = 0.15     # probability a contacted churner is retained
R_SENS = (0.105, 0.15, 0.195)   # ±30% sensitivity
C_SENS = (175.0, 250.0, 325.0)  # ±30% sensitivity


# ════════════════════════════════════════════════════════════════════
# 1. Rebuild the leakage-free churn dataset exactly like 03_churn_analysis
# ════════════════════════════════════════════════════════════════════
def build_churn_frame():
    from sklearn.preprocessing import LabelEncoder

    master = pd.read_csv(os.path.join(PROC, "master_orders.csv"), parse_dates=["order_date"])
    customers = pd.read_csv(os.path.join(RAW, "customers.csv"), parse_dates=["registration_date"])

    data_end = master["order_date"].max()
    cutoff = data_end - pd.Timedelta(days=180)

    past = master[master["order_date"] < cutoff].copy()
    future = master[master["order_date"] >= cutoff].copy()
    eligible = set(past["customer_id"].unique())

    feat = past.groupby("customer_id").agg(
        total_orders=("order_id", "nunique"),
        total_revenue=("line_total", "sum"),
        avg_order_value=("line_total", "mean"),
        total_items=("quantity", "sum"),
        avg_discount=("discount_pct_x", "mean"),
        unique_categories=("category", "nunique"),
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
    ).reset_index()

    feat["recency_days"] = (cutoff - feat["last_order_date"]).dt.days
    feat["tenure_days"] = (cutoff - feat["first_order_date"]).dt.days
    feat["order_frequency"] = feat["total_orders"] / (feat["tenure_days"] / 30).clip(lower=1)
    feat["avg_days_between"] = feat["tenure_days"] / feat["total_orders"].clip(lower=1)

    feat = feat.merge(
        customers[["customer_id", "segment", "region", "acquisition_channel", "age", "gender"]],
        on="customer_id", how="left")

    le = LabelEncoder()
    for col in ["segment", "region", "acquisition_channel", "gender"]:
        feat[col + "_enc"] = le.fit_transform(feat[col].fillna("Unknown"))

    future_buyers = set(future.loc[future["customer_id"].isin(eligible), "customer_id"].unique())
    feat["churned"] = (~feat["customer_id"].isin(future_buyers)).astype(int)
    return feat


FEATURES = [
    "total_orders", "total_revenue", "avg_order_value", "total_items",
    "avg_discount", "unique_categories", "recency_days", "tenure_days",
    "order_frequency", "avg_days_between", "age",
    "segment_enc", "region_enc", "acquisition_channel_enc", "gender_enc",
]


# ════════════════════════════════════════════════════════════════════
# 2. Calibration helpers
# ════════════════════════════════════════════════════════════════════
def reliability_table(y, p, n_bins=10):
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (p >= lo) & (p < hi) if i < n_bins - 1 else (p >= lo) & (p <= hi)
        if mask.sum() == 0:
            rows.append({"bin": f"[{lo:.1f},{hi:.1f}]", "n": 0,
                         "mean_predicted": None, "observed_rate": None})
            continue
        rows.append({
            "bin": f"[{lo:.1f},{hi:.1f}]",
            "n": int(mask.sum()),
            "mean_predicted": round(float(p[mask].mean()), 4),
            "observed_rate": round(float(y[mask].mean()), 4),
        })
    return rows


def calibration_slope_intercept(y, p):
    """Regress y on logit(p): slope=1 & intercept=0 => perfectly calibrated."""
    eps = 1e-6
    logit = np.log(np.clip(p, eps, 1 - eps) / (1 - np.clip(p, eps, 1 - eps)))
    lr = LogisticRegression(C=1e6, max_iter=1000)
    lr.fit(logit.reshape(-1, 1), y)
    return float(lr.intercept_[0]), float(lr.coef_[0, 0])


def ece(y, p, n_bins=10):
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    total = len(y)
    e = 0.0
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (p >= lo) & (p < hi) if i < n_bins - 1 else (p >= lo) & (p <= hi)
        if mask.sum() == 0:
            continue
        e += mask.sum() / total * abs(p[mask].mean() - y[mask].mean())
    return float(e)


# ════════════════════════════════════════════════════════════════════
# 3. Main analysis
# ════════════════════════════════════════════════════════════════════
def run_analysis():
    feat = build_churn_frame()
    X = feat[FEATURES].fillna(0)
    y = feat["churned"].values
    prevalence = float(y.mean())

    # fit / calibration / test  = 64% / 16% / 20%
    X_fit, X_test, y_fit, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y)
    X_fit, X_cal, y_fit, y_cal = train_test_split(
        X_fit, y_fit, test_size=0.20, random_state=42, stratify=y_fit)

    base = GradientBoostingClassifier(n_estimators=200, random_state=42)
    base.fit(X_fit, y_fit)

    p_raw_cal = base.predict_proba(X_cal)[:, 1]
    p_raw_test = base.predict_proba(X_test)[:, 1]

    # Platt (sigmoid) -- logistic regression on the raw log-odds
    platt = LogisticRegression(C=1e6, max_iter=1000)
    logit_cal = np.log(np.clip(p_raw_cal, 1e-6, 1 - 1e-6) /
                       (1 - np.clip(p_raw_cal, 1e-6, 1 - 1e-6)))
    platt.fit(logit_cal.reshape(-1, 1), y_cal)

    def platt_transform(p):
        lg = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
        return platt.predict_proba(lg.reshape(-1, 1))[:, 1]

    p_platt_cal = platt_transform(p_raw_cal)
    p_platt_test = platt_transform(p_raw_test)

    # Isotonic -- non-parametric
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(p_raw_cal, y_cal)
    p_iso_cal = iso.predict(p_raw_cal)
    p_iso_test = iso.predict(p_raw_test)

    # -- Calibration quality on the untouched TEST slice ---------------
    variants = {
        "raw": (p_raw_cal, p_raw_test),
        "platt": (p_platt_cal, p_platt_test),
        "isotonic": (p_iso_cal, p_iso_test),
    }
    calibration = {}
    for name, (pc, pt) in variants.items():
        intercept, slope = calibration_slope_intercept(y_test, pt)
        calibration[name] = {
            "brier": round(float(brier_score_loss(y_test, pt)), 4),
            "ece_10bin": round(ece(y_test, pt), 4),
            "calibration_intercept": round(intercept, 4),
            "calibration_slope": round(slope, 4),
        }

    # Ranking metrics are invariant to monotone calibration -- report once
    roc_auc = round(float(roc_auc_score(y_test, p_raw_test)), 4)
    pr_auc = round(float(average_precision_score(y_test, p_raw_test)), 4)

    # Prevalence-only reference: Brier of always predicting the base rate
    brier_ref = round(float(brier_score_loss(y_test, np.full_like(y_test, prevalence))), 4)

    # -- Cost model ----------------------------------------------------
    # V = what a retained customer actually spent during the 180-day label
    # window (observed in the data) -- horizon-aligned and directly measurable.
    # Lifetime historical spend is reported as context only.
    future_buyers = set(feat.loc[feat["churned"] == 0, "customer_id"])
    master = pd.read_csv(os.path.join(PROC, "master_orders.csv"), parse_dates=["order_date"])
    cutoff = master["order_date"].max() - pd.Timedelta(days=180)
    fut = master[master["order_date"] >= cutoff]
    fut_rev = fut[fut["customer_id"].isin(future_buyers)].groupby("customer_id")["line_total"].sum()
    v_value = round(float(fut_rev.mean()), 2)          # Rs. retained-value proxy (180d)
    v_lifetime = round(float(feat["total_revenue"].mean()), 2)  # context only

    def expected_profit(p, y_true, threshold, c, r, v):
        contact = p >= threshold
        n_contact = int(contact.sum())
        churners_caught = int((y_true[contact] == 1).sum())
        profit = r * v * churners_caught - c * n_contact
        return {
            "threshold": round(float(threshold), 4),
            "contacts": n_contact,
            "churners_captured": churners_caught,
            "capture_rate": round(churners_caught / max(int((y_true == 1).sum()), 1), 4),
            "precision": round(churners_caught / max(n_contact, 1), 4),
            "expected_profit": round(float(profit), 2),
        }

    def bayes_threshold(c, r, v):
        return c / (r * v)

    t_bayes = bayes_threshold(C_CONTACT, R_RECOVERY, v_value)

    # Select operating threshold ON THE CALIBRATION SLICE (not the test slice)
    grid = np.round(np.arange(0.05, 0.96, 0.01), 2)
    profits_cal = [expected_profit(p_iso_cal, y_cal, t, C_CONTACT, R_RECOVERY, v_value)["expected_profit"]
                   for t in grid]
    t_star = float(grid[int(np.argmax(profits_cal))])

    # -- Policy comparison on the untouched TEST slice -----------------
    policies = {
        "contact_none": expected_profit(p_iso_test, y_test, 2.0, C_CONTACT, R_RECOVERY, v_value),
        "contact_all": expected_profit(p_iso_test, y_test, 0.0, C_CONTACT, R_RECOVERY, v_value),
        "current_band_medium_plus (p>=0.33)": expected_profit(p_iso_test, y_test, 0.33, C_CONTACT, R_RECOVERY, v_value),
        "current_band_high_only (p>=0.66)": expected_profit(p_iso_test, y_test, 0.66, C_CONTACT, R_RECOVERY, v_value),
        f"data_driven_t_star (p>={t_star})": expected_profit(p_iso_test, y_test, t_star, C_CONTACT, R_RECOVERY, v_value),
        "oracle (upper bound)": {
            "threshold": None, "contacts": int((y_test == 1).sum()),
            "churners_captured": int((y_test == 1).sum()),
            "capture_rate": 1.0, "precision": 1.0,
            "expected_profit": round(float(R_RECOVERY * v_value * int((y_test == 1).sum())), 2),
        },
    }

    # Sensitivity: t* and test-set profit across ±30% cost and recovery rate
    sensitivity = []
    for r in R_SENS:
        for c in C_SENS:
            t = bayes_threshold(c, r, v_value)
            t = float(np.clip(t, 0.0, 1.0))
            prof = expected_profit(p_iso_test, y_test, t, c, r, v_value)
            sensitivity.append({
                "recovery_rate": r, "contact_cost": c,
                "bayes_threshold": round(t, 4),
                **{k: prof[k] for k in ("contacts", "churners_captured", "expected_profit")},
            })

    # -- Operating-point table (precision/recall/F1 at fixed thresholds) -
    operating_points = []
    for t in (0.25, 0.33, 0.50, 0.66, 0.75):
        pred = (p_iso_test >= t).astype(int)
        p_, r_, f1_, _ = precision_recall_fscore_support(y_test, pred, average="binary", zero_division=0)
        operating_points.append({
            "threshold": t, "precision": round(float(p_), 4),
            "recall": round(float(r_), 4), "f1": round(float(f1_), 4),
            "contacts": int(pred.sum()),
        })

    # -- Capacity curve (top-k% by predicted risk) ---------------------
    order = np.argsort(-p_iso_test)
    y_sorted = y_test[order]
    total_churners = max(int(y_sorted.sum()), 1)
    capacity = []
    for k in (5, 10, 20, 30, 50):
        n = max(int(len(y_sorted) * k / 100), 1)
        caught = int(y_sorted[:n].sum())
        capacity.append({
            "top_pct": k, "contacts": n,
            "churners_captured": caught,
            "capture_rate": round(caught / total_churners, 4),
            "precision": round(caught / n, 4),
            "lift": round((caught / n) / prevalence, 4),
        })

    # -- Error analysis at t* (who is missed / wrongly contacted?) -----
    pred_star = (p_iso_test >= t_star).astype(int)
    test_idx = X_test.index
    test_feat = feat.loc[test_idx].copy()
    test_feat["pred"] = pred_star
    test_feat["p"] = p_iso_test
    test_feat["y"] = y_test

    # RFM-ish bands from pre-cutoff behaviour
    test_feat["recency_band"] = pd.qcut(test_feat["recency_days"], 3, labels=["recent", "mid", "lapsed"])
    test_feat["frequency_band"] = pd.qcut(test_feat["total_orders"].rank(method="first"), 3,
                                          labels=["low_freq", "mid_freq", "high_freq"])
    test_feat["tenure_band"] = pd.qcut(test_feat["tenure_days"], 3, labels=["new", "established", "veteran"])

    def band_table(col):
        rows = []
        for band, g in test_feat.groupby(col, observed=True):
            fp = int(((g["pred"] == 1) & (g["y"] == 0)).sum())
            fn = int(((g["pred"] == 0) & (g["y"] == 1)).sum())
            rows.append({
                "band": str(band), "n": int(len(g)),
                "churn_rate": round(float(g["y"].mean()), 4),
                "false_positives": fp, "false_negatives": fn,
            })
        return rows

    error_analysis = {
        "threshold_used": t_star,
        "by_recency": band_table("recency_band"),
        "by_frequency": band_table("frequency_band"),
        "by_tenure": band_table("tenure_band"),
    }

    metrics = {
        "protocol": "fit 64% / calibration 16% / test 20%, stratified, random_state=42",
        "n_total": int(len(feat)), "n_fit": int(len(X_fit)),
        "n_cal": int(len(X_cal)), "n_test": int(len(X_test)),
        "prevalence": round(prevalence, 4),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier_prevalence_reference": brier_ref,
        "calibration": calibration,
        "reliability_table_isotonic": reliability_table(y_test, p_iso_test),
        "cost_model": {
            "contact_cost_inr": C_CONTACT, "recovery_rate": R_RECOVERY,
            "retained_value_proxy_inr": v_value,
            "lifetime_spend_context_inr": v_lifetime,
            "value_proxy_definition": "mean observed 180-day spend of customers who did NOT churn",
            "bayes_threshold": round(bayes_threshold(C_CONTACT, R_RECOVERY, v_value), 4),
            "t_star_selected_on_cal": t_star,
        },
        "policies_on_test": policies,
        "sensitivity": sensitivity,
        "operating_points": operating_points,
        "capacity_curve": capacity,
        "error_analysis": error_analysis,
    }
    return metrics, (feat, y_test, p_raw_test, p_platt_test, p_iso_test, t_star, v_value)


def make_figures(bundle):
    feat, y_test, p_raw_test, p_platt_test, p_iso_test, t_star, v_value = bundle

    # Figure 18 -- reliability curve
    fig, ax = plt.subplots(figsize=(7, 6))
    for (name, p), color in zip(
            [("Raw GBM", p_raw_test), ("Platt-scaled", p_platt_test), ("Isotonic", p_iso_test)],
            PALETTE):
        rows = reliability_table(y_test, p)
        xs = [r["mean_predicted"] for r in rows if r["n"] > 0]
        ys = [r["observed_rate"] for r in rows if r["n"] > 0]
        ns = [r["n"] for r in rows if r["n"] > 0]
        ax.plot(xs, ys, "o-", label=name, color=color, lw=2)
        if name == "Isotonic":
            ax.scatter(xs, ys, s=[n * 1.2 for n in ns], color=color, alpha=0.4)
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect calibration")
    ax.set_xlabel("Predicted churn probability")
    ax.set_ylabel("Observed churn rate")
    ax.set_title("Reliability curve -- churn model (test slice)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIGS, "18_churn_calibration.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # Figure 19 -- expected profit vs threshold
    fig, ax = plt.subplots(figsize=(8, 5.5))
    grid = np.round(np.arange(0.05, 0.96, 0.01), 2)
    profits = []
    for t in grid:
        contact = p_iso_test >= t
        caught = int((y_test[contact] == 1).sum())
        profits.append(R_RECOVERY * v_value * caught - C_CONTACT * int(contact.sum()))
    ax.plot(grid, profits, color=PALETTE[0], lw=2.5)
    ax.axvline(t_star, color=PALETTE[1], ls="--",
               label=f"t* selected on calibration slice = {t_star:.2f}")
    ax.axhline(0, color="k", alpha=0.4)
    ax.set_xlabel("Decision threshold (contact if predicted probability ≥ t)")
    ax.set_ylabel("Expected profit on test slice (Rs.)")
    ax.set_title("Expected campaign profit vs threshold\n"
                 f"(assumptions: cost Rs.{C_CONTACT:.0f}/contact, recovery {R_RECOVERY:.0%}, "
                 f"value Rs.{v_value:,.0f})")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIGS, "19_churn_threshold_profit.png"), dpi=150, bbox_inches="tight")
    plt.close()


def write_report(metrics):
    c = metrics["calibration"]
    cm = metrics["cost_model"]
    lines = []
    a = lines.append
    a("# Churn Model -- Calibration, Decision Thresholds & Error Analysis")
    a("### What the AUC of 0.65 does NOT tell you -- and what to do instead")
    a("")
    a(f"> Generated by `scripts/churn_calibration.py` · protocol: **{metrics['protocol']}**")
    a(f"> n = {metrics['n_total']:,} eligible customers "
      f"(fit {metrics['n_fit']:,} / calibration {metrics['n_cal']:,} / test {metrics['n_test']:,}) · "
      f"churn prevalence {metrics['prevalence']:.1%}")
    a("")
    a("---")
    a("")
    a("## 1. Are the probabilities honest? (calibration)")
    a("")
    a(f"Ranking quality: **ROC-AUC {metrics['roc_auc']}** · **PR-AUC {metrics['pr_auc']}** "
      f"(prevalence = {metrics['prevalence']:.3f}; PR-AUC is the number that matters on this "
      f"imbalanced problem -- random ranking scores ≈ prevalence).")
    a("")
    a(f"Reference: always predicting the base rate gives Brier **{metrics['brier_prevalence_reference']}**; "
      f"the model must beat this to add probability-level value.")
    a("")
    a("| Variant | Brier ↓ | ECE (10-bin) ↓ | Calib. intercept (=0 ideal) | Calib. slope (=1 ideal) |")
    a("|---|---|---|---|---|")
    for name in ("raw", "platt", "isotonic"):
        v = c[name]
        a(f"| {name} | {v['brier']} | {v['ece_10bin']} | {v['calibration_intercept']} | {v['calibration_slope']} |")
    a("")
    a("**Reading the table:** a slope < 1 means predictions are too extreme (over-confident); "
      "a slope > 1 means too timid. Isotonic/Platt scaling fix probability quality without "
      "changing the ranking (AUC is invariant to monotone transforms).")
    a("")
    a("### Reliability table (isotonic, test slice)")
    a("")
    a("| Predicted bin | n | Mean predicted | Observed churn rate |")
    a("|---|---|---|---|")
    for r in metrics["reliability_table_isotonic"]:
        mp = "--" if r["mean_predicted"] is None else r["mean_predicted"]
        or_ = "--" if r["observed_rate"] is None else r["observed_rate"]
        a(f"| {r['bin']} | {r['n']} | {mp} | {or_} |")
    a("")
    a("![Reliability curve](../docs/figures/18_churn_calibration.png)")
    a("")
    a("---")
    a("")
    a("## 2. Who should the campaign contact? (cost-based thresholds)")
    a("")
    a("> ⚠️ **Assumptions box -- read before quoting any profit number.**")
    a(f"> - Contact cost **C = Rs.{cm['contact_cost_inr']:.0f}** per customer (incentive + ops) -- *illustrative*")
    a(f"> - Recovery rate **r = {cm['recovery_rate']:.0%}** of contacted churners are retained -- *illustrative*")
    a(f"> - Retained-customer value **V = Rs.{cm['retained_value_proxy_inr']:,.0f}** -- the mean observed "
      "180-day spend of customers who did *not* churn (horizon-aligned, measured from the data; "
      f"lifetime historical spend averages Rs.{cm['lifetime_spend_context_inr']:,.0f} for context)")
    a("> - Profit figures are *expected values under these assumptions*, not measured outcomes. "
      "No campaign has been run.")
    a("")
    a(f"Under these assumptions the Bayes-optimal threshold is **t = C/(r·V) = {cm['bayes_threshold']:.3f}**: "
      f"contact anyone whose churn probability exceeds it. Selecting the threshold empirically on the "
      f"calibration slice gives **t\\* = {cm['t_star_selected_on_cal']:.2f}**.")
    a("")
    a("### Policy comparison (untouched test slice)")
    a("")
    a("| Policy | Contacts | Churners captured | Capture rate | Precision | Expected profit |")
    a("|---|---|---|---|---|---|")
    for name, p in metrics["policies_on_test"].items():
        th = p["threshold"]
        a(f"| {name} | {p['contacts']} | {p['churners_captured']} | "
          f"{p['capture_rate']:.1%} | {p['precision']:.1%} | Rs.{p['expected_profit']:,.0f} |")
    a("")
    a("![Profit vs threshold](../docs/figures/19_churn_threshold_profit.png)")
    a("")
    a("### Sensitivity (±30% on cost and recovery rate)")
    a("")
    a("| Recovery r | Cost C | Bayes t | Contacts | Churners captured | Expected profit |")
    a("|---|---|---|---|---|---|")
    for s in metrics["sensitivity"]:
        a(f"| {s['recovery_rate']:.1%} | Rs.{s['contact_cost']:.0f} | {s['bayes_threshold']:.3f} | "
          f"{s['contacts']} | {s['churners_captured']} | Rs.{s['expected_profit']:,.0f} |")
    a("")
    a("### Operating points (isotonic probabilities)")
    a("")
    a("| Threshold | Precision | Recall | F1 | Contacts |")
    a("|---|---|---|---|---|")
    for o in metrics["operating_points"]:
        a(f"| {o['threshold']} | {o['precision']:.3f} | {o['recall']:.3f} | {o['f1']:.3f} | {o['contacts']} |")
    a("")
    a("### Capacity curve -- if investigators can only reach k% of customers")
    a("")
    a("| Top-k% by risk | Contacts | Churners captured | Capture rate | Precision | Lift vs random |")
    a("|---|---|---|---|---|---|")
    for k in metrics["capacity_curve"]:
        a(f"| {k['top_pct']}% | {k['contacts']} | {k['churners_captured']} | "
          f"{k['capture_rate']:.1%} | {k['precision']:.1%} | {k['lift']:.2f}× |")
    a("")
    a("---")
    a("")
    a("## 3. Who does the model miss? (error analysis at t\\*)")
    a("")
    ea = metrics["error_analysis"]
    for title, key in [("Recency band", "by_recency"),
                       ("Purchase frequency band", "by_frequency"),
                       ("Tenure band", "by_tenure")]:
        a(f"### By {title}")
        a("")
        a("| Band | n | Churn rate | False positives | False negatives |")
        a("|---|---|---|---|---|")
        for row in ea[key]:
            a(f"| {row['band']} | {row['n']} | {row['churn_rate']:.1%} | "
              f"{row['false_positives']} | {row['false_negatives']} |")
        a("")
    a("**How to read this:** false negatives (missed churners) concentrated in one band mean the "
      "model under-serves that segment -- the fix is either segment-specific features or a "
      "segment-specific threshold. False positives concentrated in low-frequency bands usually mean "
      "small-sample noise is being read as risk (the same failure mode documented in the Zomato project).")
    a("")
    a("---")
    a("")
    a("## 4. Limitations")
    a("")
    a("1. Synthetic data -- methods transfer, numbers don't.")
    a("2. All monetary values are illustrative expected values under stated assumptions; "
      "no campaign has been run and no revenue has been recovered.")
    a("3. Threshold selection used the calibration slice; test-set results are honest, but a real "
      "deployment should re-select t\\* on recent actuals after every retraining.")
    a("4. Recovery rate r is unidentifiable from observational data -- it is the single most "
      "important assumption and the sensitivity table shows how much the answer moves with it.")
    a("5. V uses observed spend of retained customers over the 180-day window; forward-looking CLV "
      "would raise V and push t\\* downward (higher value justifies contacting more customers).")
    a("")
    a("## 5. What this changes in the project")
    a("")
    a("- The risk bands in `03_churn_analysis.py` (0.33/0.66) were arbitrary quantile cuts. "
      f"They are defensible as *communication* bands; the **action** threshold is t\\* = "
      f"{cm['t_star_selected_on_cal']:.2f} under the stated cost model.")
    a("- Probabilities should be consumed through the isotonic calibrator, not the raw GBM output.")
    a("- `docs/MODEL_CARD.md` now carries these sections.")
    a("")
    a("---")
    a("")
    a(f"*Numbers pinned by `tests/test_churn_calibration.py` against "
      f"`reports/churn_calibration_metrics.json`.*")

    with open(os.path.join(REPORTS, "churn_calibration_and_thresholds.md"), "w") as f:
        f.write("\n".join(lines))


def main():
    print("Building leakage-free churn frame...")
    metrics, bundle = run_analysis()
    print(f"ROC-AUC {metrics['roc_auc']} | PR-AUC {metrics['pr_auc']} | "
          f"Brier raw {metrics['calibration']['raw']['brier']} -> "
          f"isotonic {metrics['calibration']['isotonic']['brier']}")
    print(f"Bayes t = {metrics['cost_model']['bayes_threshold']:.3f} | "
          f"t* (cal-selected) = {metrics['cost_model']['t_star_selected_on_cal']:.2f}")
    make_figures(bundle)
    write_report(metrics)
    with open(os.path.join(REPORTS, "churn_calibration_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print("Wrote reports/churn_calibration_and_thresholds.md + churn_calibration_metrics.json")
    print("Wrote docs/figures/18_churn_calibration.png + 19_churn_threshold_profit.png")


if __name__ == "__main__":
    main()
