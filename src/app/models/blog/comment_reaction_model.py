from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, UUID, UniqueConstraint
from uuid6 import uuid7
import uuid as uuid_pkg
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Boolean, Integer
from typing import Optional


class CommentReaction(Base):
    __tablename__ = "comment_reactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        init=False,
    )

    # Foreign keys
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("blog_comments.id"),
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    reactions_type_id: Mapped[int] = mapped_column(
        ForeignKey("reaction_types.id"),
    )

    # Relationships
    comment: Mapped["BlogComment"] = relationship(
        "BlogComment",
        back_populates="reactions",
        init=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        init=False,
    )

    reaction_type: Mapped["ReactionType"] = relationship(
        "ReactionType",
        back_populates="comment_reactions",
        lazy="selectin",
        init=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "comment_id",
            "user_id",
            name="unique_comment_user_reaction",
        ),
    )
