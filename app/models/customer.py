from sqlalchemy import Column, String, Integer, Date
from sqlalchemy.orm import relationship
from app.models.base import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(10), primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    region = Column(String(20), index=True)            # North/South/East/West/Central
    segment = Column(String(20), index=True)           # B2C / B2B / Enterprise
    acquisition_channel = Column(String(50))           # Organic, Paid, Social, etc.
    registration_date = Column(Date)
    age = Column(Integer)
    gender = Column(String(10))

    # Relationships
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
