# 🔍 SQLALCHEMY 2.0 - GIẢI THÍCH CHI TIẾT

## 📚 **Mục lục:**
1. [Mapped và Type Annotations](#mapped-và-type-annotations)
2. [ForeignKey và Relationships](#foreignkey-và-relationships)  
3. [Optional và Type Hints](#optional-và-type-hints)
4. [Select Queries và CRUD](#select-queries-và-crud)
5. [Phân trang (Pagination)](#phân-trang-pagination)
6. [Query Optimization](#query-optimization)
7. [Thực hành với Examples](#thực-hành-với-examples)

---

## 🏗️ **MAPPED VÀ TYPE ANNOTATIONS**

### 📖 **Mapped[T] là gì?**

```python
from sqlalchemy.orm import Mapped, mapped_column

class Message(Base):
    # ✅ SQLAlchemy 2.0 style với type hints
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(255))
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    
    # ❌ SQLAlchemy 1.x style (deprecated)
    # id = Column(Integer, primary_key=True)
    # content = Column(String(255))
```

### 🔍 **Mapped[T] giải thích:**

```python
# 🎯 Mapped[T] = Type annotation + Runtime information

# 1️⃣ Mapped[int] - Required integer field
id: Mapped[int] = mapped_column(primary_key=True)

# 2️⃣ Mapped[Optional[str]] - Nullable string field  
description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

# 3️⃣ Mapped[datetime] - Required datetime với default
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), 
    default_factory=lambda: datetime.now(UTC)
)

# 4️⃣ Mapped[dict] - JSON field
metadata: Mapped[dict] = mapped_column(JSONB, default_factory=dict)

# 5️⃣ Mapped[bool] - Boolean với default
is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

### 🔧 **mapped_column() Parameters:**

```python
class User(Base):
    __tablename__ = "users"
    
    # 🔑 Primary Key
    id: Mapped[int] = mapped_column(
        autoincrement=True,      # Auto increment
        nullable=False,          # NOT NULL
        unique=True,            # UNIQUE constraint
        primary_key=True,       # PRIMARY KEY
        init=False,             # Không include trong __init__
        index=True              # CREATE INDEX
    )
    
    # 🎯 String với constraints
    username: Mapped[str] = mapped_column(
        String(50),             # VARCHAR(50)
        nullable=False,         # NOT NULL
        unique=True,           # UNIQUE
        index=True             # INDEX for fast lookups
    )
    
    # 📧 Email với validation
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )
    
    # 🔒 Foreign Key
    profile_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
```

---

## 🔗 **FOREIGNKEY VÀ RELATIONSHIPS**

### 🔑 **ForeignKey Definition:**

```python
# 🏗️ Cách định nghĩa Foreign Key

class Message(Base):
    __tablename__ = "messages"
    
    # 1️⃣ Basic Foreign Key
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),    # Reference to users.id
        nullable=False,
        index=True
    )
    
    # 2️⃣ Foreign Key với CASCADE
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 3️⃣ Optional Foreign Key (nullable)
    reply_to: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # 4️⃣ Self-referencing Foreign Key
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messages.id"),
        nullable=True
    )
```

### 🔗 **Relationship Types:**

#### **1️⃣ One-to-Many (1:N)**

```python
# 👤 User Model (One side)
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    
    # 🔗 One user có nhiều messages
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="sender",      # Tên relationship ở Message
        foreign_keys="Message.sender_id",  # Specify foreign key
        cascade="all, delete-orphan"  # Delete messages khi delete user
    )

# 💬 Message Model (Many side)  
class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    
    # 🔑 Foreign Key
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    
    # 🔗 Many messages thuộc về một user
    sender: Mapped["User"] = relationship(
        "User",
        back_populates="sent_messages"
    )
```

#### **2️⃣ One-to-One (1:1)**

```python
# 👤 User Model
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 🔗 One-to-One relationship
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,              # ⚠️ Quan trọng: uselist=False
        cascade="all, delete-orphan"
    )

# 📄 UserProfile Model
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 🔑 Foreign Key (unique=True for 1:1)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,               # ⚠️ Đảm bảo 1:1
        nullable=False
    )
    
    # 🔗 Back reference
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile"
    )
```

#### **3️⃣ Many-to-Many (N:N)**

```python
# 🔗 Association Table
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), default=datetime.now(UTC))
)

# 👤 User Model
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # 🔗 Many-to-Many relationship
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,       # Association table
        back_populates="users"
    )

# 🛡️ Role Model
class Role(Base):
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    
    # 🔗 Back reference
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
```

#### **4️⃣ Self-Referencing (Cây/Tree)**

```python
class Comment(Base):
    __tablename__ = "comments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    
    # 🔄 Self-referencing Foreign Key
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # 🔗 Self-referencing relationships
    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment",
        remote_side=[id],           # ⚠️ Quan trọng: chỉ định remote side
        back_populates="children"
    )
    
    children: Mapped[List["Comment"]] = relationship(
        "Comment", 
        back_populates="parent",
        cascade="all, delete-orphan"
    )
```

---

## ❓ **OPTIONAL VÀ TYPE HINTS**

### 🎯 **Optional[T] Usage:**

```python
from typing import Optional, List

class User(Base):
    # 🔍 Required fields (NOT NULL)
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # ❓ Optional fields (NULL allowed)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # 🔗 Optional relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False
    )
    
    # 📝 Required relationships (List never None, but can be empty)
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="author"
    )
```

### 🔧 **Type Mapping:**

```python
# 🗺️ Python Type → SQLAlchemy Type Mapping

# Basics
id: Mapped[int] = mapped_column()                    # INTEGER
name: Mapped[str] = mapped_column(String(100))      # VARCHAR(100)
is_active: Mapped[bool] = mapped_column()           # BOOLEAN
price: Mapped[float] = mapped_column()              # FLOAT

# Dates & Times
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
birth_date: Mapped[date] = mapped_column(Date)
meeting_time: Mapped[time] = mapped_column(Time)

# JSON & Complex Types
metadata: Mapped[dict] = mapped_column(JSON)        # JSON column
settings: Mapped[dict] = mapped_column(JSONB)       # PostgreSQL JSONB
tags: Mapped[List[str]] = mapped_column(ARRAY(String))  # PostgreSQL ARRAY

# Optional versions
description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
```

---

## 🔍 **SELECT QUERIES VÀ CRUD**

### 📖 **Basic Select Patterns:**

```python
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

async def basic_queries(db: AsyncSession):
    
    # 1️⃣ Simple select by ID
    result = await db.execute(
        select(User).where(User.id == 1)
    )
    user = result.scalar_one_or_none()  # Trả về User hoặc None
    
    # 2️⃣ Select với multiple conditions
    result = await db.execute(
        select(User).where(
            and_(
                User.is_active == True,
                User.email.like("%@gmail.com"),
                User.created_at >= datetime(2024, 1, 1)
            )
        )
    )
    users = result.scalars().all()  # Trả về List[User]
    
    # 3️⃣ Select với OR conditions  
    result = await db.execute(
        select(User).where(
            or_(
                User.username == "admin",
                User.email == "admin@example.com"
            )
        )
    )
    admin_user = result.scalar_one_or_none()
    
    # 4️⃣ Select với ordering
    result = await db.execute(
        select(User)
        .where(User.is_active == True)
        .order_by(desc(User.created_at))  # Newest first
        .limit(10)
    )
    recent_users = result.scalars().all()
    
    # 5️⃣ Count query
    result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    user_count = result.scalar()  # Trả về int
```

### 🔄 **CRUD Operations:**

```python
class UserCRUD:
    
    # 🆕 CREATE
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        # Method 1: Direct instantiation
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=hash_password(obj_in.password)
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)  # Reload để có ID và default values
        return db_obj
        
        # Method 2: Using model_dump
        obj_data = obj_in.model_dump()
        db_obj = User(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    # 📖 READ - Single record
    async def get(self, db: AsyncSession, id: int) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.id == id)
        )
        return result.scalar_one_or_none()
    
    # 📖 READ - Multiple records với conditions
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[User]:
        query = select(User)
        
        # Dynamic filtering
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(User.id)
        )
        return result.scalars().all()
    
    # 🔄 UPDATE
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: User, 
        obj_in: UserUpdate
    ) -> User:
        # Method 1: Manual field update
        if obj_in.username is not None:
            db_obj.username = obj_in.username
        if obj_in.email is not None:
            db_obj.email = obj_in.email
        
        # Method 2: Using model_dump
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    # ❌ DELETE - Hard delete
    async def remove(self, db: AsyncSession, *, id: int) -> User:
        result = await db.execute(
            select(User).where(User.id == id)
        )
        obj = result.scalar_one()
        await db.delete(obj)
        await db.commit()
        return obj
    
    # 🗑️ SOFT DELETE
    async def soft_delete(self, db: AsyncSession, *, id: int) -> bool:
        result = await db.execute(
            update(User)
            .where(User.id == id)
            .values(
                deleted=True,
                deleted_at=datetime.now(UTC)
            )
        )
        await db.commit()
        return result.rowcount > 0
```

### 🔗 **Eager Loading Strategies:**

```python
async def loading_strategies(db: AsyncSession):
    
    # 1️⃣ selectinload - Separate SELECT query
    result = await db.execute(
        select(User)
        .options(selectinload(User.posts))  # SELECT posts WHERE user_id IN (...)
        .where(User.is_active == True)
    )
    users = result.scalars().unique().all()
    
    # 2️⃣ joinedload - JOIN in single query
    result = await db.execute(
        select(User)
        .options(joinedload(User.profile))  # LEFT JOIN user_profiles
        .where(User.id == 1)
    )
    user = result.scalar_one_or_none()
    
    # 3️⃣ Nested loading
    result = await db.execute(
        select(Post)
        .options(
            joinedload(Post.author).joinedload(User.profile),  # Load author + profile
            selectinload(Post.comments).selectinload(Comment.author)  # Load comments + authors
        )
        .where(Post.published == True)
    )
    posts = result.scalars().unique().all()
    
    # 4️⃣ Conditional loading
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.posts.and_(Post.published == True))  # Only published posts
        )
        .where(User.id == 1)
    )
    user = result.scalar_one_or_none()
```

---

## 📄 **PHÂN TRANG (PAGINATION)**

### 🔢 **Offset-Based Pagination:**

```python
class PaginationParams:
    def __init__(self, page: int = 1, size: int = 20):
        self.page = max(1, page)
        self.size = min(100, max(1, size))  # Limit max size
        self.offset = (self.page - 1) * self.size

async def get_users_paginated(
    db: AsyncSession,
    pagination: PaginationParams,
    search: Optional[str] = None,
    is_active: Optional[bool] = None
) -> dict:
    
    # 🔍 Build base query
    query = select(User)
    count_query = select(func.count(User.id))
    
    # 🎯 Apply filters
    conditions = []
    if search:
        conditions.append(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # 📊 Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 📄 Get paginated data
    result = await db.execute(
        query
        .options(selectinload(User.profile))
        .order_by(desc(User.created_at))
        .offset(pagination.offset)
        .limit(pagination.size)
    )
    users = result.scalars().all()
    
    # 📋 Return pagination info
    return {
        "items": users,
        "total": total,
        "page": pagination.page,
        "size": pagination.size,
        "pages": math.ceil(total / pagination.size) if total > 0 else 0
    }
```

### 🚀 **Cursor-Based Pagination (Efficient for large datasets):**

```python
async def get_messages_cursor(
    db: AsyncSession,
    conversation_id: int,
    cursor: Optional[int] = None,  # message_id
    limit: int = 50,
    direction: str = "before"  # "before" or "after"
) -> dict:
    
    query = select(Message).where(
        Message.conversation_id == conversation_id,
        Message.deleted == False
    )
    
    # 🎯 Apply cursor
    if cursor:
        if direction == "before":
            query = query.where(Message.id < cursor)
        else:  # after
            query = query.where(Message.id > cursor)
    
    # 📄 Get messages
    result = await db.execute(
        query
        .options(selectinload(Message.sender))
        .order_by(Message.id.desc() if direction == "before" else Message.id.asc())
        .limit(limit + 1)  # +1 để check có more data không
    )
    messages = result.scalars().all()
    
    # 🔍 Check if there are more items
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:-1]  # Remove extra item
    
    # 🔄 Reverse if getting "before" messages
    if direction == "before":
        messages = list(reversed(messages))
    
    # 🧭 Set next cursor
    next_cursor = None
    prev_cursor = None
    
    if messages:
        if direction == "before":
            next_cursor = messages[-1].id if has_more else None
            prev_cursor = messages[0].id
        else:
            next_cursor = messages[-1].id
            prev_cursor = messages[0].id if has_more else None
    
    return {
        "items": messages,
        "has_more": has_more,
        "next_cursor": next_cursor,
        "prev_cursor": prev_cursor
    }
```

---

## ⚡ **QUERY OPTIMIZATION**

### 🎯 **N+1 Problem Solutions:**

```python
# ❌ N+1 Problem - BAD
async def get_posts_with_authors_bad(db: AsyncSession):
    # 1 query để lấy posts
    result = await db.execute(select(Post).limit(10))
    posts = result.scalars().all()
    
    # N queries để lấy authors (1 query per post)
    for post in posts:
        await post.awaitable_attrs.author  # Lazy loading = N queries
    
    return posts

# ✅ Solution 1: selectinload
async def get_posts_with_authors_good1(db: AsyncSession):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author))  # 1 additional query for all authors
        .limit(10)
    )
    return result.scalars().all()

# ✅ Solution 2: joinedload
async def get_posts_with_authors_good2(db: AsyncSession):
    result = await db.execute(
        select(Post)
        .options(joinedload(Post.author))  # 1 query with JOIN
        .limit(10)
    )
    return result.scalars().unique().all()  # unique() important with joins
```

### 📊 **Complex Queries:**

```python
async def advanced_queries(db: AsyncSession):
    
    # 1️⃣ Aggregation với GROUP BY
    result = await db.execute(
        select(
            User.id,
            User.username,
            func.count(Post.id).label("post_count"),
            func.avg(Post.view_count).label("avg_views")
        )
        .join(Post, Post.author_id == User.id)
        .where(Post.published == True)
        .group_by(User.id, User.username)
        .having(func.count(Post.id) > 5)  # Users with more than 5 posts
        .order_by(desc(func.count(Post.id)))
    )
    user_stats = result.all()
    
    # 2️⃣ Subquery
    subquery = select(func.avg(Post.view_count)).scalar_subquery()
    
    result = await db.execute(
        select(Post)
        .where(Post.view_count > subquery)  # Posts above average views
        .options(selectinload(Post.author))
    )
    popular_posts = result.scalars().all()
    
    # 3️⃣ EXISTS query
    exists_query = select(Comment.id).where(
        and_(
            Comment.post_id == Post.id,
            Comment.deleted == False
        )
    ).exists()
    
    result = await db.execute(
        select(Post)
        .where(exists_query)  # Posts that have comments
        .options(selectinload(Post.author))
    )
    commented_posts = result.scalars().all()
    
    # 4️⃣ Window Functions (PostgreSQL)
    result = await db.execute(
        select(
            Post.id,
            Post.title,
            Post.view_count,
            func.row_number().over(
                partition_by=Post.category_id,
                order_by=desc(Post.view_count)
            ).label("rank_in_category")
        )
        .where(Post.published == True)
    )
    ranked_posts = result.all()
```

### 🚀 **Bulk Operations:**

```python
async def bulk_operations(db: AsyncSession):
    
    # 🔄 Bulk Insert
    users_data = [
        {"username": f"user{i}", "email": f"user{i}@example.com"}
        for i in range(1000)
    ]
    
    # Method 1: bulk_insert_mappings
    await db.execute(
        insert(User),
        users_data
    )
    await db.commit()
    
    # Method 2: Using objects
    users = [User(**data) for data in users_data]
    db.add_all(users)
    await db.commit()
    
    # 🔄 Bulk Update
    await db.execute(
        update(User)
        .where(User.last_login < datetime.now(UTC) - timedelta(days=30))
        .values(is_active=False)
    )
    await db.commit()
    
    # 🔄 Bulk Delete
    await db.execute(
        delete(Post)
        .where(
            and_(
                Post.published == False,
                Post.created_at < datetime.now(UTC) - timedelta(days=7)
            )
        )
    )
    await db.commit()
```

---

## 🧪 **THỰC HÀNH VỚI EXAMPLES**

### 📝 **Message CRUD với Relationships:**

```python
# 📁 models/message.py
class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    
    # 🔑 Foreign Keys
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    reply_to: Mapped[Optional[int]] = mapped_column(ForeignKey("messages.id"))
    
    # ⏰ Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # 🚦 Status
    deleted: Mapped[bool] = mapped_column(default=False)
    
    # 🔗 Relationships
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages")
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    
    # Self-referencing
    replied_message: Mapped[Optional["Message"]] = relationship(
        "Message", 
        remote_side=[id],
        back_populates="replies"
    )
    replies: Mapped[List["Message"]] = relationship(
        "Message", 
        back_populates="replied_message",
        cascade="all, delete-orphan"
    )

# 📁 crud/message.py
class MessageCRUD:
    
    async def create_message(
        self, 
        db: AsyncSession,
        *,
        sender_id: int,
        conversation_id: int,
        content: str,
        reply_to: Optional[int] = None
    ) -> Message:
        """Create new message with validation"""
        
        # ✅ Validate conversation exists and user has access
        conversation = await db.get(Conversation, conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")
        
        # ✅ Validate reply_to message exists
        if reply_to:
            reply_message = await db.get(Message, reply_to)
            if not reply_message or reply_message.conversation_id != conversation_id:
                raise ValueError("Invalid reply target")
        
        # 🆕 Create message
        message = Message(
            sender_id=sender_id,
            conversation_id=conversation_id,
            content=content,
            reply_to=reply_to
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        # 📊 Update conversation last_message
        conversation.last_message_id = message.id
        conversation.updated_at = message.created_at
        await db.commit()
        
        return message
    
    async def get_conversation_messages(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        user_id: int,
        cursor: Optional[int] = None,
        limit: int = 50
    ) -> dict:
        """Get messages with cursor pagination"""
        
        # ✅ Check user access to conversation
        access = await self.check_conversation_access(db, conversation_id, user_id)
        if not access:
            raise PermissionError("No access to conversation")
        
        # 🔍 Build query
        query = select(Message).where(
            and_(
                Message.conversation_id == conversation_id,
                Message.deleted == False
            )
        )
        
        # 🎯 Apply cursor
        if cursor:
            query = query.where(Message.id < cursor)
        
        # 📄 Execute with eager loading
        result = await db.execute(
            query
            .options(
                selectinload(Message.sender),
                selectinload(Message.replied_message).selectinload(Message.sender)
            )
            .order_by(desc(Message.created_at))
            .limit(limit + 1)
        )
        
        messages = result.scalars().all()
        
        # 🔍 Check pagination
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:-1]
        
        return {
            "messages": list(reversed(messages)),  # Chronological order
            "has_more": has_more,
            "next_cursor": messages[-1].id if messages and has_more else None
        }
    
    async def update_message(
        self,
        db: AsyncSession,
        *,
        message_id: int,
        user_id: int,
        content: str
    ) -> Message:
        """Update message content (owner only)"""
        
        # 🔍 Get message with permission check
        result = await db.execute(
            select(Message)
            .where(
                and_(
                    Message.id == message_id,
                    Message.sender_id == user_id,
                    Message.deleted == False
                )
            )
        )
        message = result.scalar_one_or_none()
        
        if not message:
            raise ValueError("Message not found or no permission")
        
        # 🔄 Update
        message.content = content
        message.edited_at = datetime.now(UTC)
        
        await db.commit()
        await db.refresh(message)
        
        return message
    
    async def search_messages(
        self,
        db: AsyncSession,
        *,
        conversation_id: int,
        user_id: int,
        search_term: str,
        limit: int = 20
    ) -> List[Message]:
        """Search messages in conversation"""
        
        # ✅ Check access
        access = await self.check_conversation_access(db, conversation_id, user_id)
        if not access:
            raise PermissionError("No access to conversation")
        
        # 🔍 Search query
        result = await db.execute(
            select(Message)
            .options(selectinload(Message.sender))
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.content.ilike(f"%{search_term}%"),
                    Message.deleted == False
                )
            )
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        
        return result.scalars().all()
```

### 📊 **Analytics Queries:**

```python
class MessageAnalytics:
    
    async def get_conversation_stats(self, db: AsyncSession, conversation_id: int) -> dict:
        """Get comprehensive conversation statistics"""
        
        # 📊 Message stats by user
        result = await db.execute(
            select(
                User.id,
                User.username,
                func.count(Message.id).label("message_count"),
                func.min(Message.created_at).label("first_message"),
                func.max(Message.created_at).label("last_message")
            )
            .join(Message, Message.sender_id == User.id)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.deleted == False
                )
            )
            .group_by(User.id, User.username)
            .order_by(desc(func.count(Message.id)))
        )
        user_stats = result.all()
        
        # 📅 Daily message count (last 30 days)
        result = await db.execute(
            select(
                func.date(Message.created_at).label("date"),
                func.count(Message.id).label("count")
            )
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.created_at >= datetime.now(UTC) - timedelta(days=30),
                    Message.deleted == False
                )
            )
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at))
        )
        daily_stats = result.all()
        
        # 🔄 Reply statistics
        result = await db.execute(
            select(
                func.count(Message.id).label("total_messages"),
                func.count(Message.reply_to).label("replies_count"),
                func.avg(
                    func.length(Message.content)
                ).label("avg_message_length")
            )
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.deleted == False
                )
            )
        )
        reply_stats = result.first()
        
        return {
            "user_stats": [
                {
                    "user_id": stat.id,
                    "username": stat.username,
                    "message_count": stat.message_count,
                    "first_message": stat.first_message,
                    "last_message": stat.last_message
                }
                for stat in user_stats
            ],
            "daily_activity": [
                {"date": stat.date, "count": stat.count}
                for stat in daily_stats
            ],
            "overview": {
                "total_messages": reply_stats.total_messages,
                "replies_count": reply_stats.replies_count,
                "avg_message_length": float(reply_stats.avg_message_length or 0)
            }
        }
```

---

## 🎯 **TÓM TẮT QUAN TRỌNG**

### ✅ **Key Concepts:**

1. **Mapped[T]**: Type annotation cho columns với runtime validation
2. **ForeignKey**: Định nghĩa references giữa tables  
3. **relationship()**: ORM-level relationships với lazy/eager loading
4. **Optional[T]**: Nullable columns và optional relationships
5. **select()**: Modern query API thay thế Query interface
6. **Pagination**: Offset-based cho small data, cursor-based cho large data
7. **Eager Loading**: selectinload vs joinedload để tránh N+1 problem

### 🚀 **Best Practices:**

1. **Always use type hints** với Mapped[T]
2. **Add indexes** cho foreign keys và search columns
3. **Use eager loading** để tránh N+1 queries
4. **Implement pagination** cho all list endpoints
5. **Add constraints** để đảm bảo data integrity
6. **Use soft delete** thay vì hard delete
7. **Validate permissions** trong CRUD operations

Đây là foundation để hiểu và implement SQLAlchemy 2.0 hiệu quả! 🎯