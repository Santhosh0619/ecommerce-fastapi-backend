from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database.base import Base

class Permission(Base):
    __tablename__ = "permissions"

    # SQLAlchemy 2.0 mapping syntax for strong typing
    permission_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    permission_name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
