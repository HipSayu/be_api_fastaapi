from sqlalchemy import UniqueConstraint
from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Boolean, Integer, ForeignKey
from typing import Optional
from datetime import datetime, UTC
from ..user import User
from .blog_main_model import BlogMain
from .reaction_type_model import ReactionType


class BlogReaction(Base):
    __tablename__ = "blog_reactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        init=False,
    )

    blog_id: Mapped[int] = mapped_column(
        ForeignKey("blog_mains.id"),
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    reaction_type_id: Mapped[int] = mapped_column(
        ForeignKey("reaction_types.id"),
    )

    # Relationships

    blog: Mapped["BlogMain"] = relationship(
        "BlogMain",
        back_populates="reactions",
        init=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="blog_reactions",
        init=False,
    )

    reactions_type: Mapped["ReactionType"] = relationship(
        "ReactionType",
        back_populates="blog_reactions",
        lazy="selectin",
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

    # Unique constraint handled at database level
    __table_args__ = (
        UniqueConstraint("blog_id", "user_id", name="unique_blog_user_reaction"),
    )
