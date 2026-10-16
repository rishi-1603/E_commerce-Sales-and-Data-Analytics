"""
elasticity.py — Discount Response, Margin Erosion & Break-Even Analysis
==============================================================================
The pricing question this module answers:

    "Is the discount we give buying us anything — and what would have to be
     true for it to be worth giving?"

WHAT IT COMPUTES
    1. discount_response()   — measured quantity response to discount depth
                               (Kruskal-Wallis across depths + per-category
                               OLS slope with p-value). Tests whether demand
                               actually responds before assuming it does.
    2. margin_curve()        — margin rate and margin-as-%-of-list at each
                               discount depth. The cost side of the trade.
    3. break_even_table()    — the volume lift each discount depth would need
                               just to hold total margin flat. The number that
                               decides whether a discount is a strategy or a leak.
    4. repricing_scenario()  — static re-pricing: cap discounts at a chosen
                               depth and measure margin recovered holding
                               volume constant.
    5. simulate()            — the Discount Lab: given an *assumed* volume lift,
                               project revenue and margin at a chosen depth.

HONESTY NOTES (read before quoting any number)
    - This is OBSERVATIONAL data. Discount depth is chosen by the business, not
      randomly assigned, so a measured association is not automatically a causal
      effect. The scenario engine therefore reports what WOULD have to be true
      (break-even lift) rather than claiming what WILL happen.
    - In this dataset the measured quantity response to discount is
      statistically indistinguishable from zero (see the report). The finding
      is published as-is — it is the most decision-relevant result in the module.
    - repricing_scenario() holds volume constant by construction. The break-even
      table exists precisely so a reader can see how wrong that assumption would
      have to be before the recommendation flips.

Run:  python python/pricing/elasticity.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "master_orders.csv"
OUT = ROOT / "reports" / "discount_analysis.json"

DISCOUNT_LEVELS = [0.0, 0.05, 0.10, 0.15, 0.20]


def load() -> pd.DataFrame:
    """Load line-item grain data with the margin columns this module needs."""
    df = pd.read_csv(DATA)
    df["margin_rate"] = df["profit"] / df["line_total"]
    # margin expressed as a share of LIST price (removes the discount denominator
    # effect, so depths are comparable): profit / (line_total / (1 - d))
    df["margin_pct_of_list"] = df["margin_rate"] * (1 - df["discount_pct_y"])
    return df


# ──────────────────────────────────────────────────────────────────────────────
# 1. Does demand respond to discount at all?
# ──────────────────────────────────────────────────────────────────────────────
def discount_response(df: pd.DataFrame) -> dict:
    """Test for a quantity response to discount depth — before assuming one.

    Returns overall Kruskal-Wallis across depths, an overall OLS slope, and a
    per-category slope with p-value. A null result is a finding, not a failure.
    """
    groups = [g["quantity"].values for _, g in df.groupby("discount_pct_y")]
    h, p_kw = stats.kruskal(*groups)

    lr = stats.linregress(df["discount_pct_y"], df["quantity"])
    overall_mean_qty = float(df["quantity"].mean())

    per_category = {}
    for cat, g in df.groupby("category"):
        r = stats.linregress(g["discount_pct_y"], g["quantity"])
        mean_qty = float(g["quantity"].mean())
        # magnitude expressed over the observed discount range (0 → 20pp),
        # because "per 1.0 of discount" is not an interpretable business unit
        delta_at_20pp = float(r.slope) * 0.20
        per_category[cat] = {
            "n": int(len(g)),
            "slope_qty_per_unit_discount": round(float(r.slope), 4),
            "qty_change_at_20pp": round(delta_at_20pp, 4),
            "qty_change_pct_at_20pp": round(delta_at_20pp / mean_qty, 4),
            "p_value": round(float(r.pvalue), 3),
            "significant_at_5pct": bool(r.pvalue < 0.05),
        }

    return {
        "mean_quantity_by_depth": {
            f"{d:.0%}": round(float(df.loc[df.discount_pct_y == d, "quantity"].mean()), 3)
            for d in DISCOUNT_LEVELS if (df.discount_pct_y == d).any()
        },
        "kruskal_wallis_h": round(float(h), 3),
        "kruskal_wallis_p": round(float(p_kw), 3),
        "volume_response_detected": bool(p_kw < 0.05),
        "overall_slope_qty_per_unit_discount": round(float(lr.slope), 4),
        "overall_qty_change_pct_at_20pp": round(
            float(lr.slope) * 0.20 / overall_mean_qty, 4),
        "overall_p_value": round(float(lr.pvalue), 3),
        "significance_vs_materiality_note": (
            "With n≈4,000 line items per category, small slopes can reach p<0.05. "
            "Statistical significance is therefore reported alongside the effect "
            "magnitude at 20pp of discount, and compared against the break-even "
            "volume lift each depth requires. See break_even table."
        ),
        "per_category": per_category,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 2. What does the discount cost?
# ──────────────────────────────────────────────────────────────────────────────
def margin_curve(df: pd.DataFrame) -> pd.DataFrame:
    """Margin rate and margin-as-%-of-list at each discount depth."""
    rows = []
    base = df.loc[df.discount_pct_y == 0.0, "margin_pct_of_list"].mean()
    for d in DISCOUNT_LEVELS:
        g = df[df.discount_pct_y == d]
        if g.empty:
            continue
        ml = float(g["margin_pct_of_list"].mean())
        rows.append({
            "discount": d,
            "line_items": int(len(g)),
            "share_of_items": round(len(g) / len(df), 4),
            "margin_rate": round(float(g["margin_rate"].mean()), 4),
            "margin_pct_of_list": round(ml, 4),
            "margin_loss_vs_no_discount": round(float(base - ml), 4),
        })
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# 3. What would have to be true for the discount to pay for itself?
# ──────────────────────────────────────────────────────────────────────────────
def break_even_table(df: pd.DataFrame) -> pd.DataFrame:
    """Volume lift required at each depth to hold total margin flat.

    break_even_lift = (margin_per_unit at 0%) / (margin_per_unit at depth) - 1
    where both are expressed as a share of LIST price.
    """
    curve = margin_curve(df)
    base = float(curve.loc[curve.discount == 0.0, "margin_pct_of_list"].iloc[0])
    curve["break_even_volume_lift"] = (
        base / curve["margin_pct_of_list"] - 1
    ).round(4)
    return curve[["discount", "margin_rate", "margin_pct_of_list",
                  "break_even_volume_lift", "share_of_items"]]


# ──────────────────────────────────────────────────────────────────────────────
# 4. Static re-pricing scenarios
# ──────────────────────────────────────────────────────────────────────────────
def repricing_scenario(df: pd.DataFrame, cap: float) -> dict:
    """Cap all discounts above `cap` at `cap`; measure margin recovered.

    Static by construction: volume is held constant (per line item). Cost is
    unchanged; only the price the customer pays moves. Read the result as
    "margin recovered if those orders still happen at the higher price".
    """
    affected = df[df.discount_pct_y > cap].copy()
    if affected.empty:
        return {"cap": cap, "lines_affected": 0, "margin_recovered": 0.0}

    # re-price: new_line_total = old_line_total * (1 - cap) / (1 - old_d)
    factor = (1 - cap) / (1 - affected["discount_pct_y"])
    new_line_total = affected["line_total"] * factor
    new_profit = new_line_total - affected["cost_total"]
    recovered = float((new_profit - affected["profit"]).sum())

    return {
        "cap": cap,
        "lines_affected": int(len(affected)),
        "share_of_lines": round(len(affected) / len(df), 4),
        "revenue_change": round(float((new_line_total - affected["line_total"]).sum()), 2),
        "margin_recovered": round(recovered, 2),
        "margin_recovered_pct_of_total": round(
            recovered / float(df["profit"].sum()), 4),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 5. The Discount Lab — scenario simulator with an ASSUMED volume response
# ──────────────────────────────────────────────────────────────────────────────
def simulate(depth: float, assumed_volume_lift: float, df: pd.DataFrame | None = None) -> dict:
    """Project revenue and margin at a chosen depth for an ASSUMED volume lift.

    `assumed_volume_lift` is a fraction (0.10 = +10% units). Because this dataset
    cannot identify the true response, the lift is an explicit user assumption —
    the lab's job is to show the break-even line, not to pretend to predict.
    """
    if df is None:
        df = load()
    base = df[df.discount_pct_y == 0.0]
    base_units = float(base["quantity"].sum())
    base_price = float((base["line_total"] / base["quantity"]).mean())
    base_cost = float((base["cost_total"] / base["quantity"]).mean())

    price = base_price * (1 - depth)
    units = base_units * (1 + assumed_volume_lift)
    revenue = price * units
    margin = (price - base_cost) * units
    base_revenue = base_price * base_units
    base_margin = (base_price - base_cost) * base_units

    be = break_even_table(df)
    be_lift = float(be.loc[be.discount == depth, "break_even_volume_lift"].iloc[0]) \
        if depth in set(be["discount"]) else None

    return {
        "depth": depth,
        "assumed_volume_lift": assumed_volume_lift,
        "revenue": round(revenue, 2),
        "margin": round(margin, 2),
        "revenue_change_pct": round(revenue / base_revenue - 1, 4),
        "margin_change_pct": round(margin / base_margin - 1, 4),
        "break_even_volume_lift": be_lift,
        "beats_break_even": (assumed_volume_lift >= be_lift) if be_lift is not None else None,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Report
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    df = load()
    resp = discount_response(df)
    curve = margin_curve(df)
    be = break_even_table(df)
    scenarios = {f"cap_{int(c*100)}": repricing_scenario(df, c) for c in (0.10, 0.15)}

    payload = {
        "generated_by": "python/pricing/elasticity.py",
        "grain": "order line items (master_orders.csv)",
        "discount_response": resp,
        "margin_curve": curve.to_dict(orient="records"),
        "break_even": be.to_dict(orient="records"),
        "repricing_scenarios": scenarios,
        "headline": {
            "volume_response_detected": resp["volume_response_detected"],
            "kruskal_p": resp["kruskal_wallis_p"],
            "break_even_lift_at_20pct": float(
                be.loc[be.discount == 0.20, "break_even_volume_lift"].iloc[0]),
            "margin_recovered_by_10pct_cap": scenarios["cap_10"]["margin_recovered"],
        },
    }
    OUT.write_text(json.dumps(payload, indent=2))

    print("=" * 78)
    print("DISCOUNT RESPONSE, MARGIN EROSION & BREAK-EVEN")
    print("=" * 78)
    print(f"\n1. Does demand respond to discount depth?")
    print(f"   Kruskal-Wallis across depths: H={resp['kruskal_wallis_h']}, "
          f"p={resp['kruskal_wallis_p']}")
    print(f"   Overall OLS slope: {resp['overall_slope_qty_per_unit_discount']:+.4f} units "
          f"per unit of discount → {resp['overall_qty_change_pct_at_20pp']:+.2%} at 20pp "
          f"(p={resp['overall_p_value']})")
    print(f"   → volume response detected: {resp['volume_response_detected']}")
    print(f"   Mean quantity by depth: {resp['mean_quantity_by_depth']}")
    print("   Per category (significance AND magnitude — they are different things):")
    for cat, v in resp["per_category"].items():
        print(f"     {cat:14s} {v['qty_change_pct_at_20pp']:+.2%} at 20pp  "
              f"p={v['p_value']:.3f} {'(significant)' if v['significant_at_5pct'] else ''}")

    print(f"\n2. What does each discount cost in margin?")
    print(curve[["discount", "line_items", "margin_rate",
                 "margin_pct_of_list", "margin_loss_vs_no_discount"]].to_string(index=False))

    print(f"\n3. Volume lift required to break even on margin:")
    print(be[["discount", "break_even_volume_lift", "share_of_items"]].to_string(index=False))

    print(f"\n4. Static re-pricing scenarios (volume held constant):")
    for k, s in scenarios.items():
        print(f"   {k}: {s['lines_affected']:,} lines affected → "
              f"margin recovered ₹{s['margin_recovered']:,.0f} "
              f"({s['margin_recovered_pct_of_total']:.1%} of total margin)")

    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
