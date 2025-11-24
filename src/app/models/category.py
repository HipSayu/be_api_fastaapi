import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from ..core.db.database import Base


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    
    # Relationships
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="category", init=False)
    
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default_factory=uuid7, unique=True, init=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, init=False)
    is_active: Mapped[bool] = mapped_column(default=True)