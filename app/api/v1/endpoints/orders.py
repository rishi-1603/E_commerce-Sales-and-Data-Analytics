from fastapi import APIRouter, Depends, Query, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.db.session import get_db
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate, OrderResponse, OrderPagination, OrderItemResponse
from app.services.order_service import OrderService

router = APIRouter()

@router.get("", response_model=OrderPagination, tags=["Orders"])
async def list_orders(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by order status (e.g., Delivered, Cancelled)"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit
    
    count_stmt = select(func.count(Order.order_id))
    if status:
        count_stmt = count_stmt.where(Order.status == status)
    if customer_id:
        count_stmt = count_stmt.where(Order.customer_id == customer_id)
        
    total_count = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(Order)
    if status:
        stmt = stmt.where(Order.status == status)
    if customer_id:
        stmt = stmt.where(Order.customer_id == customer_id)
    stmt = stmt.order_by(Order.order_date.desc()).offset(offset).limit(limit)

    orders_res = (await db.execute(stmt)).scalars().all()

    results = []
    for ord_obj in orders_res:
        items_stmt = select(OrderItem).where(OrderItem.order_id == ord_obj.order_id)
        items_res = (await db.execute(items_stmt)).scalars().all()
        total_amount = sum(float(it.line_total) for it in items_res)
        results.append(
            OrderResponse(
                order_id=ord_obj.order_id,
                customer_id=ord_obj.customer_id,
                order_date=ord_obj.order_date,
                status=ord_obj.status,
                payment_method=ord_obj.payment_method,
                discount_pct=float(ord_obj.discount_pct or 0.0),
                shipping_cost=float(ord_obj.shipping_cost or 0.0),
                total_amount=round(total_amount, 2),
                items=[
                    OrderItemResponse(
                        item_id=str(it.item_id),
                        product_id=str(it.product_id),
                        quantity=int(it.quantity),
                        unit_price=float(it.unit_price),
                        discount_pct=float(it.discount_pct or 0.0),
                        final_price=float(it.final_price),
                        line_total=float(it.line_total),
                        cost_total=float(it.cost_total or 0.0)
                    )
                    for it in items_res
                ]
            )
        )

    return OrderPagination(
        total=total_count,
        page=page,
        limit=limit,
        orders=results
    )

@router.get("/{order_id}", response_model=OrderResponse, tags=["Orders"])
async def get_order_by_id(order_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Order).where(Order.order_id == order_id)
    ord_obj = (await db.execute(stmt)).scalar_one_or_none()
    if not ord_obj:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")

    items_stmt = select(OrderItem).where(OrderItem.order_id == order_id)
    items_res = (await db.execute(items_stmt)).scalars().all()
    total_amount = sum(float(it.line_total) for it in items_res)

    return OrderResponse(
        order_id=ord_obj.order_id,
        customer_id=ord_obj.customer_id,
        order_date=ord_obj.order_date,
        status=ord_obj.status,
        payment_method=ord_obj.payment_method,
        discount_pct=float(ord_obj.discount_pct or 0.0),
        shipping_cost=float(ord_obj.shipping_cost or 0.0),
        total_amount=round(total_amount, 2),
        items=[
            OrderItemResponse(
                item_id=str(it.item_id),
                product_id=str(it.product_id),
                quantity=int(it.quantity),
                unit_price=float(it.unit_price),
                discount_pct=float(it.discount_pct or 0.0),
                final_price=float(it.final_price),
                line_total=float(it.line_total),
                cost_total=float(it.cost_total or 0.0)
            )
            for it in items_res
        ]
    )

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, tags=["Orders"])
async def create_order(
    order_in: OrderCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db)
):
    return await OrderService.create_order(db, order_in, idempotency_key=idempotency_key)
