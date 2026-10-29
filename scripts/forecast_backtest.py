"""
forecast_backtest.py -- rolling-origin evaluation vs naive baselines
===================================================================
WHY THIS EXISTS: the shipped forecast (04_revenue_forecasting.py) reports test
MAE/RMSE for 3 months. Three points cannot establish that a model earns its
complexity. This script runs a ROLLING-ORIGIN (walk-forward) backtest over
every viable origin and answers the only question that matters:

    "Does the ensemble beat the naive baselines out-of-sample,
     consistently, and by enough to justify using it?"

Models compared at each origin:
  naive_last      ŷ(t+h) = y(t)                      (random walk / last value)
  drift           ŷ(t+h) = y(t) + h · (y(t)-y(1))/(t-1)
  seasonal_naive  ŷ(t+h) = y(t+h-12)                 (same month last year)
  linear_trend    OLS on t
  holt_winters    statsmodels (damped trend, multiplicative seasonality)
  ensemble        mean(linear_trend, holt_winters)   <- the shipped model

Metrics per origin and per horizon (h = 1..3):
  MAE, RMSE, MASE (scaled by in-sample seasonal-naive MAE, Hyndman definition)

Also evaluated: empirical coverage of the shipped bootstrap-95%-CI method
(mirrored at every origin). If the band under-covers, that is a finding.

Outputs:
  reports/forecast_backtest_metrics.json   (pinned by tests)
  reports/forecast_backtest.md
  docs/figures/20_forecast_backtest_mase.png

Run:  python scripts/forecast_backtest.py
"""
import json
import os
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "docs", "figures")
REPORTS = os.path.join(BASE, "reports")
os.makedirs(FIGS, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
PALETTE = ["#2563EB", "#D97706", "#DC2626", "#7C3AED", "#059669", "#DB2777"]

SEASON = 12
HORIZONS = (1, 2, 3)
MIN_TRAIN = 24          # first origin: at least 24 months of history
PSEUDO_TEST = 3         # mirrors 04's 3-month residual holdout
N_BOOT = 1000


def load_monthly():
    master = pd.read_csv(os.path.join(PROC, "master_orders.csv"), parse_dates=["order_date"])
    monthly = master.groupby(master["order_date"].dt.to_period("M"))["line_total"].sum()
    monthly = monthly.sort_index()
    return monthly.values.astype(float), monthly.index.to_timestamp()


# -- Models: fit on train array, forecast h steps ----------------------
def f_naive_last(train, h):
    return np.full(h, train[-1])


def f_drift(train, h):
    slope = (train[-1] - train[0]) / max(len(train) - 1, 1)
    return train[-1] + slope * np.arange(1, h + 1)


def f_seasonal_naive(train, h):
    out = []
    for k in range(1, h + 1):
        pos = len(train) + k - 1 - SEASON  # y(t+k-12) index
        out.append(train[pos] if pos >= 0 else train[-1])
    return np.array(out)


def f_linear(train, h):
    t = np.arange(len(train)).reshape(-1, 1)
    lr = LinearRegression().fit(t, train)
    return lr.predict(np.arange(len(train), len(train) + h).reshape(-1, 1))


def f_holt_winters(train, h):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    fit = ExponentialSmoothing(
        np.asarray(train, dtype=float), trend="add", damped_trend=True,
        seasonal="mul", seasonal_periods=SEASON,
    ).fit(optimized=True)
    return np.asarray(feat_forecast(fit, h), dtype=float)


def feat_forecast(fit, h):
    return fit.forecast(h)


def f_ensemble(train, h):
    return (f_linear(train, h) + f_holt_winters(train, h)) / 2


MODELS = {
    "naive_last": f_naive_last,
    "drift": f_drift,
    "seasonal_naive": f_seasonal_naive,
    "linear_trend": f_linear,
    "holt_winters": f_holt_winters,
    "ensemble": f_ensemble,
}


# -- MASE scale: in-sample seasonal-naive MAE (Hyndman) ---------------
def mase_scale(train):
    train = np.asarray(train, dtype=float)
    if len(train) <= SEASON:
        return float(np.mean(np.abs(np.diff(train))))
    return float(np.mean(np.abs(train[SEASON:] - train[:-SEASON])))


# -- Shipped CI method, mirrored at an origin -------------------------
def shipped_ci_band(series, horizon, n_boot=N_BOOT, seed=42):
    """Replicates 04's bootstrap: residuals from a 3-point pseudo-test at the
    end of the provided series, then refit on the full series and add resampled
    centered residuals to the point forecast."""
    s = np.asarray(series, dtype=float)
    if len(s) - PSEUDO_TEST < 2 * SEASON:
        # the inner pseudo-fit needs two full seasonal cycles for Holt-Winters
        return None
    train_sub, test_sub = s[:-PSEUDO_TEST], s[-PSEUDO_TEST:]
    ens_sub = f_ensemble(train_sub, PSEUDO_TEST)
    resid = (test_sub - ens_sub)
    resid = resid - resid.mean()
    point = f_ensemble(s, horizon)
    rng = np.random.default_rng(seed)
    boots = np.zeros((n_boot, horizon))
    for b in range(n_boot):
        boots[b] = point + rng.choice(resid, size=horizon, replace=True)
    return point, np.percentile(boots, 2.5, axis=0), np.percentile(boots, 97.5, axis=0)


def run_backtest():
    y, dates = load_monthly()
    n = len(y)
    origins = list(range(MIN_TRAIN, n - max(HORIZONS) + 1))  # leave room for h=3

    errors = {m: {h: [] for h in HORIZONS} for m in MODELS}
    scales = []
    coverage = {"n_checked": 0, "n_covered": 0, "by_horizon": {h: [0, 0] for h in HORIZONS}}
    per_origin = []

    for t in origins:
        train = y[:t]
        actual = y[t:t + max(HORIZONS)]
        scale = mase_scale(train)
        scales.append(scale)

        origin_row = {"origin_month": str(dates[t - 1].date())[:7], "mase_scale": round(scale, 2)}
        for name, fn in MODELS.items():
            pred = fn(train, max(HORIZONS))
            for h in HORIZONS:
                err = pred[h - 1] - actual[h - 1]
                errors[name][h].append(err)
            mae = float(np.mean(np.abs(pred[:len(actual)] - actual)))
            origin_row[name] = {"mae": round(mae, 2)}
        per_origin.append(origin_row)

        # coverage of the shipped CI method
        ci = shipped_ci_band(train, max(HORIZONS))
        if ci is not None:
            point, lo, hi = ci
            for h in HORIZONS:
                inside = lo[h - 1] <= actual[h - 1] <= hi[h - 1]
                coverage["n_checked"] += 1
                coverage["by_horizon"][h][1] += 1
                if inside:
                    coverage["n_covered"] += 1
                    coverage["by_horizon"][h][0] += 1

    # aggregate
    summary = {}
    mean_scale = float(np.mean(scales))
    for name in MODELS:
        by_h = {}
        all_errs = []
        for h in HORIZONS:
            e = np.array(errors[name][h])
            all_errs.extend(e.tolist())
            by_h[f"h{h}"] = {
                "mae": round(float(np.mean(np.abs(e))), 2),
                "rmse": round(float(np.sqrt(np.mean(e ** 2))), 2),
                "mase": round(float(np.mean(np.abs(e)) / mean_scale), 4),
            }
        all_errs = np.array(all_errs)
        summary[name] = {
            "overall_mae": round(float(np.mean(np.abs(all_errs))), 2),
            "overall_rmse": round(float(np.sqrt(np.mean(all_errs ** 2))), 2),
            "overall_mase": round(float(np.mean(np.abs(all_errs)) / mean_scale), 4),
            "by_horizon": by_h,
        }

    coverage_pct = round(coverage["n_covered"] / max(coverage["n_checked"], 1), 4)

    metrics = {
        "n_months": n,
        "n_origins": len(origins),
        "origins": [o["origin_month"] for o in per_origin],
        "horizons": list(HORIZONS),
        "mase_scale_definition": "in-sample seasonal-naive MAE (|y_t - y_t-12| mean), averaged over origins",
        "mean_mase_scale": round(mean_scale, 2),
        "models": summary,
        "coverage_95ci": {
            "empirical_coverage": coverage_pct,
            "n_checked": coverage["n_checked"],
            "by_horizon": {f"h{h}": round(v[0] / max(v[1], 1), 4) for h, v in coverage["by_horizon"].items()},
        },
        "per_origin": per_origin,
        "verdict": {},  # filled below
    }

    ens_mase = summary["ensemble"]["overall_mase"]
    snaive_mase = summary["seasonal_naive"]["overall_mase"]
    best_baseline = min(("naive_last", "drift", "seasonal_naive"),
                        key=lambda m: summary[m]["overall_mase"])
    metrics["verdict"] = {
        "ensemble_overall_mase": ens_mase,
        "seasonal_naive_overall_mase": snaive_mase,
        "best_baseline": best_baseline,
        "best_baseline_mase": summary[best_baseline]["overall_mase"],
        "ensemble_beats_best_baseline": bool(ens_mase < summary[best_baseline]["overall_mase"]),
        "recommendation": "",
    }
    if ens_mase < 1.0 and ens_mase < summary[best_baseline]["overall_mase"]:
        metrics["verdict"]["recommendation"] = (
            "Ship the ensemble: MASE < 1 and it beats the strongest naive baseline out-of-sample.")
    elif ens_mase < 1.0:
        metrics["verdict"]["recommendation"] = (
            f"The ensemble beats seasonal-naive in-sample scale (MASE<1) but NOT the "
            f"strongest baseline ({best_baseline}). Prefer the simpler baseline for "
            f"operational forecasts; keep the ensemble as a cross-check.")
    else:
        metrics["verdict"]["recommendation"] = (
            "Do NOT ship the ensemble as-is: MASE >= 1 means naive forecasts are at "
            "least as accurate. Investigate the series or simplify.")
    return metrics, (y, dates, summary, mean_scale)


def make_figure(bundle):
    y, dates, summary, mean_scale = bundle
    names = list(MODELS.keys())
    mases = [summary[n]["overall_mase"] for n in names]
    colors = [PALETTE[3] if n == "ensemble" else (PALETTE[2] if n == "seasonal_naive" else PALETTE[0])
              for n in names]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(names, mases, color=colors)
    ax.axvline(1.0, color="k", ls="--", alpha=0.6, label="MASE = 1 (seasonal-naive parity)")
    for b, m in zip(bars, mases):
        ax.text(b.get_width() + 0.01, b.get_y() + b.get_height() / 2, f"{m:.3f}", va="center")
    ax.set_xlabel("MASE (lower is better; < 1 beats the seasonal-naive scale)")
    ax.set_title("Rolling-origin backtest -- forecast accuracy vs naive baselines")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIGS, "20_forecast_backtest_mase.png"), dpi=150, bbox_inches="tight")
    plt.close()


def write_report(metrics):
    v = metrics["verdict"]
    lines = []
    a = lines.append
    a("# Revenue Forecast -- Rolling-Origin Backtest")
    a("### Does the ensemble earn its complexity? Out-of-sample evidence vs naive baselines")
    a("")
    a(f"> Generated by `scripts/forecast_backtest.py` · "
      f"**{metrics['n_origins']} origins** × {len(metrics['horizons'])} horizons "
      f"(h = {', '.join(map(str, metrics['horizons']))}) · monthly series "
      f"({metrics['n_months']} months)")
    a(f"> MASE scale: {metrics['mase_scale_definition']} = Rs.{metrics['mean_mase_scale']:,.0f}")
    a("")
    a("---")
    a("")
    a("## 1. The leaderboard (all origins pooled)")
    a("")
    a("| Model | MAE | RMSE | **MASE** | h=1 MASE | h=2 MASE | h=3 MASE |")
    a("|---|---|---|---|---|---|---|")
    for name, m in metrics["models"].items():
        star = " ⭐" if name == "ensemble" else ""
        a(f"| {name}{star} | {m['overall_mae']:,.0f} | {m['overall_rmse']:,.0f} | "
          f"**{m['overall_mase']:.3f}** | {m['by_horizon']['h1']['mase']:.3f} | "
          f"{m['by_horizon']['h2']['mase']:.3f} | {m['by_horizon']['h3']['mase']:.3f} |")
    a("")
    a("![MASE leaderboard](../docs/figures/20_forecast_backtest_mase.png)")
    a("")
    a("## 2. The verdict")
    a("")
    a(f"- Ensemble overall MASE: **{v['ensemble_overall_mase']:.3f}**")
    a(f"- Best naive baseline: **{v['best_baseline']}** (MASE {v['best_baseline_mase']:.3f})")
    a(f"- Ensemble beats best baseline: **{'YES' if v['ensemble_beats_best_baseline'] else 'NO'}**")
    a("")
    a(f"> **{v['recommendation']}**")
    a("")
    a("## 3. Is the confidence band honest? (empirical coverage)")
    a("")
    cov = metrics["coverage_95ci"]
    a(f"The shipped bootstrap-95% CI method (residuals from a 3-point holdout) was "
      f"mirrored at every origin. Empirical coverage of the nominal 95% band: "
      f"**{cov['empirical_coverage']:.1%}** ({cov['n_checked']} forecast points).")
    a("")
    a("| Horizon | Empirical coverage |")
    a("|---|---|")
    for h, c in cov["by_horizon"].items():
        a(f"| {h} | {c:.1%} |")
    a("")
    if cov["empirical_coverage"] < 0.85:
        a("> ⚠️ **Finding:** the band under-covers. Three residuals are a very small "
          "sample to estimate forecast variance -- treat the shipped 95% CI as "
          "*indicative width*, not a calibrated interval. A real deployment should "
          "estimate error variance from the full rolling-origin residual history "
          f"(this backtest: {metrics['n_origins']} origins × 3 horizons).")
    else:
        a("> Coverage is close to nominal; the band is usable as shipped.")
    a("")
    a("## 4. Per-origin detail")
    a("")
    a("| Origin (last train month) | MASE scale | " +
      " | ".join(MODELS.keys()) + " (MAE) |")
    a("|---|---|" + "---|" * len(MODELS))
    for o in metrics["per_origin"]:
        row = f"| {o['origin_month']} | {o['mase_scale']:,.0f} | "
        row += " | ".join(f"{o[n]['mae']:,.0f}" for n in MODELS.keys())
        a(row + " |")
    a("")
    a("## 5. Limitations")
    a("")
    a("1. Synthetic revenue series (36 months) -- the *method* transfers, the numbers don't.")
    a("2. Only 3-step horizons are evaluated; the shipped 6-month forecast extrapolates "
      "beyond anything this backtest can verify.")
    a(f"3. MASE scaling uses seasonal-naive in-sample error (period {12}); comparisons "
      "assume monthly seasonality is real in the series.")
    a("4. Origins overlap (expanding window) -- per-origin MAEs are not independent; "
      "the leaderboard is a summary, not a significance test.")
    a("5. The Holt-Winters configuration is fixed (damped trend, multiplicative "
      "seasonality); no per-origin hyperparameter search was performed.")
    a("")
    a("---")
    a("")
    a("*Numbers pinned by `tests/test_forecast_backtest.py` against "
      "`reports/forecast_backtest_metrics.json`.*")
    with open(os.path.join(REPORTS, "forecast_backtest.md"), "w") as f:
        f.write("\n".join(lines))


def main():
    print("Loading monthly revenue series...")
    metrics, bundle = run_backtest()
    v = metrics["verdict"]
    print(f"origins: {metrics['n_origins']} | ensemble MASE {v['ensemble_overall_mase']:.3f} | "
          f"best baseline {v['best_baseline']} {v['best_baseline_mase']:.3f}")
    print(f"95% CI empirical coverage: {metrics['coverage_95ci']['empirical_coverage']:.1%}")
    make_figure(bundle)
    write_report(metrics)
    with open(os.path.join(REPORTS, "forecast_backtest_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print("Wrote reports/forecast_backtest.md + forecast_backtest_metrics.json")
    print("Wrote docs/figures/20_forecast_backtest_mase.png")


if __name__ == "__main__":
    main()
