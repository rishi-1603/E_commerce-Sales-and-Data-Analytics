"""
03_churn_analysis.py  —  LEAKAGE-FREE customer churn prediction
================================================================
FIX (2026 review): the previous version derived the churn label from
`recency_days` while ALSO feeding `recency_days` to the model as a feature.
Because the label was a direct function of one feature, all three models
reported AUC = 1.0 — that was target leakage, not predictive power.

This version uses a proper FORWARD-TIME (temporal) split:

    CUTOFF = 2024-07-01   (6 months before the last order date)
    FEATURES = customer behaviour computed ONLY from orders before CUTOFF
    LABEL    = 1 if the customer made NO purchase in the 180 days AFTER CUTOFF

Features are built from the past; the label lives in the future. A model can
no longer "cheat" by reading the rule used to define churn. An honest churn
model on this dataset should land around AUC 0.65–0.80. If it reports ~1.0,
something is leaking again.

Run:  python python/churn/03_churn_analysis.py   (after run_pipeline step 2)
"""
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, roc_curve)

warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROC = os.path.join(BASE, "data", "processed")
RAW  = os.path.join(BASE, "data", "raw")
FIGS = os.path.join(BASE, "docs", "figures")
os.makedirs(PROC, exist_ok=True)
os.makedirs(FIGS, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
PALETTE = ["#2563EB", "#DB2777", "#D97706", "#059669", "#7C3AED"]

# ── Load ──────────────────────────────────────────────────────────────
print("Loading data...")
master    = pd.read_csv(f"{PROC}/master_orders.csv", parse_dates=["order_date"])
customers = pd.read_csv(os.path.join(RAW, "customers.csv"),
                        parse_dates=["registration_date"])

# ── Temporal split setup ──────────────────────────────────────────────
DATA_END   = master["order_date"].max()                 # 2024-12-31
CUTOFF     = DATA_END - pd.Timedelta(days=180)          # ~2024-07-04
HORIZON    = 180                                        # label window (days)
print(f"Data end: {DATA_END.date()} | CUTOFF (feature cutoff): "
      f"{CUTOFF.date()} | Label window: +{HORIZON}d")

past   = master[master["order_date"] < CUTOFF].copy()
future = master[master["order_date"] >= CUTOFF].copy()

# Customers who purchased at least once before the cutoff are eligible.
eligible = set(past["customer_id"].unique())

# ── Features: behaviour BEFORE the cutoff only ────────────────────────
feat = past.groupby("customer_id").agg(
    total_orders        =("order_id", "nunique"),
    total_revenue       =("line_total", "sum"),
    avg_order_value     =("line_total", "mean"),
    total_items         =("quantity", "sum"),
    avg_discount        =("discount_pct_x", "mean"),
    unique_categories   =("category", "nunique"),
    first_order_date    =("order_date", "min"),
    last_order_date     =("order_date", "max"),
).reset_index()

# Recency is measured RELATIVE TO THE CUTOFF, not "today". This is legitimate
# signal (recent buyers churn less) — it is NOT leakage because the label
# is defined on the *future* window, not on recency itself.
feat["recency_days"]     = (CUTOFF - feat["last_order_date"]).dt.days
feat["tenure_days"]      = (CUTOFF - feat["first_order_date"]).dt.days
feat["order_frequency"]  = feat["total_orders"] / (feat["tenure_days"] / 30).clip(lower=1)
feat["avg_days_between"] = feat["tenure_days"] / feat["total_orders"].clip(lower=1)

# Demographic context
feat = feat.merge(
    customers[["customer_id", "segment", "region", "acquisition_channel", "age", "gender"]],
    on="customer_id", how="left")

le = LabelEncoder()
for col in ["segment", "region", "acquisition_channel", "gender"]:
    feat[col + "_enc"] = le.fit_transform(feat[col].fillna("Unknown"))

# ── Label: any purchase in the 180 days AFTER the cutoff? ─────────────
future_buyers = set(future.loc[future["customer_id"].isin(eligible), "customer_id"].unique())
feat["churned"] = (~feat["customer_id"].isin(future_buyers)).astype(int)

print(f"Eligible customers: {len(feat):,}")
print(f"Churn rate (no purchase in +{HORIZON}d): {feat['churned'].mean()*100:.1f}%")

# ── Model matrix ──────────────────────────────────────────────────────
FEATURES = [
    "total_orders", "total_revenue", "avg_order_value", "total_items",
    "avg_discount", "unique_categories", "recency_days", "tenure_days",
    "order_frequency", "avg_days_between", "age",
    "segment_enc", "region_enc", "acquisition_channel_enc", "gender_enc",
]
X = feat[FEATURES].fillna(0)
y = feat["churned"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

scaler   = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

models = {
    "Logistic Regression": LogisticRegression(max_iter=500, random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=200, random_state=42),
    "Gradient Boosting":   GradientBoostingClassifier(n_estimators=200, random_state=42),
}

results = {}
for name, model in models.items():
    Xs = X_train_s if name == "Logistic Regression" else X_train.values
    model.fit(Xs, y_train)
    Xt = X_test_s  if name == "Logistic Regression" else X_test.values
    preds = model.predict(Xt)
    proba = model.predict_proba(Xt)[:, 1]
    auc   = roc_auc_score(y_test, proba)
    results[name] = {"model": model, "preds": preds, "proba": proba, "auc": auc}
    print(f"\n{name} — AUC: {auc:.4f}")
    print(classification_report(y_test, preds, target_names=["Retained", "Churned"]))

# Pick best by held-out AUC
best_name = max(results, key=lambda n: results[n]["auc"])
best = results[best_name]
print(f"\nBest model by held-out AUC: {best_name} ({best['auc']:.4f})")

# ── Cross-validated AUC (more robust than a single split) ─────────────
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_auc = cross_val_score(best["model"], X.values, y, cv=cv, scoring="roc_auc")
print(f"5-fold CV AUC ({best_name}): {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")
print("  (Headline = CV mean ± std. A single split can mislead; CV shows stability.)")

# ── Calibrated-ish risk bands + per-customer scores (refit best on all) ─
best_model = results[best_name]["model"]
if best_name == "Logistic Regression":
    best_model.fit(scaler.fit_transform(X), y)
    all_proba = best_model.predict_proba(scaler.transform(X))[:, 1]
else:
    best_model.fit(X.values, y)
    all_proba = best_model.predict_proba(X.values)[:, 1]

feat["churn_probability"] = all_proba
feat["churn_risk"] = pd.cut(
    all_proba, bins=[-0.001, 0.33, 0.66, 1.0],
    labels=["Low Risk", "Medium Risk", "High Risk"])

feat[["customer_id", "segment", "region", "acquisition_channel",
       "total_revenue", "recency_days", "order_frequency",
       "churn_probability", "churn_risk", "churned"]].to_csv(
    f"{PROC}/churn_features.csv", index=False)
print(f"\nChurn scores saved for {len(feat):,} customers -> {PROC}/churn_features.csv")

# ── ROC + Feature importance ──────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for i, (name, res) in enumerate(results.items()):
    fpr, tpr, _ = roc_curve(y_test, res["proba"])
    axes[0].plot(fpr, tpr, lw=2, label=f"{name} (AUC={res['auc']:.3f})", color=PALETTE[i])
axes[0].plot([0, 1], [0, 1], 'k--', alpha=0.4)
axes[0].set_xlabel("False Positive Rate")
axes[0].set_ylabel("True Positive Rate")
axes[0].set_title("ROC — Forward-Time Churn Model")
axes[0].legend()

if hasattr(best_model, "feature_importances_"):
    fi = pd.Series(best_model.feature_importances_, index=FEATURES).sort_values()
    axes[1].barh(fi.index[-12:], fi.values[-12:], color=PALETTE[0])
    axes[1].set_title(f"Top Feature Importances ({best_name})")
    axes[1].set_xlabel("Importance")
else:
    co = pd.Series(best_model.coef_[0], index=FEATURES).sort_values()
    axes[1].barh(co.index[-12:], co.values[-12:], color=PALETTE[0])
    axes[1].set_title(f"Top Coefficients ({best_name})")
plt.tight_layout()
plt.savefig(f"{FIGS}/09_churn_model.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Risk distribution ─────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
risk_counts = feat["churn_risk"].value_counts().reindex(["Low Risk", "Medium Risk", "High Risk"])
axes[0].bar(risk_counts.index, risk_counts.values, color=["#059669", "#D97706", "#DC2626"])
axes[0].set_title("Customers by Churn Risk Band")
axes[0].set_ylabel("Customer Count")
for i, v in enumerate(risk_counts.values):
    axes[0].text(i, v + 5, str(v), ha='center', fontweight='bold')
axes[1].hist(all_proba, bins=40, color=PALETTE[0], edgecolor='white', alpha=0.8)
axes[1].axvline(0.33, color='#D97706', linestyle='--', label='Low/Med')
axes[1].axvline(0.66, color='#DC2626', linestyle='--', label='Med/High')
axes[1].set_xlabel("Churn Probability")
axes[1].set_ylabel("Customer Count")
axes[1].set_title("Churn Probability Distribution")
axes[1].legend()
plt.suptitle("Customer Churn Analysis (leakage-free)", fontsize=14, y=1.01)
plt.tight_layout()
plt.savefig(f"{FIGS}/10_churn_distribution.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Confusion matrix (best model on test) ─────────────────────────────
cm = confusion_matrix(y_test, best["preds"])
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=["Retained", "Churned"], yticklabels=["Retained", "Churned"])
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title(f"Confusion Matrix — {best_name}")
plt.tight_layout()
plt.savefig(f"{FIGS}/11_confusion_matrix.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Cumulative Gains & Lift chart (the artifact retention teams use) ──
# Answers: "If I can only contact the top X% of customers, what share of
# likely churners do I capture?" This is how campaign size gets decided.
order_test = np.argsort(-best["proba"])             # highest risk first
y_sorted = y_test.values[order_test]
cum_capture = np.cumsum(y_sorted) / y_sorted.sum() * 100
pct_contacted = np.arange(1, len(y_sorted) + 1) / len(y_sorted) * 100
base_rate = y_test.mean()
lift = (cum_capture / 100) / pct_contacted * 100     # lift vs random

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(pct_contacted, cum_capture, color=PALETTE[0], lw=2.5,
             label=f"{best_name}")
axes[0].plot([0, 100], [0, 100], 'k--', alpha=0.5, label="Random (no model)")
top_decile = cum_capture[np.searchsorted(pct_contacted, 20)]
axes[0].axvline(20, color=PALETTE[4], ls=':', alpha=0.6)
axes[0].annotate(f"Top 20% contacted\n≈ {top_decile:.0f}% of churners",
                 xy=(20, top_decile), xytext=(35, top_decile - 25),
                 arrowprops=dict(arrowstyle="->", color=PALETTE[4]))
axes[0].set_xlabel("% of customers contacted (highest risk first)")
axes[0].set_ylabel("% of churners captured")
axes[0].set_title("Cumulative Gains Chart — Churn")
axes[0].legend()

axes[1].plot(pct_contacted, lift, color=PALETTE[2], lw=2.5)
axes[1].axhline(1, color='k', ls='--', alpha=0.5, label="Random (lift = 1)")
axes[1].set_xlabel("% of customers contacted")
axes[1].set_ylabel("Lift over random")
axes[1].set_title("Lift Chart — targeting efficiency")
axes[1].legend()
plt.suptitle(f"Churn targeting: top 20% of customers capture "
             f"~{top_decile:.0f}% of likely churners", fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig(f"{FIGS}/11b_churn_lift.png", dpi=150, bbox_inches="tight")
plt.close()

print("\nChurn analysis complete. Run 04_revenue_forecasting.py next.")
print("NOTE: AUC is now an honest number (~0.65–0.80). If it is ~1.0, a "
      "feature is leaking — audit before trusting it.")
