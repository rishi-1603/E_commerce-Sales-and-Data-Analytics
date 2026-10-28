import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_analytics_overview_contract(async_client: AsyncClient):
    response = await async_client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    data = response.json()

    assert "total_revenue" in data
    assert "total_orders" in data
    assert "total_customers" in data
    assert "avg_order_value" in data
    assert "cancellation_rate_pct" in data

    # Sanity checks on business logic
    assert data["total_revenue"] > 1000000.0  # Over 1 Cr revenue in this dataset
    assert data["total_orders"] > 5000
    assert data["total_customers"] > 1000
    assert data["avg_order_value"] > 0
    assert 0.0 <= data["cancellation_rate_pct"] <= 100.0

@pytest.mark.asyncio
async def test_analytics_trends(async_client: AsyncClient):
    response = await async_client.get("/api/v1/analytics/trends")
    assert response.status_code == 200
    data = response.json()
    assert data["granularity"] == "monthly"
    assert len(data["trends"]) > 0
    first_month = data["trends"][0]
    assert "period" in first_month
    assert "total_revenue" in first_month
    assert "order_count" in first_month

@pytest.mark.asyncio
async def test_analytics_top_products(async_client: AsyncClient):
    response = await async_client.get("/api/v1/analytics/top-products?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5
    if data:
        prod = data[0]
        assert "product_id" in prod
        assert "product_name" in prod
        assert "total_revenue" in prod
        assert "profit_margin_pct" in prod
