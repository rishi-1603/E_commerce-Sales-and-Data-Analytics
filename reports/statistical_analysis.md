# Statistical Analysis
### Hypothesis tests answering business questions

> **Honesty caveat:** the dataset is synthetic with random, independent assignments. These tests demonstrate **method**. On synthetic data a *non-significant* result is the correct, expected outcome — there is usually no true effect to detect. Significance level used: α = 0.05.

## Test 1 — Do B2B/Enterprise customers spend more per order than B2C?

- **Question:** Is the average order value (AOV) higher for B2B/Enterprise vs B2C?
- **H0:** No difference in AOV between groups.  **H1:** There is a difference.
- **Test:** Welch's independent t-test (does not assume equal variance).
- **B2C AOV:** ₹5,954 (n=6,834)  |  **B2B/Enterprise AOV:** ₹6,000 (n=3,099)
- **t = 0.44, p = 0.6626** · mean diff ₹45 (95% CI ₹-159 to ₹250) · Cohen's d = 0.010
- **Result:** **Not statistically significant** (fail to reject H₀)
- **Effect size:** negligible (d=0.010) — even if significant, is it meaningful?
- **Business read:** A statistically significant *and* large effect would justify segment-specific pricing/marketing. Here, on synthetic data, expect no meaningful effect.

## Test 2 — Does average order value differ across acquisition channels?

- **Question:** Is AOV the same across all acquisition channels?
- **H0:** All channel means are equal.  **H1:** At least one differs.
- **Test:** One-way ANOVA, with Kruskal-Wallis as a non-parametric cross-check (AOV is typically right-skewed).
- **ANOVA:** F = 0.98, p = 0.4335
- **Kruskal-Wallis:** H = 10.25, p = 0.1145 (robust to non-normality)
- **Effect size (η²):** 0.0006 (negligible)
- **Result:** **Not statistically significant** (fail to reject H₀)
- **Business read:** A significant result would tell marketing which channels bring higher-value orders, informing CAC budgeting.

## Test 3 — Is order status (e.g. Returned) independent of discount level?

- **Question:** Do higher-discount orders get returned/cancelled at a different rate?
- **H0:** Status and discount band are independent.  **H1:** They are associated.
- **Test:** Chi-square test of independence.
```
disc_band   No discount  Low (≤10%)  High (>10%)
status                                          
Delivered          3780        3808         1724
Processing          225         283          113
```
- **χ² = 5.87, dof = 2, p = 0.0531**
- **Effect size (Cramér's V):** 0.024 (negligible)
- **Result:** **Not statistically significant** (fail to reject H₀)
- **Business read:** A significant association would warn that aggressive discounting increases returns — a margin leak. **Correlation ≠ causation**; confirm with an A/B test before changing discount policy.

## Test 4 — Outlier detection on order value (IQR method)

- **Q1 = ₹2,288, Q3 = ₹8,516, IQR = ₹6,228**
- **Fence:** ₹-7,055 to ₹17,859
- **Outliers flagged:** 271 of 9,933 orders (2.7%)
- **Max order value:** ₹32,814
- **Business read:** Don't auto-delete outliers — investigate. They may be legit B2B bulk orders (keep) or data-entry errors (fix). The decision matters more than the count.

