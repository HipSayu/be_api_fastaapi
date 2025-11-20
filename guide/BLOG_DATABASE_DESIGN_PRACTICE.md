# 🏗️ THỰC HÀNH: THIẾT KẾ DATABASE BLOG SYSTEM

## 🎯 Mục tiêu: Thiết kế database hoàn chỉnh cho blog system

### 📋 Yêu cầu chức năng:
- Users có thể đăng ký, login
- Users có roles (admin, editor, author, reader)
- Posts có categories và tags
- Comments system với threading
- Like/Unlike posts và comments  
- Follow/Unfollow users
- Bookmark posts
- User profiles với social links

---

## 🗄️ BƯỚC 1: THIẾT KẾ ERD (Entity Relationship Diagram)

```
📊 RELATIONSHIPS MAPPING:

Users (1) ←→ (N) Posts           [One-to-Many: User có nhiều Posts]
Users (N) ←→ (N) Roles           [Many-to-Many: User có nhiều Roles]  
Posts (N) ←→ (N) Tags            [Many-to-Many: Post có nhiều Tags]
Posts (N) ←→ (1) Categories      [Many-to-One: Post thuộc một Category]
Posts (1) ←→ (N) Comments        [One-to-Many: Post có nhiều Comments]
Comments (1) ←→ (N) Comments     [Self-Referencing: Comment reply Comment]
Users (N) ←→ (N) Users           [Many-to-Many: User follow User]
Users (1) ←→ (1) UserProfiles    [One-to-One: User có một Profile]

Generic Relationships:
- Likes: User like (Post | Comment)
- Bookmarks: User bookmark Post
```

---

## 🏗️ BƯỚC 2: TẠO BASE MODELS

```python
# src/app/models/base.py
from datetime import datetime, UTC
from typing import Optional, Any
from sqlalchemy import String, DateTime, Boolean, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Base(DeclarativeBase):
    """Base declarative class"""
    type_annotation_map = {
        dict[str, Any]: JSON
    }

class TimestampMixin:
    """Mixin cho timestamps"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.now(UTC),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
        nullable=False
    )

class SoftDeleteMixin:
    """Mixin cho soft delete"""
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """Base model với common fields"""
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # UUID cho public references (không expose internal IDs)
    uuid: Mapped[str] = mapped_column(
        String(36), 
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
        index=True
    )

class AuditMixin:
    """Mixin cho audit trail"""
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), 
        nullable=True
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), 
        nullable=True
    )
```

---

## 👤 BƯỚC 3: USER SYSTEM

### User Model với Profile (1:1)

```python
# src/app/models/user.py
from typing import Optional, List
from sqlalchemy import String, Boolean, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from .base import BaseModel, AuditMixin

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class User(BaseModel):
    __tablename__ = "users"
    
    # 🔐 Authentication fields
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 👤 Basic info
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 📧 Email verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # 🚦 Account status
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus), 
        default=UserStatus.PENDING
    )
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # 🔗 ONE-TO-ONE: User Profile
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # 🔗 ONE-TO-MANY: User's content
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="author",
        foreign_keys="Post.author_id",
        cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan"
    )
    
    # 🔗 MANY-TO-MANY: User Roles
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 🔗 MANY-TO-MANY: Following system  
    following: Mapped[List["UserFollow"]] = relationship(
        "UserFollow",
        foreign_keys="UserFollow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )
    followers: Mapped[List["UserFollow"]] = relationship(
        "UserFollow",
        foreign_keys="UserFollow.following_id", 
        back_populates="following"
    )
    
    # 🔗 User interactions
    likes: Mapped[List["Like"]] = relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    bookmarks: Mapped[List["Bookmark"]] = relationship(
        "Bookmark", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 🔧 Helper properties
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def public_name(self) -> str:
        return self.display_name or self.full_name
    
    def get_active_roles(self) -> List["Role"]:
        """Lấy active roles của user"""
        return [ur.role for ur in self.user_roles if ur.is_active]

class UserProfile(BaseModel):
    __tablename__ = "user_profiles"
    
    # 🔑 ONE-TO-ONE reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # 👤 Profile info
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # 📍 Location
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 📞 Contact
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 🌐 Social links
    social_links: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Example: {"github": "username", "twitter": "@username", "linkedin": "profile-url"}
    
    # ⚙️ Preferences
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Example: {"email_notifications": true, "theme": "dark", "language": "en"}
    
    # 📊 Stats (computed fields)
    followers_count: Mapped[int] = mapped_column(Integer, default=0)
    following_count: Mapped[int] = mapped_column(Integer, default=0)
    posts_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 🔗 Relationship
    user: Mapped["User"] = relationship("User", back_populates="profile")
```

---

## 🛡️ BƯỚC 4: ROLE SYSTEM (Many-to-Many với Association Object)

```python
# src/app/models/role.py
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class Role(BaseModel):
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 🔒 Permissions as JSON
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    # Example: {"posts": ["create", "read", "update", "delete"], "users": ["read"]}
    
    # 🎨 UI properties
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 🚦 Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)  # Default role cho new users
    
    # 🔗 Relationships
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="role"
    )

class UserRole(BaseModel):
    """Association object cho User-Role relationship với metadata"""
    __tablename__ = "user_roles"
    
    # 🔑 Foreign Keys
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 📅 Assignment info
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.now(UTC)
    )
    assigned_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), 
        nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # 🚦 Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 🗒️ Notes
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 🔗 Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    assigned_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by])
    
    # 🔒 Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='unique_user_role'),
        Index('idx_user_role_active', 'user_id', 'is_active'),
    )
```

---

## 📝 BƯỚC 5: CONTENT SYSTEM

### Categories (Self-Referencing Tree)

```python
# src/app/models/category.py
from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class Category(BaseModel):
    __tablename__ = "categories"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 🎨 Display properties
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 🌳 Tree structure
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # 🚦 Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 📊 SEO & metadata
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meta_keywords: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 📊 Stats
    posts_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 🔗 Self-referencing relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    # 🔗 Category có nhiều Posts
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="category"
    )
    
    # 🔧 Helper methods
    @property
    def full_name(self) -> str:
        """Lấy full path của category"""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name
    
    def get_all_children(self) -> List["Category"]:
        """Lấy tất cả descendants"""
        children = list(self.children)
        for child in self.children:
            children.extend(child.get_all_children())
        return children
```

### Tags (Many-to-Many với Posts)

```python
# src/app/models/tag.py
from typing import List
from sqlalchemy import String, Integer, Boolean, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, Base

# 🔗 Association table cho Post-Tag relationship
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime(timezone=True), default=datetime.now(UTC))
)

class Tag(BaseModel):
    __tablename__ = "tags"
    
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 🎨 Display
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # 📊 Stats  
    posts_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 🚦 Status
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 👤 Created by (có thể tự tạo bởi users)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), 
        nullable=True
    )
    
    # 🔗 Relationships
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        secondary=post_tags,
        back_populates="tags"
    )
    creator: Mapped[Optional["User"]] = relationship("User")
```

### Posts Model

```python
# src/app/models/post.py
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from .base import BaseModel, AuditMixin

class PostStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published" 
    SCHEDULED = "scheduled"
    ARCHIVED = "archived"

class PostType(Enum):
    ARTICLE = "article"
    PAGE = "page"
    TUTORIAL = "tutorial"
    NEWS = "news"

class Post(BaseModel, AuditMixin):
    __tablename__ = "posts"
    
    # 📝 Content
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 🎨 Media
    featured_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    featured_image_alt: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 📊 Classification
    status: Mapped[PostStatus] = mapped_column(SQLEnum(PostStatus), default=PostStatus.DRAFT, index=True)
    post_type: Mapped[PostType] = mapped_column(SQLEnum(PostType), default=PostType.ARTICLE)
    
    # 📅 Publishing
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 👤 Author & Editor
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # 🗂️ Category
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # 📊 SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meta_keywords: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 🔧 Settings
    allow_comments: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sticky: Mapped[bool] = mapped_column(Boolean, default=False)  # Pin to top
    
    # 📊 Stats (updated by triggers/events)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 📖 Reading stats  
    reading_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Minutes
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 🔗 Relationships
    author: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[author_id],
        back_populates="posts"
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="posts"
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=post_tags,
        back_populates="posts"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan"
    )
    likes: Mapped[List["Like"]] = relationship(
        "Like",
        back_populates="post",
        cascade="all, delete-orphan"
    )
    bookmarks: Mapped[List["Bookmark"]] = relationship(
        "Bookmark",
        back_populates="post", 
        cascade="all, delete-orphan"
    )
    
    # 🔧 Helper methods
    @property
    def is_published(self) -> bool:
        return self.status == PostStatus.PUBLISHED and self.published_at is not None
    
    @property
    def is_scheduled(self) -> bool:
        return (self.status == PostStatus.SCHEDULED and 
                self.scheduled_at is not None and 
                self.scheduled_at > datetime.now(UTC))
```

---

## 💬 BƯỚC 6: COMMENT SYSTEM (Self-Referencing Threading)

```python
# src/app/models/comment.py
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class Comment(BaseModel):
    __tablename__ = "comments"
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 🔗 Belongs to Post
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 👤 Author
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 🔄 Threading system
    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # 🌳 Tree helpers
    depth: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Example path: "1" for root, "1.5" for reply to comment 1, "1.5.3" for reply to 1.5
    
    # 🚦 Status
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 📊 Stats
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 🔗 Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")
    
    # 🔄 Self-referencing
    parent_comment: Mapped[Optional["Comment"]] = relationship(
        "Comment",
        remote_side="Comment.id",
        back_populates="replies"
    )
    replies: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="parent_comment",
        cascade="all, delete-orphan"
    )
    
    # 🔗 Likes
    likes: Mapped[List["Like"]] = relationship(
        "Like",
        back_populates="comment",
        cascade="all, delete-orphan"
    )
    
    # 🔧 Helper methods
    @property
    def is_top_level(self) -> bool:
        return self.parent_comment_id is None
    
    def get_thread_root(self) -> "Comment":
        """Lấy comment gốc của thread"""
        current = self
        while current.parent_comment:
            current = current.parent_comment
        return current
    
    def generate_path(self) -> str:
        """Generate path for comment threading"""
        if self.parent_comment:
            return f"{self.parent_comment.path}.{self.id}"
        return str(self.id)
```

---

## 💖 BƯỚC 7: INTERACTION SYSTEM (Generic Relationships)

### Following System (User-User Many-to-Many)

```python
# src/app/models/follow.py
from sqlalchemy import ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class UserFollow(BaseModel):
    __tablename__ = "user_follows"
    
    # 🔑 Many-to-Many User-User
    follower_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    following_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 📅 Follow metadata
    followed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.now(UTC)
    )
    
    # 🔔 Notification settings
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 🔗 Relationships
    follower: Mapped["User"] = relationship(
        "User",
        foreign_keys=[follower_id],
        back_populates="following"
    )
    following: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[following_id],
        back_populates="followers"
    )
    
    # 🔒 Constraints
    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='unique_follow'),
        CheckConstraint('follower_id != following_id', name='no_self_follow'),
        Index('idx_follower_following', 'follower_id', 'following_id'),
    )
```

### Like System (Generic Polymorphic)

```python
# src/app/models/like.py
from sqlalchemy import String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class Like(BaseModel):
    __tablename__ = "likes"
    
    # 👤 User who liked
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 🔄 Generic Foreign Key pattern
    content_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        index=True
    )  # "post", "comment"
    object_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # 🔗 Relationships
    user: Mapped["User"] = relationship("User", back_populates="likes")
    
    # 🔒 Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'content_type', 'object_id', name='unique_like'),
        Index('idx_content_object', 'content_type', 'object_id'),
    )
    
    # 🔧 Helper methods
    async def get_liked_object(self, db: AsyncSession):
        """Lấy object được like"""
        if self.content_type == "post":
            from .post import Post
            return await db.get(Post, self.object_id)
        elif self.content_type == "comment":
            from .comment import Comment
            return await db.get(Comment, self.object_id)
        return None

# Add methods to Post and Comment models
class Post(BaseModel):
    # ... existing fields ...
    
    def get_likes(self) -> List[Like]:
        """Lấy likes của post"""
        return [like for like in self.likes if like.content_type == "post"]
    
    async def is_liked_by(self, user_id: int, db: AsyncSession) -> bool:
        """Kiểm tra user đã like post chưa"""
        result = await db.execute(
            select(Like).where(
                Like.user_id == user_id,
                Like.content_type == "post", 
                Like.object_id == self.id
            )
        )
        return result.scalar_one_or_none() is not None
```

### Bookmark System

```python
# src/app/models/bookmark.py
from typing import Optional
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class Bookmark(BaseModel):
    __tablename__ = "bookmarks"
    
    # 👤 User who bookmarked
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 📝 Post being bookmarked
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 🗒️ Optional note
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 🏷️ Optional folder/collection
    folder: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 🔗 Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookmarks")
    post: Mapped["Post"] = relationship("Post", back_populates="bookmarks")
    
    # 🔒 Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='unique_bookmark'),
        Index('idx_user_folder', 'user_id', 'folder'),
    )
```

---

## 🔍 BƯỚC 8: QUERY EXAMPLES

### Complex Relationship Queries

```python
# src/app/crud/blog_queries.py
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload, joinedload, contains_eager

class BlogQueries:
    
    async def get_popular_posts_with_authors(self, db: AsyncSession, limit: int = 10):
        """Lấy posts phổ biến với author info"""
        result = await db.execute(
            select(Post)
            .options(
                joinedload(Post.author).joinedload(User.profile),
                selectinload(Post.tags),
                joinedload(Post.category)
            )
            .where(Post.status == PostStatus.PUBLISHED)
            .order_by(
                desc(Post.like_count + Post.bookmark_count + Post.view_count)
            )
            .limit(limit)
        )
        return result.scalars().unique().all()
    
    async def get_user_feed(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20):
        """Lấy feed từ users mà user đang follow"""
        result = await db.execute(
            select(Post)
            .join(UserFollow, Post.author_id == UserFollow.following_id)
            .options(
                joinedload(Post.author).joinedload(User.profile),
                selectinload(Post.tags),
                selectinload(Post.comments.and_(Comment.depth == 0)).selectinload(Comment.author)
            )
            .where(
                and_(
                    UserFollow.follower_id == user_id,
                    Post.status == PostStatus.PUBLISHED
                )
            )
            .order_by(desc(Post.published_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().unique().all()
    
    async def get_trending_tags(self, db: AsyncSession, days: int = 7, limit: int = 10):
        """Lấy tags trending trong X ngày"""
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        
        result = await db.execute(
            select(
                Tag.id,
                Tag.name,
                Tag.color,
                func.count(Post.id).label("recent_posts_count")
            )
            .join(post_tags, Tag.id == post_tags.c.tag_id)
            .join(Post, post_tags.c.post_id == Post.id)
            .where(
                and_(
                    Post.status == PostStatus.PUBLISHED,
                    Post.published_at >= cutoff_date
                )
            )
            .group_by(Tag.id, Tag.name, Tag.color)
            .order_by(desc(func.count(Post.id)))
            .limit(limit)
        )
        return result.all()
    
    async def get_user_stats(self, db: AsyncSession, user_id: int):
        """Lấy comprehensive stats của user"""
        # Posts stats
        posts_result = await db.execute(
            select(
                func.count(Post.id).label("total_posts"),
                func.sum(Post.view_count).label("total_views"),
                func.sum(Post.like_count).label("total_likes"),
                func.sum(Post.comment_count).label("total_comments")
            )
            .where(
                and_(
                    Post.author_id == user_id,
                    Post.status == PostStatus.PUBLISHED
                )
            )
        )
        posts_stats = posts_result.first()
        
        # Follow stats
        followers_count = await db.scalar(
            select(func.count(UserFollow.id))
            .where(UserFollow.following_id == user_id)
        )
        following_count = await db.scalar(
            select(func.count(UserFollow.id))
            .where(UserFollow.follower_id == user_id)
        )
        
        return {
            "posts": {
                "total": posts_stats.total_posts or 0,
                "total_views": posts_stats.total_views or 0,
                "total_likes": posts_stats.total_likes or 0,
                "total_comments": posts_stats.total_comments or 0
            },
            "social": {
                "followers": followers_count or 0,
                "following": following_count or 0
            }
        }
    
    async def search_posts_advanced(
        self, 
        db: AsyncSession,
        query: str,
        category_id: Optional[int] = None,
        tag_ids: Optional[List[int]] = None,
        author_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 20
    ):
        """Advanced search với multiple filters"""
        stmt = select(Post).options(
            joinedload(Post.author),
            selectinload(Post.tags),
            joinedload(Post.category)
        )
        
        conditions = [Post.status == PostStatus.PUBLISHED]
        
        # Text search
        if query:
            conditions.append(
                or_(
                    Post.title.ilike(f"%{query}%"),
                    Post.content.ilike(f"%{query}%"),
                    Post.excerpt.ilike(f"%{query}%")
                )
            )
        
        # Category filter
        if category_id:
            conditions.append(Post.category_id == category_id)
        
        # Author filter
        if author_id:
            conditions.append(Post.author_id == author_id)
        
        # Date range
        if date_from:
            conditions.append(Post.published_at >= date_from)
        if date_to:
            conditions.append(Post.published_at <= date_to)
        
        stmt = stmt.where(and_(*conditions))
        
        # Tag filter (requires join)
        if tag_ids:
            stmt = stmt.join(post_tags).where(post_tags.c.tag_id.in_(tag_ids))
        
        result = await db.execute(
            stmt.order_by(desc(Post.published_at)).limit(limit)
        )
        return result.scalars().unique().all()
```

---

## 🎯 TỔNG KẾT: PATTERNS ĐÃ ÁP DỤNG

### ✅ **Relationship Patterns:**

1. **One-to-One**: User ↔ UserProfile
2. **One-to-Many**: User → Posts, Post → Comments, Category → Posts
3. **Many-to-Many Simple**: Post ↔ Tag
4. **Many-to-Many với Association Object**: User ↔ Role (UserRole)
5. **Self-Referencing**: Category → Children, Comment → Replies
6. **Polymorphic/Generic**: Like system cho Post/Comment
7. **Following Pattern**: User ↔ User với metadata

### ✅ **Design Principles:**

1. **Soft Delete**: Tất cả models support soft delete
2. **Audit Trail**: Track created_by, updated_by
3. **Timestamps**: Created_at, updated_at automatic
4. **UUID Support**: Public references không expose internal IDs
5. **Indexing Strategy**: Proper indexes cho performance
6. **Constraints**: Unique, Check, Foreign Key constraints
7. **JSON Fields**: Flexible metadata và settings
8. **Stats Caching**: Denormalized counts cho performance

### ✅ **Performance Optimizations:**

1. **Eager Loading**: selectinload, joinedload cho relationships
2. **Composite Indexes**: Multi-column indexes cho complex queries
3. **Path Enumeration**: Comment threading với path field
4. **Denormalized Counts**: Cache counts trong models
5. **Query Optimization**: Efficient joins và subqueries

Đây là một blog system database design hoàn chỉnh với tất cả relationship patterns! 🚀