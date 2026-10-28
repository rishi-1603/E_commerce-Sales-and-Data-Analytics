from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.db.session import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import OverviewKPIResponse, SalesTrendResponse
from app.schemas.product import TopProductResponse

router = APIRouter()

@router.get("/overview", response_model=OverviewKPIResponse, tags=["Analytics"])
async def get_overview_kpis(
    start_date: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns high-level executive KPIs anchored to the reconciled valid_orders rule:
    Only orders with status IN ('Delivered', 'Processing') generate valid revenue.
    """
    return await AnalyticsService.get_overview_kpis(db, start_date, end_date)

@router.get("/trends", response_model=SalesTrendResponse, tags=["Analytics"])
async def get_sales_trends(db: AsyncSession = Depends(get_db)):
    """
    Returns monthly revenue, order volume, and average order value trends.
    """
    return await AnalyticsService.get_monthly_trends(db)

@router.get("/top-products", response_model=List[TopProductResponse], tags=["Analytics"])
async def get_top_products(
    limit: int = Query(10, ge=1, le=50, description="Number of top products to retrieve"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns top-performing products ranked by total revenue, including profit margins.
    """
    return await AnalyticsService.get_top_products(db, limit)
