from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, UUID
from uuid6 import uuid7
import uuid as uuid_pkg
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Boolean, Integer
from typing import Optional


class Blog(Base):
    __tablename__ = "blogs"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        init=False,
    )
    # Fields without defaults first
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        String(50000),
        nullable=False,
    )

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        nullable=False,
        index=True,
        init=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
        nullable=False,
        index=True,
        init=False,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        init=False,
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        init=False,
    )

    # Fields with defaults last - using init=False to avoid dataclass issues
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True),
        default_factory=uuid7,
        unique=True,
        init=False,
    )
