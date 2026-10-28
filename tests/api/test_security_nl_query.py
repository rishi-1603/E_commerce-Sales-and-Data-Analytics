import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_natural_language_query_valid_question(async_client: AsyncClient):
    payload = {"question": "What is the total revenue by product category?"}
    response = await async_client.post("/api/v1/query/nl-to-sql", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_safe"] is True
    assert data["row_count"] > 0
    assert len(data["data"]) > 0
    assert "category" in data["data"][0]

@pytest.mark.asyncio
async def test_ast_blocks_malicious_drop_query(async_client: AsyncClient):
    from app.services.query_service import QueryService

    malicious_sql = "DROP TABLE customers; SELECT * FROM orders;"
    is_safe, sanitized_sql, reason = QueryService.sanitize_sql(malicious_sql)
    assert is_safe is False
    assert "Security Violation" in reason

@pytest.mark.asyncio
async def test_ast_blocks_unauthorized_table_access(async_client: AsyncClient):
    from app.services.query_service import QueryService

    unauthorized_sql = "SELECT * FROM sqlite_master;"
    is_safe, sanitized_sql, reason = QueryService.sanitize_sql(unauthorized_sql)
    assert is_safe is False
    assert "sqlite_master" in reason
