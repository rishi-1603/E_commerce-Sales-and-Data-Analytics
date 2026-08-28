"""
02_rfm_segmentation.py
Customer Segmentation via RFM (Recency, Frequency, Monetary) Analysis
K-Means Clustering overlay on RFM segments
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import os, warnings
warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "docs", "figures")
os.makedirs(PROC, exist_ok=True); os.makedirs(FIGS, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
PALETTE = ["#2563EB","#7C3AED","#DB2777","#D97706","#059669","#DC2626","#0891B2","#65A30D"]

# ── Load ─────────────────────────────────────────────────
print("Loading master dataset...")
master = pd.read_csv(f"{PROC}/master_orders.csv", parse_dates=["order_date"])
SNAPSHOT = master["order_date"].max() + pd.Timedelta(days=1)

# ── Compute RFM ───────────────────────────────────────────
rfm = master.groupby("customer_id").agg(
    recency   =("order_date", lambda x: (SNAPSHOT - x.max()).days),
    frequency =("order_id",   "nunique"),
    monetary  =("line_total", "sum")
).reset_index()

# Score 1–5 (5 = best)
rfm["R"] = pd.qcut(rfm["recency"],   5, labels=[5,4,3,2,1]).astype(int)
rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
rfm["M"] = pd.qcut(rfm["monetary"],  5, labels=[1,2,3,4,5]).astype(int)
rfm["rfm_score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)
rfm["rfm_total"] = rfm["R"] + rfm["F"] + rfm["M"]

# ── Segment Map ───────────────────────────────────────────
def segment(row):
    r, f, m = row["R"], row["F"], row["M"]
    if r >= 4 and f >= 4 and m >= 4:   return "Champions"
    if r >= 3 and f >= 3:               return "Loyal Customers"
    if r >= 4 and f <= 2:               return "Recent Customers"
    if r >= 3 and m >= 3:               return "Potential Loyalists"
    if r <= 2 and f >= 4:               return "At Risk"
    if r <= 2 and f >= 2:               return "About To Sleep"
    if r == 1:                           return "Lost Customers"
    return "Needs Attention"

rfm["segment"] = rfm.apply(segment, axis=1)

# ── K-Means Clustering ────────────────────────────────────
scaler = StandardScaler()
X = scaler.fit_transform(rfm[["recency","frequency","monetary"]])

inertias = []
silhouettes = []
K_range = range(2, 9)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    inertias.append(km.inertia_)
    silhouettes.append(silhouette_score(X, labels))

# Choose k by silhouette score (data-driven), not a hardcoded constant.
best_k = list(K_range)[int(np.argmax(silhouettes))]
print(f"Silhouette scores by k: {dict(zip(K_range, [round(s,3) for s in silhouettes]))}")
print(f"Chosen k={best_k} (highest silhouette) — was previously hardcoded to 5")
km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
rfm["cluster"] = km_final.fit_predict(X)

# PCA for 2-D viz
pca   = PCA(n_components=2)
X_pca = pca.fit_transform(X)
rfm["pca1"] = X_pca[:, 0]
rfm["pca2"] = X_pca[:, 1]

# ── Save ─────────────────────────────────────────────────
rfm.to_csv(f"{PROC}/rfm_segments.csv", index=False)
print(f"RFM table saved: {len(rfm):,} customers")
print(rfm["segment"].value_counts().to_string())

# ── Plot 1: Segment Distribution ──────────────────────────
seg_counts = rfm["segment"].value_counts()
colors_seg = PALETTE[:len(seg_counts)]
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

axes[0].barh(seg_counts.index, seg_counts.values, color=colors_seg)
axes[0].set_xlabel("Customer Count")
axes[0].set_title("Customer Count by RFM Segment")
for i, (idx, val) in enumerate(seg_counts.items()):
    axes[0].text(val + 5, i, str(val), va='center', fontsize=10)

seg_rev = rfm.groupby("segment")["monetary"].sum().sort_values(ascending=False)
axes[1].barh(seg_rev.index, seg_rev.values/1e6, color=PALETTE[:len(seg_rev)])
axes[1].set_xlabel("Revenue (₹ Millions)")
axes[1].set_title("Revenue Contribution by Segment")

plt.suptitle("RFM Customer Segmentation", fontsize=15, y=1.01)
plt.tight_layout()
plt.savefig(f"{FIGS}/05_rfm_segments.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 2: RFM Bubble Chart ──────────────────────────────
seg_summary = rfm.groupby("segment").agg(
    avg_recency =("recency",   "mean"),
    avg_frequency=("frequency","mean"),
    avg_monetary =("monetary", "mean"),
    count=("customer_id","count")
).reset_index()

fig, ax = plt.subplots(figsize=(12, 8))
scatter_colors = PALETTE[:len(seg_summary)]
for i, row in seg_summary.iterrows():
    ax.scatter(row["avg_recency"], row["avg_frequency"],
               s=row["avg_monetary"]/30, alpha=0.7,
               color=scatter_colors[i % len(scatter_colors)],
               edgecolors='white', linewidth=1.5)
    ax.annotate(row["segment"],
                (row["avg_recency"], row["avg_frequency"]),
                textcoords="offset points", xytext=(8, 8),
                fontsize=9, fontweight='bold')

ax.set_xlabel("Avg Recency (days ago)", fontsize=12)
ax.set_ylabel("Avg Purchase Frequency", fontsize=12)
ax.set_title("RFM Segment Map\n(bubble size = avg monetary value)", fontsize=14, pad=10)
ax.invert_xaxis()
plt.tight_layout()
plt.savefig(f"{FIGS}/06_rfm_bubble.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 3: K-Means Elbow ────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(list(K_range), inertias, marker='o', color=PALETTE[0], lw=2.5, ms=8)
ax.axvline(best_k, color=PALETTE[2], linestyle='--', alpha=0.7, label=f'Chosen k={best_k}')
ax.set_xlabel("Number of Clusters (k)")
ax.set_ylabel("Inertia")
ax.set_title("K-Means Elbow Curve", fontsize=13)
ax.legend()
plt.tight_layout()
plt.savefig(f"{FIGS}/07_kmeans_elbow.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 4: PCA Cluster Plot ──────────────────────────────
fig, ax = plt.subplots(figsize=(10, 7))
cluster_colors = PALETTE[:best_k]
for cl in range(best_k):
    mask = rfm["cluster"] == cl
    ax.scatter(rfm.loc[mask,"pca1"], rfm.loc[mask,"pca2"],
               alpha=0.5, s=25, color=cluster_colors[cl], label=f"Cluster {cl}")
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% var)")
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% var)")
ax.set_title("K-Means Customer Clusters (PCA projection)", fontsize=13)
ax.legend(title="Cluster", bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()
plt.savefig(f"{FIGS}/08_kmeans_clusters.png", dpi=150, bbox_inches="tight")
plt.close()

print("\nRFM segmentation complete. Run 03_churn_analysis.py next.")
