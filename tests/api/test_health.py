import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_returns_200(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Commerce Intelligence API"
    assert "connected" in data["database"]

@pytest.mark.asyncio
async def test_root_returns_metadata(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["docs"] == "/docs"
    assert data["api_v1"] == "/api/v1"
