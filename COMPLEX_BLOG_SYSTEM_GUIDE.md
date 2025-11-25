# Hướng Dẫn Xây Dựng Hệ Thống Blog Phức Tạp
## Blog + Reactions + Nested Comments

## Mục Lục
1. [Thiết Kế Database Schema](#thiết-kế-database-schema)
2. [Models Implementation](#models-implementation)
3. [Schemas Design](#schemas-design)
4. [Services Layer](#services-layer)
5. [API Controllers](#api-controllers)
6. [Advanced Features](#advanced-features)

---

## Thiết Kế Database Schema

### 1. Core Tables Overview

```sql
-- Blogs table
CREATE TABLE blogs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft', -- draft, published, archived
    author_id INTEGER REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    featured_image_url VARCHAR(500),
    meta_description TEXT,
    tags TEXT[], -- PostgreSQL array
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Reaction types table
CREATE TABLE reaction_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL, -- like, dislike, love, haha, wow, sad, angry
    emoji VARCHAR(10) NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Blog reactions table
CREATE TABLE blog_reactions (
    id SERIAL PRIMARY KEY,
    blog_id INTEGER REFERENCES blogs(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    reaction_type_id INTEGER REFERENCES reaction_types(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(blog_id, user_id) -- One reaction per user per blog
);

-- Comments table (supports nested comments)
CREATE TABLE blog_comments (
    id SERIAL PRIMARY KEY,
    blog_id INTEGER REFERENCES blogs(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES blog_comments(id) ON DELETE CASCADE, -- For nested comments
    content TEXT NOT NULL,
    is_edited BOOLEAN DEFAULT FALSE,
    edited_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Comment reactions table
CREATE TABLE comment_reactions (
    id SERIAL PRIMARY KEY,
    comment_id INTEGER REFERENCES blog_comments(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    reaction_type_id INTEGER REFERENCES reaction_types(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(comment_id, user_id)
);

-- Blog views tracking
CREATE TABLE blog_views (
    id SERIAL PRIMARY KEY,
    blog_id INTEGER REFERENCES blogs(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Allow anonymous views
    ip_address INET,
    user_agent TEXT,
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(255)
);
```

---

## Models Implementation

### 1. Base Models với Mixins

```python
# src/app/models/blog/blog_models.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import INET
from datetime import datetime, UTC
from typing import List, Optional
from ...core.db.database import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin

class BlogStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"

class Blog(Base, TimestampMixin, SoftDeleteMixin, UUIDMixin):
    __tablename__ = "blogs"
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        init=False,
    )
    
    # Core fields
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Status và metadata
    status: Mapped[BlogStatus] = mapped_column(
        String(20),
        default=BlogStatus.DRAFT,
        nullable=False,
        init=False,
    )
    
    meta_description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    featured_image_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=None)
    
    # Metrics
    view_count: Mapped[int] = mapped_column(Integer, default=0, init=False)
    
    # Timestamps
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        init=False,
    )
    
    # Foreign keys
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("blog_categories.id"),
        default=None,
        index=True,
    )
    
    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="blogs",
        lazy="selectin",
        init=False,
    )
    
    category: Mapped[Optional["BlogCategory"]] = relationship(
        "BlogCategory",
        back_populates="blogs",
        lazy="selectin",
        init=False,
    )
    
    reactions: Mapped[List["BlogReaction"]] = relationship(
        "BlogReaction",
        back_populates="blog",
        cascade="all, delete-orphan",
        lazy="dynamic",
        init=False,
    )
    
    comments: Mapped[List["BlogComment"]] = relationship(
        "BlogComment",
        back_populates="blog",
        cascade="all, delete-orphan",
        lazy="dynamic",
        init=False,
    )
    
    views: Mapped[List["BlogView"]] = relationship(
        "BlogView",
        back_populates="blog",
        cascade="all, delete-orphan",
        lazy="dynamic",
        init=False,
    )

class ReactionType(Base):
    __tablename__ = "reaction_types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, init=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, init=False)
    
    # Relationships
    blog_reactions: Mapped[List["BlogReaction"]] = relationship(
        "BlogReaction",
        back_populates="reaction_type",
        init=False,
    )
    
    comment_reactions: Mapped[List["CommentReaction"]] = relationship(
        "CommentReaction",
        back_populates="reaction_type",
        init=False,
    )

class BlogReaction(Base, TimestampMixin):
    __tablename__ = "blog_reactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    
    # Foreign keys
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reaction_type_id: Mapped[int] = mapped_column(ForeignKey("reaction_types.id"))
    
    # Relationships
    blog: Mapped["Blog"] = relationship("Blog", back_populates="reactions", init=False)
    user: Mapped["User"] = relationship("User", back_populates="blog_reactions", init=False)
    reaction_type: Mapped["ReactionType"] = relationship(
        "ReactionType",
        back_populates="blog_reactions",
        lazy="selectin",
        init=False,
    )
    
    # Unique constraint handled at database level
    __table_args__ = (
        UniqueConstraint('blog_id', 'user_id', name='unique_blog_user_reaction'),
    )

class BlogComment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "blog_comments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Edit tracking
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, init=False)
    edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        init=False,
    )
    
    # Foreign keys
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("blog_comments.id"),
        default=None,
        index=True,
    )
    
    # Relationships
    blog: Mapped["Blog"] = relationship("Blog", back_populates="comments", init=False)
    user: Mapped["User"] = relationship("User", back_populates="blog_comments", init=False)
    
    # Self-referential relationship for nested comments
    parent: Mapped[Optional["BlogComment"]] = relationship(
        "BlogComment",
        back_populates="replies",
        remote_side="BlogComment.id",
        init=False,
    )
    
    replies: Mapped[List["BlogComment"]] = relationship(
        "BlogComment",
        back_populates="parent",
        cascade="all, delete-orphan",
        init=False,
    )
    
    reactions: Mapped[List["CommentReaction"]] = relationship(
        "CommentReaction",
        back_populates="comment",
        cascade="all, delete-orphan",
        lazy="dynamic",
        init=False,
    )

class CommentReaction(Base, TimestampMixin):
    __tablename__ = "comment_reactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    
    # Foreign keys
    comment_id: Mapped[int] = mapped_column(ForeignKey("blog_comments.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reaction_type_id: Mapped[int] = mapped_column(ForeignKey("reaction_types.id"))
    
    # Relationships
    comment: Mapped["BlogComment"] = relationship(
        "BlogComment",
        back_populates="reactions",
        init=False,
    )
    user: Mapped["User"] = relationship("User", init=False)
    reaction_type: Mapped["ReactionType"] = relationship(
        "ReactionType",
        back_populates="comment_reactions",
        lazy="selectin",
        init=False,
    )
    
    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', name='unique_comment_user_reaction'),
    )

class BlogView(Base):
    __tablename__ = "blog_views"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    
    # Tracking fields
    ip_address: Mapped[Optional[str]] = mapped_column(INET, default=None)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, default=None)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        init=False,
    )
    
    # Foreign keys
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        default=None,
        index=True,
    )
    
    # Relationships
    blog: Mapped["Blog"] = relationship("Blog", back_populates="views", init=False)
    user: Mapped[Optional["User"]] = relationship("User", init=False)

class BlogCategory(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "blog_categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    color: Mapped[Optional[str]] = mapped_column(String(7), default=None)  # Hex color
    
    # Relationships
    blogs: Mapped[List["Blog"]] = relationship(
        "Blog",
        back_populates="category",
        init=False,
    )
```

---

## Schemas Design

### 1. Blog Schemas

```python
# src/app/schemas/blog/blog_schemas.py
from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Annotated, Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BlogStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"

# Base schemas
class BlogBase(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=255)]
    content: Annotated[str, Field(min_length=1)]
    meta_description: Optional[str] = None
    featured_image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class BlogCreate(BlogBase):
    model_config = ConfigDict(extra="forbid")
    
    slug: Optional[str] = None  # Auto-generated from title if not provided
    category_id: Optional[int] = None
    status: BlogStatus = BlogStatus.DRAFT
    scheduled_publish_at: Optional[datetime] = None

class BlogUpdate(BaseModel):
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
```

### 2. Reaction Schemas

```python
# src/app/schemas/blog/reaction_schemas.py
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ReactionTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    emoji: str
    display_name: str
    sort_order: int

class BlogReactionCreate(BaseModel):
    reaction_type_name: str  # like, dislike, love, haha, wow, sad, angry

class BlogReactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    reaction_type: ReactionTypeRead
    created_at: datetime

class CommentReactionCreate(BaseModel):
    reaction_type_name: str

class ReactionSummary(BaseModel):
    """Summary of reactions for a blog/comment"""
    total_count: int
    reactions: List[ReactionCount]
    user_reaction: Optional[str] = None
```

### 3. Comment Schemas

```python
# src/app/schemas/blog/comment_schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, List, Optional
from datetime import datetime

class CommentBase(BaseModel):
    content: Annotated[str, Field(min_length=1, max_length=5000)]

class CommentCreate(CommentBase):
    model_config = ConfigDict(extra="forbid")
    
    parent_id: Optional[int] = None  # For nested comments

class CommentUpdate(BaseModel):
    content: Annotated[str, Field(min_length=1, max_length=5000)]

class CommentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    content: str
    is_edited: bool
    edited_at: Optional[datetime]
    created_at: datetime
    parent_id: Optional[int]
    
    user: CommentUser

class CommentWithReplies(CommentRead):
    """Comment với nested replies"""
    replies: List['CommentWithReplies'] = []
    reaction_counts: List[ReactionCount] = []
    total_reactions: int = 0
    user_reaction: Optional[str] = None
    
    # Enable forward references
    model_rebuild()

class CommentTree(BaseModel):
    """Hierarchical comment structure"""
    comments: List[CommentWithReplies]
    total_count: int
```

---

## Services Layer

### 1. Blog Service

```python
# src/app/services/blog/blog_service.py
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, UTC
import re
from slugify import slugify

from ...models.blog.blog_models import Blog, BlogCategory, BlogReaction, ReactionType
from ...schemas.blog.blog_schemas import BlogCreate, BlogUpdate, BlogStatus
from ...core.exceptions import NotFoundError, ValidationError, PermissionError
from ..base import BaseService

class BlogService(BaseService[Blog, BlogCreate, BlogUpdate]):
    
    def __init__(self):
        super().__init__(Blog)
    
    async def create_blog(
        self,
        db: AsyncSession,
        blog_in: BlogCreate,
        author_id: int
    ) -> Blog:
        """Create new blog với auto-slug generation"""
        
        # Generate slug if not provided
        if not blog_in.slug:
            base_slug = slugify(blog_in.title)
            slug = await self._generate_unique_slug(db, base_slug)
        else:
            slug = slugify(blog_in.slug)
            # Check slug uniqueness
            existing = await self._get_by_slug(db, slug)
            if existing:
                raise ValidationError("Slug already exists")
        
        # Validate category if provided
        if blog_in.category_id:
            category = await db.get(BlogCategory, blog_in.category_id)
            if not category or category.is_deleted:
                raise ValidationError("Invalid category")
        
        blog_data = blog_in.model_dump(exclude={'scheduled_publish_at'})
        blog_data.update({
            'slug': slug,
            'author_id': author_id,
        })
        
        # Handle scheduled publishing
        if blog_in.status == BlogStatus.SCHEDULED and blog_in.scheduled_publish_at:
            if blog_in.scheduled_publish_at <= datetime.now(UTC):
                raise ValidationError("Scheduled publish time must be in the future")
            # In real app, you'd set up a background job here
        
        # Auto-publish if status is published
        if blog_in.status == BlogStatus.PUBLISHED:
            blog_data['published_at'] = datetime.now(UTC)
        
        blog = Blog(**blog_data)
        db.add(blog)
        await db.commit()
        await db.refresh(blog)
        return blog
    
    async def update_blog(
        self,
        db: AsyncSession,
        blog_id: int,
        blog_update: BlogUpdate,
        user_id: int
    ) -> Blog:
        """Update blog với permission check"""
        
        blog = await self.get(db, blog_id, load_relationships=True)
        if not blog:
            raise NotFoundError("Blog not found")
        
        # Permission check
        if blog.author_id != user_id:
            raise PermissionError("You can only edit your own blogs")
        
        update_data = blog_update.model_dump(exclude_unset=True)
        
        # Handle status changes
        if 'status' in update_data:
            if update_data['status'] == BlogStatus.PUBLISHED and not blog.published_at:
                update_data['published_at'] = datetime.now(UTC)
            elif update_data['status'] != BlogStatus.PUBLISHED:
                update_data['published_at'] = None
        
        # Update blog
        for field, value in update_data.items():
            setattr(blog, field, value)
        
        blog.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(blog)
        return blog
    
    async def get_published_blogs(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",  # created_at, published_at, view_count, title
        sort_order: str = "desc"
    ) -> Tuple[List[Blog], int]:
        """Get published blogs với filtering và sorting"""
        
        query = select(Blog).options(
            selectinload(Blog.author),
            selectinload(Blog.category)
        ).where(
            and_(
                Blog.status == BlogStatus.PUBLISHED,
                Blog.is_deleted == False
            )
        )
        
        # Apply filters
        if category_id:
            query = query.where(Blog.category_id == category_id)
        
        if search:
            search_filter = or_(
                Blog.title.ilike(f"%{search}%"),
                Blog.content.ilike(f"%{search}%"),
                Blog.meta_description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        if tags:
            # PostgreSQL array overlap
            query = query.where(Blog.tags.overlap(tags))
        
        # Apply sorting
        sort_column = getattr(Blog, sort_by, Blog.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        blogs_query = query.offset(skip).limit(limit)
        result = await db.execute(blogs_query)
        blogs = result.scalars().all()
        
        return blogs, total
    
    async def get_blog_with_stats(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get blog với reaction counts và user's reaction"""
        
        blog = await self.get(db, blog_id, load_relationships=True)
        if not blog:
            return None
        
        # Get reaction counts
        reaction_counts_query = (
            select(
                ReactionType.name,
                ReactionType.emoji,
                func.count(BlogReaction.id).label('count')
            )
            .select_from(
                ReactionType
                .outerjoin(BlogReaction, and_(
                    BlogReaction.reaction_type_id == ReactionType.id,
                    BlogReaction.blog_id == blog_id
                ))
            )
            .where(ReactionType.is_active == True)
            .group_by(ReactionType.id, ReactionType.name, ReactionType.emoji)
            .order_by(ReactionType.sort_order)
        )
        
        result = await db.execute(reaction_counts_query)
        reaction_data = result.all()
        
        reaction_counts = [
            {
                "reaction_type": row.name,
                "emoji": row.emoji,
                "count": row.count
            }
            for row in reaction_data
        ]
        
        total_reactions = sum(r["count"] for r in reaction_counts)
        
        # Get user's reaction if authenticated
        user_reaction = None
        if user_id:
            user_reaction_query = (
                select(ReactionType.name)
                .select_from(
                    BlogReaction.join(ReactionType)
                )
                .where(
                    and_(
                        BlogReaction.blog_id == blog_id,
                        BlogReaction.user_id == user_id
                    )
                )
            )
            result = await db.execute(user_reaction_query)
            user_reaction = result.scalar_one_or_none()
        
        # Get comment count
        comment_count_query = select(func.count(BlogComment.id)).where(
            and_(
                BlogComment.blog_id == blog_id,
                BlogComment.is_deleted == False
            )
        )
        result = await db.execute(comment_count_query)
        comment_count = result.scalar()
        
        return {
            "blog": blog,
            "reaction_counts": reaction_counts,
            "total_reactions": total_reactions,
            "user_reaction": user_reaction,
            "comment_count": comment_count
        }
    
    async def increment_view_count(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Track blog view và increment counter"""
        
        # Check if this view should be counted (avoid spam)
        should_count = await self._should_count_view(
            db, blog_id, user_id, ip_address, session_id
        )
        
        if should_count:
            # Create view record
            blog_view = BlogView(
                blog_id=blog_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            db.add(blog_view)
            
            # Increment view count
            await db.execute(
                update(Blog)
                .where(Blog.id == blog_id)
                .values(view_count=Blog.view_count + 1)
            )
            
            await db.commit()
    
    # Helper methods
    async def _generate_unique_slug(self, db: AsyncSession, base_slug: str) -> str:
        """Generate unique slug"""
        slug = base_slug
        counter = 1
        
        while await self._get_by_slug(db, slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    async def _get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Blog]:
        """Get blog by slug"""
        query = select(Blog).where(Blog.slug == slug)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _should_count_view(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: Optional[int],
        ip_address: Optional[str],
        session_id: Optional[str]
    ) -> bool:
        """Determine if view should be counted (anti-spam)"""
        
        # Time window for unique views (e.g., 1 hour)
        time_threshold = datetime.now(UTC) - timedelta(hours=1)
        
        filters = [
            BlogView.blog_id == blog_id,
            BlogView.viewed_at > time_threshold
        ]
        
        if user_id:
            filters.append(BlogView.user_id == user_id)
        elif ip_address and session_id:
            filters.append(and_(
                BlogView.ip_address == ip_address,
                BlogView.session_id == session_id
            ))
        else:
            return False  # Can't identify unique view
        
        query = select(func.count(BlogView.id)).where(and_(*filters))
        result = await db.execute(query)
        existing_views = result.scalar()
        
        return existing_views == 0

blog_service = BlogService()
```

### 2. Reaction Service

```python
# src/app/services/blog/reaction_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from sqlalchemy.orm import selectinload

from ...models.blog.blog_models import BlogReaction, CommentReaction, ReactionType
from ...schemas.blog.reaction_schemas import BlogReactionCreate, CommentReactionCreate
from ...core.exceptions import NotFoundError, ValidationError

class ReactionService:
    
    async def toggle_blog_reaction(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: int,
        reaction_create: BlogReactionCreate
    ) -> Dict[str, Any]:
        """Toggle reaction on blog (add/remove/change)"""
        
        # Get reaction type
        reaction_type = await self._get_reaction_type_by_name(
            db, reaction_create.reaction_type_name
        )
        if not reaction_type:
            raise ValidationError("Invalid reaction type")
        
        # Check existing reaction
        existing_reaction = await self._get_user_blog_reaction(db, blog_id, user_id)
        
        if existing_reaction:
            if existing_reaction.reaction_type_id == reaction_type.id:
                # Same reaction - remove it
                await db.delete(existing_reaction)
                action = "removed"
            else:
                # Different reaction - update it
                existing_reaction.reaction_type_id = reaction_type.id
                existing_reaction.updated_at = datetime.now(UTC)
                action = "changed"
        else:
            # New reaction - create it
            new_reaction = BlogReaction(
                blog_id=blog_id,
                user_id=user_id,
                reaction_type_id=reaction_type.id
            )
            db.add(new_reaction)
            action = "added"
        
        await db.commit()
        
        # Get updated reaction counts
        reaction_summary = await self.get_blog_reaction_summary(db, blog_id, user_id)
        
        return {
            "action": action,
            "reaction_type": reaction_type.name,
            "summary": reaction_summary
        }
    
    async def toggle_comment_reaction(
        self,
        db: AsyncSession,
        comment_id: int,
        user_id: int,
        reaction_create: CommentReactionCreate
    ) -> Dict[str, Any]:
        """Toggle reaction on comment"""
        
        reaction_type = await self._get_reaction_type_by_name(
            db, reaction_create.reaction_type_name
        )
        if not reaction_type:
            raise ValidationError("Invalid reaction type")
        
        existing_reaction = await self._get_user_comment_reaction(db, comment_id, user_id)
        
        if existing_reaction:
            if existing_reaction.reaction_type_id == reaction_type.id:
                await db.delete(existing_reaction)
                action = "removed"
            else:
                existing_reaction.reaction_type_id = reaction_type.id
                existing_reaction.updated_at = datetime.now(UTC)
                action = "changed"
        else:
            new_reaction = CommentReaction(
                comment_id=comment_id,
                user_id=user_id,
                reaction_type_id=reaction_type.id
            )
            db.add(new_reaction)
            action = "added"
        
        await db.commit()
        
        reaction_summary = await self.get_comment_reaction_summary(db, comment_id, user_id)
        
        return {
            "action": action,
            "reaction_type": reaction_type.name,
            "summary": reaction_summary
        }
    
    async def get_blog_reaction_summary(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get reaction summary for blog"""
        
        # Get reaction counts
        query = (
            select(
                ReactionType.name,
                ReactionType.emoji,
                ReactionType.display_name,
                func.count(BlogReaction.id).label('count')
            )
            .select_from(
                ReactionType
                .outerjoin(BlogReaction, and_(
                    BlogReaction.reaction_type_id == ReactionType.id,
                    BlogReaction.blog_id == blog_id
                ))
            )
            .where(ReactionType.is_active == True)
            .group_by(ReactionType.id)
            .order_by(ReactionType.sort_order)
        )
        
        result = await db.execute(query)
        reaction_data = result.all()
        
        reactions = [
            {
                "reaction_type": row.name,
                "emoji": row.emoji,
                "display_name": row.display_name,
                "count": row.count
            }
            for row in reaction_data if row.count > 0
        ]
        
        total_count = sum(r["count"] for r in reactions)
        
        # Get user's reaction
        user_reaction = None
        if user_id:
            user_reaction_result = await self._get_user_blog_reaction(db, blog_id, user_id)
            if user_reaction_result:
                user_reaction = user_reaction_result.reaction_type.name
        
        return {
            "total_count": total_count,
            "reactions": reactions,
            "user_reaction": user_reaction
        }
    
    async def get_comment_reaction_summary(
        self,
        db: AsyncSession,
        comment_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get reaction summary for comment"""
        
        query = (
            select(
                ReactionType.name,
                ReactionType.emoji,
                ReactionType.display_name,
                func.count(CommentReaction.id).label('count')
            )
            .select_from(
                ReactionType
                .outerjoin(CommentReaction, and_(
                    CommentReaction.reaction_type_id == ReactionType.id,
                    CommentReaction.comment_id == comment_id
                ))
            )
            .where(ReactionType.is_active == True)
            .group_by(ReactionType.id)
            .order_by(ReactionType.sort_order)
        )
        
        result = await db.execute(query)
        reaction_data = result.all()
        
        reactions = [
            {
                "reaction_type": row.name,
                "emoji": row.emoji,
                "display_name": row.display_name,
                "count": row.count
            }
            for row in reaction_data if row.count > 0
        ]
        
        total_count = sum(r["count"] for r in reactions)
        
        user_reaction = None
        if user_id:
            user_reaction_result = await self._get_user_comment_reaction(db, comment_id, user_id)
            if user_reaction_result:
                user_reaction = user_reaction_result.reaction_type.name
        
        return {
            "total_count": total_count,
            "reactions": reactions,
            "user_reaction": user_reaction
        }
    
    async def get_available_reaction_types(self, db: AsyncSession) -> List[ReactionType]:
        """Get all available reaction types"""
        query = select(ReactionType).where(
            ReactionType.is_active == True
        ).order_by(ReactionType.sort_order)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    # Helper methods
    async def _get_reaction_type_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[ReactionType]:
        query = select(ReactionType).where(
            and_(
                ReactionType.name == name,
                ReactionType.is_active == True
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_user_blog_reaction(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: int
    ) -> Optional[BlogReaction]:
        query = select(BlogReaction).options(
            selectinload(BlogReaction.reaction_type)
        ).where(
            and_(
                BlogReaction.blog_id == blog_id,
                BlogReaction.user_id == user_id
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_user_comment_reaction(
        self,
        db: AsyncSession,
        comment_id: int,
        user_id: int
    ) -> Optional[CommentReaction]:
        query = select(CommentReaction).options(
            selectinload(CommentReaction.reaction_type)
        ).where(
            and_(
                CommentReaction.comment_id == comment_id,
                CommentReaction.user_id == user_id
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

reaction_service = ReactionService()
```

---

## API Controllers

### 1. Blog Controller

```python
# src/app/api/v1/blog/blog_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from typing import Annotated, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.db.database import async_get_db
from ....services.blog.blog_service import blog_service
from ....services.blog.reaction_service import reaction_service
from ....schemas.blog.blog_schemas import (
    BlogCreate, BlogUpdate, BlogRead, BlogDetail, BlogWithStats, BlogList
)
from ....schemas.blog.reaction_schemas import BlogReactionCreate
from ....api.dependencies import get_current_user, get_optional_current_user
from ....models.user import User

router = APIRouter(prefix="/blogs", tags=["blogs"])

@router.post("/", response_model=BlogDetail, status_code=201)
async def create_blog(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    blog_in: BlogCreate,
    current_user: Annotated[User, Depends(get_current_user)]
) -> BlogDetail:
    """Create new blog post"""
    try:
        blog = await blog_service.create_blog(db, blog_in, current_user.id)
        return BlogDetail.model_validate(blog)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=BlogList)
async def list_blogs(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    category_id: Annotated[Optional[int], Query()] = None,
    search: Annotated[Optional[str], Query(max_length=255)] = None,
    tags: Annotated[Optional[List[str]], Query()] = None,
    sort_by: Annotated[str, Query(regex="^(created_at|published_at|view_count|title)$")] = "created_at",
    sort_order: Annotated[str, Query(regex="^(asc|desc)$")] = "desc"
) -> BlogList:
    """
    List published blogs với filtering options:
    
    - **category_id**: Filter by category
    - **search**: Search in title, content, meta_description
    - **tags**: Filter by tags
    - **sort_by**: Sort by field (created_at, published_at, view_count, title)
    - **sort_order**: asc hoặc desc
    """
    blogs, total = await blog_service.get_published_blogs(
        db=db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        search=search,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return BlogList(
        items=[BlogRead.model_validate(blog) for blog in blogs],
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.get("/{blog_id}", response_model=BlogWithStats)
async def get_blog(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    blog_id: Annotated[int, Path(gt=0)],
    request: Request,
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)] = None
) -> BlogWithStats:
    """Get blog detail với reactions và comments count"""
    
    blog_data = await blog_service.get_blog_with_stats(
        db, blog_id, current_user.id if current_user else None
    )
    
    if not blog_data:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Track view
    await blog_service.increment_view_count(
        db=db,
        blog_id=blog_id,
        user_id=current_user.id if current_user else None,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        session_id=request.session.get("session_id")
    )
    
    return BlogWithStats(
        **BlogDetail.model_validate(blog_data["blog"]).model_dump(),
        reaction_counts=blog_data["reaction_counts"],
        total_reactions=blog_data["total_reactions"],
        user_reaction=blog_data["user_reaction"],
        comment_count=blog_data["comment_count"]
    )

@router.put("/{blog_id}", response_model=BlogDetail)
async def update_blog(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    blog_id: Annotated[int, Path(gt=0)],
    blog_update: BlogUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
) -> BlogDetail:
    """Update blog (only author can update)"""
    try:
        blog = await blog_service.update_blog(db, blog_id, blog_update, current_user.id)
        return BlogDetail.model_validate(blog)
    except (NotFoundError, PermissionError) as e:
        status_code = 404 if isinstance(e, NotFoundError) else 403
        raise HTTPException(status_code=status_code, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{blog_id}", status_code=204)
async def delete_blog(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    blog_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> None:
    """Soft delete blog (only author can delete)"""
    try:
        blog = await blog_service.get(db, blog_id)
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        if blog.author_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only delete your own blogs")
        
        await blog_service.soft_delete(db, blog_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Reaction endpoints
@router.post("/{blog_id}/reactions", response_model=dict)
async def toggle_blog_reaction(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    blog_id: Annotated[int, Path(gt=0)],
    reaction_in: BlogReactionCreate,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """Toggle reaction on blog (like, dislike, love, etc.)"""
    try:
        # Verify blog exists
        blog = await blog_service.get(db, blog_id)
        if not blog or blog.status != "published":
            raise HTTPException(status_code=404, detail="Blog not found")
        
        result = await reaction_service.toggle_blog_reaction(
            db, blog_id, current_user.id, reaction_in
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{blog_id}/reactions", response_model=dict)
async def get_blog_reactions(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    blog_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)] = None
) -> dict:
    """Get blog reaction summary"""
    summary = await reaction_service.get_blog_reaction_summary(
        db, blog_id, current_user.id if current_user else None
    )
    return summary

# Get user's own blogs
@router.get("/my/blogs", response_model=BlogList)
async def get_my_blogs(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    status: Annotated[Optional[str], Query()] = None
) -> BlogList:
    """Get current user's blogs"""
    filters = {"author_id": current_user.id}
    if status:
        filters["status"] = status
    
    blogs = await blog_service.get_multi(
        db, skip=skip, limit=limit, filters=filters
    )
    
    # Get total count
    total = await blog_service.count_with_filters(db, filters)
    
    return BlogList(
        items=[BlogRead.model_validate(blog) for blog in blogs],
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )
```

Hướng dẫn này đã cover các aspects chính của hệ thống blog phức tạp với reactions và nested comments. Bạn có thể extend thêm nhiều features khác như notifications, advanced search, content moderation, etc. 🚀