# Hướng dẫn chi tiết: Viết CRUD API từ Model đến API

## Mục lục
1. [CRUD cơ bản - Model không có quan hệ](#crud-cơ-bản)
2. [CRUD nâng cao - Model có quan hệ](#crud-có-quan-hệ)
3. [Giải thích chi tiết các thành phần](#giải-thích-chi-tiết)
4. [Best Practices](#best-practices)

---

## CRUD cơ bản

### 1. Tạo Model (SQLAlchemy)

```python
# src/app/models/category.py
import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from ..core.db.database import Base

class Category(Base):
    __tablename__ = "category"

    # Primary key
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    
    # Data fields
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    
    # Relationships (sẽ thêm sau)
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="category", init=False)
    
    # Metadata fields
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default_factory=uuid7, unique=True, init=False)
    created_at: Mapped[datetime] = mapped_column(default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, init=False)
    is_active: Mapped[bool] = mapped_column(default=True)
```

**Giải thích:**
- `__tablename__`: Tên bảng trong database
- `Mapped[type]`: Type hint cho SQLAlchemy 2.0
- `mapped_column()`: Định nghĩa column với constraints
- `init=False`: Không tạo parameter trong constructor (dành cho auto-generated fields)
- `unique=True`: Tạo unique constraint
- `index=True`: Tạo database index để tăng tốc query
- `default_factory`: Function để tạo default value

### 2. Tạo Schemas (Pydantic)

```python
# src/app/schemas/category.py
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# Base schema - chứa các field chung
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    is_active: bool = Field(True, description="Is category active")

# Schema cho tạo mới
class CategoryCreate(CategoryBase):
    pass

# Schema cho update
class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

# Schema cho response
class CategoryResponse(CategoryBase):
    id: int
    uuid: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Cho phép tạo từ SQLAlchemy model

# Schema cho list response có pagination
class CategoryListResponse(BaseModel):
    categories: list[CategoryResponse]
    total: int
    page: int
    size: int
    pages: int
```

**Giải thích:**
- `BaseModel`: Base class của Pydantic
- `Field()`: Định nghĩa validation rules
- `...`: Required field (Ellipsis)
- `Optional[type]`: Field có thể None
- `from_attributes = True`: Cho phép serialize từ SQLAlchemy object
- Inheritance: `CategoryCreate` kế thừa từ `CategoryBase`

### 3. Tạo CRUD Operations

```python
# src/app/crud/category.py
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.category import Category
from ..schemas.category import CategoryCreate, CategoryUpdate

class CategoryCRUD:
    """CRUD operations for Category model"""
    
    async def create(self, db: AsyncSession, *, obj_in: CategoryCreate) -> Category:
        """Create new category"""
        category = Category(
            name=obj_in.name,
            description=obj_in.description,
            is_active=obj_in.is_active
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)  # Reload từ DB để có ID và timestamps
        return category
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Category]:
        """Get category by ID"""
        stmt = select(Category).where(Category.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Category]:
        """Get category by name"""
        stmt = select(Category).where(Category.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> tuple[list[Category], int]:
        """Get multiple categories with pagination"""
        # Build base query
        stmt = select(Category)
        count_stmt = select(func.count(Category.id))
        
        # Add filters
        if is_active is not None:
            stmt = stmt.where(Category.is_active == is_active)
            count_stmt = count_stmt.where(Category.is_active == is_active)
        
        # Add pagination
        stmt = stmt.offset(skip).limit(limit).order_by(Category.created_at.desc())
        
        # Execute queries
        result = await db.execute(stmt)
        count_result = await db.execute(count_stmt)
        
        categories = result.scalars().all()
        total = count_result.scalar()
        
        return categories, total
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Category, 
        obj_in: CategoryUpdate
    ) -> Category:
        """Update category"""
        update_data = obj_in.model_dump(exclude_unset=True)  # Chỉ lấy fields được set
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """Delete category"""
        stmt = select(Category).where(Category.id == id)
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()
        
        if category:
            await db.delete(category)
            await db.commit()
            return True
        return False

# Create instance
category_crud = CategoryCRUD()
```

**Giải thích:**
- `AsyncSession`: Database session cho async operations
- `select()`: Tạo SELECT query
- `scalar_one_or_none()`: Trả về 1 record hoặc None
- `scalars().all()`: Trả về list records
- `func.count()`: SQL COUNT function
- `offset()`, `limit()`: Pagination
- `exclude_unset=True`: Chỉ lấy fields được explicitly set trong request

### 4. Tạo API Endpoints

```python
# src/app/api/v1/categories.py
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
    # Business logic validation
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
        raise HTTPException(status_code=404, detail="Category not found")
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
        raise HTTPException(status_code=404, detail="Category not found")
    
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
        raise HTTPException(status_code=404, detail="Category not found")
```

**Giải thích:**
- `APIRouter`: Tạo router group
- `Annotated[type, Depends()]`: Dependency injection
- `Query()`: Query parameter với validation
- `HTTPException`: Throw HTTP errors
- `status_code=201`: HTTP 201 Created
- `status_code=204`: HTTP 204 No Content
- `model_validate()`: Convert SQLAlchemy object sang Pydantic

---

## CRUD có quan hệ

### 1. Tạo Model có Foreign Key

```python
# src/app/models/article.py
import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from ..core.db.database import Base

class Article(Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    
    # Data fields
    title: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(String(500), default=None)
    
    # Foreign keys
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), index=True, init=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, init=False)
    
    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="articles", init=False)
    author: Mapped["User"] = relationship("User", back_populates="articles", init=False)
    
    # Metadata
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default_factory=uuid7, unique=True, init=False)
    created_at: Mapped[datetime] = mapped_column(default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, init=False)
    is_published: Mapped[bool] = mapped_column(default=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
```

**Giải thích:**
- `ForeignKey("table.column")`: Tạo foreign key constraint
- `relationship()`: Định nghĩa relationship với model khác
- `back_populates`: Tên attribute ở model kia
- `Text`: Column type cho text dài
- Forward reference `"Model"`: Dùng string khi model chưa được define

### 2. Update Model có relationship

```python
# Update trong src/app/models/category.py
class Category(Base):
    # ... existing fields ...
    
    # Relationships
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="category", init=False)
```

```python
# Update trong src/app/models/user.py
class User(Base):
    # ... existing fields ...
    
    # Relationships
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="author", init=False)
```

### 3. Schemas với Relationships

```python
# src/app/schemas/article.py
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .category import CategoryResponse
from .user import UserResponse

# Base schemas
class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    summary: Optional[str] = Field(None, max_length=500)
    category_id: int
    is_published: bool = Field(False)
    is_active: bool = Field(True)

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
    category: CategoryResponse  # Nested object
    author: UserResponse        # Nested object

    class Config:
        from_attributes = True
```

**Giải thích:**
- Import schemas từ module khác để tạo nested objects
- Tạo 2 versions: Simple (chỉ IDs) và Full (với nested objects)
- Nested objects tự động được serialize từ relationships

### 4. CRUD với Relationships

```python
# src/app/crud/article.py
from sqlalchemy.orm import selectinload

class ArticleCRUD:
    async def get_with_relations(self, db: AsyncSession, *, id: int) -> Optional[Article]:
        """Get article by ID with relationships loaded"""
        stmt = (
            select(Article)
            .options(
                selectinload(Article.category),  # Eager load category
                selectinload(Article.author)     # Eager load author
            )
            .where(Article.id == id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi_with_relations(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        category_id: Optional[int] = None,
        author_id: Optional[int] = None
    ) -> tuple[list[Article], int]:
        """Get multiple articles with relationships loaded"""
        stmt = (
            select(Article)
            .options(
                selectinload(Article.category),
                selectinload(Article.author)
            )
        )
        count_stmt = select(func.count(Article.id))
        
        # Add filters
        if category_id is not None:
            stmt = stmt.where(Article.category_id == category_id)
            count_stmt = count_stmt.where(Article.category_id == category_id)
        
        if author_id is not None:
            stmt = stmt.where(Article.author_id == author_id)
            count_stmt = count_stmt.where(Article.author_id == author_id)
        
        # Pagination
        stmt = stmt.offset(skip).limit(limit).order_by(Article.created_at.desc())
        
        result = await db.execute(stmt)
        count_result = await db.execute(count_stmt)
        
        articles = result.scalars().all()
        total = count_result.scalar()
        
        return articles, total
    
    async def verify_category_exists(self, db: AsyncSession, *, category_id: int) -> bool:
        """Verify if category exists and is active"""
        stmt = select(Category).where(
            Category.id == category_id,
            Category.is_active == True
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
```

**Giải thích:**
- `selectinload()`: Eager loading để tránh N+1 queries
- `options()`: Thêm loading options vào query
- Separate methods cho simple và with-relations queries
- Validation methods để check foreign key existence

### 5. API với Multiple Response Types

```python
# src/app/api/v1/articles.py
@router.get("/", response_model=ArticleListResponse)
async def get_articles(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    author_id: Optional[int] = Query(None, description="Filter by author ID"),
    is_published: Optional[bool] = Query(None)
) -> ArticleListResponse:
    """Get articles - simple response (IDs only)"""
    skip = (page - 1) * size
    articles, total = await article_crud.get_multi(
        db, skip=skip, limit=size, 
        category_id=category_id, author_id=author_id, is_published=is_published
    )
    
    pages = math.ceil(total / size) if total > 0 else 1
    
    return ArticleListResponse(
        articles=[ArticleResponseSimple.model_validate(article) for article in articles],
        total=total, page=page, size=size, pages=pages
    )

@router.get("/detailed", response_model=ArticleDetailListResponse)
async def get_articles_detailed(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    author_id: Optional[int] = Query(None),
    is_published: Optional[bool] = Query(None)
) -> ArticleDetailListResponse:
    """Get articles - detailed response (with relationships)"""
    skip = (page - 1) * size
    articles, total = await article_crud.get_multi_with_relations(
        db, skip=skip, limit=size, 
        category_id=category_id, author_id=author_id, is_published=is_published
    )
    
    pages = math.ceil(total / size) if total > 0 else 1
    
    return ArticleDetailListResponse(
        articles=[ArticleResponse.model_validate(article) for article in articles],
        total=total, page=page, size=size, pages=pages
    )

@router.post("/", response_model=ArticleResponseSimple, status_code=201)
async def create_article(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    article_in: ArticleCreate,
    current_user_id: int = 1  # TODO: Get from authentication
) -> ArticleResponseSimple:
    """Create new article"""
    # Validate foreign keys
    if not await article_crud.verify_category_exists(db, category_id=article_in.category_id):
        raise HTTPException(status_code=400, detail="Category not found or inactive")
    
    if not await article_crud.verify_author_exists(db, author_id=current_user_id):
        raise HTTPException(status_code=400, detail="Author not found")
    
    article = await article_crud.create(db, obj_in=article_in, author_id=current_user_id)
    return ArticleResponseSimple.model_validate(article)
```

**Giải thích:**
- 2 endpoints: `/` (simple) và `/detailed` (with relationships)
- Validation cho foreign keys trước khi create/update
- Error handling với meaningful messages
- Placeholder cho authentication (current_user_id)

---

## Giải thích chi tiết các thành phần

### 1. Kiến trúc Layered Architecture

```
┌─────────────────┐
│   API Layer     │  ← FastAPI routes, validation, serialization
├─────────────────┤
│   CRUD Layer    │  ← Business logic, database operations
├─────────────────┤
│  Schema Layer   │  ← Pydantic models, validation, serialization
├─────────────────┤
│  Model Layer    │  ← SQLAlchemy models, database schema
└─────────────────┘
```

#### **Model Layer (SQLAlchemy)**
Đây là layer thấp nhất, định nghĩa cấu trúc database:

```python
# Vai trò: Định nghĩa bảng, relationships, constraints
class Category(Base):
    __tablename__ = "category"  # Tên bảng trong DB
    
    # Primary Key - tự động tăng
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True, init=False)
    
    # Business Fields - dữ liệu thực tế
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    
    # Metadata Fields - thông tin hệ thống
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), default_factory=uuid7, unique=True, init=False)
    created_at: Mapped[datetime] = mapped_column(default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, init=False)
    is_active: Mapped[bool] = mapped_column(default=True)
```

**Giải thích từng phần:**
- `__tablename__`: Tên bảng trong database, SQLAlchemy sẽ tạo bảng với tên này
- `Mapped[type]`: Type annotation cho SQLAlchemy 2.0, giúp IDE hiểu type và validate
- `mapped_column()`: Định nghĩa column với các options
- `init=False`: Không tạo parameter trong `__init__()`, dành cho auto-generated fields
- `autoincrement=True`: Database tự động tăng giá trị
- `primary_key=True`: Đánh dấu là primary key
- `unique=True`: Tạo unique constraint, không cho phép duplicate
- `index=True`: Tạo database index để tăng tốc query
- `default_factory`: Function để tạo default value mỗi khi tạo record mới
- `String(100)`: VARCHAR(100) trong database
- `Text`: LONGTEXT/TEXT trong database cho nội dung dài

#### **Schema Layer (Pydantic)**
Định nghĩa cách validate và serialize data:

```python
# Base Schema - chứa fields chung
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    is_active: bool = Field(True, description="Is category active")

# Create Schema - dành cho tạo mới
class CategoryCreate(CategoryBase):
    pass  # Kế thừa tất cả từ CategoryBase

# Update Schema - dành cho update (tất cả fields đều optional)
class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

# Response Schema - dành cho trả về API
class CategoryResponse(CategoryBase):
    id: int                                    # Thêm ID
    uuid: uuid.UUID                           # Thêm UUID
    created_at: datetime                      # Thêm timestamps
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Cho phép tạo từ SQLAlchemy object
```

**Giải thích validation:**
- `Field(...)`: `...` (Ellipsis) có nghĩa là required field
- `Field(None, ...)`: None là default value, field này optional
- `min_length=1`: Tối thiểu 1 ký tự
- `max_length=100`: Tối đa 100 ký tự
- `Optional[str]`: Field có thể là string hoặc None
- `from_attributes = True`: Pydantic có thể serialize từ SQLAlchemy object

#### **CRUD Layer (Business Logic)**
Xử lý tất cả database operations và business logic:

```python
class CategoryCRUD:
    async def create(self, db: AsyncSession, *, obj_in: CategoryCreate) -> Category:
        # 1. Tạo SQLAlchemy object từ Pydantic schema
        category = Category(
            name=obj_in.name,
            description=obj_in.description,
            is_active=obj_in.is_active
        )
        
        # 2. Thêm vào session (chưa commit)
        db.add(category)
        
        # 3. Commit transaction (lưu vào DB)
        await db.commit()
        
        # 4. Refresh để lấy ID và timestamps từ DB
        await db.refresh(category)
        
        return category
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Category]:
        # 1. Tạo SELECT query
        stmt = select(Category).where(Category.id == id)
        
        # 2. Execute query
        result = await db.execute(stmt)
        
        # 3. Lấy một record hoặc None
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0,           # Offset cho pagination
        limit: int = 100,        # Limit cho pagination
        is_active: Optional[bool] = None  # Filter condition
    ) -> tuple[list[Category], int]:
        
        # 1. Tạo base queries
        stmt = select(Category)                    # SELECT * FROM category
        count_stmt = select(func.count(Category.id))  # SELECT COUNT(id) FROM category
        
        # 2. Thêm WHERE conditions
        if is_active is not None:
            stmt = stmt.where(Category.is_active == is_active)
            count_stmt = count_stmt.where(Category.is_active == is_active)
        
        # 3. Thêm pagination và sorting
        stmt = stmt.offset(skip).limit(limit).order_by(Category.created_at.desc())
        
        # 4. Execute cả 2 queries
        result = await db.execute(stmt)
        count_result = await db.execute(count_stmt)
        
        # 5. Process results
        categories = result.scalars().all()  # List[Category]
        total = count_result.scalar()        # int
        
        return categories, total
```

**Giải thích database operations:**
- `db.add()`: Thêm object vào session (chưa lưu DB)
- `await db.commit()`: Commit transaction, lưu changes vào DB
- `await db.refresh()`: Reload object từ DB để lấy auto-generated values
- `select()`: Tạo SELECT query
- `where()`: Thêm WHERE condition
- `offset()`, `limit()`: Pagination
- `order_by()`: Sorting
- `func.count()`: SQL COUNT function
- `scalar_one_or_none()`: Lấy 1 record hoặc None
- `scalars().all()`: Lấy list records

#### **API Layer (FastAPI)**
Xử lý HTTP requests, validation, authentication:

```python
@router.post("/", response_model=CategoryResponse, status_code=201)
async def create_category(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],  # DI: Database session
    category_in: CategoryCreate                          # Request body validation
) -> CategoryResponse:
    # 1. Business logic validation
    existing_category = await category_crud.get_by_name(db, name=category_in.name)
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category with this name already exists"
        )
    
    # 2. Call CRUD layer
    category = await category_crud.create(db, obj_in=category_in)
    
    # 3. Convert SQLAlchemy object to Pydantic response
    return CategoryResponse.model_validate(category)

@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    # Query parameters với validation
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
) -> CategoryListResponse:
    # 1. Calculate pagination
    skip = (page - 1) * size
    
    # 2. Get data từ CRUD layer
    categories, total = await category_crud.get_multi(
        db, skip=skip, limit=size, is_active=is_active
    )
    
    # 3. Calculate pagination metadata
    pages = math.ceil(total / size) if total > 0 else 1
    
    # 4. Return structured response
    return CategoryListResponse(
        categories=[CategoryResponse.model_validate(cat) for cat in categories],
        total=total,
        page=page,
        size=size,
        pages=pages
    )
```

**Giải thích API components:**
- `@router.post()`: HTTP POST endpoint
- `response_model`: Pydantic model cho response serialization
- `status_code=201`: HTTP 201 Created
- `Annotated[type, Depends()]`: Dependency injection
- `Query()`: Query parameter với validation
- `ge=1`: Greater than or equal 1
- `le=100`: Less than or equal 100
- `HTTPException`: Throw HTTP error với status code và message
- `model_validate()`: Convert SQLAlchemy object sang Pydantic

**Lợi ích của Layered Architecture:**
- **Separation of concerns**: Mỗi layer có trách nhiệm riêng biệt
- **Testability**: Có thể test từng layer độc lập
- **Maintainability**: Dễ maintain và extend features
- **Reusability**: CRUD layer có thể dùng ở CLI, background jobs, etc.

### 2. SQLAlchemy 2.0 Features Chi Tiết

#### **Type Annotations với Mapped[]**
```python
# Cách cũ (SQLAlchemy 1.x)
name = Column(String(100), nullable=False)
description = Column(String(500), nullable=True)

# Cách mới (SQLAlchemy 2.0)
name: Mapped[str] = mapped_column(String(100))                    # NOT NULL
description: Mapped[str | None] = mapped_column(String(500))      # NULLABLE
articles: Mapped[list["Article"]] = relationship(...)             # One-to-Many
```

**Giải thích:**
- `Mapped[str]`: Type hint cho non-nullable string
- `Mapped[str | None]`: Type hint cho nullable string (Union type)
- `Mapped[list["Article"]]`: One-to-Many relationship, trả về danh sách Article
- `"Article"`: Forward reference (string) vì class Article chưa được define

#### **Modern Query Syntax**
```python
# SELECT queries
stmt = select(Category).where(Category.id == id)
stmt = select(Category).where(Category.name.like("%test%"))
stmt = select(Category).where(Category.is_active == True)

# JOIN queries
stmt = select(Article).join(Category).where(Category.name == "Tech")

# Aggregate functions
stmt = select(func.count(Category.id)).where(Category.is_active == True)

# Subqueries
subq = select(Category.id).where(Category.is_active == True).subquery()
stmt = select(Article).where(Article.category_id.in_(subq))

# Complex filtering
stmt = select(Category).where(
    and_(
        Category.is_active == True,
        or_(
            Category.name.like("%tech%"),
            Category.description.like("%tech%")
        )
    )
)
```

#### **Async Database Operations**
```python
# Execute và lấy kết quả
async def get_category(db: AsyncSession, id: int):
    stmt = select(Category).where(Category.id == id)
    result = await db.execute(stmt)  # Execute query
    return result.scalar_one_or_none()  # Lấy 1 record hoặc None

# Multiple records
async def get_categories(db: AsyncSession):
    stmt = select(Category).order_by(Category.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()  # Lấy list records

# Count records
async def count_categories(db: AsyncSession):
    stmt = select(func.count(Category.id))
    result = await db.execute(stmt)
    return result.scalar()  # Lấy single value

# Insert record
async def create_category(db: AsyncSession, name: str):
    category = Category(name=name)
    db.add(category)           # Thêm vào session
    await db.commit()          # Commit transaction
    await db.refresh(category) # Reload để lấy ID
    return category

# Update record
async def update_category(db: AsyncSession, category: Category, name: str):
    category.name = name
    category.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(category)
    return category

# Delete record
async def delete_category(db: AsyncSession, category: Category):
    await db.delete(category)
    await db.commit()
```

**Ưu điểm SQLAlchemy 2.0:**
- **Type Safety**: IDE có thể detect lỗi type ngay khi code
- **Better Performance**: Optimized query execution
- **Async Support**: Native async/await, không block event loop
- **Clear Syntax**: Query syntax rõ ràng và dễ đọc
- **Migration Path**: Tương thích ngược với SQLAlchemy 1.x

### 3. Pydantic Validation Chi Tiết

#### **Field Validation**
```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional
import re

class CategoryCreate(BaseModel):
    # String validation
    name: str = Field(
        ...,                          # Required field
        min_length=1,                 # Tối thiểu 1 ký tự
        max_length=100,               # Tối đa 100 ký tự
        regex=r"^[a-zA-Z0-9\s]+$",   # Chỉ cho phép chữ, số, space
        description="Category name"    # Mô tả cho API docs
    )
    
    # Optional field với default
    description: Optional[str] = Field(
        None,                         # Default value
        max_length=500,
        description="Category description"
    )
    
    # Boolean với default
    is_active: bool = Field(True, description="Is category active")
    
    # Number validation
    priority: int = Field(1, ge=1, le=10, description="Priority 1-10")
    
    # Email validation
    contact_email: Optional[str] = Field(None, regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")

# Custom validators
class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    category_id: int = Field(..., gt=0)
    tags: Optional[list[str]] = Field(default_factory=list)
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty or only whitespace')
        return v.strip().title()  # Capitalize each word
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Remove duplicates và lowercase
            return list(set(tag.lower().strip() for tag in v if tag.strip()))
        return []
    
    @validator('content')
    def validate_content(cls, v):
        # Remove HTML tags
        clean_content = re.sub(r'<[^>]+>', '', v)
        if len(clean_content.strip()) < 10:
            raise ValueError('Content must be at least 10 characters (excluding HTML)')
        return v
    
    @root_validator
    def validate_article(cls, values):
        title = values.get('title', '')
        content = values.get('content', '')
        
        # Title không được trùng với content
        if title and content and title.lower() in content.lower()[:100]:
            raise ValueError('Title should not be repeated in content beginning')
        
        return values
```

#### **Response Models với Computed Fields**
```python
from pydantic import computed_field

class CategoryResponse(CategoryBase):
    id: int
    uuid: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed field - không lưu trong DB nhưng có trong response
    @computed_field
    @property
    def age_in_days(self) -> int:
        return (datetime.now(UTC) - self.created_at).days
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    class Config:
        from_attributes = True

# Response với relationships
class ArticleDetailResponse(BaseModel):
    id: int
    title: str
    content: str
    author: UserResponse      # Nested object
    category: CategoryResponse # Nested object
    tags: list[str]
    created_at: datetime
    
    @computed_field
    @property
    def reading_time(self) -> int:
        # Estimate reading time (words per minute)
        word_count = len(self.content.split())
        return max(1, word_count // 200)  # Assuming 200 WPM
    
    @computed_field
    @property
    def excerpt(self) -> str:
        # First 150 characters
        return self.content[:150] + "..." if len(self.content) > 150 else self.content
    
    class Config:
        from_attributes = True
```

#### **Advanced Validation Examples**
```python
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, regex=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)
    confirm_password: str
    age: int = Field(..., ge=13, le=120)  # Greater equal 13, less equal 120
    website: Optional[str] = Field(None, regex=r"^https?://")
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @root_validator
    def validate_passwords_match(cls, values):
        password = values.get('password')
        confirm_password = values.get('confirm_password')
        if password != confirm_password:
            raise ValueError('Passwords do not match')
        return values
    
    @validator('email')
    def validate_email_domain(cls, v):
        # Chỉ cho phép certain domains
        allowed_domains = ['gmail.com', 'yahoo.com', 'company.com']
        domain = v.split('@')[1].lower()
        if domain not in allowed_domains:
            raise ValueError(f'Email domain must be one of: {", ".join(allowed_domains)}')
        return v.lower()

# Update model với partial validation
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=20, regex=r"^[a-zA-Z0-9_]+$")
    email: Optional[str] = Field(None, regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: Optional[int] = Field(None, ge=13, le=120)
    website: Optional[str] = Field(None, regex=r"^https?://")
    
    @validator('email')
    def validate_email_if_provided(cls, v):
        if v:  # Only validate if provided
            return v.lower()
        return v
```

#### **Model Configuration**
```python
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    
    class Config:
        # JSON Schema configuration
        schema_extra = {
            "example": {
                "name": "Technology",
                "description": "Articles about technology and programming"
            }
        }
        
        # Validation configuration
        str_strip_whitespace = True    # Auto strip whitespace
        validate_assignment = True     # Validate khi assign values
        use_enum_values = True         # Use enum values instead of names
        allow_population_by_field_name = True  # Allow both field names and aliases
        
        # Serialization configuration
        json_encoders = {
            datetime: lambda v: v.isoformat(),  # Custom datetime encoding
            uuid.UUID: lambda v: str(v)        # Convert UUID to string
        }
```

**Tính năng chính của Pydantic:**
- **Automatic Validation**: Tự động validate input data
- **Type Conversion**: Tự động convert types (string to int, etc.)
- **Custom Validators**: Tạo validation logic phức tạp
- **JSON Schema**: Tự động generate schema cho API documentation
- **Error Messages**: Error messages chi tiết và dễ hiểu
- **Performance**: Fast validation với Rust backend (Pydantic v2)
- **IDE Support**: Type hints giúp IDE autocomplete và detect errors

### 4. FastAPI Dependency Injection Chi Tiết

#### **Database Dependencies**
```python
# src/app/core/db/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Database engine
async_engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Database dependency
async def async_get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Provide session to endpoint
        finally:
            await session.close()  # Auto cleanup

# Usage trong endpoint
async def create_category(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],  # DI: Database session
    category_in: CategoryCreate
):
    # db session tự động được inject và cleanup
    return await category_crud.create(db, obj_in=category_in)
```

#### **Authentication Dependencies**
```python
# src/app/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(async_get_db)
) -> User:
    """Extract user từ JWT token"""
    try:
        # Decode JWT token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user từ database
        user = await user_crud.get_by_username(db, username=username)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Optional authentication
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get user nếu có token, None nếu không có"""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

# Admin only dependency
async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Chỉ admin mới được access"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, 
            detail="Not enough permissions"
        )
    return current_user

# Resource ownership dependency
def require_ownership(resource_field: str = "user_id"):
    async def check_ownership(
        resource_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(async_get_db)
    ):
        # Generic ownership check
        resource = await get_resource_by_id(db, resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        if getattr(resource, resource_field) != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        return resource
    return check_ownership
```

#### **Validation Dependencies**
```python
# Query parameter dependencies
async def common_parameters(
    page: int = Query(1, ge=1, le=1000, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    sort: str = Query("created_at", regex="^(created_at|updated_at|name)$"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    """Common pagination và sorting parameters"""
    return {
        "skip": (page - 1) * size,
        "limit": size,
        "sort_field": sort,
        "sort_order": order,
        "page": page,
        "size": size
    }

# Search parameters
async def search_parameters(
    q: Optional[str] = Query(None, min_length=1, max_length=100, description="Search query"),
    category_id: Optional[int] = Query(None, ge=1, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    return {
        "search_query": q,
        "category_id": category_id,
        "is_active": is_active
    }

# Usage trong endpoint
@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    *,
    db: AsyncSession = Depends(async_get_db),
    params: dict = Depends(common_parameters),
    filters: dict = Depends(search_parameters),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    categories, total = await category_crud.get_multi(
        db, 
        skip=params["skip"], 
        limit=params["limit"],
        search_query=filters["search_query"],
        category_id=filters["category_id"],
        is_active=filters["is_active"]
    )
    
    return CategoryListResponse(
        categories=[CategoryResponse.model_validate(cat) for cat in categories],
        total=total,
        page=params["page"],
        size=params["size"],
        pages=math.ceil(total / params["size"]) if total > 0 else 1
    )
```

#### **Custom Dependencies**
```python
# Rate limiting dependency
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def rate_limit(requests: str):
    """Rate limiting decorator"""
    def decorator(func):
        return limiter.limit(requests)(func)
    return decorator

# Usage
@router.post("/")
@rate_limit("5/minute")  # 5 requests per minute
async def create_category(...):
    pass

# Cache dependency
from functools import lru_cache
import redis

@lru_cache()
def get_redis():
    return redis.Redis(host="localhost", port=6379, db=0)

async def get_cached_data(
    cache_key: str,
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get data từ cache hoặc None nếu không có"""
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    return None

# Background task dependency
from fastapi import BackgroundTasks

async def log_activity(
    action: str,
    user_id: int,
    background_tasks: BackgroundTasks
):
    """Log user activity in background"""
    def write_log():
        # Write to log file or database
        with open("activity.log", "a") as f:
            f.write(f"{datetime.now()}: User {user_id} performed {action}\n")
    
    background_tasks.add_task(write_log)

# Endpoint sử dụng background tasks
@router.post("/")
async def create_category(
    *,
    category_in: CategoryCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # Create category
    category = await category_crud.create(db, obj_in=category_in)
    
    # Log activity in background
    await log_activity("create_category", current_user.id, background_tasks)
    
    return CategoryResponse.model_validate(category)
```

#### **Testing với Dependency Override**
```python
# tests/conftest.py
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user():
    return User(id=1, username="testuser", email="test@example.com", is_superuser=True)

# Setup test client
app.dependency_overrides[async_get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

# Test
def test_create_category():
    response = client.post(
        "/api/v1/categories/",
        json={"name": "Test Category", "description": "Test description"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Category"
```

**Lợi ích của Dependency Injection:**
- **Automatic Injection**: FastAPI tự động inject dependencies
- **Parameter Validation**: Validate parameters trước khi vào function
- **Reusable Dependencies**: Có thể dùng lại ở nhiều endpoints
- **Easy Testing**: Override dependencies cho testing
- **Clean Code**: Code logic tách biệt với infrastructure
- **Type Safety**: Full type hints và IDE support
- **Nested Dependencies**: Dependencies có thể depend on dependencies khác

### 5. Database Relationships Chi Tiết

#### **One-to-Many Relationship**
```python
# Parent Model (Category)
class Category(Base):
    __tablename__ = "category"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    
    # One-to-Many: Một category có nhiều articles
    articles: Mapped[list["Article"]] = relationship(
        "Article",                    # Target model
        back_populates="category",    # Tên field ở Article model
        cascade="all, delete-orphan", # Khi xóa category thì xóa articles
        lazy="selectin"               # Loading strategy
    )

# Child Model (Article)
class Article(Base):
    __tablename__ = "article"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    
    # Foreign Key
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), index=True)
    
    # Many-to-One: Nhiều articles thuộc về một category
    category: Mapped["Category"] = relationship(
        "Category", 
        back_populates="articles"
    )
```

#### **Many-to-Many Relationship**
```python
# Association table cho Many-to-Many
article_tags = Table(
    'article_tags',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('article.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True)
)

class Article(Base):
    __tablename__ = "article"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    
    # Many-to-Many: Một article có nhiều tags, một tag có nhiều articles
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=article_tags,      # Association table
        back_populates="articles",
        lazy="selectin"
    )

class Tag(Base):
    __tablename__ = "tag"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    
    # Many-to-Many back reference
    articles: Mapped[list["Article"]] = relationship(
        "Article",
        secondary=article_tags,
        back_populates="tags",
        lazy="selectin"
    )
```

#### **Self-Referencing Relationship**
```python
class Category(Base):
    __tablename__ = "category"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    
    # Self-referencing: Category có thể có parent category
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    
    # Parent relationship
    parent: Mapped["Category"] = relationship(
        "Category",
        remote_side=[id],           # Specify remote side cho self-reference
        back_populates="children"
    )
    
    # Children relationship
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
```

#### **Loading Strategies Chi Tiết**

```python
# 1. LAZY LOADING (Default) - N+1 Problem
async def get_articles_lazy():
    # Query 1: Load articles
    articles = await db.execute(select(Article))
    
    # Query 2, 3, 4, ...: Load category for each article
    for article in articles.scalars():
        print(article.category.name)  # Triggers separate query!
    
    # Result: 1 + N queries (N = number of articles)

# 2. EAGER LOADING - Single Query với JOIN
async def get_articles_eager():
    # Single query với LEFT JOIN
    stmt = select(Article).options(selectinload(Article.category))
    articles = await db.execute(stmt)
    
    for article in articles.scalars():
        print(article.category.name)  # No additional query!
    
    # Result: 1 query total

# 3. JOINED LOADING - SQL JOIN trong single query
async def get_articles_joined():
    stmt = select(Article).options(joinedload(Article.category))
    articles = await db.execute(stmt)
    
    # SQL: SELECT article.*, category.* FROM article LEFT JOIN category ...

# 4. SUBQUERY LOADING
async def get_articles_subquery():
    stmt = select(Article).options(subqueryload(Article.category))
    articles = await db.execute(stmt)
    
    # 2 queries: Main query + subquery for categories

# 5. NESTED RELATIONSHIPS
async def get_articles_with_nested():
    stmt = select(Article).options(
        selectinload(Article.category),           # Load category
        selectinload(Article.author),             # Load author
        selectinload(Article.tags),               # Load tags
        selectinload(Article.comments).selectinload(Comment.author)  # Nested loading
    )
    articles = await db.execute(stmt)
```

#### **Complex Relationship Queries**

```python
# Query articles với category name
async def get_articles_by_category_name(db: AsyncSession, category_name: str):
    stmt = (
        select(Article)
        .join(Category)  # INNER JOIN category ON article.category_id = category.id
        .where(Category.name == category_name)
        .options(selectinload(Article.category))
    )
    result = await db.execute(stmt)
    return result.scalars().all()

# Query categories với article count
async def get_categories_with_article_count(db: AsyncSession):
    stmt = (
        select(
            Category,
            func.count(Article.id).label('article_count')
        )
        .outerjoin(Article)  # LEFT JOIN để include categories không có articles
        .group_by(Category.id)
        .order_by(func.count(Article.id).desc())
    )
    result = await db.execute(stmt)
    
    categories_with_count = []
    for category, count in result:
        category_dict = category.__dict__.copy()
        category_dict['article_count'] = count
        categories_with_count.append(category_dict)
    
    return categories_with_count

# Query với multiple joins
async def get_articles_with_author_and_category(db: AsyncSession):
    stmt = (
        select(Article)
        .join(Category)     # JOIN category
        .join(User)         # JOIN user (author)
        .where(
            and_(
                Category.is_active == True,
                User.is_active == True,
                Article.is_published == True
            )
        )
        .options(
            selectinload(Article.category),
            selectinload(Article.author)
        )
        .order_by(Article.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

# Subquery example
async def get_categories_with_recent_articles(db: AsyncSession):
    # Subquery: Recent articles (last 30 days)
    recent_articles = (
        select(Article.category_id)
        .where(Article.created_at >= datetime.now() - timedelta(days=30))
        .subquery()
    )
    
    # Main query: Categories that have recent articles
    stmt = (
        select(Category)
        .where(Category.id.in_(
            select(recent_articles.c.category_id)
        ))
        .options(selectinload(Category.articles))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
```

#### **Association Object Pattern (Many-to-Many với extra data)**
```python
# Association object với extra data
class ArticleTag(Base):
    __tablename__ = "article_tag"
    
    article_id: Mapped[int] = mapped_column(ForeignKey("article.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tag.id"), primary_key=True)
    
    # Extra data
    created_at: Mapped[datetime] = mapped_column(default_factory=lambda: datetime.now(UTC))
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))
    
    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="article_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="article_tags")
    creator: Mapped["User"] = relationship("User")

class Article(Base):
    # ... other fields ...
    
    # Association object relationship
    article_tags: Mapped[list["ArticleTag"]] = relationship(
        "ArticleTag", 
        back_populates="article",
        cascade="all, delete-orphan"
    )
    
    # Convenience property để access tags directly
    @property
    def tags(self) -> list["Tag"]:
        return [at.tag for at in self.article_tags]

# Usage
async def add_tag_to_article(db: AsyncSession, article_id: int, tag_id: int, user_id: int):
    article_tag = ArticleTag(
        article_id=article_id,
        tag_id=tag_id,
        created_by=user_id
    )
    db.add(article_tag)
    await db.commit()
```

**Best Practices cho Relationships:**
- **Index Foreign Keys**: Luôn tạo index cho foreign key columns
- **Use selectinload()**: Để tránh N+1 queries
- **Cascade Options**: Cẩn thận với cascade delete
- **Lazy Loading**: Default lazy loading có thể gây N+1 problem
- **Proper Join Types**: INNER vs LEFT JOIN tùy business logic
- **Association Objects**: Dùng khi Many-to-Many cần extra data

### 6. Pagination Pattern

```python
def paginate(page: int, size: int, total: int):
    skip = (page - 1) * size
    pages = math.ceil(total / size) if total > 0 else 1
    
    return {
        "skip": skip,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }
```

### 7. Error Handling Pattern

```python
# Validation errors
if not category:
    raise HTTPException(status_code=404, detail="Category not found")

# Business logic errors  
if existing_category:
    raise HTTPException(status_code=400, detail="Category already exists")

# Authorization errors
if article.author_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not enough permissions")
```

---

## Best Practices

### 1. Model Design
- Sử dụng `init=False` cho auto-generated fields
- Thêm indexes cho foreign keys và frequently queried fields
- Sử dụng meaningful constraints (unique, not null)
- Thêm soft delete với `is_active` field

### 2. Schema Design
- Tách Base, Create, Update, Response schemas
- Sử dụng `Optional[]` cho update schemas
- Validation với `Field()` constraints
- Nested schemas cho relationships

### 3. CRUD Design
- Async methods cho database operations
- Return types với `Optional[]` cho single records
- Pagination cho list methods
- Separate methods cho with/without relationships
- Validation methods cho business rules

### 4. API Design
- RESTful URLs (`/categories`, `/categories/{id}`)
- Appropriate HTTP status codes
- Query parameters cho filtering và pagination
- Multiple endpoints cho different response types
- Proper error handling với meaningful messages

### 5. Performance
- Sử dụng `selectinload()` để tránh N+1 queries
- Database indexes cho frequently queried fields
- Pagination để limit response size
- Caching cho frequently accessed data

### 6. Security
- Input validation với Pydantic
- Authorization checks
- SQL injection protection với parameterized queries
- Rate limiting cho public APIs

### 7. Testing
```python
# Test CRUD operations
async def test_create_category():
    category_data = CategoryCreate(name="Test", description="Test desc")
    category = await category_crud.create(db, obj_in=category_data)
    assert category.name == "Test"

# Test API endpoints
def test_get_categories(client: TestClient):
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
```

### 8. Migration Best Practices
```bash
# Tạo migration
alembic revision --autogenerate -m "Add category model"

# Review migration file trước khi apply
# Apply migration
alembic upgrade head

# Rollback nếu cần
alembic downgrade -1
```

---

## Tổng kết

Workflow hoàn chỉnh để tạo CRUD API:

1. **Design database schema** → Models
2. **Define validation rules** → Schemas  
3. **Implement business logic** → CRUD
4. **Create API endpoints** → Routes
5. **Register routes** → Router
6. **Create migration** → Alembic
7. **Test endpoints** → Swagger UI

Pattern này có thể scale từ simple CRUD đến complex business logic với multiple relationships, authentication, authorization, caching, và nhiều features khác.