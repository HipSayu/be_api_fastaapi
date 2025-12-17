from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Annotated, Optional, List, Dict, Any
from datetime import datetime


class BlogStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"


# Base schemas
class BlogMainBase(BaseModel):
    title: Annotated[
        str,
        Field(min_length=1, max_length=255),
    ]
    content: Annotated[
        str,
        Field(min_length=1),
    ]
    meta_description: Optional[str] = None
    featured_image_url: Optional[str] = None
    tags: Optional[List[str]] = None


class BlogMainCreate(BlogMainBase):
    model_config = ConfigDict(extra="forbid")

    slug: Optional[str] = None  # Auto-generated from title if not provided
    category_id: Optional[int] = None
    status: BlogStatus = BlogStatus.DRAFT
    scheduled_publish_at: Optional[datetime] = None


class BlogMainUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = None
    content: Optional[str] = None
    meta_description: Optional[str] = None
    featured_image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[int] = None
    status: Optional[BlogStatus] = None


# Read schemas


class BlogAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class BlogCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    color: Optional[str] = None


class ReactionCount(BaseModel):
    reaction_type: str
    emoji: str
    count: int


class BlogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    slug: str
    content: str
    status: BlogStatus
    meta_description: Optional[str]
    featured_image_url: Optional[str]
    tags: Optional[List[str]]
    view_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    author: BlogAuthor
    category: Optional[BlogCategory]


class BlogDetail(BlogRead):
    """Detailed blog view với reactions và comments count"""

    @computed_field
    @property
    def reading_time(self) -> int:
        """Estimate reading time in minutes"""
        words = len(self.content.split())
        return max(1, words // 200)  # Average 200 words per minute

    @computed_field
    @property
    def is_published(self) -> bool:
        return self.status == BlogStatus.PUBLISHED


class BlogWithStats(BlogDetail):
    """Blog với reaction counts và comment count"""
    reaction_counts: List[ReactionCount] = []
    total_reactions: int = 0
    comment_count: int = 0
    user_reaction: Optional[str] = None  # Current user's reaction


class BlogList(BaseModel):
    """Paginated blog list"""
    items: List[BlogRead]
    total: int
    page: int
    size: int
    pages: int
    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
