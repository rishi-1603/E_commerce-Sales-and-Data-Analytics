from pydantic import BaseModel
from typing import List, Optional

class OverviewKPIResponse(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    avg_order_value: float
    cancellation_rate_pct: float
    delivered_orders_count: int

class SalesTrendItem(BaseModel):
    period: str
    total_revenue: float
    order_count: int
    avg_order_value: float

class SalesTrendResponse(BaseModel):
    granularity: str
    trends: List[SalesTrendItem]

class CohortRetentionItem(BaseModel):
    cohort_month: str
    cohort_size: int
    m1_pct: float
    m2_pct: float
    m3_pct: float

class CohortRetentionResponse(BaseModel):
    cohorts: List[CohortRetentionItem]
