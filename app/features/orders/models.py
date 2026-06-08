from sqlalchemy import String, Integer, DateTime, ForeignKey, Date, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from decimal import Decimal
from datetime import date, datetime
from app.database.base import Base

class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    address_id: Mapped[int] = mapped_column(ForeignKey("user_addresses.address_id"), nullable=False)
    
    order_status: Mapped[str] = mapped_column(SQLEnum('Pending', 'Confirmed', 'Packed', 'Out For Delivery', 'Delivered', 'Cancelled', name="order_status_enum"), nullable=False, default='Pending')
    payment_status: Mapped[str] = mapped_column(SQLEnum('Pending', 'Success', 'Failed', 'Cancelled', name="payment_status_enum"), nullable=False, default='Pending')
    
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    expected_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("app.features.users.models.User", back_populates="orders")
    address = relationship("app.features.addresses.models.Address", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("app.features.payments.models.Payment", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    product_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product = relationship("app.features.products.models.Product", back_populates="order_items")
