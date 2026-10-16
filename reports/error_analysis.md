# Error Analysis — Churn Model
### Who the model misses, who it over-contacts, and what would fix it

> Failure cases extracted from the fit/cal/test protocol (`scripts/churn_calibration.py`),
> operating point **t\* = 0.10** (isotonic probabilities). Customer IDs and feature
> values are real rows from the seeded dataset.

## 1. The confusion at t\* = 0.10 (test slice, n = 318)

| | Predicted churn | Predicted stay |
|---|---|---|
| **Actually churned** | 70 | **11 (FN)** |
| **Actually stayed** | **147 (FP)** | 90 |

Precision 32.1% · Recall 86.4% — recall-oriented by design (contacts are cheap
relative to lost customers under the stated cost model).

## 2. False negatives — the 11 missed churners

| Customer | p | Recency | Orders | Tenure | Frequency | Revenue |
|---|---|---|---|---|---|---|
| CUST01971 | 0.069 | 11d | 1 | 11d | 1.00/mo | ₹6,375 |
| CUST00462 | 0.069 | 21d | 6 | 157d | 1.15/mo | ₹40,801 |
| CUST00108 | 0.069 | 5d | 1 | 5d | 1.00/mo | ₹7,449 |
| CUST00923 | 0.069 | 1d | 1 | 1d | 1.00/mo | ₹9,201 |
| CUST00036 | 0.069 | 6d | 3 | 94d | 0.96/mo | ₹14,470 |
| CUST00997 | 0.096 | 16d | 1 | 16d | 1.00/mo | ₹15,878 |

**Profile of the miss:**

| Group | Median recency | Median orders | Median tenure |
|---|---|---|---|
| Missed churners (FN) | **16d** | **2** | **94d** |
| All churners | 100d | 3 | 480d |
| Whole test set | 83d | 3 | 325d |

**Why the model misses them:** the dominant learned pattern is *"recent purchase
→ stays"*. These customers bought recently (low recency) and therefore score
low — but they are **new, low-history customers who never return**. One purchase
in their first weeks, then nothing. The model cannot distinguish "active loyal"
from "one-and-done new" because it never sees a *recency × tenure interaction*.

**What would fix it (ranked by cost):**
1. **Feature:** `orders_per_tenure_week` × `recency` interaction, plus an
   `is_new_customer` flag (tenure < 60d). Cheap, likely recovers most of the 11.
2. **Segment-specific threshold:** lower t for tenure < 60d (new customers churn
   at a different rate; the cost model already supports per-segment thresholds).
3. **Data:** first-purchase channel / acquisition source (not in this dataset).

## 3. False positives — the 147 over-contacted customers

Top of the list (highest predicted risk among customers who stayed anyway):

| Customer | p | Recency | Orders | Tenure | Frequency | Revenue |
|---|---|---|---|---|---|---|
| CUST01061 | **0.945** | 217d | 8 | 854d | 0.28/mo | ₹56,339 |
| CUST00898 | 0.571 | 21d | 10 | 411d | 0.73/mo | ₹69,379 |
| CUST01820 | 0.467 | 99d | 5 | 633d | 0.24/mo | ₹26,671 |
| CUST01764 | 0.467 | 200d | 4 | 633d | 0.19/mo | ₹29,943 |
| CUST01853 | 0.467 | 3d | 4 | 601d | 0.20/mo | ₹40,034 |
| CUST00542 | 0.467 | 303d | 6 | 833d | 0.22/mo | ₹43,712 |

**Why the model over-contacts them:** long-tenure, low-frequency customers with
long gaps look exactly like churners *on average* — but this group contains
**seasonal/episodic returners** (e.g., CUST01061: 217-day gap, 8 orders over
854 days — a pattern of long pauses, then return). The model has no seasonality
signal; a 217-day gap is not the same as a broken relationship.

**What would fix it (ranked by cost):**
1. **Feature:** `historical_max_gap` and `gaps_over_180d` — customers with a
   history of long pauses are known-returners, not churners.
2. **Policy:** the cost model already prices this — 147 FPs × ₹250 = ₹36,750 of
   "wasted" contact cost, which the expected-profit calculation *accepts*
   because the 70 TPs are worth more. The FP count is not a bug; it is the
   priced-in cost of recall.
3. **Do NOT "fix" it by raising the threshold blindly** — that trades recall for
   precision and moves the profit curve in the wrong direction under base
   assumptions (see `reports/churn_calibration_and_thresholds.md`).

## 4. What this analysis changes

- The next model iteration should add the two interaction features above **and
  re-run the backtest + threshold analysis** — the error analysis predicts where
  the gains are.
- Until then: treat the cooling-off band as a *campaign audience with a 32%
  hit rate*, not a churn list. The win-back experiment design
  (`docs/experiment_design_winback.md`) already prices this reality.

## 5. Limitations

1. Synthetic data — these customers do not exist; the *patterns* are the value.
2. One operating point (t\* = 0.10) analyzed; other thresholds move the FN/FP mix.
3. The FP "waste" framing assumes the base-case cost model; with higher recovery
   rates the FPs cost even less relative to the TPs found.
