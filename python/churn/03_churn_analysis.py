"""
03_churn_analysis.py  —  LEAKAGE-FREE customer churn prediction
================================================================
FIX (2026 review): the original version derived the churn label from
`recency_days` while ALSO feeding `recency_days` to the model, so all three
models reported AUC = 1.0 — target leakage, not predictive power.

The label now lives in a forward window:

    CUTOFF   = last order date - 180 days (2024-07-03)
    FEATURES = behaviour strictly BEFORE the cutoff
    LABEL    = 1 if the customer made NO purchase in the 180 days AFTER it

EVALUATION PROTOCOL (2026 review, second pass)
  * Model selection: 5-fold stratified CV on the training split only.
    The held-out 20% is scored once, for the selected model.
  * Published per-customer scores are CROSS-VALIDATED: training customers get
    out-of-fold probabilities, holdout customers get the model's predictions.
    In-sample refit probabilities are never published (the old version did).
  * Probabilities are isotonic-calibrated on the out-of-fold training
    predictions, so `churn_probability` is on a real probability scale.
  * A rolling-origin backtest re-runs the procedure at 5 cutoffs and writes
    reports/churn_temporal_backtest.json. The 80/20 holdout is cross-sectional,
    NOT temporal — the backtest is what supports time-based claims.

A purchase for the activity/label definition is an order with status Delivered
or Returned (data/metrics.json). Revenue features keep the project revenue
convention (master_orders.csv: Delivered + Processing) so historical spend
matches every other revenue figure in the repo. Both come from
scripts/churn_data.py, the single source of truth shared with
scripts/churn_calibration.py.

Run:  python python/churn/03_churn_analysis.py   (after run_pipeline step 2)
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import clone
from sklearn.model_selection import (train_test_split, StratifiedKFold,
                                     cross_val_score, cross_val_predict)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (classification_report, confusion_matrix, f1_score,
                             roc_auc_score, roc_curve, average_precision_score,
                             brier_score_loss)

warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "scripts"))
from churn_data import build_churn_frame, FEATURES, HORIZON_DAYS  # noqa: E402

PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "docs", "figures")
REPO = os.path.join(BASE, "reports")
os.makedirs(PROC, exist_ok=True)
os.makedirs(FIGS, exist_ok=True)
os.makedirs(REPO, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
PALETTE = ["#2563EB", "#DB2777", "#D97706", "#059669", "#7C3AED"]

BAND_MED = 0.33          # Low/Medium boundary == operational decision threshold
BAND_HIGH = 0.66         # Medium/High boundary
RISK_BINS = [-0.001, BAND_MED, BAND_HIGH, 1.0]
RISK_LABELS = ["Low Risk", "Medium Risk", "High Risk"]

# Rolling-origin backtest cutoffs (production cutoff appended at run time)
BACKTEST_ORIGINS = ["2023-07-01", "2023-10-01", "2024-01-01", "2024-04-01"]


def expected_calibration_error(y_true, prob, bins=10):
    """Mean |observed - predicted| per probability bin, weighted by bin size."""
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.digitize(prob, edges[1:-1])
    total = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            total += m.mean() * abs(y_true[m].mean() - prob[m].mean())
    return float(total)


# ── Dataset (shared definition) ───────────────────────────────────────
print("Building churn frame...")
feat, CUTOFF = build_churn_frame()
print(f"Cutoff (feature cutoff): {CUTOFF.date()} | Label window: +{HORIZON_DAYS}d")
print(f"Eligible customers: {len(feat):,}")
print(f"Churn rate (no purchase in +{HORIZON_DAYS}d): {feat['churned'].mean()*100:.1f}%")

X = feat[FEATURES].fillna(0)
y = feat["churned"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

models = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=500, random_state=42)),
    ]),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=200, random_state=42),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# ── Model selection: 5-fold CV on the TRAINING split only ─────────────
cv_rows, oof_cache = {}, {}
for name, model in models.items():
    auc = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
    oof = cross_val_predict(clone(model), X_train, y_train, cv=cv,
                            method="predict_proba")[:, 1]
    oof_cache[name] = oof
    cv_rows[name] = {
        "roc_auc_mean": round(float(auc.mean()), 4),
        "roc_auc_std": round(float(auc.std()), 4),
        # F1 at the Low/Medium band boundary, pooled out-of-fold
        "f1_mean": round(float(f1_score(y_train, (oof >= BAND_MED).astype(int))), 4),
    }
    print(f"{name:20s} CV AUC {auc.mean():.4f} ± {auc.std():.4f} "
          f"| CV F1@{BAND_MED:.2f} {cv_rows[name]['f1_mean']:.4f}")

best_name = max(cv_rows, key=lambda n: cv_rows[n]["roc_auc_mean"])
print(f"\nSelected by CV AUC: {best_name} ({cv_rows[best_name]['roc_auc_mean']:.4f})")

# ── Single holdout evaluation of the selected model ───────────────────
best_model = clone(models[best_name])
best_model.fit(X_train, y_train)
test_raw = best_model.predict_proba(X_test)[:, 1]

# ── Calibration on out-of-fold TRAINING predictions only ──────────────
oof_best = oof_cache[best_name]
iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
iso.fit(oof_best, y_train)

raw_all = np.full(len(feat), np.nan)
cal_all = np.full(len(feat), np.nan)
train_idx = X_train.index.to_numpy()
test_idx = X_test.index.to_numpy()
raw_all[train_idx] = oof_best
cal_all[train_idx] = iso.predict(oof_best)
raw_all[test_idx] = test_raw
cal_all[test_idx] = iso.predict(test_raw)
assert not np.isnan(raw_all).any() and not np.isnan(cal_all).any()

test_cal = cal_all[test_idx]
holdout = {
    "n": int(len(y_test)),
    "roc_auc": round(float(roc_auc_score(y_test, test_raw)), 4),
    "pr_auc": round(float(average_precision_score(y_test, test_raw)), 4),
    "brier_raw": round(float(brier_score_loss(y_test, test_raw)), 4),
    "brier_calibrated": round(float(brier_score_loss(y_test, test_cal)), 4),
    "ece_calibrated": round(expected_calibration_error(
        y_test.to_numpy(), test_cal), 4),
}
print(f"Holdout (n={holdout['n']}): AUC {holdout['roc_auc']:.4f} | "
      f"PR-AUC {holdout['pr_auc']:.4f} | Brier {holdout['brier_raw']:.4f} "
      f"-> {holdout['brier_calibrated']:.4f} | ECE {holdout['ece_calibrated']:.4f}")

# ── Published per-customer scores (cross-validated, calibrated) ───────
feat["churn_probability_raw"] = raw_all
feat["churn_probability"] = cal_all
feat["churn_risk"] = pd.cut(cal_all, bins=RISK_BINS, labels=RISK_LABELS)
band_counts = feat["churn_risk"].value_counts().reindex(RISK_LABELS).fillna(0)
print("Risk bands:", {k: int(v) for k, v in band_counts.items()})

feat[["customer_id", "segment", "region", "acquisition_channel",
      "total_revenue", "recency_days", "order_frequency",
      "churn_probability", "churn_probability_raw", "churn_risk",
      "churned"]].to_csv(f"{PROC}/churn_features.csv", index=False)
print(f"Churn scores saved for {len(feat):,} customers -> {PROC}/churn_features.csv")

# ── Rolling-origin backtest ───────────────────────────────────────────
# At each origin the whole procedure is re-run: features before the origin,
# label = no purchase in the following 180 days, 5-fold CV within that frame.
# This is the evidence behind any time-based claim; the 80/20 split is not.
backtest = []
for origin in BACKTEST_ORIGINS + [None]:
    frame, cut = build_churn_frame(pd.Timestamp(origin) if origin else None)
    Xb, yb = frame[FEATURES].fillna(0), frame["churned"]
    auc = cross_val_score(clone(models[best_name]), Xb, yb, cv=cv, scoring="roc_auc")
    backtest.append({
        "cutoff": str(cut.date()),
        "n_customers": int(len(frame)),
        "prevalence": round(float(yb.mean()), 4),
        "cv_roc_auc_mean": round(float(auc.mean()), 4),
        "cv_roc_auc_std": round(float(auc.std()), 4),
    })
    print(f"  origin {cut.date()} | n={len(frame):4d} | "
          f"prevalence {yb.mean():.3f} | CV AUC {auc.mean():.4f} ± {auc.std():.4f}")

with open(os.path.join(REPO, "churn_temporal_backtest.json"), "w") as fh:
    json.dump({
        "evaluation": ("rolling-origin backtest: at each cutoff, features use "
                       "purchases strictly before it and the label is no "
                       "purchase in the following 180 days; the selected model "
                       "is re-fit under 5-fold stratified CV within each frame"),
        "model": best_name,
        "horizon_days": HORIZON_DAYS,
        "origins": backtest,
    }, fh, indent=2)

with open(os.path.join(REPO, "churn_model_metrics.json"), "w") as fh:
    json.dump({
        "cutoff": str(CUTOFF.date()),
        "horizon_days": HORIZON_DAYS,
        "purchase_definition": "Delivered or Returned",
        "value_definition": "master_orders.csv (Delivered + Processing)",
        "n_customers": int(len(feat)),
        "prevalence": round(float(y.mean()), 4),
        "cv": cv_rows,
        "selected_model": best_name,
        "holdout": holdout,
        "calibration": ("isotonic fitted on out-of-fold training predictions; "
                        "published scores are cross-validated for training "
                        "customers and holdout predictions for test customers"),
        "risk_bands": {k: int(v) for k, v in band_counts.items()},
        "risk_bins": RISK_BINS,
    }, fh, indent=2)

# ── ROC (selected model, holdout) + feature importance ────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fpr, tpr, _ = roc_curve(y_test, test_raw)
axes[0].plot(fpr, tpr, lw=2, color=PALETTE[0],
             label=f"{best_name} (AUC={holdout['roc_auc']:.3f})")
axes[0].plot([0, 1], [0, 1], 'k--', alpha=0.4)
axes[0].set_xlabel("False Positive Rate")
axes[0].set_ylabel("True Positive Rate")
axes[0].set_title("ROC — held-out 20% (model chosen by 5-fold CV)")
axes[0].legend()

clf = best_model.named_steps["clf"] if hasattr(best_model, "named_steps") else best_model
if hasattr(clf, "feature_importances_"):
    fi = pd.Series(clf.feature_importances_, index=FEATURES).sort_values()
    axes[1].set_title(f"Top Feature Importances ({best_name})")
else:
    fi = pd.Series(clf.coef_[0], index=FEATURES).sort_values()
    axes[1].set_title(f"Top Coefficients ({best_name}, standardised)")
axes[1].barh(fi.index[-12:], fi.values[-12:], color=PALETTE[0])
axes[1].set_xlabel("Importance / coefficient")
plt.tight_layout()
plt.savefig(f"{FIGS}/09_churn_model.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Risk distribution ─────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].bar(band_counts.index, band_counts.values,
            color=["#059669", "#D97706", "#DC2626"])
axes[0].set_title("Customers by Churn Risk Band")
axes[0].set_ylabel("Customer Count")
for i, v in enumerate(band_counts.values):
    axes[0].text(i, v + 5, str(int(v)), ha='center', fontweight='bold')
axes[1].hist(cal_all, bins=40, color=PALETTE[0], edgecolor='white', alpha=0.8)
axes[1].axvline(BAND_MED, color='#D97706', linestyle='--', label='Low/Med')
axes[1].axvline(BAND_HIGH, color='#DC2626', linestyle='--', label='Med/High')
axes[1].set_xlabel("Calibrated Churn Probability")
axes[1].set_ylabel("Customer Count")
axes[1].set_title("Calibrated Churn Probability Distribution")
axes[1].legend()
plt.suptitle("Customer Churn Analysis (leakage-free, cross-validated scores)",
             fontsize=14, y=1.01)
plt.tight_layout()
plt.savefig(f"{FIGS}/10_churn_distribution.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Confusion matrix at the operational threshold (band boundary) ─────
pred_test = (test_cal >= BAND_MED).astype(int)
print(f"\n{best_name} — holdout at threshold {BAND_MED:.2f} "
      "(Medium-risk band boundary):")
print(classification_report(y_test, pred_test, target_names=["Retained", "Churned"],
                            zero_division=0))
cm = confusion_matrix(y_test, pred_test)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=["Retained", "Churned"], yticklabels=["Retained", "Churned"])
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title(f"Confusion Matrix — {best_name} (threshold {BAND_MED:.2f})")
plt.tight_layout()
plt.savefig(f"{FIGS}/11_confusion_matrix.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Cumulative Gains & Lift (the artifact retention teams use) ────────
order_test = np.argsort(-test_cal)
y_sorted = y_test.to_numpy()[order_test]
cum_capture = np.cumsum(y_sorted) / y_sorted.sum() * 100
pct_contacted = np.arange(1, len(y_sorted) + 1) / len(y_sorted) * 100
lift = (cum_capture / 100) / pct_contacted * 100

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(pct_contacted, cum_capture, color=PALETTE[0], lw=2.5,
             label=best_name)
axes[0].plot([0, 100], [0, 100], 'k--', alpha=0.5, label="Random (no model)")
top20 = cum_capture[np.searchsorted(pct_contacted, 20)]
axes[0].axvline(20, color=PALETTE[4], ls=':', alpha=0.6)
axes[0].annotate(f"Top 20% contacted\n≈ {top20:.0f}% of churners",
                 xy=(20, top20), xytext=(35, max(top20 - 25, 5)),
                 arrowprops=dict(arrowstyle="->", color=PALETTE[4]))
axes[0].set_xlabel("% of customers contacted (highest risk first)")
axes[0].set_ylabel("% of churners captured")
axes[0].set_title("Cumulative Gains Chart — Churn (holdout)")
axes[0].legend()

axes[1].plot(pct_contacted, lift, color=PALETTE[2], lw=2.5)
axes[1].axhline(1, color='k', ls='--', alpha=0.5, label="Random (lift = 1)")
axes[1].set_xlabel("% of customers contacted")
axes[1].set_ylabel("Lift over random")
axes[1].set_title("Lift Chart — targeting efficiency")
axes[1].legend()
plt.suptitle(f"Churn targeting: top 20% of customers capture "
             f"~{top20:.0f}% of likely churners", fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig(f"{FIGS}/11b_churn_lift.png", dpi=150, bbox_inches="tight")
plt.close()

print("\nChurn analysis complete. Run 04_revenue_forecasting.py next.")
print("NOTE: the headline AUC is CV/holdout, never in-sample. If it reports "
      "~1.0, a feature is leaking — audit before trusting it.")
