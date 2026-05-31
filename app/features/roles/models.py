from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database.base import Base

class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RolePermission(Base):
    """
    Mapping table for the Many-to-Many relationship between Roles and Permissions.
    This resolves the exact 'role_permissions' table requirement you provided.
    """
    __tablename__ = "role_permissions"

    role_permission_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # ondelete="CASCADE" means if a role is deleted, its permissions mapping is automatically deleted too
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.permission_id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
