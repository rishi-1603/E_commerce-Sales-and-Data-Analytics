"""Accuracy and refusal contract for the FastAPI NL-to-SQL endpoint.

The endpoint is a deterministic intent router, not an open-domain model.
It must answer the questions it can ground and refuse the rest -- never
return an unrelated query that looks like an answer.

Expected totals are recomputed from the same database with a direct query,
so this test checks the router's definitions (joins, filters, grain) and is
not disturbed by other API tests that insert orders.
"""
import pytest
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

REFUSED = [
    "What is the meaning of life?",
    "What is the weather tomorrow?",
    "What is total revenue by customer segment?",
    "What is total revenue in 2024?",
    # Scoped questions the deterministic router must refuse (fail-closed),
    # not answer at overall grain.
    "What is the average order value by category?",
]


async def _ask(async_client, question):
    response = await async_client.post(
        "/api/v1/query/nl-to-sql", json={"question": question}
    )
    assert response.status_code == 200
    return response.json()


async def _reference_totals():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT ROUND(SUM(oi.line_total), 2) AS revenue,
                   ROUND(SUM(oi.line_total - oi.cost_total), 2) AS profit,
                   COUNT(DISTINCT o.order_id) AS orders,
                   COUNT(DISTINCT o.customer_id) AS customers
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status NOT IN ('Cancelled', 'Returned')
        """))
        return result.mappings().one()


@pytest.mark.asyncio
async def test_aggregates_match_the_database(async_client):
    ref = await _reference_totals()
    expected = {
        "What is total revenue?": ("total_revenue", ref["revenue"]),
        "What is the total profit?": ("total_profit", ref["profit"]),
        "How many total orders do we have?": ("total_orders", ref["orders"]),
        "How many customers do we have?": ("total_customers", ref["customers"]),
        "What is the overall margin?": (
            "margin_pct",
            round(100 * ref["profit"] / ref["revenue"], 2),
        ),
    }
    for question, (column, value) in expected.items():
        data = await _ask(async_client, question)
        assert data["is_safe"] is True, question
        assert data["row_count"] == 1, question
        assert data["data"][0][column] == pytest.approx(value, rel=1e-6), question


@pytest.mark.asyncio
async def test_revenue_is_not_answered_with_order_status_counts(async_client):
    """Regression: the old fallback returned status counts for every unknown."""
    data = await _ask(async_client, "What is total revenue?")
    assert list(data["data"][0]) == ["total_revenue"]


@pytest.mark.asyncio
async def test_region_and_category_breakdowns(async_client):
    region = await _ask(async_client, "Which region has the highest revenue?")
    assert region["row_count"] == 5
    assert region["data"][0]["region"] == "West"

    category = await _ask(async_client, "Which category has the highest margin?")
    assert category["data"][0]["category"] == "Sports"
    assert category["data"][0]["margin_pct"] == pytest.approx(56.5, abs=0.1)


@pytest.mark.asyncio
async def test_status_distribution_is_available_when_asked(async_client):
    data = await _ask(async_client, "What is the order status distribution?")
    assert data["row_count"] == 4
    assert data["data"][0] == {"status": "Delivered", "order_count": 9312}


@pytest.mark.asyncio
@pytest.mark.parametrize("question", REFUSED)
async def test_unsupported_questions_are_refused(async_client, question):
    data = await _ask(async_client, question)
    assert data["generated_sql"] == ""
    assert data["row_count"] == 0
    assert data["data"] == []
    assert data["explanation"].startswith("Refused:")
