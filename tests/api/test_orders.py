import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_orders_pagination(async_client: AsyncClient):
    response = await async_client.get("/api/v1/orders?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["total"] > 1000
    assert len(data["orders"]) == 10

    first_order = data["orders"][0]
    assert "order_id" in first_order
    assert "customer_id" in first_order
    assert "total_amount" in first_order
    assert len(first_order["items"]) > 0

@pytest.mark.asyncio
async def test_filter_orders_by_status(async_client: AsyncClient):
    response = await async_client.get("/api/v1/orders?status=Delivered&limit=5")
    assert response.status_code == 200
    data = response.json()
    for ord_item in data["orders"]:
        assert ord_item["status"] == "Delivered"

@pytest.mark.asyncio
async def test_get_order_by_id(async_client: AsyncClient):
    # Fetch an existing order first
    list_res = await async_client.get("/api/v1/orders?limit=1")
    existing_id = list_res.json()["orders"][0]["order_id"]

    response = await async_client.get(f"/api/v1/orders/{existing_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == existing_id
    assert len(data["items"]) > 0

@pytest.mark.asyncio
async def test_get_nonexistent_order_returns_404(async_client: AsyncClient):
    response = await async_client.get("/api/v1/orders/ORD-NONEXISTENT-999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
