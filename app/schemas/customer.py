from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    region: Optional[str] = None
    segment: Optional[str] = None
    acquisition_channel: Optional[str] = None
    registration_date: Optional[date] = None
    age: Optional[int] = None
    gender: Optional[str] = None

class CustomerResponse(CustomerBase):
    customer_id: str
    model_config = ConfigDict(from_attributes=True)

class CustomerSummaryResponse(CustomerResponse):
    total_orders: int = 0
    total_spend: float = 0.0
    last_order_date: Optional[date] = None
