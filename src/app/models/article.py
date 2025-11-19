import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from ..core.db.database import Base


class Article(Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    
    title: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(String(500), default=None)
    
    # Foreign keys
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), index=True, init=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, init=False)
    
    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="articles", init=False)
    author: Mapped["User"] = relationship("User", back_populates="articles", init=False)
    
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default_factory=uuid7, unique=True, init=False)
    created_at: Mapped[datetime] = mapped_column(default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, init=False)
    is_published: Mapped[bool] = mapped_column(default=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)