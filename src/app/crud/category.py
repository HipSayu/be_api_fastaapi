from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.category import Category
from ..schemas.category import CategoryCreate, CategoryUpdate


class CategoryCRUD:
    """CRUD operations for Category model"""
    
    async def create(self, db: AsyncSession, *, obj_in: CategoryCreate) -> Category:
        """Create new category"""
        category = Category(
            name=obj_in.name,
            description=obj_in.description,
            is_active=obj_in.is_active
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Category]:
        """Get category by ID"""
        stmt = select(Category).where(Category.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Category]:
        """Get category by name"""
        stmt = select(Category).where(Category.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> tuple[list[Category], int]:
        """Get multiple categories with pagination"""
        # Build base query
        stmt = select(Category)
        count_stmt = select(func.count(Category.id))
        
        # Add filters
        if is_active is not None:
            stmt = stmt.where(Category.is_active == is_active)
            count_stmt = count_stmt.where(Category.is_active == is_active)
        
        # Add pagination
        stmt = stmt.offset(skip).limit(limit).order_by(Category.created_at.desc())
        
        # Execute queries
        result = await db.execute(stmt)
        count_result = await db.execute(count_stmt)
        
        categories = result.scalars().all()
        total = count_result.scalar()
        
        return categories, total
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Category, 
        obj_in: CategoryUpdate
    ) -> Category:
        """Update category"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """Delete category"""
        stmt = select(Category).where(Category.id == id)
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()
        
        if category:
            await db.delete(category)
            await db.commit()
            return True
        return False
    
    async def soft_delete(self, db: AsyncSession, *, id: int) -> Optional[Category]:
        """Soft delete category (set is_active to False)"""
        category = await self.get(db, id=id)
        if category:
            category.is_active = False
            category.updated_at = datetime.now(UTC)
            await db.commit()
            await db.refresh(category)
        return category


# Create instance
category_crud = CategoryCRUD()