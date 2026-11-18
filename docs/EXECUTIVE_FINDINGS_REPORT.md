# Executive Findings & Business Recommendations Report
**Target Audience:** Commercial Leadership, VP of E-Commerce, Head of Product
**Author:** Rishi Dappu, Data Analyst
**Dataset Scope:** Rs. 5.93 Cr in Gross Sales, 9,933 Valid Orders, 1,991 Customers

---

## 1. Executive Summary
This analysis evaluates 36 months (2022-2024) of synthetic retail transaction records across customer cohorts, SKU pricing sensitivity, and logistics operations. The dataset is disclosed as synthetic and seeded; the methods transfer but the numbers are illustrative.

The investigation covers three areas: dormant-customer risk in cooling-off segments, discount margin economics, and returns/cancellation handling.

---

## 2. Key Analytical Findings

### Finding 1: Customer Retention & Cooling-Off Spend Exposure
- **Observation:** Cohort analysis identified that **448 previously high-value customers** have had zero purchase activity in the last 90+ days.
- **Financial Dimension:** These 448 accounts historically contributed **Rs. 1.24 Cr** (20.9% of cumulative sales).
- **Underlying Driver:** Reported onboarding drop-off between order 2 and order 3 (see limitations).

### Finding 2: Discount Margin Economics & Observed Response
- **Observation:** Statistical testing across discount depths found **no statistically significant quantity response** to discount depth (Kruskal-Wallis p = 0.305).
- **Financial Dimension:** Because the synthetic generator assigns discounts randomly, the observed margin erosion is a demonstration of the cost model, not a measured causal leak. The break-even analysis quantifies the volume lift required for each depth to hold margin.

### Finding 3: Returns & Cancellations
- **Observation:** Returns and cancellations are quantified at the order level; returned-basket value is computed from raw order status.
- **Financial Dimension:** Return/cancellation exposure is tracked as a margin-relevant operational cost.

---

## 3. Concrete Business Recommendations

### Recommendation 1: Implement Automated Tiered Win-Back Campaigns
- **Action:** Transition from mass email blasts to an automated 60-day and 90-day RFM trigger workflow. Offer targeted 10% personalized replenishment incentives to the 448 cooling-off accounts before they transition into permanent churn.
- **Projected Impact:** Design-only estimate under stated assumptions (contact cost Rs. 250, recovery 15%, retained value Rs. 12,931). No campaign has been run; projected recovered revenue is illustrative.

### Recommendation 2: Cap Blanket Promotional Discounts
- **Action:** Restrict aggressive discounting; substitute blanket markdowns with bundle thresholds (e.g., minimum cart value for free express shipping).
- **Projected Impact:** The break-even table quantifies the volume lift needed at each depth to hold margin; a 10% cap was modelled to recover approximately Rs. 6.45L in margin.

---

## 4. Methodological Limitations
1. **Synthetic Nature:** Revenue and customer profiles reflect a calibrated synthetic distribution. Methods transfer; numbers do not.
2. **Fixed-Volume Assumption:** Discount elasticity scenarios model immediate unit economics and assume competitor pricing remains static.
3. **Processing Orders:** Revenue basis includes Delivered + Processing orders; Processing orders are not yet fulfilled. Separately reported.
4. **Evaluation Status:** Churn scoring, purchase definitions, and statistical tests have been corrected to align with raw-source semantics (see `docs/AUDIT_2026-11-18.md`).

---

## 5. Verification Status
All findings above are supported by reproducible artifacts in `reports/`, `data/`, `docs/` and pinned by the 235-test suite plus the AI evaluation harness. See `docs/AUDIT_2026-11-18.md` for the final ledger.
