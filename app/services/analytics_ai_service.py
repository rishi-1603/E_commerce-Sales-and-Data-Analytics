"""
analytics_ai_service.py — Simple EcomAI Business Analyst
=========================================================
Architecture:
    1. User asks a question
    2. Python determines relevant analysis & calculates KPIs from verified data
    3. Results sent to Gemini for professional business interpretation
    4. Dashboard displays the answer with evidence

Principles:
- LLM NEVER calculates - only interprets verified Python results
- All numbers come from data/processed/*.csv via pandas
- Synthetic data disclosure always included
- Respect existing metric definitions in data/metrics.json
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

import pandas as pd
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger("commerce_api")

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROC = os.path.join(BASE, "data", "processed")


@dataclass
class BusinessKPIs:
    """Core business KPIs calculated from data."""
    total_revenue: float
    total_profit: float
    gross_margin_pct: float
    total_orders: int
    active_customers: int
    aov: float
    top_category: str
    top_region: str
    revenue_by_category: Dict[str, float]
    revenue_by_region: Dict[str, float]
    order_status_distribution: Dict[str, int]


@dataclass
class CustomerAnalysis:
    """Customer segmentation analysis."""
    rfm_segments: List[Dict[str, Any]]
    cooling_off_customers: int
    cooling_off_historical_spend: float
    churn_rate_pct: float
    inactive_customers_180d: int


@dataclass
class BusinessStatus:
    """Business health status assessments."""
    revenue_status: str
    profitability_status: str
    customer_status: str
    sales_status: str
    operational_status: str


@dataclass
class AnalysisResult:
    """Complete analysis package sent to Gemini."""
    question: str
    kpis: BusinessKPIs
    customer_analysis: CustomerAnalysis
    business_status: BusinessStatus
    monthly_revenue: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]
    generated_at: str
    data_period: Dict[str, str]


class AnalyticsAIService:
    """Simple EcomAI Analyst - Python calculates, Gemini explains."""

    _gemini_model = None
    _data_cache = {}

    @classmethod
    def _get_gemini(cls):
        """Lazy-initialize the Gemini client."""
        if cls._gemini_model is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            cls._gemini_model = genai.Client(api_key=api_key)
        return cls._gemini_model

    @classmethod
    def _load_data(cls) -> Dict[str, pd.DataFrame]:
        """Load all processed data files once."""
        if not cls._data_cache:
            cls._data_cache = {
                "master": pd.read_csv(f"{PROC}/master_orders.csv", parse_dates=["order_date"]),
                "rfm": pd.read_csv(f"{PROC}/rfm_segments.csv"),
                "churn": pd.read_csv(f"{PROC}/churn_features.csv"),
                "products": pd.read_csv(f"{PROC}/product_profitability.csv"),
                "forecast": pd.read_csv(f"{PROC}/revenue_forecast.csv", parse_dates=["date"]),
            }
        return cls._data_cache

    @classmethod
    def calculate_kpis(cls) -> BusinessKPIs:
        """Calculate all core business KPIs from master_orders."""
        data = cls._load_data()
        master = data["master"]

        # Valid orders = Delivered + Processing (per metric definitions)
        valid = master[master["status"].isin(["Delivered", "Processing"])]

        revenue = valid["line_total"].sum()
        profit = valid["profit"].sum()
        margin = (profit / revenue * 100) if revenue > 0 else 0
        orders = valid["order_id"].nunique()
        customers = valid["customer_id"].nunique()
        aov = revenue / orders if orders > 0 else 0

        rev_by_cat = valid.groupby("category")["line_total"].sum().sort_values(ascending=False)
        rev_by_reg = valid.groupby("region")["line_total"].sum().sort_values(ascending=False)
        status_dist = master["status"].value_counts().to_dict()

        return BusinessKPIs(
            total_revenue=round(revenue, 2),
            total_profit=round(profit, 2),
            gross_margin_pct=round(margin, 1),
            total_orders=int(orders),
            active_customers=int(customers),
            aov=round(aov, 2),
            top_category=str(rev_by_cat.index[0]) if len(rev_by_cat) else "N/A",
            top_region=str(rev_by_reg.index[0]) if len(rev_by_reg) else "N/A",
            revenue_by_category={k: round(v, 2) for k, v in rev_by_cat.items()},
            revenue_by_region={k: round(v, 2) for k, v in rev_by_reg.items()},
            order_status_distribution={k: int(v) for k, v in status_dist.items()},
        )

    @classmethod
    def calculate_customer_analysis(cls) -> CustomerAnalysis:
        """Calculate customer segmentation and churn metrics."""
        data = cls._load_data()
        rfm = data["rfm"]
        churn = data["churn"]

        # RFM segments
        seg = rfm.groupby("segment").agg(
            customers=("customer_id", "count"),
            spend=("monetary", "sum")
        ).sort_values("spend", ascending=False).reset_index()

        rfm_segments = [
            {"segment": str(row["segment"]), "customers": int(row["customers"]),
             "historical_spend": round(float(row["spend"]), 2)}
            for _, row in seg.iterrows()
        ]

        # Cooling-off customers (Medium + High risk)
        at_risk = churn[churn["churn_risk"].isin(["Medium Risk", "High Risk"])]
        cooling_off = int(len(at_risk))
        cooling_off_spend = round(float(at_risk["total_revenue"].sum()), 2)

        # Churn rate (model label prevalence)
        churn_rate = round(float(churn["churned"].mean() * 100), 1)

        # Raw 180-day inactivity (Delivered + Returned)
        raw = pd.read_csv(f"{BASE}/data/raw/orders.csv", parse_dates=["order_date"])
        end_date = raw["order_date"].max()
        last_purchase = raw[raw["status"].isin(["Delivered", "Returned"])].groupby("customer_id")["order_date"].max()
        inactive = int((last_purchase < end_date - pd.Timedelta(days=180)).sum())

        return CustomerAnalysis(
            rfm_segments=rfm_segments,
            cooling_off_customers=cooling_off,
            cooling_off_historical_spend=cooling_off_spend,
            churn_rate_pct=churn_rate,
            inactive_customers_180d=inactive,
        )

    @classmethod
    def calculate_business_status(cls, kpis: BusinessKPIs, cust: CustomerAnalysis,
                                   monthly: List[Dict[str, Any]]) -> BusinessStatus:
        """Determine business health status using transparent rules."""
        statuses = {}

        # Revenue status: compare last two months
        if len(monthly) >= 2:
            curr = monthly[-1]["revenue"]
            prev = monthly[-2]["revenue"]
            pct_change = (curr - prev) / prev * 100 if prev > 0 else 0
            if pct_change >= 10:
                statuses["revenue"] = "Positive"
            elif pct_change >= 0:
                statuses["revenue"] = "Stable"
            elif pct_change >= -10:
                statuses["revenue"] = "Watch"
            else:
                statuses["revenue"] = "Needs Attention"
        else:
            statuses["revenue"] = "Stable"

        # Profitability status
        if kpis.gross_margin_pct >= 50:
            statuses["profitability"] = "Positive"
        elif kpis.gross_margin_pct >= 40:
            statuses["profitability"] = "Stable"
        elif kpis.gross_margin_pct >= 30:
            statuses["profitability"] = "Watch"
        else:
            statuses["profitability"] = "Needs Attention"

        # Customer status
        if cust.churn_rate_pct <= 20:
            statuses["customer"] = "Positive"
        elif cust.churn_rate_pct <= 30:
            statuses["customer"] = "Stable"
        elif cust.churn_rate_pct <= 40:
            statuses["customer"] = "Watch"
        else:
            statuses["customer"] = "Needs Attention"

        # Sales status: AOV trend
        if len(monthly) >= 2:
            curr_aov = monthly[-1]["revenue"] / monthly[-1]["orders"] if monthly[-1]["orders"] > 0 else 0
            prev_aov = monthly[-2]["revenue"] / monthly[-2]["orders"] if monthly[-2]["orders"] > 0 else 0
            aov_change = (curr_aov - prev_aov) / prev_aov * 100 if prev_aov > 0 else 0
            if aov_change >= 5:
                statuses["sales"] = "Positive"
            elif aov_change >= -5:
                statuses["sales"] = "Stable"
            else:
                statuses["sales"] = "Watch"
        else:
            statuses["sales"] = "Stable"

        # Operational status: order fulfilment
        total = sum(kpis.order_status_distribution.values())
        delivered = kpis.order_status_distribution.get("Delivered", 0)
        fulfilment_rate = delivered / total * 100 if total > 0 else 0
        if fulfilment_rate >= 80:
            statuses["operational"] = "Positive"
        elif fulfilment_rate >= 70:
            statuses["operational"] = "Stable"
        elif fulfilment_rate >= 60:
            statuses["operational"] = "Watch"
        else:
            statuses["operational"] = "Needs Attention"

        return BusinessStatus(
            revenue_status=statuses["revenue"],
            profitability_status=statuses["profitability"],
            customer_status=statuses["customer"],
            sales_status=statuses["sales"],
            operational_status=statuses["operational"],
        )

    @classmethod
    def get_monthly_revenue(cls) -> List[Dict[str, Any]]:
        """Get monthly revenue trend from master_orders."""
        data = cls._load_data()
        master = data["master"]
        valid = master[master["status"].isin(["Delivered", "Processing"])]
        valid = valid.copy()
        valid["month"] = valid["order_date"].dt.to_period("M")
        monthly = valid.groupby("month").agg(
            revenue=("line_total", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique")
        ).reset_index()
        monthly["month"] = monthly["month"].dt.strftime("%Y-%m")
        return [
            {"month": row["month"], "revenue": round(row["revenue"], 2),
             "orders": int(row["orders"]), "customers": int(row["customers"])}
            for _, row in monthly.iterrows()
        ]

    @classmethod
    def get_top_products(cls, n: int = 10) -> List[Dict[str, Any]]:
        """Get top products by profit."""
        data = cls._load_data()
        prod = data["products"]
        top = prod.nlargest(n, "profit")
        return [
            {"name": str(row["product_name"]), "category": str(row["category"]),
             "revenue": round(float(row["revenue"]), 2),
             "profit": round(float(row["profit"]), 2),
             "margin_pct": round(float(row["margin_pct"]), 1),
             "units_sold": int(row["units_sold"])}
            for _, row in top.iterrows()
        ]

    @classmethod
    def perform_full_analysis(cls, question: str) -> AnalysisResult:
        """Run complete business analysis for a question."""
        kpis = cls.calculate_kpis()
        customer = cls.calculate_customer_analysis()
        monthly = cls.get_monthly_revenue()
        status = cls.calculate_business_status(kpis, customer, monthly)
        top_products = cls.get_top_products()

        data = cls._load_data()
        master = data["master"]

        return AnalysisResult(
            question=question,
            kpis=kpis,
            customer_analysis=customer,
            business_status=status,
            monthly_revenue=monthly,
            top_products=top_products,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            data_period={
                "start": str(master["order_date"].min().date()),
                "end": str(master["order_date"].max().date()),
            },
        )

    @classmethod
    def _build_gemini_prompt(cls, analysis: AnalysisResult) -> str:
        """Build the prompt for Gemini with analysis results."""
        # Convert to JSON-serializable dict
        analysis_dict = {
            "question": analysis.question,
            "kpis": asdict(analysis.kpis),
            "customer_analysis": asdict(analysis.customer_analysis),
            "business_status": asdict(analysis.business_status),
            "monthly_revenue": analysis.monthly_revenue,
            "top_products": analysis.top_products,
            "generated_at": analysis.generated_at,
            "data_period": analysis.data_period,
        }

        # System prompt for Gemini
        system_prompt = """You are a Senior E-Commerce Business Analyst.
Your job: explain verified analysis results in professional business language.
You receive verified calculations from Python (pandas) - you NEVER calculate.

RULES:
1. Use only the numbers provided. Never invent, estimate, or hallucinate figures.
2. Distinguish: Gross profit ≠ net profit. Revenue = Delivered + Processing orders only.
3. Returned (1,223 orders, 10.2%) is its own exit status, not subtracted from Delivered.
4. Churn rate = model label prevalence on scored population, not business churn rate.
5. Cooling-off customers' spend = historical, NOT future revenue at risk.
6. Forecast = historical backtest (Jan-Jun 2025), not live projection.
7. Win-back experiment = DESIGN ONLY, no campaign has been run.
7. State limitations when data is insufficient.
8. Avoid generic chatbot language. Be direct and specific.
9. When explaining changes, cite the actual period comparisons.
10. Format: Executive Summary, Key KPIs, Business Status, Key Findings, Growth Opportunities, Business Risks, Recommendations, Next Steps. Omit sections not relevant to the question.

Return plain text (no markdown unless asked)."""

        user_prompt = f"""Analyze this business question: "{analysis.question}"

VERIFIED ANALYSIS RESULTS:
{json.dumps(analysis_dict, indent=2)}

Provide a professional business analysis following the structure above."""

        return system_prompt, user_prompt

    @classmethod
    def ask(cls, question: str) -> Dict[str, Any]:
        """
        Main entry point: analyze question → calculate KPIs → Gemini explains → return result.
        """
        # 1. Run Python analysis
        analysis = cls.perform_full_analysis(question)

        # 2. Get Gemini interpretation
        try:
            client = cls._get_gemini()
            system_prompt, user_prompt = cls._build_gemini_prompt(analysis)

            # Correct format for google-genai SDK: list of ContentDicts with role and parts
            contents = [
                types.Content(role="user", parts=[types.Part(text=system_prompt)]),
                types.Content(role="model", parts=[types.Part(text="Understood. I will provide professional business analysis based only on the verified numbers you provide.")]),
                types.Content(role="user", parts=[types.Part(text=user_prompt)]),
            ]

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                ),
            )

            gemini_text = response.text if response.text else "Analysis completed but LLM response was empty."
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            gemini_text = f"Analysis computed successfully. LLM interpretation unavailable: {str(e)}"

        # 3. Build response
        return {
            "question": question,
            "analysis": {
                "kpis": asdict(analysis.kpis),
                "customer_analysis": asdict(analysis.customer_analysis),
                "business_status": asdict(analysis.business_status),
                "monthly_revenue": analysis.monthly_revenue,
                "top_products": analysis.top_products,
                "data_period": analysis.data_period,
            },
            "gemini_response": gemini_text,
            "generated_at": analysis.generated_at,
            "disclaimer": (
                "All figures are calculated from the synthetic, seeded dataset "
                "(12,000 orders / 1,991 customers / 150 SKUs, 2022-2024). "
                "Gross profit is revenue minus product cost, not net income. "
                "Churn rates are model label prevalences, not business churn rates. "
                "Cooling-off spend is historical, not future revenue at risk. "
                "No win-back campaign has been executed."
            ),
        }