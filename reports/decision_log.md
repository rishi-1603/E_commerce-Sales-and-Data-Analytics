# Key Decisions Supported
### Decision Log — what evidence leads to what action

> This is the layer that separates an **analytics deliverable** from a student
> assignment. Every recommendation is traced back to evidence, assigned an
> owner, a KPI, and an expected outcome that can be checked later.
> **Honesty note:** figures below come from synthetic data and are
> illustrative. The *structure* (problem → evidence → decision → KPI) is what
> transfers to a real engagement.

---

## Decision 1 — Tiered win-back for cooling-off customers
| Field | Detail |
|-------|--------|
| **Business problem** | Revenue is at risk from customers who have stopped purchasing |
| **Evidence** | RFM places ~700 customers in At-Risk / About-to-Sleep / Lost; churn model flags a High-Risk band |
| **Recommended decision** | Launch a 3-tier campaign: email → incentive → human outreach for the top-value subset, **with a randomized 20% holdout control** |
| **Owner** | CRM / Retention Marketing Lead |
| **KPI** | 90-day reactivation rate; incremental revenue per reactivated customer (treated − control) |
| **Expected outcome** | Recover a measurable share of lapsed spend. **Do NOT assume a recovery %** — let the control group establish it |
| **Cost of inaction** | These customers drift to permanent loss; CAC to replace them is several × higher |

## Decision 2 — Loyalty program for Champions + Loyal
| Field | Detail |
|-------|--------|
| **Business problem** | Best customers are indistinguishable from average ones and receive no differentiated treatment |
| **Evidence** | RFM Champions + Loyal Customers concentrate the majority of historical revenue |
| **Recommended decision** | Launch a rewards tier (points/early access/review requests) for the top ~800 customers |
| **Owner** | Marketing Lead |
| **KPI** | Purchase frequency and AOV lift, enrolled vs. unenrolled, over 2 quarters |
| **Expected outcome** | Higher frequency and basket size among the most profitable cohort |
| **Cost of inaction** | Competitors with loyalty programs capture repeat share |

## Decision 3 — Rebalance catalog using the BCG view
| Field | Detail |
|-------|--------|
| **Business problem** | Marketing budget and inventory are spread evenly across products regardless of true profitability |
| **Evidence** | Product profitability + BCG bucketing separates reliable earners from low-margin Dogs |
| **Recommended decision** | Shift paid-media weight toward Stars/Cash Cows; review Dogs for delisting or repricing |
| **Owner** | Category Manager |
| **KPI** | Blended gross margin % per category, quarter over quarter |
| **Expected outcome** | Improved margin mix; capital reallocated from losers to winners |
| **Cost of inaction** | Margin continues to leak into low-return SKUs |

## Decision 4 — Establish a monthly retention review cadence
| Field | Detail |
|-------|--------|
| **Business problem** | There is no regular forum where retention and churn are reviewed against a target |
| **Evidence** | The pipeline can refresh RFM, churn scores, and cohort retention on a schedule |
| **Recommended decision** | Monthly 30-min retention review: churn rate vs. target, top risk segments, win-back campaign results |
| **Owner** | Head of E-commerce |
| **KPI** | Net retention rate trend month over month |
| **Expected outcome** | Retention becomes a managed metric, not an afterthought |

---

### How to read this log
Every row should eventually have a **closing entry**: *did the KPI move, by
how much, vs. the control?* A decision with no follow-up measurement is only
half a decision.
