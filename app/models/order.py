from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(12), primary_key=True, index=True)
    customer_id = Column(String(10), ForeignKey("customers.customer_id"), nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # Delivered/Returned/Cancelled/Processing
    payment_method = Column(String(30))
    discount_pct = Column(Numeric(5, 2), default=0.0)
    shipping_cost = Column(Numeric(8, 2), default=0.0)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    item_id = Column(String(20), primary_key=True, index=True)
    order_id = Column(String(12), ForeignKey("orders.order_id"), nullable=False, index=True)
    product_id = Column(String(8), ForeignKey("products.product_id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_pct = Column(Numeric(5, 2), default=0.0)
    final_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)
    cost_total = Column(Numeric(12, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
