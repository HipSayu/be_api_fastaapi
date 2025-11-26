from sqlalchemy import Enum
from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Integer, Text, ARRAY, ForeignKey
from typing import List, Optional
from datetime import datetime, UTC
from ..user import User

class BlogComment(Base):
    __tablename__ = "blog_comments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        init=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_edited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        init=False,
    )

    edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        init=False,
    )

    # Foreign keys
    blog_id: Mapped[int] = mapped_column(
        ForeignKey("blog_mains.id"),
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("blog_comments.id"),
        default=None,
        index=True,
    )

    # Relationships
    blog: Mapped["Blog"] = relationship(
        "Blog",
        back_populates="comments",
        init=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="blog_comments",
        init=False,
    )

    # Self-referential relationship for nested comments

    parent: Mapped[Optional["BlogComment"]] = relationship(
        "BlogComment",
        back_populates="replies",
        remote_side="BlogComment.id",
        init=False,
    )

    replies: Mapped[List["BlogComment"]] = relationship(
        "BlogComment",
        back_populates="parent",
        cascade="all, delete-orphan",
        init=False,
    )

    reactions: Mapped[List["CommentReaction"]] = relationship(
        "CommentReaction",
        back_populates="comment",
        cascade="all, delete-orphan",
        lazy="dynamic",
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
