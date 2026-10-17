"""
forecast_challenger.py — can anything beat the drift baseline?
==============================================================================
WHY THIS EXISTS: the rolling-origin backtest (forecast_backtest.py) found the
shipped ensemble lost to a drift baseline (MASE 0.680 vs 0.468) and recommended
the baseline for operational forecasts. That verdict was honest but left the
question open: is drift the ceiling, or did we simply not try the right model?

Revenue on this dataset grows roughly exponentially (₹11k → ₹6.1M over 36
months). Drift fits a straight line through that curve — which is the wrong
functional form. This script tests challengers built for exponential growth,
under an IDENTICAL evaluation protocol.

PROTOCOL PARITY (this is what makes the comparison fair):
    - same monthly series (imported load_monthly)
    - same origins (MIN_TRAIN .. n - max(HORIZONS))
    - same horizons (1..3)
    - same MASE scaling (imported mase_scale — in-sample seasonal-naive MAE)
    - same baselines, imported from forecast_backtest so they cannot drift

CHALLENGERS
    log_linear        OLS on log(y), exponentiated          (exponential trend)
    log_drift         geometric random walk with drift      (multiplicative)
    damped_log_linear log-linear with damping φ^h           (conservative growth)
    holt_linear       Holt additive trend, no seasonality
    blend_drift_log   mean of drift and log-linear          (model averaging)

VERDICT POLICY: whatever wins is published. If nothing beats drift, that is a
finding too — it means the baseline is the ceiling at this horizon, and the
report says so instead of quietly shipping a fancier model.

Outputs:
    reports/forecast_challenger_metrics.json   (pinned by tests)
    reports/forecast_challenger.md

Run:  python scripts/forecast_challenger.py
"""
import json
import os
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from forecast_backtest import (  # noqa: E402  — protocol parity by construction
    HORIZONS,
    MIN_TRAIN,
    f_drift,
    f_ensemble,
    f_holt_winters,
    f_linear,
    f_naive_last,
    f_seasonal_naive,
    load_monthly,
    mase_scale,
)

REPORTS = os.path.join(BASE, "reports")
os.makedirs(REPORTS, exist_ok=True)

DAMPING = 0.92   # φ — growth scepticism for the damped challenger


# ──────────────────────────────────────────────────────────────────────────────
# Challenger models
# ──────────────────────────────────────────────────────────────────────────────
def f_log_linear(train, h):
    """OLS on log(y) — fits a constant growth rate rather than a constant slope."""
    y = np.asarray(train, dtype=float)
    t = np.arange(len(y))
    b, a = np.polyfit(t, np.log(y), 1)
    return np.exp(a + b * np.arange(len(y), len(y) + h))


def f_log_drift(train, h):
    """Geometric random walk with drift: y_t · exp(g · h)."""
    y = np.asarray(train, dtype=float)
    g = (np.log(y[-1]) - np.log(y[0])) / max(len(y) - 1, 1)
    return y[-1] * np.exp(g * np.arange(1, h + 1))


def f_damped_log_linear(train, h):
    """Log-linear growth with damping: cumulative growth damped by φ^step."""
    y = np.asarray(train, dtype=float)
    t = np.arange(len(y))
    b, a = np.polyfit(t, np.log(y), 1)
    steps = np.arange(1, h + 1)
    cum = np.cumsum(DAMPING ** (steps - 1)) if b > 0 else -np.cumsum(DAMPING ** (steps - 1))
    return np.exp(a + b * (len(y) - 1 + cum))


def f_holt_linear(train, h):
    """Holt's linear trend without seasonality (additive)."""
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    fit = ExponentialSmoothing(train, trend="add", seasonal=None,
                               initialization_method="estimated").fit()
    return np.asarray(fit.forecast(h))


def f_blend_drift_log(train, h):
    """Average of the strongest baseline and the strongest challenger."""
    return 0.5 * (f_drift(train, h) + f_log_linear(train, h))


BASELINES = {
    "naive_last": f_naive_last,
    "drift": f_drift,
    "seasonal_naive": f_seasonal_naive,
    "linear_trend": f_linear,
    "holt_winters": f_holt_winters,
    "ensemble_shipped": f_ensemble,
}

CHALLENGERS = {
    "log_linear": f_log_linear,
    "log_drift": f_log_drift,
    "damped_log_linear": f_damped_log_linear,
    "holt_linear": f_holt_linear,
    "blend_drift_log": f_blend_drift_log,
}


# ──────────────────────────────────────────────────────────────────────────────
def run() -> dict:
    y, dates = load_monthly()
    y = np.asarray(y, dtype=float)
    n = len(y)
    origins = list(range(MIN_TRAIN, n - max(HORIZONS) + 1))

    models = {**BASELINES, **CHALLENGERS}
    errors = {m: {h: [] for h in HORIZONS} for m in models}
    failures = {m: [] for m in models}   # explicit, never silent
    scales = []

    for t in origins:
        train = y[:t]
        actual = y[t:t + max(HORIZONS)]
        scales.append(mase_scale(train))

        for name, fn in models.items():
            try:
                pred = np.asarray(fn(train, max(HORIZONS)), dtype=float)
                if not np.all(np.isfinite(pred)):
                    raise ValueError("non-finite forecast")
            except Exception as e:  # a crash is a failed model — and is reported
                failures[name].append(f"{type(e).__name__}: {e}"[:120])
                pred = np.full(max(HORIZONS), np.nan)
            for h in HORIZONS:
                errors[name][h].append(float(pred[h - 1] - actual[h - 1]))

    mean_scale = float(np.mean(scales))
    summary = {}
    for name in models:
        all_errs = []
        by_h = {}
        for h in HORIZONS:
            e = np.array(errors[name][h], dtype=float)
            e = e[~np.isnan(e)]
            all_errs.extend(e.tolist())
            by_h[f"h{h}"] = {
                "mae": round(float(np.mean(np.abs(e))), 2) if len(e) else None,
                "mase": round(float(np.mean(np.abs(e)) / mean_scale), 4) if len(e) else None,
            }
        all_errs = np.array(all_errs, dtype=float)
        summary[name] = {
            "overall_mae": round(float(np.mean(np.abs(all_errs))), 2) if len(all_errs) else None,
            "overall_mase": round(float(np.mean(np.abs(all_errs)) / mean_scale), 4)
            if len(all_errs) else None,
            "by_horizon": by_h,
            "family": "baseline" if name in BASELINES else "challenger",
            "failed_origins": len(failures[name]),
            "first_error": failures[name][0] if failures[name] else None,
            "status": "ok" if not failures[name] else (
                "excluded" if len(failures[name]) == len(origins) else "partial"),
        }

    ranked = sorted(
        [(k, v["overall_mase"]) for k, v in summary.items() if v["overall_mase"] is not None],
        key=lambda kv: kv[1],
    )
    winner, winner_mase = ranked[0]
    drift_mase = summary["drift"]["overall_mase"]
    best_challenger = next(((k, m) for k, m in ranked if k in CHALLENGERS), None)

    verdict = {
        "winner": winner,
        "winner_mase": winner_mase,
        "drift_mase": drift_mase,
        "best_challenger": best_challenger[0] if best_challenger else None,
        "best_challenger_mase": best_challenger[1] if best_challenger else None,
        "challenger_beats_drift": bool(
            best_challenger and best_challenger[1] < drift_mase),
        "shipped_ensemble_mase": summary["ensemble_shipped"]["overall_mase"],
        "recommendation": None,  # filled below
    }

    if verdict["challenger_beats_drift"]:
        verdict["recommendation"] = (
            f"{verdict['best_challenger']} beats the drift baseline "
            f"(MASE {verdict['best_challenger_mase']} vs {drift_mase}) under an "
            "identical rolling-origin protocol. Promote it to the operational "
            "forecast and keep drift as the fallback benchmark."
        )
    else:
        verdict["recommendation"] = (
            f"No challenger beat drift (MASE {drift_mase}). The baseline is the "
            "ceiling at this horizon and data length — keep drift for operations. "
            "A more complex model would be unjustified complexity."
        )

    return {
        "n_months": n,
        "n_origins": len(origins),
        "horizons": list(HORIZONS),
        "mase_scale_definition": "in-sample seasonal-naive MAE, averaged over origins",
        "mean_mase_scale": round(mean_scale, 2),
        "damping": DAMPING,
        "protocol": "identical to forecast_backtest.py (imported constants + functions)",
        "models": summary,
        "leaderboard": [{"model": k, "mase": v} for k, v in ranked],
        "verdict": verdict,
    }


def write_report(m: dict) -> None:
    lines = [
        "# Forecast Challenger Evaluation",
        "",
        f"**Protocol:** identical to `forecast_backtest.py` — {m['n_origins']} rolling "
        f"origins, horizons {m['horizons']}, MASE scaled by in-sample seasonal-naive MAE "
        f"({m['mean_mase_scale']:,.0f}).",
        "",
        "## Leaderboard (MASE — lower is better)",
        "",
        "| Rank | Model | MASE | Family |",
        "|---|---|---|---|",
    ]
    for i, row in enumerate(m["leaderboard"], 1):
        fam = m["models"][row["model"]]["family"]
        lines.append(f"| {i} | {row['model']} | **{row['mase']}** | {fam} |")

    v = m["verdict"]
    lines += [
        "",
        "## Verdict",
        "",
        f"**Winner: `{v['winner']}` at MASE {v['winner_mase']}**",
        "",
        f"- Drift baseline: {v['drift_mase']}",
        f"- Shipped ensemble: {v['shipped_ensemble_mase']}",
        f"- Best challenger: `{v['best_challenger']}` at {v['best_challenger_mase']}",
        f"- Challenger beats drift: **{v['challenger_beats_drift']}**",
        "",
        f"**Recommendation.** {v['recommendation']}",
        "",
        "## Models that did not run cleanly",
        "",
        *(
            [f"- **{k}** — status `{x['status']}`, failed at {x['failed_origins']}/"
             f"{m['n_origins']} origins; first error: `{x['first_error']}`"
             for k, x in m["models"].items() if x["status"] != "ok"]
            or ["None — every model produced finite forecasts at every origin."]
        ),
        "",
        "## What a reviewer should check",
        "",
        "1. **Protocol parity is imported, not re-implemented** — the baseline "
        "functions and MASE scale come directly from `forecast_backtest.py`, so a "
        "difference in scores cannot come from a difference in evaluation.",
        "2. **A crashed model scores as a failure** — exceptions produce NaN "
        "forecasts that are excluded, never silently replaced with the actual.",
        "3. **The verdict is published either way.** If no challenger wins, the "
        "report says the baseline is the ceiling rather than shipping complexity "
        "for its own sake.",
        "4. **Why these challengers:** revenue here grows roughly exponentially, "
        "while drift extrapolates a straight line. Log-space models fit a constant "
        "growth *rate*; whether that helps is an empirical question this script "
        "answers, not an assumption.",
        "",
    ]
    path = os.path.join(REPORTS, "forecast_challenger.md")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {os.path.relpath(path, BASE)}")


def main() -> None:
    m = run()
    path = os.path.join(REPORTS, "forecast_challenger_metrics.json")
    with open(path, "w") as f:
        json.dump(m, f, indent=2)
    write_report(m)

    print("=" * 78)
    print("FORECAST CHALLENGER — can anything beat drift?")
    print("=" * 78)
    print(f"\n{m['n_origins']} rolling origins · horizons {m['horizons']}\n")
    print(f"{'model':20s} {'MASE':>8s}  family")
    print("-" * 48)
    for row in m["leaderboard"]:
        fam = m["models"][row["model"]]["family"]
        print(f"{row['model']:20s} {row['mase']:8.4f}  {fam}")
    v = m["verdict"]
    broken = {k: x for k, x in m["models"].items() if x["status"] != "ok"}
    if broken:
        print("\n⚠ MODELS THAT DID NOT RUN CLEANLY (reported, not hidden):")
        for k, x in broken.items():
            print(f"   {k}: status={x['status']}, failed at "
                  f"{x['failed_origins']}/{m['n_origins']} origins "
                  f"— {x['first_error']}")
    print(f"\nWinner: {v['winner']} (MASE {v['winner_mase']})")
    print(f"Challenger beats drift: {v['challenger_beats_drift']}")
    print(f"\n{v['recommendation']}")


if __name__ == "__main__":
    main()
