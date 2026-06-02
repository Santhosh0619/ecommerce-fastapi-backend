from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.base import Base

class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.category_id"), nullable=False, index=True)
    
    product_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    product_slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    
    product_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    product_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    product_status: Mapped[str] = mapped_column(SQLEnum('Active', 'Inactive', 'Archived', name="product_status_enum"), nullable=False, default='Inactive')
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    
    average_rating: Mapped[float] = mapped_column(DECIMAL(3, 2), nullable=False, default=0.00)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    images: Mapped[list["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    category = relationship("app.features.categories.models.Category")
    vendor = relationship("app.features.users.models.User")

class ProductImage(Base):
    __tablename__ = "product_images"

    product_image_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product: Mapped["Product"] = relationship("Product", back_populates="images")
