from sqlalchemy import Enum
from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Integer, Text, ARRAY, ForeignKey
from typing import List, Optional
from datetime import datetime, UTC


class ReactionType(Base):
    __tablename__ = "reaction_types"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        init=False,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    emoji: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    display_name: Mapped[str] = (
        mapped_column(
            String(50),
            nullable=False,
        ),
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        init=False,
    )

    blog_reactions: Mapped[List["BlogReaction"]] = relationship(
        "BlogReaction",
        back_populates="reaction_type",
        init=False,
    )

    commnet_reaction: Mapped[List["CommentReaction"]] = relationship(
        "CommentReaction",
        back_populates="reaction_type",
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
