from sqlalchemy import Column, String, Integer, Numeric, Date
from sqlalchemy.orm import relationship
from app.models.base import Base

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(8), primary_key=True, index=True)
    product_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50))
    cost_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    stock_qty = Column(Integer, default=0)
    rating = Column(Numeric(3, 1))
    launch_date = Column(Date)

    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
