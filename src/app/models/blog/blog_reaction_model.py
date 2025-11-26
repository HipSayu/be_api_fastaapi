from sqlalchemy import Enum
from ...core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Integer, Text, ARRAY, ForeignKey
from typing import List, Optional
from datetime import datetime, UTC


class BlogReaction(Base):
    __tablename__: "blog_reactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        init=False,
    )
    
    
