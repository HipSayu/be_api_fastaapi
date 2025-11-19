import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Base schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    is_active: bool = Field(True, description="Is category active")


# Schema for creating category
class CategoryCreate(CategoryBase):
    pass


# Schema for updating category
class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


# Schema for response
class CategoryResponse(CategoryBase):
    id: int
    uuid: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schema for list response with pagination
class CategoryListResponse(BaseModel):
    categories: list[CategoryResponse]
    total: int
    page: int
    size: int
    pages: int