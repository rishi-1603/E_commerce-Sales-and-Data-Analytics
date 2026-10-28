from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import date

class OrderItemBase(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, description="Quantity must be at least 1")
    unit_price: float = Field(ge=0.0, description="Unit price must be non-negative")
    discount_pct: float = Field(default=0.0, ge=0.0, le=1.0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    item_id: str
    final_price: float
    line_total: float
    cost_total: Optional[float] = 0.0
    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    customer_id: str
    order_date: date
    status: str = "Processing"
    payment_method: Optional[str] = "Credit Card"
    discount_pct: float = 0.0
    shipping_cost: float = 0.0

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(min_length=1, description="Order must contain at least one item")

class OrderResponse(OrderBase):
    order_id: str
    items: List[OrderItemResponse] = []
    total_amount: Optional[float] = 0.0
    model_config = ConfigDict(from_attributes=True)

class OrderPagination(BaseModel):
    total: int
    page: int
    limit: int
    orders: List[OrderResponse]
