from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from app.database.base import Base

class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent_category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.category_id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Self-referential relationship for parent-child hierarchies
    parent: Mapped["Category"] = relationship(
        "Category", 
        remote_side=[category_id], 
        back_populates="subcategories"
    )
    
    subcategories: Mapped[list["Category"]] = relationship(
        "Category", 
        back_populates="parent"
    )

    __table_args__ = (
        UniqueConstraint('category_name', 'parent_category_id', name='uq_category_name_parent_id'),
    )
