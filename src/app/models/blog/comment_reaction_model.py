from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, UUID
from uuid6 import uuid7
import uuid as uuid_pkg
from sqlalchemy.orm import Mapped, mapped_column
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
