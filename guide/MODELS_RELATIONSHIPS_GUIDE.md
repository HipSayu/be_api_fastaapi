# 🗄️ HƯỚNG DẪN CHI TIẾT: MODELS VÀ RELATIONSHIPS

## 📋 TỔNG QUAN VỀ RELATIONSHIPS

### 🔗 Các loại relationships:
1. **One-to-Many (1:N)** - Một bản ghi có nhiều bản ghi liên quan
2. **Many-to-One (N:1)** - Nhiều bản ghi thuộc về một bản ghi  
3. **One-to-One (1:1)** - Một bản ghi tương ứng với một bản ghi khác
4. **Many-to-Many (N:N)** - Nhiều bản ghi liên quan với nhiều bản ghi khác

---

## 🏗️ CẤU HÌNH MODEL CƠ BẢN

### 📝 Template Model Foundation

```python
# src/app/models/base_model.py
from datetime import datetime, UTC
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    """Base class cho tất cả models"""
    pass

class TimestampMixin:
    """Mixin để thêm timestamps cho models"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.now(UTC),
        nullable=False,
        index=True  # Index cho sorting
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
        nullable=False,
        index=True
    )

class SoftDeleteMixin:
    """Mixin để thêm soft delete"""
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """Base model với tất cả common fields"""
    __abstract__ = True  # Không tạo table cho class này
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        index=True,
        autoincrement=True
    )
```

### 🎯 Quy tắc đặt tên

```python
# ✅ ĐÚNG
class User(Base):
    __tablename__ = "users"  # Số nhiều, snake_case
    
    # Fields: snake_case
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email_address: Mapped[str] = mapped_column(String(255))
    
    # Foreign Keys: table_id format
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    
    # Relationships: PascalCase cho class names
    company: Mapped["Company"] = relationship("Company", back_populates="employees")

# ❌ SAI
class user(Base):  # Class nên PascalCase
    __tablename__ = "User"  # Table nên snake_case số nhiều
    
    firstName: str  # Field nên snake_case
    CompanyID: int  # Nên company_id
```

---

## 🔗 ONE-TO-MANY RELATIONSHIPS (1:N)

### 📚 Ví dụ: User có nhiều Posts

```python
# src/app/models/user.py
from typing import List
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    # Basic Fields
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 🔗 ONE-TO-MANY: User có nhiều Posts
    posts: Mapped[List["Post"]] = relationship(
        "Post",                    # Target model
        back_populates="author",   # Field ở phía bên kia
        cascade="all, delete-orphan",  # Xóa user → xóa tất cả posts
        lazy="select"              # Loading strategy
    )
    
    # 🔗 ONE-TO-MANY: User có nhiều Comments  
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan"
    )
```

```python
# src/app/models/post.py
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import BaseModel

class Post(BaseModel):
    __tablename__ = "posts"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # 🔑 FOREIGN KEY: Many posts → One user
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),  # Xóa user → xóa posts
        nullable=False,
        index=True  # Index cho joins
    )
    
    # 🔗 MANY-TO-ONE: Post thuộc về một User
    author: Mapped["User"] = relationship(
        "User", 
        back_populates="posts"
    )
    
    # 🔗 ONE-TO-MANY: Post có nhiều Comments
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan"
    )
```

### 💡 Giải thích Chi tiết:

1. **Foreign Key Position**: Luôn ở phía "Many" (Post có author_id)
2. **Cascade Options**:
   - `"all, delete-orphan"`: Xóa parent → xóa tất cả children
   - `"save-update"`: Chỉ sync khi save/update
   - `"delete"`: Xóa parent → xóa children
3. **ondelete Options**:
   - `"CASCADE"`: Database level cascade delete
   - `"SET NULL"`: Set FK = NULL khi parent bị xóa
   - `"RESTRICT"`: Không cho xóa parent nếu có children

---

## 🔗 MANY-TO-MANY RELATIONSHIPS (N:N)

### 📚 Ví dụ: Users và Roles (N:N)

```python
# src/app/models/associations.py
"""
Association tables cho many-to-many relationships
Đặt trong file riêng để tránh circular imports
"""
from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime, String
from datetime import datetime, UTC
from .base_model import Base

# 🔗 ASSOCIATION TABLE: users ↔ roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('id', Integer, primary_key=True),  # Optional: primary key
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
    
    # 📅 Thêm timestamps cho audit
    Column('assigned_at', DateTime(timezone=True), default=datetime.now(UTC)),
    Column('assigned_by', Integer, ForeignKey('users.id'), nullable=True),
    
    # 🔒 Unique constraint
    UniqueConstraint('user_id', 'role_id', name='unique_user_role')
)

# 🔗 ASSOCIATION TABLE: posts ↔ tags  
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE')),
    Column('created_at', DateTime(timezone=True), default=datetime.now(UTC)),
    
    # Primary key composite
    PrimaryKeyConstraint('post_id', 'tag_id')
)
```

```python
# src/app/models/user.py (updated)
from sqlalchemy.orm import relationship
from .associations import user_roles

class User(BaseModel):
    __tablename__ = "users"
    
    # ... existing fields ...
    
    # 🔗 MANY-TO-MANY: User có nhiều Roles
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,        # Association table
        back_populates="users",      # Field ở Role model
        lazy="selectin"              # Eager loading strategy
    )
```

```python
# src/app/models/role.py
from typing import List, Optional
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import BaseModel
from .associations import user_roles

class Role(BaseModel):
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 🔒 Permissions as JSON
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 🔗 MANY-TO-MANY: Role có nhiều Users
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
```

### 🎯 Association Object Pattern (Advanced N:N)

```python
# src/app/models/user_role_association.py
"""
Association Object - khi cần thêm fields vào relationship
"""
from datetime import datetime, UTC
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import BaseModel

class UserRole(BaseModel):
    """
    Association Object cho User-Role relationship
    Sử dụng khi cần thêm metadata vào relationship
    """
    __tablename__ = "user_roles"
    
    # 🔑 Foreign Keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    
    # 📅 Additional Fields
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    assigned_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 🗒️ Notes về assignment
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 🔗 Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", foreign_keys=[role_id], back_populates="user_roles")
    assigned_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by])
    
    # 🔒 Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='unique_active_user_role'),
    )

# Update User model
class User(BaseModel):
    # ... existing fields ...
    
    # 🔗 Relationship với Association Object
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", 
        foreign_keys="UserRole.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 🔗 Convenience property để lấy roles trực tiếp
    @property
    def active_roles(self) -> List["Role"]:
        """Lấy roles đang active"""
        return [ur.role for ur in self.user_roles if ur.is_active and 
                (ur.expires_at is None or ur.expires_at > datetime.now(UTC))]
```

---

## 🔗 ONE-TO-ONE RELATIONSHIPS (1:1)

### 📚 Ví dụ: User và UserProfile

```python
# src/app/models/user_profile.py
from typing import Optional
from sqlalchemy import String, Text, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import BaseModel

class UserProfile(BaseModel):
    __tablename__ = "user_profiles"
    
    # 🔑 ONE-TO-ONE: Một profile thuộc về một user
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,  # Đảm bảo 1:1 relationship
        nullable=False
    )
    
    # Profile fields
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Social links
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 🔗 Relationship
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="profile",
        uselist=False  # Đảm bảo return single object, không phải list
    )

# Update User model
class User(BaseModel):
    # ... existing fields ...
    
    # 🔗 ONE-TO-ONE: User có một profile
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,  # Single object
        cascade="all, delete-orphan"  # Xóa user → xóa profile
    )
```

---

## 🔗 SELF-REFERENCING RELATIONSHIPS

### 📚 Ví dụ: Category Tree (Parent-Children)

```python
# src/app/models/category.py
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import BaseModel

class Category(BaseModel):
    __tablename__ = "categories"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 🔄 SELF-REFERENCING: Category có parent category
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,  # Root categories không có parent
        index=True
    )
    
    # 🔢 Tree helper fields
    level: Mapped[int] = mapped_column(Integer, default=0)  # Độ sâu trong tree
    order: Mapped[int] = mapped_column(Integer, default=0)  # Thứ tự hiển thị
    
    # 🔗 Self-referencing relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",  # Chỉ định side nào là "remote"
        back_populates="children"
    )
    
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"  # Xóa parent → xóa children
    )
    
    # 🔗 Category có nhiều Posts
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="category"
    )
    
    # 🔧 Helper methods
    @property
    def is_root(self) -> bool:
        """Kiểm tra có phải root category không"""
        return self.parent_id is None
    
    @property  
    def is_leaf(self) -> bool:
        """Kiểm tra có phải leaf category không"""
        return len(self.children) == 0
    
    def get_ancestors(self) -> List["Category"]:
        """Lấy tất cả ancestors của category"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants(self) -> List["Category"]:
        """Lấy tất cả descendants của category"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
```

### 📚 Ví dụ: Comment Threading

```python
# src/app/models/comment.py
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_model import BaseModel

class Comment(BaseModel):
    __tablename__ = "comments"
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 🔗 Comment thuộc về Post
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    
    # 🔗 Comment được viết bởi User  
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # 🔄 REPLY SYSTEM: Comment có thể reply comment khác
    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # 🔢 Threading helpers
    depth: Mapped[int] = mapped_column(Integer, default=0)  # Độ sâu reply
    thread_order: Mapped[int] = mapped_column(Integer, default=0)  # Thứ tự trong thread
    
    # 🔗 Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")
    
    # 🔄 Self-referencing cho threading
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
    
    # 🔧 Helper methods
    @property
    def is_top_level(self) -> bool:
        """Kiểm tra có phải comment gốc không"""
        return self.parent_comment_id is None
    
    def get_thread_root(self) -> "Comment":
        """Lấy comment gốc của thread"""
        current = self
        while current.parent_comment:
            current = current.parent_comment
        return current
    
    def get_all_replies(self) -> List["Comment"]:
        """Lấy tất cả replies (recursive)"""
        all_replies = []
        for reply in self.replies:
            all_replies.append(reply)
            all_replies.extend(reply.get_all_replies())
        return all_replies
```

---

## 🎯 LOADING STRATEGIES

### 📊 Lazy Loading Options

```python
class User(BaseModel):
    # 🔄 LAZY LOADING STRATEGIES
    
    # 1. LAZY = "select" (default)
    posts: Mapped[List["Post"]] = relationship(
        "Post", 
        back_populates="author",
        lazy="select"  # Load khi access, tạo separate query
    )
    
    # 2. LAZY = "selectin"  
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        lazy="selectin"  # Load với IN clause, efficient cho collections
    )
    
    # 3. LAZY = "joined"
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        lazy="joined"  # Load với LEFT JOIN, tốt cho 1:1 relationships
    )
    
    # 4. LAZY = "subquery"
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        lazy="subquery"  # Load với subquery, tốt cho small collections
    )
    
    # 5. LAZY = "dynamic"
    notifications: Mapped["Query"] = relationship(
        "Notification",
        lazy="dynamic"  # Trả về Query object, tốt cho large collections
    )
```

### 🚀 Eager Loading trong Queries

```python
# src/app/crud/crud_user.py
from sqlalchemy.orm import selectinload, joinedload, subqueryload

class UserCRUD:
    
    async def get_user_with_posts(self, db: AsyncSession, user_id: int):
        """Load user với posts sử dụng selectinload"""
        result = await db.execute(
            select(User)
            .options(selectinload(User.posts))  # Eager load posts
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_with_profile_and_roles(self, db: AsyncSession, user_id: int):
        """Load user với profile và roles"""
        result = await db.execute(
            select(User)
            .options(
                joinedload(User.profile),      # 1:1 dùng joinedload
                selectinload(User.roles)       # N:N dùng selectinload
            )
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_users_with_nested_data(self, db: AsyncSession):
        """Load users với nested relationships"""
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.posts).selectinload(Post.comments),  # Nested loading
                selectinload(User.roles),
                joinedload(User.profile)
            )
        )
        return result.scalars().all()
```

---

## 🔧 ADVANCED PATTERNS

### 🎯 Polymorphic Relationships

```python
# src/app/models/polymorphic.py
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

class Notification(BaseModel):
    """Base notification class"""
    __tablename__ = "notifications"
    
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 🔄 Polymorphic fields
    notification_type: Mapped[str] = mapped_column(String(50))
    
    # 🔗 Polymorphic relationship
    target_type: Mapped[str] = mapped_column(String(50))  # "post", "comment", "user"
    target_id: Mapped[int] = mapped_column(Integer)
    
    __mapper_args__ = {
        "polymorphic_on": notification_type,
        "polymorphic_identity": "base"
    }

class PostNotification(Notification):
    """Notification cho Post"""
    __mapper_args__ = {"polymorphic_identity": "post"}
    
    @declared_attr
    def post_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("posts.id"), nullable=True)
    
    @declared_attr  
    def post(cls) -> Mapped["Post"]:
        return relationship("Post")

class CommentNotification(Notification):
    """Notification cho Comment"""
    __mapper_args__ = {"polymorphic_identity": "comment"}
    
    @declared_attr
    def comment_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("comments.id"), nullable=True)
    
    @declared_attr
    def comment(cls) -> Mapped["Comment"]:
        return relationship("Comment")
```

### 🎯 Generic Foreign Keys

```python
# src/app/models/generic.py
from typing import Union

class Like(BaseModel):
    """Generic Like system - có thể like Posts, Comments, etc."""
    __tablename__ = "likes"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # 🔄 Generic Foreign Key pattern
    content_type: Mapped[str] = mapped_column(String(50))  # "post", "comment", etc.
    object_id: Mapped[int] = mapped_column(Integer)
    
    # 🔗 Relationships
    user: Mapped["User"] = relationship("User")
    
    # 🔒 Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'content_type', 'object_id', name='unique_like'),
        Index('idx_content_object', 'content_type', 'object_id'),  # Index cho queries
    )
    
    # 🔧 Helper methods
    def get_liked_object(self, db: AsyncSession):
        """Lấy object được like"""
        if self.content_type == "post":
            from .post import Post
            return db.get(Post, self.object_id)
        elif self.content_type == "comment":
            from .comment import Comment
            return db.get(Comment, self.object_id)
        return None

# Add likes count to models
class Post(BaseModel):
    # ... existing fields ...
    
    @hybrid_property
    def likes_count(self) -> int:
        """Đếm số likes của post"""
        return len([like for like in self.likes if like.content_type == "post"])
    
    @likes_count.expression
    def likes_count(cls):
        """SQL expression cho likes count"""
        return (
            select(func.count(Like.id))
            .where(Like.content_type == "post")
            .where(Like.object_id == cls.id)
            .scalar_subquery()
        )
```

---

## 🔍 QUERY PATTERNS

### 📊 Complex Joins

```python
# src/app/crud/advanced_queries.py

class AdvancedQueries:
    
    async def get_users_with_post_stats(self, db: AsyncSession):
        """Lấy users với thống kê posts"""
        result = await db.execute(
            select(
                User.id,
                User.username,
                User.email,
                func.count(Post.id).label("post_count"),
                func.avg(Post.view_count).label("avg_views"),
                func.max(Post.created_at).label("last_post_date")
            )
            .outerjoin(Post, User.id == Post.author_id)
            .group_by(User.id, User.username, User.email)
            .order_by(func.count(Post.id).desc())
        )
        return result.all()
    
    async def get_popular_posts_with_authors(self, db: AsyncSession, limit: int = 10):
        """Lấy posts phổ biến với thông tin authors"""
        result = await db.execute(
            select(Post, User, func.count(Like.id).label("likes_count"))
            .join(User, Post.author_id == User.id)
            .outerjoin(Like, and_(
                Like.content_type == "post",
                Like.object_id == Post.id
            ))
            .group_by(Post.id, User.id)
            .order_by(func.count(Like.id).desc())
            .limit(limit)
        )
        return result.all()
    
    async def get_nested_comments_tree(self, db: AsyncSession, post_id: int):
        """Lấy comment tree cho post"""
        # Common Table Expression (CTE) cho recursive query
        comment_tree = (
            select(Comment)
            .where(Comment.post_id == post_id)
            .where(Comment.parent_comment_id.is_(None))
            .cte(name="comment_tree", recursive=True)
        )
        
        comment_tree = comment_tree.union_all(
            select(Comment)
            .join(comment_tree, Comment.parent_comment_id == comment_tree.c.id)
        )
        
        result = await db.execute(
            select(Comment)
            .from_statement(
                select(comment_tree).order_by(comment_tree.c.created_at)
            )
            .options(selectinload(Comment.author))
        )
        return result.scalars().all()
```

### 🔄 Bulk Operations

```python
# src/app/crud/bulk_operations.py

class BulkOperations:
    
    async def bulk_assign_roles(self, db: AsyncSession, user_ids: List[int], role_id: int):
        """Bulk assign role cho multiple users"""
        # Tạo UserRole records
        user_roles_data = [
            {"user_id": user_id, "role_id": role_id, "assigned_at": datetime.now(UTC)}
            for user_id in user_ids
        ]
        
        await db.execute(
            insert(UserRole).values(user_roles_data)
        )
        await db.commit()
    
    async def bulk_update_post_status(self, db: AsyncSession, post_ids: List[int], status: str):
        """Bulk update post status"""
        await db.execute(
            update(Post)
            .where(Post.id.in_(post_ids))
            .values(status=status, updated_at=datetime.now(UTC))
        )
        await db.commit()
    
    async def bulk_delete_old_notifications(self, db: AsyncSession, days_old: int = 30):
        """Bulk delete old notifications"""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)
        
        result = await db.execute(
            delete(Notification)
            .where(Notification.created_at < cutoff_date)
            .where(Notification.is_read == True)
        )
        await db.commit()
        return result.rowcount
```

---

## 🎯 PERFORMANCE TIPS

### 1. **Indexing Strategy**
```python
class Post(BaseModel):
    # Single column indexes
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    
    # Composite indexes
    __table_args__ = (
        Index('idx_author_status', 'author_id', 'status'),
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_search', 'title', 'content'),  # For text search
    )
```

### 2. **Query Optimization**
```python
# ✅ GOOD: Eager loading
users = await db.execute(
    select(User)
    .options(selectinload(User.posts), selectinload(User.roles))
    .limit(10)
)

# ❌ BAD: N+1 queries
users = await db.execute(select(User).limit(10))
for user in users:
    print(user.posts)  # Tạo separate query cho mỗi user
```

### 3. **Pagination Best Practices**
```python
# ✅ GOOD: Cursor-based pagination
async def get_posts_cursor(self, db: AsyncSession, cursor: Optional[int] = None, limit: int = 20):
    query = select(Post).order_by(Post.id.desc())
    
    if cursor:
        query = query.where(Post.id < cursor)
    
    result = await db.execute(query.limit(limit))
    return result.scalars().all()

# ❌ BAD: Offset pagination với large offsets
async def get_posts_offset(self, db: AsyncSession, page: int = 1, limit: int = 20):
    offset = (page - 1) * limit
    result = await db.execute(
        select(Post).offset(offset).limit(limit)  # Slow với large offsets
    )
    return result.scalars().all()
```

Đây là hướng dẫn comprehensive về models và relationships trong SQLAlchemy! 🚀