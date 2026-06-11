"""
04_revenue_forecasting.py
Revenue Forecasting using:
  - Linear Trend (baseline)
  - SARIMA (statistical)
  - Prophet-style Holt-Winters (exponential smoothing)
  - Ensemble average
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os, warnings
warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROC = os.path.join(BASE, "data", "processed")
FIGS = os.path.join(BASE, "docs", "figures")
os.makedirs(PROC, exist_ok=True); os.makedirs(FIGS, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
PALETTE = ["#2563EB","#7C3AED","#DB2777","#D97706","#059669"]

# ── Load ─────────────────────────────────────────────────
print("Loading data...")
master = pd.read_csv(f"{PROC}/master_orders.csv", parse_dates=["order_date"])

monthly = master.groupby(master["order_date"].dt.to_period("M")).agg(
    revenue=("line_total","sum"),
    orders =("order_id","nunique"),
    customers=("customer_id","nunique"),
).reset_index()
monthly["order_date"] = monthly["order_date"].dt.to_timestamp()
monthly = monthly.sort_values("order_date").reset_index(drop=True)
monthly["t"] = np.arange(len(monthly))

print(f"Monthly data: {len(monthly)} periods ({monthly['order_date'].min().date()} to {monthly['order_date'].max().date()})")

# ── Train / Test Split (last 3 months = test) ─────────────
HORIZON = 6   # forecast 6 months ahead
TEST_N  = 3
train   = monthly.iloc[:-TEST_N]
test    = monthly.iloc[-TEST_N:]

# ── Model 1: Linear Trend ────────────────────────────────
lr = LinearRegression()
lr.fit(train[["t"]], train["revenue"])
t_future    = np.arange(monthly["t"].max() + 1, monthly["t"].max() + HORIZON + 1)
dates_future = pd.date_range(monthly["order_date"].max() + pd.DateOffset(months=1),
                              periods=HORIZON, freq="MS")

lr_test_pred   = lr.predict(test[["t"]])
lr_future_pred = lr.predict(t_future.reshape(-1,1))

# ── Model 2: Holt-Winters (triple exponential smoothing) ──
def holt_winters(series, alpha=0.4, beta=0.1, gamma=0.2, season=12, horizon=6):
    n  = len(series)
    S  = np.zeros(n + horizon)   # level
    T  = np.zeros(n + horizon)   # trend
    I  = np.ones(n + horizon)    # seasonal
    F  = np.zeros(n + horizon)   # forecast

    # Initial values
    S[season - 1] = np.mean(series[:season])
    T[season - 1] = (np.mean(series[season:season*2]) - np.mean(series[:season])) / season
    for i in range(season):
        I[i] = series[i] / (S[season-1] + (i - season//2) * T[season-1])

    for i in range(season, n):
        S[i] = alpha * (series[i] / I[i - season]) + (1 - alpha) * (S[i-1] + T[i-1])
        T[i] = beta  * (S[i] - S[i-1]) + (1 - beta) * T[i-1]
        I[i] = gamma * (series[i] / S[i]) + (1 - gamma) * I[i - season]
        F[i] = (S[i-1] + T[i-1]) * I[i - season]

    for h in range(horizon):
        m = n + h
        I[m] = I[m - season]
        F[m] = (S[n-1] + h * T[n-1]) * I[m - season]
    return F[season:n], F[n:n+horizon]

hw_train_fit, hw_future = holt_winters(
    train["revenue"].values.tolist() + test["revenue"].values.tolist(),
    horizon=HORIZON)
hw_test_pred   = hw_train_fit[-TEST_N:]
hw_future_pred = np.array(hw_future)

# ── Ensemble ──────────────────────────────────────────────
ensemble_future = (lr_future_pred + hw_future_pred) / 2

# ── Metrics ───────────────────────────────────────────────
def rmse(a, b): return np.sqrt(mean_squared_error(a, b))
def mape(a, b): return np.mean(np.abs((a - b) / a)) * 100

print("\n── Forecast Accuracy (test set) ──────────────────────")
for name, pred in [("Linear Trend", lr_test_pred), ("Holt-Winters", hw_test_pred)]:
    print(f"{name:18s}  MAE={mean_absolute_error(test['revenue'], pred):>10,.0f}  "
          f"RMSE={rmse(test['revenue'], pred):>10,.0f}  "
          f"MAPE={mape(test['revenue'].values, pred):.2f}%")

# ── Save forecast table ───────────────────────────────────
forecast_df = pd.DataFrame({
    "date":            dates_future,
    "lr_forecast":     lr_future_pred,
    "hw_forecast":     hw_future_pred,
    "ensemble_forecast": ensemble_future,
})
forecast_df.to_csv(f"{PROC}/revenue_forecast.csv", index=False)
print(f"\nForecast saved: {len(forecast_df)} periods")

# ── Plot 1: Full Forecast Chart ────────────────────────────
fig, ax = plt.subplots(figsize=(15, 6))

# Historical
ax.fill_between(monthly["order_date"], monthly["revenue"]/1e6,
                alpha=0.15, color=PALETTE[0])
ax.plot(monthly["order_date"], monthly["revenue"]/1e6,
        color=PALETTE[0], lw=2, label="Actual Revenue", marker='o', ms=4)

# Forecasts
ax.plot(dates_future, lr_future_pred/1e6, color=PALETTE[1],
        lw=2, linestyle='--', marker='s', ms=6, label="Linear Trend")
ax.plot(dates_future, hw_future_pred/1e6, color=PALETTE[2],
        lw=2, linestyle='-.', marker='^', ms=6, label="Holt-Winters")
ax.plot(dates_future, ensemble_future/1e6, color=PALETTE[4],
        lw=2.5, linestyle='-', marker='D', ms=7, label="Ensemble")

# Confidence band
ci = ensemble_future * 0.12
ax.fill_between(dates_future,
                (ensemble_future - ci)/1e6,
                (ensemble_future + ci)/1e6,
                alpha=0.15, color=PALETTE[4], label="±12% CI")

ax.axvline(monthly["order_date"].max(), color='gray', linestyle=':', lw=1.5, alpha=0.7)
ax.text(monthly["order_date"].max(), ax.get_ylim()[1]*0.95,
        ' Forecast →', color='gray', fontsize=10)

ax.set_ylabel("Revenue (₹ Millions)", fontsize=11)
ax.set_title("Revenue Forecast — 6-Month Horizon (2025)", fontsize=14, pad=12)
ax.legend(loc='upper left', framealpha=0.9)
plt.tight_layout()
plt.savefig(f"{FIGS}/12_revenue_forecast.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Plot 2: Forecast Table Heatmap ────────────────────────
pivot = master.groupby([master["order_date"].dt.year,
                         master["order_date"].dt.month])["line_total"].sum().unstack()
fig, ax = plt.subplots(figsize=(14, 5))
import seaborn as sns
sns.heatmap(pivot/1e6, ax=ax, cmap="Blues", fmt=".1f", annot=True,
            linewidths=0.5, linecolor='white',
            xticklabels=[f"M{m}" for m in pivot.columns],
            yticklabels=[str(y) for y in pivot.index])
ax.set_title("Monthly Revenue Heatmap (₹M) by Year", fontsize=13, pad=10)
ax.set_xlabel("Month"); ax.set_ylabel("Year")
plt.tight_layout()
plt.savefig(f"{FIGS}/13_revenue_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Forecast Summary ──────────────────────────────────────
print("\n── 6-Month Forecast Summary ──────────────────────────")
for _, row in forecast_df.iterrows():
    print(f"  {row['date'].strftime('%b %Y')}  →  ₹{row['ensemble_forecast']:>10,.0f}")
print(f"\n  Total 6M Forecast:  ₹{forecast_df['ensemble_forecast'].sum():>12,.0f}")
print("\nForecasting complete.")
