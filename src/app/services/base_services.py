from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from ..core.db.database import Base
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self):
        super().__init__()
        self.model = ModelType

    async def create(
        self, db: AsyncSession, obj_in: CreateSchemaType | Dict[str, Any], **kwargs
    ) -> ModelType:
        """Create new object"""
        # Convert Pydantic model to dict
        if isinstance(obj_in, BaseModel):
            obj_data = obj_in.model_dump(exclude=True)
        else:
            obj_data = obj_in

        obj_data.update(kwargs)

        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(
        self, db: AsyncSession, id: int, load_relationships: bool = False
    ) -> Optional[ModelType]:
        """Get object by Id"""
        query = select(self.model).where(self.model.id == id)

        if load_relationships:
            for relationship in self.model.__mapper__.relationships:
                query = query.opions(
                    selectinload(
                        getattr(self.model, relationship.key),
                    ),
                )

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[ModelType]:
        """Get multiple objects với filtering và pagination"""
        query = select(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        query = query.where(getattr(self.model, field).in_(value))
                    else:
                        query = query.where(getattr(self.model, field) == value)

        if order_by:
            if order_by.startswith("-"):
                field = order_by[1:]
                if hasattr(self.model, field):
                    query = query.order_by(getattr(self.model, order_by))

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalar().all()

    async def update(
        self,
        db: AsyncSession,
        id: int,
        obj_in: UpdateSchemaType | Dict[str, Any],
        **kwargs,
    ) -> Optional[ModelType]:
        """Update object"""
        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(exclude=True)
        else:
            update_data = {k: v for k, v in obj_in.items() if v is not None}

        update_data.update(kwargs)

        if not update_data:
            return await self.get(db, id)

        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )

        result = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )

        result = await db.execute(query)
        await db.commit()
        return result.scalar_one_or_none()

    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Hard delete object"""
        query = delete(self.model).where(self.model.id == id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    async def soft_delete(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """
        Soft delete object (chỉ hoạt động nếu model có is_deleted field)
        """
        if not hasattr(self.model, "is_deleted"):
            raise NotImplementedError(
                f"{self.model.__name__} doesn't support soft delete"
            )

        from datetime import datetime, UTC

        return await self.update(
            db, id, {"is_deleted": True, "deleted_at": datetime.now(UTC)}
        )

    async def count(
        self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count objects với optional filters"""
        query = select(func.count(self.model.id))

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        query = query.where(getattr(self.model, field).in_(value))
                    else:
                        query = query.where(getattr(self.model, field) == value)

        result = await db.execute(query)
        return result.scalar()

    async def exists(self, db: AsyncSession, id: int) -> bool:
        """Check if object exists"""
        query = select(func.count(self.model.id)).where(self.model.id == id)
        result = await db.execute(query)
        count = result.scalar()
        return count > 0

    async def get_or_404(self, db: AsyncSession, id: int) -> ModelType:
        """Get object or raise NotFoundError"""
        from ..core.exceptions import NotFoundError

        obj = await self.get(db, id)
        if not obj:
            raise NotFoundError(f"{self.model.__name__} with id {id} not found")
        return obj
