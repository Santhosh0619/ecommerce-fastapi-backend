from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, DECIMAL, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from decimal import Decimal
from app.database.base import Base

class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    gateway_provider: Mapped[str] = mapped_column(String(50), nullable=False) # 'stripe', 'mock'
    
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False, index=True)
    
    payment_method: Mapped[str] = mapped_column(SQLEnum('UPI', 'Card', 'COD', name="payment_method_enum"), nullable=False)
    payment_status: Mapped[str] = mapped_column(SQLEnum('Pending', 'Success', 'Failed', 'Cancelled', name="payment_status_enum"), nullable=False, default='Pending')
    
    payment_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    gateway_response: Mapped[str] = mapped_column(Text, nullable=True)
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    transaction_reference: Mapped[str] = mapped_column(String(255), unique=True, nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    order = relationship("app.features.orders.models.Order", back_populates="payments")
