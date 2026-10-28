from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductResponse

router = APIRouter()

@router.get("", response_model=List[ProductResponse], tags=["Products"])
async def list_products(
    category: str = Query(None, description="Filter by product category"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists catalog products with optional category filtering.
    """
    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category == category)
    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{product_id}", response_model=ProductResponse, tags=["Products"])
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves single product specification.
    """
    stmt = select(Product).where(Product.product_id == product_id)
    res = await db.execute(stmt)
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")
    return product
