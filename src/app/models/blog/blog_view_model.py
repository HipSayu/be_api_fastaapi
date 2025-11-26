from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, UUID, Text, UniqueConstraint, INET
from uuid6 import uuid7
import uuid as uuid_pkg
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Boolean, Integer
from typing import Optional
from sqlalchemy.dialects.postgresql import INET


class BlogView(Base):
    __tablename__ = "blog_views"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        init=False,
    )

    # Tracking fields
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        default=None,
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        default=None,
    )

    session_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        default=None,
    )

    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        init=False,
    )

    # Foreign keys
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        default=None,
        index=True,
    )
    
    # Audit
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

    # Relationships
    blog: Mapped["Blog"] = relationship("Blog", back_populates="views", init=False)
    user: Mapped[Optional["User"]] = relationship("User", init=False)
