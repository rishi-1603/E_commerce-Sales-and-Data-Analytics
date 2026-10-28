from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class ProductBase(BaseModel):
    product_name: str
    category: str
    subcategory: Optional[str] = None
    cost_price: float
    selling_price: float
    stock_qty: int = 0
    rating: Optional[float] = None
    launch_date: Optional[date] = None

class ProductResponse(ProductBase):
    product_id: str
    model_config = ConfigDict(from_attributes=True)

class TopProductResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    total_units_sold: int
    total_revenue: float
    total_profit: float
    profit_margin_pct: float
