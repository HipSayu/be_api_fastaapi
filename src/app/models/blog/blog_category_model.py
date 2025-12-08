from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Integer, Text
from typing import List, Optional
from datetime import datetime, UTC
from .blog_main_model import BlogMain
class BlogCategory(Base):
    __tablename__ = "blog_categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        init=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        default=None,
    )

    color: Mapped[Optional[str]] = mapped_column(
        String(7),
        default=None,
    )

    # Relationships
    blogs: Mapped[List["BlogMain"]] = relationship(
        "BlogMain",
        back_populates="category",
        init=False,
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
