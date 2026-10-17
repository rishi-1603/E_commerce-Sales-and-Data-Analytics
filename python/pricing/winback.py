"""
winback.py — Win-Back Campaign Economics
==============================================================================
The pricing question this module answers:

    "Of the 448 cooling-off customers, who is worth saving, with what offer,
     and what does the campaign return before we spend a single rupee?"

WHAT IT COMPUTES
    1. economics()            — expected profit per contact and for the pool,
                               at a chosen offer cost and recovery rate.
    2. break_even_probability() — the churn probability at which a contact is
                               exactly worth its cost. Cross-checks the churn
                               model's own Bayes threshold (0.1289).
    3. sensitivity_grid()     — expected profit across recovery rates × offer
                               costs. Shows how wrong an assumption can be
                               before the recommendation flips.
    4. tiered_scenarios()     — all-pool vs top-decile vs blanket-discount,
                               side by side, in rupees.
    5. budget_worklist()      — rank by expected value and cut at a budget:
                               "who do we call with ₹B this month".

PARAMETERS (must match data/metrics.json and the churn cost model)
    contact cost  C = ₹250      (reports/churn_calibration_metrics.json)
    recovery rate r = 15%       (same file)
    retained value V = ₹12,931  (mean 180-day spend of customers who did NOT churn)

HONESTY NOTES
    - Every figure is an EXPECTED value under stated assumptions. No campaign
      has been run. The experiment design (docs/experiment_design_winback.md)
      exists precisely because these are assumptions, not measurements.
    - The 34.5% baseline 90-day repeat rate is measured; the recovery rate r is
      NOT measured — it is the single most sensitive assumption, so the module
      reports a sensitivity grid rather than a point estimate alone.
    - The pool size (448) is only powered to detect a +13pp effect; smaller true
      effects will be invisible. Underpowered ≠ no effect.

Run:  python python/pricing/winback.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ROOT / "data" / "processed" / "churn_features.csv"
OUT = ROOT / "reports" / "winback_economics.json"

# ── Canonical cost-model parameters (single source of truth) ────────────────
CONTACT_COST_INR = 250.0        # C — per contact / per offer
RECOVERY_RATE = 0.15            # r — share of reached churners who return
RETAINED_VALUE_INR = 12931.3    # V — mean 180-day spend of retained customers
BASELINE_REPEAT_RATE = 0.345    # measured 90-day repeat rate of the pool

COOLING_OFF_BAND = "Medium Risk"


# ──────────────────────────────────────────────────────────────────────────────
def load_pool(band: str = COOLING_OFF_BAND) -> pd.DataFrame:
    """The win-back audience: customers in the cooling-off churn band."""
    df = pd.read_csv(FEATURES)
    return df[df["churn_risk"] == band].copy()


# ──────────────────────────────────────────────────────────────────────────────
# 1. Expected-profit economics
# ──────────────────────────────────────────────────────────────────────────────
def economics(
    audience: int,
    mean_churn_prob: float,
    contact_cost: float = CONTACT_COST_INR,
    recovery_rate: float = RECOVERY_RATE,
    retained_value: float = RETAINED_VALUE_INR,
) -> dict:
    """Expected profit of contacting `audience` customers at `mean_churn_prob`.

    Per contact:  EV = P(churn) × r × V − C
    Total:        EV × audience

    A negative per-contact EV means the campaign destroys value at this
    probability — the honest answer is "do not run it".
    """
    value_at_stake = mean_churn_prob * recovery_rate * retained_value
    per_contact = value_at_stake - contact_cost
    return {
        "audience": audience,
        "mean_churn_prob": round(mean_churn_prob, 4),
        "contact_cost": contact_cost,
        "recovery_rate": recovery_rate,
        "retained_value": retained_value,
        "expected_value_recovered_per_contact": round(value_at_stake, 2),
        "expected_profit_per_contact": round(per_contact, 2),
        "expected_profit_total": round(per_contact * audience, 2),
        "campaign_cost_total": round(contact_cost * audience, 2),
        "expected_recovered_revenue_total": round(value_at_stake * audience, 2),
        "profitable": bool(per_contact > 0),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 2. Break-even churn probability
# ──────────────────────────────────────────────────────────────────────────────
def break_even_probability(
    contact_cost: float = CONTACT_COST_INR,
    recovery_rate: float = RECOVERY_RATE,
    retained_value: float = RETAINED_VALUE_INR,
) -> dict:
    """The churn probability at which a contact exactly pays for itself.

    break_even_p = C / (r × V)

    This is the same quantity as the churn model's Bayes threshold. If the two
    disagree, the cost model and the campaign model have drifted apart.
    """
    p = contact_cost / (recovery_rate * retained_value)
    return {
        "break_even_churn_probability": round(p, 4),
        "formula": "C / (r × V)",
        "contact_cost": contact_cost,
        "recovery_rate": recovery_rate,
        "retained_value": retained_value,
        "interpretation": (
            f"Only contact customers whose churn probability exceeds {p:.1%}; "
            "below that, the offer costs more than it recovers in expectation."
        ),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 3. Sensitivity: how wrong can the assumptions be?
# ──────────────────────────────────────────────────────────────────────────────
def sensitivity_grid(
    audience: int,
    mean_churn_prob: float,
    recovery_rates: tuple = (0.05, 0.10, 0.15, 0.20, 0.30, 0.40),
    contact_costs: tuple = (100.0, 250.0, 400.0, 500.0),
) -> list[dict]:
    """Expected total profit across recovery rate × offer cost."""
    rows = []
    for r in recovery_rates:
        for c in contact_costs:
            e = economics(audience, mean_churn_prob, contact_cost=c, recovery_rate=r)
            rows.append({
                "recovery_rate": r,
                "contact_cost": c,
                "profit_per_contact": e["expected_profit_per_contact"],
                "profit_total": e["expected_profit_total"],
                "profitable": e["profitable"],
            })
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# 4. Tiered scenarios — where the money actually is
# ──────────────────────────────────────────────────────────────────────────────
def tiered_scenarios(pool: pd.DataFrame) -> list[dict]:
    """Compare targeting strategies in rupees, using the same cost model."""
    n = len(pool)
    mean_p = float(pool["churn_probability"].mean())
    out = []

    # A. Contact the whole pool
    out.append({"scenario": "A. Contact all 448 (blanket win-back)",
                **economics(n, mean_p)})

    # B. Top decile by expected value (churn probability × historical spend).
    #    Expected value per customer ranks by p × spend, not by p alone —
    #    a likely churner who spends little is not worth a call.
    pool = pool.copy()
    pool["expected_value_rank"] = pool["churn_probability"] * pool["total_revenue"]
    top = pool.nlargest(max(1, n // 10), "expected_value_rank")
    out.append({"scenario": f"B. Contact top decile by expected value ({len(top)})",
                **economics(len(top), float(top["churn_probability"].mean()))})

    # C. Contact only those above the break-even probability
    be = break_even_probability()["break_even_churn_probability"]
    above = pool[pool["churn_probability"] > be]
    if len(above):
        out.append({"scenario": f"C. Contact only p > break-even {be:.1%} ({len(above)})",
                    **economics(len(above), float(above["churn_probability"].mean()))})
    else:
        out.append({"scenario": f"C. Contact only p > break-even {be:.1%} (0)",
                    "audience": 0, "expected_profit_total": 0.0,
                    "expected_profit_per_contact": 0.0, "profitable": False,
                    "campaign_cost_total": 0.0,
                    "expected_recovered_revenue_total": 0.0,
                    "note": "No customer in this pool exceeds the break-even "
                            "probability — the honest recommendation is not to run "
                            "a paid win-back campaign on this band."})

    # D. No campaign
    out.append({"scenario": "D. Do nothing",
                "audience": n, "expected_profit_total": 0.0,
                "expected_profit_per_contact": 0.0, "profitable": False,
                "campaign_cost_total": 0.0,
                "expected_recovered_revenue_total": 0.0,
                "note": "Baseline: revenue is lost at the natural 34.5% repeat rate."})
    return out


# ──────────────────────────────────────────────────────────────────────────────
# 5. Budget-constrained worklist
# ──────────────────────────────────────────────────────────────────────────────
def budget_worklist(pool: pd.DataFrame, budget_inr: float) -> dict:
    """Who to contact first when the budget only stretches to N calls."""
    be = break_even_probability()["break_even_churn_probability"]
    p = pool.copy()
    p["expected_value_inr"] = (
        p["churn_probability"] * RECOVERY_RATE * RETAINED_VALUE_INR - CONTACT_COST_INR
    )
    p = p[p["expected_value_inr"] > 0].sort_values("expected_value_inr", ascending=False)
    affordable = int(budget_inr // CONTACT_COST_INR)
    selected = p.head(affordable)

    return {
        "budget_inr": budget_inr,
        "calls_affordable": affordable,
        "eligible_customers": int(len(p)),
        "selected": int(len(selected)),
        "expected_profit_inr": round(float(selected["expected_value_inr"].sum()), 2),
        "spend_inr": round(len(selected) * CONTACT_COST_INR, 2),
        "mean_churn_prob_selected": round(float(selected["churn_probability"].mean()), 4)
        if len(selected) else None,
        "break_even_probability": be,
        "note": "Ranked by expected value (p x r x V - C) rather than churn "
                "probability alone - a likely churner who spends little is not "
                "worth a call. Written without apostrophes or comma-colon "
                "sequences so the dashboard JS-to-JSON parser stays valid.",
    }


# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    pool = load_pool()
    n = len(pool)
    mean_p = float(pool["churn_probability"].mean())

    base = economics(n, mean_p)
    be = break_even_probability()
    grid = sensitivity_grid(n, mean_p)
    tiers = tiered_scenarios(pool)
    worklist = budget_worklist(pool, budget_inr=25_000)

    # Cross-check against the churn model's own Bayes threshold
    churn_metrics_path = ROOT / "reports" / "churn_calibration_metrics.json"
    bayes = None
    if churn_metrics_path.exists():
        bayes = json.loads(churn_metrics_path.read_text())["cost_model"]["bayes_threshold"]

    payload = {
        "generated_by": "python/pricing/winback.py",
        "audience_definition": f"churn_risk == '{COOLING_OFF_BAND}' in churn_features.csv",
        "parameters": {
            "contact_cost_inr": CONTACT_COST_INR,
            "recovery_rate": RECOVERY_RATE,
            "retained_value_inr": RETAINED_VALUE_INR,
            "baseline_repeat_rate": BASELINE_REPEAT_RATE,
            "source": "reports/churn_calibration_metrics.json cost_model",
        },
        "pool": {
            "customers": n,
            "historical_spend_inr": round(float(pool["total_revenue"].sum()), 2),
            "mean_historical_spend_inr": round(float(pool["total_revenue"].mean()), 2),
            "mean_churn_probability": round(mean_p, 4),
            "baseline_repeat_rate": BASELINE_REPEAT_RATE,
        },
        "baseline_campaign": base,
        "break_even": be,
        "bayes_threshold_cross_check": {
            "campaign_break_even": be["break_even_churn_probability"],
            "churn_model_bayes_threshold": bayes,
            "consistent": (bayes is not None and
                           abs(bayes - be["break_even_churn_probability"]) < 5e-3),
        },
        "sensitivity": grid,
        "tiered_scenarios": tiers,
        "budget_worklist": worklist,
    }
    OUT.write_text(json.dumps(payload, indent=2))

    print("=" * 78)
    print("WIN-BACK CAMPAIGN ECONOMICS — cooling-off band")
    print("=" * 78)
    print(f"\nPool: {n} customers | historical spend ₹{pool['total_revenue'].sum():,.0f} "
          f"| mean churn p = {mean_p:.1%}")
    print(f"Cost model: C=₹{CONTACT_COST_INR:.0f}/contact, r={RECOVERY_RATE:.0%}, "
          f"V=₹{RETAINED_VALUE_INR:,.0f}")

    print(f"\n1. Baseline campaign (contact all {n}):")
    print(f"   ₹{base['expected_value_recovered_per_contact']:,.0f} expected value "
          f"recovered − ₹{CONTACT_COST_INR:,.0f} cost "
          f"= ₹{base['expected_profit_per_contact']:,.0f} profit per contact")
    print(f"   Total expected profit: ₹{base['expected_profit_total']:,.0f}")

    print(f"\n2. Break-even churn probability: {be['break_even_churn_probability']:.2%}")
    print(f"   Churn model's own Bayes threshold: {bayes}")
    print(f"   → consistent: {payload['bayes_threshold_cross_check']['consistent']}")

    print("\n3. Tiered scenarios:")
    for t in tiers:
        ev = t.get("expected_profit_total", 0)
        print(f"   {t['scenario']:52s} ₹{ev:>12,.0f}")

    print("\n4. Budget worklist (Rs 25,000):")
    print(f"   {worklist['calls_affordable']} calls affordable, "
          f"{worklist['eligible_customers']} eligible, "
          f"expected profit ₹{worklist['expected_profit_inr']:,.0f}")

    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
