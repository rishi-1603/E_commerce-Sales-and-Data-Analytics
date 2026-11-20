"""
test_analytics_ai_service.py — tests for the simple EcomAI Analyst service.
==========================================================================
Verifies:
1. KPI calculations match existing pinned values
2. Customer analysis matches existing metrics
3. Business status rules work correctly
4. Unsupported questions handled
5. API failure handling
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest
from unittest.mock import patch, MagicMock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

DASHBOARD_COPIES = [
    "dashboard.html",
    "index.html",
    "dashboard/dashboard.html",
    "dashboard/index.html",
]

from app.services.analytics_ai_service import AnalyticsAIService


class TestKPICalculations:
    """Core KPI calculations must match the pinned metrics."""

    def test_calculate_kpis_matches_metrics_json(self):
        kpis = AnalyticsAIService.calculate_kpis()
        # From data/metrics.json
        assert kpis.total_revenue == pytest.approx(59283619.32, rel=1e-3)  # ₹5.93 Cr
        assert kpis.gross_margin_pct == pytest.approx(54.0, abs=0.1)
        assert kpis.total_orders == 9933
        assert kpis.active_customers == 1991
        assert kpis.aov == pytest.approx(5968.35, rel=1e-3)
        assert kpis.top_category == "Sports"
        assert kpis.top_region == "West"

    def test_revenue_by_category_sums_to_total(self):
        kpis = AnalyticsAIService.calculate_kpis()
        total = sum(kpis.revenue_by_category.values())
        assert total == pytest.approx(kpis.total_revenue, rel=1e-6)

    def test_order_status_distribution_matches_funnel(self):
        kpis = AnalyticsAIService.calculate_kpis()
        # master_orders.csv only contains Delivered + Processing (valid revenue orders)
        # The full funnel with all 4 statuses comes from raw orders.csv
        assert kpis.order_status_distribution.get("Delivered") == 19713  # lines, not orders
        assert kpis.order_status_distribution.get("Processing") == 1353
        assert "Cancelled" not in kpis.order_status_distribution
        assert "Returned" not in kpis.order_status_distribution
        assert sum(kpis.order_status_distribution.values()) == 21066


class TestCustomerAnalysis:
    """Customer segmentation and churn metrics."""

    def test_calculate_customer_analysis_matches_metrics(self):
        cust = AnalyticsAIService.calculate_customer_analysis()
        # From data/metrics.json
        assert cust.cooling_off_customers == 441
        assert cust.cooling_off_historical_spend == pytest.approx(12998872.58, rel=1e-3)
        assert cust.churn_rate_pct == pytest.approx(23.5, abs=0.1)
        # Raw inactivity from dashboard AI answers
        assert cust.inactive_customers_180d == 376

    def test_rfm_segments_complete_and_ordered(self):
        cust = AnalyticsAIService.calculate_customer_analysis()
        assert len(cust.rfm_segments) == 8
        # Sorted by spend descending
        spends = [s["historical_spend"] for s in cust.rfm_segments]
        assert spends == sorted(spends, reverse=True)
        # All expected segments present
        segment_names = {s["segment"] for s in cust.rfm_segments}
        expected = {"Champions", "Loyal Customers", "Potential Loyalists",
                    "Recent Customers", "About To Sleep", "Needs Attention",
                    "At Risk", "Lost Customers"}
        assert segment_names == expected


class TestBusinessStatus:
    """Business status rules are transparent and deterministic."""

    def test_revenue_status_positive_when_growth_ge_10pct(self):
        # Build mock monthly data with 10%+ growth
        monthly = [
            {"revenue": 100, "orders": 10},
            {"revenue": 110, "orders": 11},  # 10% growth
        ]
        kpis = AnalyticsAIService.calculate_kpis()
        cust = AnalyticsAIService.calculate_customer_analysis()
        status = AnalyticsAIService.calculate_business_status(kpis, cust, monthly)
        assert status.revenue_status == "Positive"

    def test_revenue_status_watch_when_decline_5_to_10pct(self):
        monthly = [
            {"revenue": 100, "orders": 10},
            {"revenue": 95, "orders": 10},  # -5% decline
        ]
        kpis = AnalyticsAIService.calculate_kpis()
        cust = AnalyticsAIService.calculate_customer_analysis()
        status = AnalyticsAIService.calculate_business_status(kpis, cust, monthly)
        assert status.revenue_status == "Watch"

    def test_profitability_status_from_margin(self):
        monthly = [{"revenue": 100, "orders": 10}, {"revenue": 100, "orders": 10}]
        kpis = AnalyticsAIService.calculate_kpis()
        # Margin is 54% -> Positive
        cust = AnalyticsAIService.calculate_customer_analysis()
        status = AnalyticsAIService.calculate_business_status(kpis, cust, monthly)
        assert status.profitability_status == "Positive"

    def test_customer_status_from_churn_rate(self):
        monthly = [{"revenue": 100, "orders": 10}, {"revenue": 100, "orders": 10}]
        kpis = AnalyticsAIService.calculate_kpis()
        # Churn rate 23.5% -> Stable (20-30%)
        cust = AnalyticsAIService.calculate_customer_analysis()
        status = AnalyticsAIService.calculate_business_status(kpis, cust, monthly)
        assert status.customer_status == "Stable"


class TestFullAnalysis:
    """End-to-end analysis pipeline."""

    def test_perform_full_analysis_returns_complete_structure(self):
        result = AnalyticsAIService.perform_full_analysis("Test question")
        assert result.question == "Test question"
        assert isinstance(result.kpis, object)
        assert isinstance(result.customer_analysis, object)
        assert isinstance(result.business_status, object)
        assert isinstance(result.monthly_revenue, list)
        assert isinstance(result.top_products, list)
        assert "start" in result.data_period
        assert "end" in result.data_period

    def test_monthly_revenue_has_required_fields(self):
        monthly = AnalyticsAIService.get_monthly_revenue()
        assert len(monthly) > 0
        for m in monthly:
            assert "month" in m
            assert "revenue" in m
            assert "orders" in m
            assert "customers" in m

    def test_top_products_sorted_by_profit(self):
        products = AnalyticsAIService.get_top_products(5)
        assert len(products) == 5
        profits = [p["profit"] for p in products]
        assert profits == sorted(profits, reverse=True)


class TestGeminiIntegration:
    """Gemini API integration - mocked."""

    @patch("app.services.analytics_ai_service.genai")
    def test_ask_returns_structured_response(self, mock_genai):
        # Mock the Gemini response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test business analysis from Gemini."
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Need to reset the class variable
        AnalyticsAIService._gemini_model = None

        # Mock environment variable
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            result = AnalyticsAIService.ask("Test question")

        assert result["question"] == "Test question"
        assert "analysis" in result
        assert "gemini_response" in result
        assert result["gemini_response"] == "Test business analysis from Gemini."
        assert "disclaimer" in result
        assert "synthetic" in result["disclaimer"].lower()

    @patch("app.services.analytics_ai_service.genai")
    def test_ask_handles_gemini_error_gracefully(self, mock_genai):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API timeout")
        mock_genai.Client.return_value = mock_client
        AnalyticsAIService._gemini_model = None

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            result = AnalyticsAIService.ask("Test question")

        assert "gemini_response" in result
        assert "unavailable" in result["gemini_response"].lower() or "error" in result["gemini_response"].lower()


class TestAPIEndpoint:
    """FastAPI endpoint tests."""

    @patch("app.services.analytics_ai_service.AnalyticsAIService.ask")
    def test_ai_analyst_endpoint_returns_response(self, mock_ask):
        from fastapi.testclient import TestClient
        from app.main import app

        mock_ask.return_value = {
            "question": "Test",
            "analysis": {"kpis": {"total_revenue": 100}},
            "gemini_response": "Test response",
            "generated_at": "2024-01-01 12:00",
            "disclaimer": "Test disclaimer"
        }

        client = TestClient(app)
        resp = client.post("/api/v1/ai/ai-analyst", json={"question": "How is my business?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["question"] == "Test"
        assert "gemini_response" in data

    def test_ai_analyst_endpoint_rejects_empty_question(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.post("/api/v1/ai/ai-analyst", json={"question": ""})
        assert resp.status_code == 422  # Pydantic validation

    def test_cors_does_not_reflect_unlisted_origins(self):
        # Wildcard + allow_credentials would reflect any origin; explicit
        # origins must echo only allowlisted ones.
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        evil = client.get("/health", headers={"Origin": "https://evil.example"})
        assert evil.headers.get("access-control-allow-origin") is None
        good = client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert good.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_ai_analyst_endpoint_rejects_too_short_question(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.post("/api/v1/ai/ai-analyst", json={"question": "ab"})
        assert resp.status_code == 422

    def test_ai_analyst_endpoint_rejects_too_long_question(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.post("/api/v1/ai/ai-analyst", json={"question": "x" * 501})
        assert resp.status_code == 422


class TestFrontendHelpers:
    """Frontend rendering helpers."""

    def test_fmtINR_formats_correctly(self):
        # This is a JS function, but we can verify the Python equivalent
        def fmt_inr(x):
            x = float(x)
            if abs(x) >= 1e7:
                return f"Rs.{x/1e7:,.2f} Cr"
            if abs(x) >= 1e5:
                return f"Rs.{x/1e5:,.1f} L"
            return f"Rs.{x:,.0f}"

        assert fmt_inr(59283619.32) == "Rs.5.93 Cr"
        assert fmt_inr(12998872.58) == "Rs.1.30 Cr"
        assert fmt_inr(644518) == "Rs.6.4 L"  # 6.45 rounded to 1 decimal = 6.4
        assert fmt_inr(523) == "Rs.523"

    def test_escape_html_js_source_has_replacements(self):
        # The helper must entity-encode in all four byte-identical copies.
        # A raw-character replacement (e.g. replace(/&/g, '&')) is an XSS bug, not a fix.
        expected = [
            "replace(/&/g, '&amp;')",
            "replace(/</g, '&lt;')",
            "replace(/>/g, '&gt;')",
            "replace(/\"/g, '&quot;')",
            "replace(/'/g, '&#39;')",
        ]
        for rel in DASHBOARD_COPIES:
            with open(os.path.join(BASE, rel), encoding="utf-8") as f:
                js = f.read()
            for snippet in expected:
                assert snippet in js, f"{rel} missing {snippet}"
            assert "replace(/'/g, '''" not in js, f"{rel} has malformed quote replacement"

    def test_inline_scripts_pass_node_syntax_check(self):
        node = shutil.which("node")
        if not node:
            pytest.skip("node not installed")
        for rel in DASHBOARD_COPIES:
            with open(os.path.join(BASE, rel), encoding="utf-8") as f:
                html = f.read()
            blocks = re.findall(
                r"<script(?![^>]*\bsrc=)(?![^>]*type=[\"']application/(?:ld\+json|json)[\"'])[^>]*>"
                r"(.*?)</script>",
                html,
                re.S,
            )
            assert blocks, f"{rel}: no inline script blocks found"
            for i, block in enumerate(blocks):
                if not block.strip():
                    continue
                with tempfile.NamedTemporaryFile(
                    "w", suffix=".js", delete=False, encoding="utf-8"
                ) as fh:
                    fh.write(block)
                    tmp = fh.name
                try:
                    result = subprocess.run(
                        [node, "--check", tmp], capture_output=True, text=True
                    )
                finally:
                    os.unlink(tmp)
                assert result.returncode == 0, (
                    f"{rel} inline block {i} has a syntax error: {result.stderr[:500]}"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])