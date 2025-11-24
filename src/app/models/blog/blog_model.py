from ...core.db.database import Base
from ...models.base_model import BaseCustomModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, ForeignKey, UUID
from uuid6 import uuid7
import uuid as uuid_pkg


class Blog(Base, BaseCustomModel):
    __tablename__ = "blogs"

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    content: Mapped[str] = (
        mapped_column(
            String(50000),
            nullable=False,
        ),
    )
    
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"),
        index=True,
    )
    
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True),
        default_factory=uuid7,
        unique=True,
    )
