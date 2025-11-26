from sqlalchemy import Enum
from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Integer, Text, ARRAY, ForeignKey
from typing import List, Optional
from datetime import datetime, UTC


class BlogStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"


class BlogMain(Base):
    __tablename__ = "blog_mains"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        init=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        String(50000),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    status: Mapped[BlogStatus] = mapped_column(
        String(20),
        default=BlogStatus.DRAFT,
        nullable=False,
        init=False,
    )

    meta_description: Mapped[Optional[str]] = mapped_column(
        Text,
        default=None,
    )

    featured_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        default=None,
    )

    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        default=None,
    )

    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        init=False,
    )

    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        init=False,
    )

    create_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="blog_mains",
        lazy="selectin",
        init=False,
    )

    category: Mapped[Optional["BlogCategory"]] = relationship(
        "BlogCategory",
        back_populates="blog_mains",
        lazy="selectin",
        init=False,
    )

    reactions: Mapped[List["BlogReaction"]] = relationship(
        "BlogReaction",
        back_populates="blog_mains",
        cascade="all, delete-orphan",
        lazy="dynamic",
        init=False,
    )

    comments: Mapped[List["BlogComment"]] = relationship(
        "BlogComment",
        back_populates="blog_mains",
        cascade="all, delete-orphan",
        lazy="dynamic",
        init=False,
    )

    views: Mapped[List["BlogView"]] = relationship(
        "BlogView",
        back_populates="blog_mains",
        cascade="all, delete-orphan",
        lazy="dynamic",
        init=False,
    )

    #Audit
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
