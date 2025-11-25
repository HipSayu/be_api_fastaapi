from fastapi import APIRouter, Depends, HTTPException, Query
from ....schemas.blog.blog_schemas import (
    BlogRead,
    BlogCreate,
    BlogListResponse,
    BlogUpdate,
)
from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.db.database import async_get_db
from ....services.blog.crud_blog_service import blog_service
from ....models.user import User
from ....api.dependencies import get_current_superuser, get_current_user
import math

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


@router.get("/get/{blog_id}", response_model=BlogRead)
async def get_blog_by_id(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    blog_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
) -> BlogRead:
    """Get Blog_ID (Requires Authentication)"""
    blog = await blog_service.get(db, id=blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return BlogRead.model_validate(blog)


@router.get("/get-all", response_model=BlogListResponse)
async def get_all_blogs(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
) -> BlogListResponse:
    """Get list blog with pagination"""
    skip = (page - 1) * size
    blogs, total = await blog_service.get_multi_blog(db=db, skip=skip, limit=size)
    pages = math.ceil(total / size) if total > 0 else 1

    return BlogListResponse(
        data=[BlogRead.model_validate(cat) for cat in blogs],
        total=total,
        page=page,
        pages=pages,
        size=size,
    )

@router.put("/update/{blog_id}", response_model=BlogRead)
async def update_blog(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    blog_id: int,
    input: BlogUpdate,
) -> BlogRead:
    """Update Blog"""
    blog = await blog_service.get(db=db, id=blog_id)
    if not blog:
        raise HTTPException(
            status_code=404,
            detail="Blog not found",
        )
    update_blog = await blog_service.update_blog(db, blog, input)
    return BlogRead.model_validate(update_blog)
