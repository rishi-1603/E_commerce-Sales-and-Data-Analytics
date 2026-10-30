# Live Demo & Offline Fallback Guide — E-Commerce Analytics
**Primary Live Web App:** https://ecomanalytics-dashboard.vercel.app/  
**API Health Status:** https://ecomanalytics-dashboard.vercel.app/api/analytics/kpis  

---

## 1. What to Do If the Cloud Instance is Sleeping or Cold-Starting
Cloud-hosted serverless containers (e.g., Vercel / Render / Streamlit Community Cloud) may take 10-20 seconds to spin up from an idle state. If reviewing during an interview:

### Option A: Local Instant Execution (Recommended Fallback)
```bash
# Clone and enter directory
git clone https://github.com/rishi-1603/E_commerce-Sales-and-Data-Analytics.git
cd E_commerce-Sales-and-Data-Analytics

# Install requirements
pip install -r requirements.txt

# Launch API server & local dashboard
uvicorn api.main:app --reload --port 8000
```
Then open `http://localhost:8000` in your browser.

### Option B: Quick CLI Smoke-Test (5 Seconds)
To inspect core revenue, customer, and SKU metrics directly without spinning up a browser:
```bash
python -m src.metrics --summary
```

### Option C: Inspect Verified Static Artifacts
- **Power BI DAX Measures:** See `powerbi/dax_measures.md`
- **Reconciliation Parity Proof:** See `powerbi/reconciliation_matrix.csv`
- **Executive Findings Report:** See `docs/EXECUTIVE_FINDINGS_REPORT.md`
