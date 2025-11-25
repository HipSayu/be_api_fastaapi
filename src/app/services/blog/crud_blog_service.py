from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db.database import Base
from ...schemas.blog.blog_schemas import BlogCreate, BlogUpdate
from ...models.blog.blog_model import Blog
from typing import Annotated, Optional, Any
from fastapi import Depends
from ...core.auth import get_current_active_user
from ...models.user import User
from sqlalchemy import select, func
from datetime import UTC, datetime


class BlogService:
    """
    Services
    """
    async def create(
        self,
        db: AsyncSession,
        input: BlogCreate,
        current_user: User,
    ) -> dict[str, Any]:
        """Create Blog"""
        blog = Blog(
            content=input.content,
            title=input.title,
            created_by_user_id=current_user["id"],
        )
        db.add(blog)
        await db.commit()
        await db.refresh(blog)
        return blog

    async def get_by_name(self, db: AsyncSession, title: str) -> Optional[Blog]:
        """Get category by name"""
        stmt = select(Blog).where(Blog.title == title)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get(self, db: AsyncSession, id: int) -> Optional[Blog]:
        """Get Blog by id"""
        query = select(Blog).where(Blog.id == id and Blog.is_deleted != True)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi_blog(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Blog], int]:
        """Get Multi Blogs with pagination"""
        query = select(Blog).where(Blog.is_deleted != True)
        count_query = select(func.count(Blog.id)).where(Blog.is_deleted != True)

        query = query.offset(skip).limit(limit).order_by(Blog.created_at)

        result = await db.execute(query)
        count_result = await db.execute(count_query)

        blogs = result.scalars().all()
        total = count_result.scalar()

        return blogs, total

    async def update_blog(
        self,
        db: AsyncSession,
        data: Blog,
        input: BlogUpdate,
    ) -> Blog:
        """Update Blog"""
        update_data = input.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(data, field, value)

        data.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(data)
        return data

    async def delete_blog(
        self,
        db: AsyncSession,
        blog_id: int,
    ) -> Optional[Blog]:
        """DELETE SOFT BLOG"""
        blog = await self.get(db, blog_id)
        if blog:
            blog.is_deleted = True
            blog.deleted_at = datetime.now(UTC)
            await db.commit()
            await db.refresh(blog)
        return blog


blog_service = BlogService()
