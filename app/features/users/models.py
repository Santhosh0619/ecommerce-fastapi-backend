from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.base import Base

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # We never store plain text passwords, only the bcrypt hash
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # onupdate=func.now() automatically updates this column whenever the row is modified!
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cart = relationship("app.features.cart.models.Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")
    addresses = relationship("app.features.addresses.models.Address", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("app.features.orders.models.Order", back_populates="user", cascade="all, delete-orphan")

class UserRole(Base):
    """Mapping table for Many-to-Many relationship between Users and Roles."""
    __tablename__ = "user_roles"

    user_role_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('user_id', 'role_id', name='uq_user_role'),)

class UserPermission(Base):
    """Mapping table for explicit User Permissions (bypassing Roles)."""
    __tablename__ = "user_permissions"

    user_permission_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.permission_id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('user_id', 'permission_id', name='uq_user_permission'),)

class UserProfile(Base):
    """1-to-1 Profile table for Users to keep auth table lightweight"""
    __tablename__ = "user_profiles"

    profile_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    profile_picture_url: Mapped[str] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

