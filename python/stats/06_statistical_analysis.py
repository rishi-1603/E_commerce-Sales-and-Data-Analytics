"""
06_statistical_analysis.py — Hypothesis testing that answers business questions
===============================================================================
PURPOSE: Fill the #1 missing skill in most data-analyst portfolios — moving from
"here is a chart" to "here is a statistically defensible answer."

Every test below follows the same discipline:
    1. State a business question.
    2. Pick the right test (and state WHY).
    3. Check assumptions (normality, equal variance, independence).
    4. Report statistic, p-value, effect size, CI.
    5. Give a plain-language business interpretation.

CRITICAL HONESTY CAVEAT:
    The dataset is SYNTHETIC and its variables are assigned independently at
    random. So these tests primarily demonstrate METHOD. On real data the same
    code yields real findings; here a non-significant result is the EXPECTED,
    CORRECT outcome (there is no true effect to detect). A significant result
    on this data would itself be a flag worth inspecting.

Outputs:
    docs/figures/14_statistical_tests.png
    reports/statistical_analysis.md
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "docs", "figures")
REPO = os.path.join(BASE, "reports")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(REPO, exist_ok=True)

ALPHA = 0.05
report = ["# Statistical Analysis",
          "### Hypothesis tests answering business questions",
          "",
          "> **Honesty caveat:** the dataset is synthetic with random, "
          "independent assignments. These tests demonstrate **method**. "
          "On synthetic data a *non-significant* result is the correct, "
          "expected outcome — there is usually no true effect to detect. "
          "Significance level used: α = 0.05.",
          ""]


def interpret(p, alpha=ALPHA):
    return ("**Statistically significant** (reject H₀)" if p < alpha
            else "**Not statistically significant** (fail to reject H₀)")


# ── Load ──────────────────────────────────────────────────────────────
master = pd.read_csv(f"{PROC}/master_orders.csv", parse_dates=["order_date"])
customers = pd.read_csv(os.path.join(BASE, "data", "raw", "customers.csv"))

# Per-order value (line-level revenue per order)
order_val = master.groupby("order_id").agg(
    value=("line_total", "sum"),
    discount=("discount_pct_x", "mean"),
    segment=("segment", "first"),
    channel=("acquisition_channel", "first"),
    region=("region", "first"),
).reset_index()

print(f"Orders for testing: {len(order_val):,}")

# ── TEST 1: Do B2B/Enterprise customers have higher AOV than B2C? ─────
report.append("## Test 1 — Do B2B/Enterprise customers spend more per order than B2C?")
report.append("")
report.append("- **Question:** Is the average order value (AOV) higher for B2B/Enterprise vs B2C?")
report.append("- **H0:** No difference in AOV between groups.  **H1:** There is a difference.")
report.append("- **Test:** Welch's independent t-test (does not assume equal variance).")
b2c = order_val.loc[order_val["segment"] == "B2C", "value"]
b2b = order_val.loc[order_val["segment"].isin(["B2B", "Enterprise"]), "value"]
# assumption check (Shapiro on a sample for normality note)
_, p_norm = stats.shapiro(b2c.sample(min(5000, len(b2c)), random_state=42))
t_stat, p_val = stats.ttest_ind(b2b, b2c, equal_var=False)
# effect size (Cohen's d) + 95% CI for the mean difference
pooled = np.sqrt(((len(b2b)-1)*b2b.std()**2 + (len(b2c)-1)*b2c.std()**2)
                 / (len(b2b)+len(b2c)-2))
cohens_d = (b2b.mean() - b2c.mean()) / pooled if pooled else float("nan")
diff = b2b.mean() - b2c.mean()
se = np.sqrt(b2b.var()/len(b2b) + b2c.var()/len(b2c))
ci_lo, ci_hi = diff - 1.96*se, diff + 1.96*se
report += [
    f"- **B2C AOV:** ₹{b2c.mean():,.0f} (n={len(b2c):,})  |  "
    f"**B2B/Enterprise AOV:** ₹{b2b.mean():,.0f} (n={len(b2b):,})",
    f"- **t = {t_stat:.2f}, p = {p_val:.4f}** · mean diff ₹{diff:,.0f} "
    f"(95% CI ₹{ci_lo:,.0f} to ₹{ci_hi:,.0f}) · Cohen's d = {cohens_d:.3f}",
    f"- **Result:** {interpret(p_val)}",
    f"- **Effect size:** {'negligible' if abs(cohens_d) < 0.2 else 'small' if abs(cohens_d) < 0.5 else 'medium' if abs(cohens_d) < 0.8 else 'large'} "
    f"(d={abs(cohens_d):.3f}) — even if significant, is it meaningful?",
    "- **Business read:** A statistically significant *and* large effect would "
    "justify segment-specific pricing/marketing. Here, on synthetic data, expect "
    "no meaningful effect.",
    ""]

# ── TEST 2: Does AOV differ across acquisition channels? (ANOVA) ──────
report.append("## Test 2 — Does average order value differ across acquisition channels?")
report.append("")
report.append("- **Question:** Is AOV the same across all acquisition channels?")
report.append("- **H0:** All channel means are equal.  **H1:** At least one differs.")
report.append("- **Test:** One-way ANOVA, with Kruskal-Wallis as a non-parametric cross-check "
              "(AOV is typically right-skewed).")
groups = [g["value"].values for _, g in order_val.groupby("channel") if len(g) > 30]
f_stat, p_anova = stats.f_oneway(*groups)
h_stat, p_kw = stats.kruskal(*groups)
# effect size eta-squared (approx)
ss_between = sum(len(g)*(g.mean()-order_val["value"].mean())**2 for g in groups)
ss_total = ((order_val["value"]-order_val["value"].mean())**2).sum()
eta2 = ss_between/ss_total if ss_total else float("nan")
report += [
    f"- **ANOVA:** F = {f_stat:.2f}, p = {p_anova:.4f}",
    f"- **Kruskal-Wallis:** H = {h_stat:.2f}, p = {p_kw:.4f} (robust to non-normality)",
    f"- **Effect size (η²):** {eta2:.4f} "
    f"({'negligible' if eta2 < 0.01 else 'small' if eta2 < 0.06 else 'medium' if eta2 < 0.14 else 'large'})",
    f"- **Result:** {interpret(p_anova)}",
    "- **Business read:** A significant result would tell marketing which channels "
    "bring higher-value orders, informing CAC budgeting.",
    ""]

# ── TEST 3: Is order status independent of discount level? (Chi-square) ─
report.append("## Test 3 — Is order status (e.g. Returned) independent of discount level?")
report.append("")
report.append("- **Question:** Do higher-discount orders get returned/cancelled at a different rate?")
report.append("- **H0:** Status and discount band are independent.  **H1:** They are associated.")
report.append("- **Test:** Chi-square test of independence.")
orders_full = master.groupby("order_id").agg(
    status=("status", "first"),
    discount=("discount_pct_x", "mean")).reset_index()
orders_full["disc_band"] = pd.cut(orders_full["discount"], bins=[-0.01, 0, 0.1, 0.21],
                                  labels=["No discount", "Low (≤10%)", "High (>10%)"])
ct = pd.crosstab(orders_full["status"], orders_full["disc_band"])
chi2, p_chi, dof, _ = stats.chi2_contingency(ct)
cramers_v = np.sqrt(chi2 / (len(orders_full) * (min(ct.shape)-1)))
report += [
    "```",
    ct.to_string(),
    "```",
    f"- **χ² = {chi2:.2f}, dof = {dof}, p = {p_chi:.4f}**",
    f"- **Effect size (Cramér's V):** {cramers_v:.3f} "
    f"({'negligible' if cramers_v < 0.1 else 'small' if cramers_v < 0.3 else 'medium' if cramers_v < 0.5 else 'large'})",
    f"- **Result:** {interpret(p_chi)}",
    "- **Business read:** A significant association would warn that aggressive "
    "discounting increases returns — a margin leak. **Correlation ≠ causation**; "
    "confirm with an A/B test before changing discount policy.",
    ""]

# ── TEST 4: Outlier detection on order value (IQR method) ────────────
report.append("## Test 4 — Outlier detection on order value (IQR method)")
report.append("")
q1, q3 = order_val["value"].quantile([0.25, 0.75])
iqr = q3 - q1
lo, hi = q1 - 1.5*iqr, q3 + 1.5*iqr
outliers = order_val[(order_val["value"] < lo) | (order_val["value"] > hi)]
report += [
    f"- **Q1 = ₹{q1:,.0f}, Q3 = ₹{q3:,.0f}, IQR = ₹{iqr:,.0f}**",
    f"- **Fence:** ₹{lo:,.0f} to ₹{hi:,.0f}",
    f"- **Outliers flagged:** {len(outliers):,} of {len(order_val):,} orders "
    f"({len(outliers)/len(order_val)*100:.1f}%)",
    f"- **Max order value:** ₹{order_val['value'].max():,.0f}",
    "- **Business read:** Don't auto-delete outliers — investigate. They may be "
    "legit B2B bulk orders (keep) or data-entry errors (fix). The decision matters "
    "more than the count.",
    ""]

# ── Save report ───────────────────────────────────────────────────────
with open(f"{REPO}/statistical_analysis.md", "w") as f:
    f.write("\n".join(report) + "\n")

# ── Chart: AOV by channel with confidence intervals ───────────────────
ch = order_val.groupby("channel")["value"].agg(["mean", "sem", "count"]).reset_index()
ch["ci95"] = 1.96 * ch["sem"]
ch = ch.sort_values("mean")

fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh(ch["channel"], ch["mean"], xerr=ch["ci95"],
               color="#2563EB", alpha=0.85, edgecolor="white",
               error_kw={"ecolor": "#1e3a8a", "capsize": 4})
ax.set_xlabel("Average Order Value (₹)  ±  95% CI")
ax.set_title("AOV by Acquisition Channel with 95% Confidence Intervals\n"
             "(overlap of CIs ≈ visual cue for non-significance)",
             fontsize=12)
for bar, val in zip(bars, ch["mean"]):
    ax.text(val + ch["ci95"].max()*0.1, bar.get_y()+bar.get_height()/2,
            f"₹{val:,.0f}", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(f"{FIGS}/14_statistical_tests.png", dpi=150, bbox_inches="tight")
plt.close()

print("Statistical analysis complete.")
print(f"  Report: {REPO}/statistical_analysis.md")
print(f"  Chart : {FIGS}/14_statistical_tests.png")
print("\nKey p-values:")
print(f"  Test 1 (B2B vs B2C AOV):  p = {p_val:.4f}")
print(f"  Test 2 (AOV ~ channel):   p = {p_anova:.4f}")
print(f"  Test 3 (status ~ disc):   p = {p_chi:.4f}")
