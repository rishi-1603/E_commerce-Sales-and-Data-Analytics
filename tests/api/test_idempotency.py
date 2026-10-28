import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_order_creation_with_idempotency(async_client: AsyncClient):
    # Fetch valid customer and product
    cust_res = await async_client.get("/api/v1/customers?limit=1")
    customer_id = cust_res.json()[0]["customer_id"]

    prod_res = await async_client.get("/api/v1/products?limit=1")
    product_id = prod_res.json()[0]["product_id"]

    idempotency_key = f"key-{uuid.uuid4().hex}"
    payload = {
        "customer_id": customer_id,
        "order_date": "2026-10-28",
        "status": "Processing",
        "payment_method": "Credit Card",
        "discount_pct": 0.0,
        "shipping_cost": 50.0,
        "items": [
            {
                "product_id": product_id,
                "quantity": 2,
                "unit_price": 500.0,
                "discount_pct": 0.0
            }
        ]
    }

    headers = {"Idempotency-Key": idempotency_key}

    # 1. First submission: creates the order
    res1 = await async_client.post("/api/v1/orders", json=payload, headers=headers)
    assert res1.status_code == 201
    order1 = res1.json()
    assert order1["order_id"].startswith("ORD")
    assert order1["total_amount"] == 1000.0

    # 2. Duplicate submission with exact same key: returns cached response without duplicate DB insert
    res2 = await async_client.post("/api/v1/orders", json=payload, headers=headers)
    assert res2.status_code == 201
    order2 = res2.json()
    assert order2["order_id"] == order1["order_id"]
    assert order2["total_amount"] == order1["total_amount"]
