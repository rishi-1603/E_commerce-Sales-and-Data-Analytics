"""
03_churn_analysis.py
Customer Churn Prediction using Logistic Regression + Random Forest
Generates churn probability scores for each customer
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                              roc_auc_score, roc_curve, precision_recall_curve)
import os, warnings
warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "docs", "figures")
os.makedirs(PROC, exist_ok=True); os.makedirs(FIGS, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
PALETTE = ["#2563EB","#DB2777","#D97706","#059669","#7C3AED"]

# ── Load ─────────────────────────────────────────────────
print("Loading data...")
master    = pd.read_csv(f"{PROC}/master_orders.csv", parse_dates=["order_date"])
customers = pd.read_csv(os.path.join(BASE,"data","raw","customers.csv"),
                        parse_dates=["registration_date"])
SNAPSHOT  = master["order_date"].max() + pd.Timedelta(days=1)
CHURN_THRESHOLD = 180  # days without purchase = churned

# ── Feature Engineering ───────────────────────────────────
cust_features = master.groupby("customer_id").agg(
    total_orders    =("order_id",    "nunique"),
    total_revenue   =("line_total",  "sum"),
    avg_order_value =("line_total",  "mean"),
    total_items     =("quantity",    "sum"),
    avg_discount    =("discount_pct_x","mean"),
    unique_categories=("category",  "nunique"),
    last_order_date =("order_date",  "max"),
    first_order_date=("order_date",  "min"),
).reset_index()

cust_features["recency_days"] = (SNAPSHOT - cust_features["last_order_date"]).dt.days
cust_features["customer_age_days"] = (
    SNAPSHOT - cust_features["first_order_date"]).dt.days
cust_features["order_frequency"] = (
    cust_features["total_orders"] /
    (cust_features["customer_age_days"] / 30).clip(lower=1))

# Merge customer metadata
cust_features = cust_features.merge(
    customers[["customer_id","segment","region","acquisition_channel","age","gender"]],
    on="customer_id", how="left")

# Label encode categoricals
le = LabelEncoder()
for col in ["segment","region","acquisition_channel","gender"]:
    cust_features[col + "_enc"] = le.fit_transform(cust_features[col].fillna("Unknown"))

# Define churn label
cust_features["churned"] = (
    cust_features["recency_days"] > CHURN_THRESHOLD).astype(int)

print(f"\nChurn rate: {cust_features['churned'].mean()*100:.1f}%")

# ── Prepare Features ──────────────────────────────────────
FEATURES = [
    "total_orders","total_revenue","avg_order_value","total_items",
    "avg_discount","unique_categories","recency_days","customer_age_days",
    "order_frequency","age","segment_enc","region_enc",
    "acquisition_channel_enc","gender_enc"
]
X = cust_features[FEATURES].fillna(0)
y = cust_features["churned"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

scaler  = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# ── Models ────────────────────────────────────────────────
models = {
    "Logistic Regression": LogisticRegression(max_iter=500, random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
    "Gradient Boosting":   GradientBoostingClassifier(n_estimators=100, random_state=42),
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
    print(classification_report(y_test, preds, target_names=["Active","Churned"]))

# Best model = Random Forest
best = results["Random Forest"]
rf_model = best["model"]

# ── Churn Probabilities for all customers ─────────────────
all_proba = rf_model.predict_proba(X.values)[:, 1]
cust_features["churn_probability"] = all_proba
cust_features["churn_risk"] = pd.cut(
    all_proba, bins=[0, 0.3, 0.6, 1.0],
    labels=["Low Risk","Medium Risk","High Risk"])

cust_features.to_csv(f"{PROC}/churn_features.csv", index=False)
print(f"\nChurn scores saved for {len(cust_features):,} customers")

# ── Plot 1: ROC Curves ────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for i, (name, res) in enumerate(results.items()):
    fpr, tpr, _ = roc_curve(y_test, res["proba"])
    axes[0].plot(fpr, tpr, lw=2, label=f"{name} (AUC={res['auc']:.3f})",
                 color=PALETTE[i])
axes[0].plot([0,1],[0,1],'k--', alpha=0.4)
axes[0].set_xlabel("False Positive Rate"); axes[0].set_ylabel("True Positive Rate")
axes[0].set_title("ROC Curve Comparison"); axes[0].legend()

# Feature Importance
fi = pd.Series(rf_model.feature_importances_, index=FEATURES).sort_values(ascending=True)
axes[1].barh(fi.index[-12:], fi.values[-12:], color=PALETTE[0])
axes[1].set_title("Top Feature Importances (Random Forest)")
axes[1].set_xlabel("Importance")
plt.tight_layout()
plt.savefig(f"{FIGS}/09_churn_model.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 2: Churn Risk Distribution ───────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
risk_counts = cust_features["churn_risk"].value_counts()
axes[0].bar(risk_counts.index, risk_counts.values,
            color=["#059669","#D97706","#DC2626"])
axes[0].set_title("Customers by Churn Risk Band")
axes[0].set_ylabel("Customer Count")
for i, v in enumerate(risk_counts.values):
    axes[0].text(i, v+5, str(v), ha='center', fontweight='bold')

axes[1].hist(all_proba, bins=40, color=PALETTE[0], edgecolor='white', alpha=0.8)
axes[1].axvline(0.3, color='#D97706', linestyle='--', label='Low/Med threshold')
axes[1].axvline(0.6, color='#DC2626', linestyle='--', label='Med/High threshold')
axes[1].set_xlabel("Churn Probability")
axes[1].set_ylabel("Customer Count")
axes[1].set_title("Churn Probability Distribution")
axes[1].legend()
plt.suptitle("Customer Churn Analysis", fontsize=14, y=1.01)
plt.tight_layout()
plt.savefig(f"{FIGS}/10_churn_distribution.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Confusion Matrix ──────────────────────────────────────
cm = confusion_matrix(y_test, best["preds"])
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=["Active","Churned"], yticklabels=["Active","Churned"])
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
ax.set_title("Confusion Matrix — Random Forest")
plt.tight_layout()
plt.savefig(f"{FIGS}/11_confusion_matrix.png", dpi=150, bbox_inches="tight")
plt.close()

print("\nChurn analysis complete. Run 04_revenue_forecasting.py next.")
