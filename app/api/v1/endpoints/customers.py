from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.db.session import get_db
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.schemas.customer import CustomerResponse, CustomerSummaryResponse

router = APIRouter()

@router.get("", response_model=List[CustomerResponse], tags=["Customers"])
async def list_customers(
    region: Optional[str] = Query(None, description="Filter by customer region"),
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists customer accounts with optional geographic and segment filtering.
    """
    stmt = select(Customer)
    if region:
        stmt = stmt.where(Customer.region == region)
    if segment:
        stmt = stmt.where(Customer.segment == segment)
    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{customer_id}", response_model=CustomerSummaryResponse, tags=["Customers"])
async def get_customer_summary(customer_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves customer profile with aggregated order history and spend statistics.
    """
    stmt = select(Customer).where(Customer.customer_id == customer_id)
    res = await db.execute(stmt)
    customer = res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")

    # Aggregate spend & orders
    orders_stmt = select(
        func.count(Order.order_id).label("total_orders"),
        func.max(Order.order_date).label("last_order_date")
    ).where(Order.customer_id == customer_id)
    orders_res = (await db.execute(orders_stmt)).mappings().one()

    # Calculate total spend on valid orders
    spend_stmt = select(
        func.coalesce(func.sum(OrderItem.line_total), 0.0)
    ).select_from(Order).join(OrderItem).where(
        Order.customer_id == customer_id,
        Order.status.notin_(["Cancelled", "Returned"])
    )
    spend_res = (await db.execute(spend_stmt)).scalar() or 0.0

    return CustomerSummaryResponse(
        customer_id=customer.customer_id,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        region=customer.region,
        segment=customer.segment,
        acquisition_channel=customer.acquisition_channel,
        registration_date=customer.registration_date,
        age=customer.age,
        gender=customer.gender,
        total_orders=orders_res["total_orders"] or 0,
        total_spend=round(float(spend_res), 2),
        last_order_date=orders_res["last_order_date"]
    )
