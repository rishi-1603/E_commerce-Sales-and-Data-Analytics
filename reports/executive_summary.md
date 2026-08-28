# Executive Summary
### E-Commerce Sales & Customer Analytics — Boardroom Brief
*Prepared for: CRM / Retention Lead, Category Manager, FP&A  ·  Period covered: Jan 2022 – Dec 2024*

> **Read me first:** This is a one-page, non-technical summary. The full
> methodology, data dictionary, and validation steps live in
> `reports/methodology.md` and `reports/assumptions_and_limitations.md`.
> **Important caveat:** the dataset is **synthetically generated** to
> demonstrate an end-to-end pipeline. The *methods* are production-grade;
> the specific numbers are illustrative, not measured business results.

---

## 1. What was the problem?
The business cannot tell, at any given moment, **which customers are worth
retaining, which are quietly leaving, which products genuinely make money,
and how much revenue to plan for.** Without that, retention budget is spent
evenly instead of targeted, and margin leaks into the wrong products.

## 2. What did the analysis find? (top 3)
1. **Most revenue is concentrated in a small set of customers.** RFM
   segmentation shows Champions + Loyal Customers account for the bulk of
   historical spend — protecting and growing this group is the cheapest
   revenue available.
2. **A meaningful slice of customers is cooling off.** Hundreds of customers
   sit in At-Risk / About-to-Sleep / Lost segments; their **historical** spend
   is large, and their **future** spend is at risk.
3. **Profitability is uneven across the catalog.** A BCG-style view separates
   reliable earners (Cash Cows) from low-margin or loss-making SKUs (Dogs).

## 3. What is the biggest risk?
**Silent churn of high-value customers.** The cost of replacing a lost
customer is several times the cost of keeping one, and right now the business
has no reliable, forward-looking signal for *who* is about to leave.

## 4. What is the biggest opportunity?
**A targeted, measured win-back campaign** aimed at the cooling-off segment,
run against a held-out control group so the business can *prove* the uplift
before scaling spend.

## 5. What should management do? (in priority order)
| # | Action | Owner | Why now |
|---|--------|-------|---------|
| 1 | Run a tiered win-back on At-Risk customers, with a control group | CRM Lead | Protects revenue already at risk; fastest to measure |
| 2 | Stand up a loyalty program for Champions + Loyal | Marketing | Defends the most profitable relationships |
| 3 | Review Dogs/low-margin SKUs for delisting or repricing | Category Mgr | Releases margin trapped in underperformers |

## 6. What metric should we monitor?
- **Retention/reactivation rate** of treated vs. control customers (90-day).
- **Repeat-purchase rate** by cohort.
- **Blended gross margin %** by category.

*These metrics let leadership distinguish "we did something" from "it worked."*

---
*For the evidence behind each finding, see `reports/decision_log.md`.*
