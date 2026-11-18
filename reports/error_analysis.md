# Error Analysis — Churn Model
### Who the model misses, who it over-contacts, and what would fix it

> Failure cases are summarized from the regenerated
> `reports/churn_calibration_metrics.json` (`error_analysis` section), operating
> point **t\* = 0.12** on the 320-customer holdout. Score bands and per-customer
> IDs changed with the 2026-11-18 purchase-definition rework, so the old
> hand-copied ID tables were removed rather than left stale.

## 1. The confusion at t\* = 0.12 (holdout, n = 320)

| | Predicted churn | Predicted stay |
|---|---|---|
| **Actually churned** | 65 | **10 (FN)** |
| **Actually stayed** | **162 (FP)** | 83 |

Precision 28.6% · Recall 86.7% — recall-oriented by design (a missed churner
costs more than an extra contact under the stated cost model).

## 2. False negatives — the 10 missed churners

| Group | n | Churn rate | FPs | FNs |
|---|---|---|---|---|
| Recent | 108 | 18.5% | 32 | 4 |
| Mid recency | 105 | 22.9% | 59 | 4 |
| Lapsed | 107 | 29.0% | 71 | 2 |
| **New tenure** | 108 | 13.0% | 14 | **10** |
| Established tenure | 106 | 23.6% | 78 | 0 |
| Veteran tenure | 106 | 34.0% | 70 | 0 |

**Profile of the miss:** all 10 FNs are in the **new-tenure** band. The model
learned "recent purchase → stays"; new customers have short histories, so a
single recent purchase scores low even when they never return. It cannot yet
separate "active loyal" from "one-and-done new" because there is no
recency × tenure interaction feature.

**What would fix it (ranked by cost):**
1. **Feature:** `orders_per_tenure_week` × `recency` interaction plus an
   `is_new_customer` flag (tenure < 60d). Cheap; targets the only band with FNs.
2. **Segment-specific threshold:** lower t for new customers (their churn rate
   is 13.0% vs 34.0% for veterans; the cost model supports per-segment t).
3. **Data:** first-purchase channel / acquisition source (not in this dataset).

## 3. False positives — the 162 over-contacted customers

| Group | n | Churn rate | FPs |
|---|---|---|---|
| Recent | 108 | 18.5% | 32 |
| Mid recency | 105 | 22.9% | 59 |
| Lapsed | 107 | 29.0% | 71 |
| Low frequency | 107 | 15.9% | 43 |
| Mid frequency | 106 | 25.5% | 56 |
| High frequency | 107 | 29.0% | 63 |

**Why the model over-contacts them:** long-tenure, low-frequency customers with
long gaps look like churners *on average*, but this group contains
seasonal/episodic returners. A 180-day gap is not necessarily a broken
relationship; the model has no seasonality signal.

**What would fix it (ranked by cost):**
1. **Feature:** `historical_max_gap` and `gaps_over_180d` — customers with a
   history of long pauses are known returners.
2. **Policy:** the cost model already prices this — 162 FPs × ₹250 = ₹40,500 of
   contact cost, accepted because the 65 TPs are worth more. The FP count is the
   priced-in cost of recall, not a bug.
3. **Do NOT raise the threshold blindly** — that trades recall for precision and
   moves the profit curve in the wrong direction under base assumptions (see
   `reports/churn_calibration_and_thresholds.md`).

## 4. What this analysis changes

- The next model iteration should add the two interaction features above **and
  re-run the backtest + threshold analysis** — the error analysis predicts where
  the gains are.
- Until then: treat the cooling-off band as a *campaign audience with a ~29%
  hit rate*, not a churn list. The win-back experiment design
  (`docs/experiment_design_winback.md`) already prices this reality.

## 5. Limitations

1. Synthetic data — these patterns are the value, not the individual rows.
2. One operating point (t\* = 0.12) is analyzed; other thresholds move the FN/FP mix.
3. The FP "waste" framing assumes the base-case cost model; with higher recovery
   rates the FPs cost even less relative to the TPs found.
