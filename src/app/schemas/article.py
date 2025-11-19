import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .category import CategoryResponse
from .user import UserResponse


# Base schemas
class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Article title")
    content: str = Field(..., min_length=1, description="Article content")
    summary: Optional[str] = Field(None, max_length=500, description="Article summary")
    category_id: int = Field(..., description="Category ID")
    is_published: bool = Field(False, description="Is article published")
    is_active: bool = Field(True, description="Is article active")


# Schema for creating article
class ArticleCreate(ArticleBase):
    pass


# Schema for updating article
class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


# Schema for response without relationships
class ArticleResponseSimple(ArticleBase):
    id: int
    author_id: int
    uuid: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schema for response with relationships
class ArticleResponse(ArticleResponseSimple):
    category: CategoryResponse
    author: UserResponse

    class Config:
        from_attributes = True


# Schema for list response with pagination
class ArticleListResponse(BaseModel):
    articles: list[ArticleResponseSimple]
    total: int
    page: int
    size: int
    pages: int


# Schema for detailed list response with relationships
class ArticleDetailListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
    page: int
    size: int
    pages: int