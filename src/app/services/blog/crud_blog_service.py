from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db.database import Base
from ...schemas.blog.blog_schemas import BlogCreate, BlogCreateInternal
from ...models.blog.blog_model import Blog
from typing import Annotated, Optional, Any
from fastapi import Depends
from ...core.auth import get_current_active_user
from ...models.user import User
from sqlalchemy import select, func


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
        print(current_user)
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


blog_service = BlogService()
