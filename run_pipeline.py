"""
run_pipeline.py — One-command E-Commerce Analytics Pipeline
Usage: python run_pipeline.py
"""
import subprocess, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))

scripts = [
    ("data/raw/generate_data.py",                   "1/5  Generating synthetic dataset"),
    ("python/eda/01_eda_preprocessing.py",           "2/5  EDA & preprocessing"),
    ("python/segmentation/02_rfm_segmentation.py",  "3/5  RFM customer segmentation"),
    ("python/churn/03_churn_analysis.py",            "4/5  Churn prediction model"),
    ("python/forecasting/04_revenue_forecasting.py", "5/5  Revenue forecasting"),
]

print("\n🚀 E-Commerce Analytics Pipeline\n" + "="*45)
for rel, label in scripts:
    print(f"\n▶  {label}")
    r = subprocess.run([sys.executable, os.path.join(BASE, rel)])
    if r.returncode != 0:
        print(f"✗  Failed at: {rel}"); sys.exit(1)
    print(f"   ✓ Complete")

print("\n" + "="*45)
print("✅  Pipeline complete!")
print("   → Open dashboard/dashboard.html in your browser")
