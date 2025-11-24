import math
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_active_user, get_current_user_optional
from ...core.db.database import async_get_db
from ...crud.article import article_crud
from ...models.user import User
from ...schemas.article import (
    ArticleCreate,
    ArticleResponse,
    ArticleResponseSimple,
    ArticleUpdate,
    ArticleListResponse,
    ArticleDetailListResponse
)

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("/", response_model=ArticleResponseSimple, status_code=201)
async def create_article(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    article_in: ArticleCreate,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ArticleResponseSimple:
    """Create new article"""
    # Verify category exists
    if not await article_crud.verify_category_exists(db, category_id=article_in.category_id):
        raise HTTPException(
            status_code=400,
            detail="Category not found or inactive"
        )
    
    # Verify author exists
    if not await article_crud.verify_author_exists(db, author_id=current_user.id):
        raise HTTPException(
            status_code=400,
            detail="Author not found"
        )
    
    article = await article_crud.create(db, obj_in=article_in, author_id=current_user.id)
    return ArticleResponseSimple.model_validate(article)


@router.get("/", response_model=ArticleListResponse)
async def get_articles(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
) -> ArticleListResponse:
    """Get articles with pagination and filters"""
    skip = (page - 1) * size
    articles, total = await article_crud.get_multi(
        db, 
        skip=skip, 
        limit=size, 
        category_id=category_id,
        author_id=author_id,
        is_published=is_published,
        is_active=is_active
    )
    
    pages = math.ceil(total / size) if total > 0 else 1
    
    return ArticleListResponse(
        articles=[ArticleResponseSimple.model_validate(article) for article in articles],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/detailed", response_model=ArticleDetailListResponse)
async def get_articles_detailed(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
) -> ArticleDetailListResponse:
    """Get articles with relationships included"""
    skip = (page - 1) * size
    articles, total = await article_crud.get_multi_with_relations(
        db, 
        skip=skip, 
        limit=size, 
        category_id=category_id,
        author_id=author_id,
        is_published=is_published,
        is_active=is_active
    )
    
    pages = math.ceil(total / size) if total > 0 else 1
    
    return ArticleDetailListResponse(
        articles=[ArticleResponse.model_validate(article) for article in articles],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{article_id}", response_model=ArticleResponseSimple)
async def get_article(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    article_id: int
) -> ArticleResponseSimple:
    """Get article by ID"""
    article = await article_crud.get(db, id=article_id)
    if not article:
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    return ArticleResponseSimple.model_validate(article)


@router.get("/{article_id}/detailed", response_model=ArticleResponse)
async def get_article_detailed(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    article_id: int
) -> ArticleResponse:
    """Get article by ID with relationships"""
    article = await article_crud.get_with_relations(db, id=article_id)
    if not article:
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    return ArticleResponse.model_validate(article)


@router.put("/{article_id}", response_model=ArticleResponseSimple)
async def update_article(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    article_id: int,
    article_in: ArticleUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ArticleResponseSimple:
    """Update article"""
    article = await article_crud.get(db, id=article_id)
    if not article:
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    
    # Verify ownership (only author or superuser can update)
    if article.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify category exists if being updated
    if article_in.category_id and not await article_crud.verify_category_exists(db, category_id=article_in.category_id):
        raise HTTPException(
            status_code=400,
            detail="Category not found or inactive"
        )
    
    updated_article = await article_crud.update(db, db_obj=article, obj_in=article_in)
    return ArticleResponseSimple.model_validate(updated_article)


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    article_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> None:
    """Delete article"""
    article = await article_crud.get(db, id=article_id)
    if not article:
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    
    # Verify ownership (only author or superuser can delete)
    if article.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    success = await article_crud.delete(db, id=article_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )