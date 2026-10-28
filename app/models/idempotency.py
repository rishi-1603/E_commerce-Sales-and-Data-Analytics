from sqlalchemy import Column, String, Integer, Text, DateTime
from datetime import datetime, timezone
from app.models.base import Base

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    idempotency_key = Column(String(100), unique=True, nullable=False, index=True)
    endpoint = Column(String(200), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
