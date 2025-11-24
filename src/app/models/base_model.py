from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Boolean, Integer
from typing import Optional


class Base(DeclarativeBase):
    """Base class cho tất cả models"""

    pass


class TimestampMixin:
    """Mixin để thêm timestamps cho models"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
        nullable=False,
        index=True,
    )


class SoftDeleteMixin:
    """Mixin để thêm soft delete"""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )

    deleted_at: Mapped[Optional[datetime]] = (
        mapped_column(
            DateTime(timezone=True),
            nullable=True,
        ),
    )


class BaseCustomModel(Base, TimestampMixin, SoftDeleteMixin):
    """Base model với tất cả common fields"""

    __abstract__ = True  # Không tạo table cho class này

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
