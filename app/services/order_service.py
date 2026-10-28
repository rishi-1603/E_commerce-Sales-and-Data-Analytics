from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.idempotency import IdempotencyRecord
from app.schemas.order import OrderCreate, OrderResponse, OrderItemResponse
from fastapi import HTTPException
import json
import uuid

class OrderService:
    @staticmethod
    async def check_idempotency(db: AsyncSession, key: str, endpoint: str):
        stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.idempotency_key == key,
            IdempotencyRecord.endpoint == endpoint
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            return json.loads(record.response_body), record.status_code
        return None, None

    @staticmethod
    async def save_idempotency(db: AsyncSession, key: str, endpoint: str, status_code: int, response_dict: dict):
        record = IdempotencyRecord(
            idempotency_key=key,
            endpoint=endpoint,
            status_code=status_code,
            response_body=json.dumps(response_dict)
        )
        db.add(record)
        await db.commit()

    @staticmethod
    async def create_order(db: AsyncSession, order_in: OrderCreate, idempotency_key: str = None) -> OrderResponse:
        endpoint = "/api/v1/orders"
        if idempotency_key:
            cached_data, status_code = await OrderService.check_idempotency(db, idempotency_key, endpoint)
            if cached_data:
                return OrderResponse(**cached_data)

        cust_stmt = select(Customer).where(Customer.customer_id == order_in.customer_id)
        cust_res = await db.execute(cust_stmt)
        customer = cust_res.scalar_one_or_none()
        if not customer:
            raise HTTPException(status_code=400, detail=f"Customer '{order_in.customer_id}' does not exist.")

        new_order_id = f"ORD{uuid.uuid4().hex[:7].upper()}"

        try:
            order_obj = Order(
                order_id=new_order_id,
                customer_id=order_in.customer_id,
                order_date=order_in.order_date,
                status=order_in.status,
                payment_method=order_in.payment_method,
                discount_pct=order_in.discount_pct,
                shipping_cost=order_in.shipping_cost
            )
            db.add(order_obj)

            total_amount = 0.0
            saved_item_dtos = []

            for idx, item_in in enumerate(order_in.items):
                prod_stmt = select(Product).where(Product.product_id == item_in.product_id)
                prod_res = await db.execute(prod_stmt)
                product = prod_res.scalar_one_or_none()
                if not product:
                    raise HTTPException(status_code=400, detail=f"Product '{item_in.product_id}' not found.")

                unit_price = float(item_in.unit_price)
                discount = float(item_in.discount_pct or 0.0)
                final_price = round(unit_price * (1.0 - discount), 2)
                line_total = round(final_price * item_in.quantity, 2)
                cost_total = round(float(product.cost_price) * item_in.quantity, 2)
                total_amount += line_total

                item_id = f"ITEM-{new_order_id}-{idx+1}"
                item_obj = OrderItem(
                    item_id=item_id,
                    order_id=new_order_id,
                    product_id=item_in.product_id,
                    quantity=item_in.quantity,
                    unit_price=unit_price,
                    discount_pct=discount,
                    final_price=final_price,
                    line_total=line_total,
                    cost_total=cost_total
                )
                db.add(item_obj)

                saved_item_dtos.append(
                    OrderItemResponse(
                        item_id=item_id,
                        product_id=item_in.product_id,
                        quantity=item_in.quantity,
                        unit_price=unit_price,
                        discount_pct=discount,
                        final_price=final_price,
                        line_total=line_total,
                        cost_total=cost_total
                    )
                )

            await db.flush()
            await db.commit()

            response_data = OrderResponse(
                order_id=new_order_id,
                customer_id=order_in.customer_id,
                order_date=order_in.order_date,
                status=order_in.status,
                payment_method=order_in.payment_method,
                discount_pct=float(order_in.discount_pct),
                shipping_cost=float(order_in.shipping_cost),
                total_amount=round(total_amount, 2),
                items=saved_item_dtos
            )

            if idempotency_key:
                await OrderService.save_idempotency(db, idempotency_key, endpoint, 201, response_data.model_dump(mode="json"))

            return response_data

        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")
