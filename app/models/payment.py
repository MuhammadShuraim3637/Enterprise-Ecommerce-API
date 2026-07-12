import enum
from datetime import datetime, timezone  # <-- Sahi import pehle se tha
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    transaction_id = Column(String, unique=True, index=True, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default=PaymentStatus.PENDING.value, nullable=False)
    provider = Column(String, default="dummy_gateway", nullable=False)
    
    # Dono fields ko lowercase timezone.utc par shift kar diya
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    order = relationship("Order", back_populates="payment")