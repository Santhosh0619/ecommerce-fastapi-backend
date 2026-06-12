import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, DECIMAL, Enum as SQLEnum, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.base import Base

class ReviewStatus(str, enum.Enum):
    Published = "Published"
    Hidden = "Hidden"
    Deleted = "Deleted"

class Review(Base):
    __tablename__ = "reviews"

    review_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False, index=True)
    
    rating: Mapped[float] = mapped_column(DECIMAL(2, 1), nullable=False)  # 0.5 to 5.0
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text('false'), nullable=False)
    helpful_votes: Mapped[int] = mapped_column(Integer, default=0, server_default=text('0'), nullable=False)
    
    vendor_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vendor_reply_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    review_status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus, name="review_status_enum"),
        default=ReviewStatus.Published,
        server_default=text("'Published'"),
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("app.features.products.models.Product")
    user = relationship("app.features.users.models.User")
    order = relationship("app.features.orders.models.Order")

    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_review_user_product'),
    )

class ReviewHelpfulVote(Base):
    __tablename__ = "review_helpful_votes"

    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.review_id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    review = relationship("Review", backref="votes")
    user = relationship("app.features.users.models.User")
