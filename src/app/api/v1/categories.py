import math
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...crud.category import category_crud
from ...schemas.category import (
    CategoryCreate,
    CategoryResponse, 
    CategoryUpdate,
    CategoryListResponse
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryResponse, status_code=201)
async def create_category(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    category_in: CategoryCreate
) -> CategoryResponse:
    """Create new category"""
    # Check if category name already exists
    existing_category = await category_crud.get_by_name(db, name=category_in.name)
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category with this name already exists"
        )
    
    category = await category_crud.create(db, obj_in=category_in)
    return CategoryResponse.model_validate(category)


@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
) -> CategoryListResponse:
    """Get categories with pagination"""
    skip = (page - 1) * size
    categories, total = await category_crud.get_multi(
        db, skip=skip, limit=size, is_active=is_active
    )
    
    pages = math.ceil(total / size) if total > 0 else 1
    
    return CategoryListResponse(
        categories=[CategoryResponse.model_validate(cat) for cat in categories],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    category_id: int
) -> CategoryResponse:
    """Get category by ID"""
    category = await category_crud.get(db, id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    category_id: int,
    category_in: CategoryUpdate
) -> CategoryResponse:
    """Update category"""
    category = await category_crud.get(db, id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    
    # Check name uniqueness if name is being updated
    if category_in.name and category_in.name != category.name:
        existing_category = await category_crud.get_by_name(db, name=category_in.name)
        if existing_category:
            raise HTTPException(
                status_code=400,
                detail="Category with this name already exists"
            )
    
    updated_category = await category_crud.update(db, db_obj=category, obj_in=category_in)
    return CategoryResponse.model_validate(updated_category)


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    category_id: int
) -> None:
    """Delete category"""
    success = await category_crud.delete(db, id=category_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )


@router.patch("/{category_id}/deactivate", response_model=CategoryResponse)
async def deactivate_category(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    category_id: int
) -> CategoryResponse:
    """Soft delete category (deactivate)"""
    category = await category_crud.soft_delete(db, id=category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    return CategoryResponse.model_validate(category)