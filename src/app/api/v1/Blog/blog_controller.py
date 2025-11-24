from fastapi import APIRouter, Depends, HTTPException, Query
from ....schemas.blog.blog_schemas import BlogRead, BlogCreate
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.db.database import async_get_db
from ....services.blog.crud_blog_service import blog_service
from ....models.user import User
from ....api.dependencies import get_current_superuser, get_current_user

router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.post("/create", response_model=BlogRead, status_code=200)
async def create_blog(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    input: BlogCreate,
    current_user: Annotated[User, Depends(get_current_user)],
) -> BlogRead:
    """Create Blog"""
    exitsting_blog = await blog_service.get_by_name(db, input.title)
    if exitsting_blog:
        raise HTTPException(
            status_code=400, detail="Blog with this name already exists"
        )
    blog = await blog_service.create(db, input, current_user)
    return BlogRead.model_validate(blog)
