# Hướng Dẫn Viết Model và API Phức Tạp với FastAPI + SQLAlchemy

## Mục Lục
1. [Thiết Kế Model Phức Tạp](#thiết-kế-model-phức-tạp)
2. [Relationships và Foreign Keys](#relationships-và-foreign-keys)
3. [Schema Design Pattern](#schema-design-pattern)
4. [Service Layer Architecture](#service-layer-architecture)
5. [API Controller Best Practices](#api-controller-best-practices)
6. [Advanced Query Patterns](#advanced-query-patterns)
7. [Error Handling và Validation](#error-handling-và-validation)
8. [Performance Optimization](#performance-optimization)

---

## Thiết Kế Model Phức Tạp

### 1. Base Model Pattern

```python
# src/app/models/base.py
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped, mapped_column
from sqlalchemy import Integer, DateTime, Boolean, UUID
from datetime import datetime, UTC
from typing import Optional
import uuid

class Base(DeclarativeBase, MappedAsDataclass):
    """Base class cho tất cả models với common fields"""
    pass

class TimestampMixin:
    """Mixin cho timestamp fields"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        nullable=False,
        index=True,
        init=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
        nullable=False,
        index=True,
        init=False,
    )

class SoftDeleteMixin:
    """Mixin cho soft delete functionality"""
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        init=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        init=False,
    )

class UUIDMixin:
    """Mixin cho UUID field"""
    uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default_factory=uuid.uuid4,
        unique=True,
        init=False,
    )
```

### 2. Complex Model Example

```python
# src/app/models/ecommerce/product.py
from ..base import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Text, ForeignKey, Table
from typing import List, Optional
from decimal import Decimal

# Many-to-many association table
product_categories = Table(
    'product_categories',
    Base.metadata,
    mapped_column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    mapped_column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
)

class Product(Base, TimestampMixin, SoftDeleteMixin, UUIDMixin):
    __tablename__ = "products"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        init=False,
    )
    
    # Required fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    
    # Optional fields
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    # Foreign keys
    brand_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("brands.id"),
        nullable=True,
        index=True,
        default=None,
    )
    
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=True,
        index=True,
        default=None,
    )
    
    # Relationships
    brand: Mapped[Optional["Brand"]] = relationship(
        "Brand",
        back_populates="products",
        lazy="selectin",
        init=False,
    )
    
    supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier",
        back_populates="products",
        lazy="selectin",
        init=False,
    )
    
    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary=product_categories,
        back_populates="products",
        lazy="selectin",
        init=False,
    )
    
    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
    )
    
    reviews: Mapped[List["ProductReview"]] = relationship(
        "ProductReview",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="dynamic",  # Dynamic loading cho performance
        init=False,
    )

class Category(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        init=False,
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Self-referential relationship cho nested categories
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True,
        default=None,
    )
    
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="children",
        remote_side="Category.id",
        init=False,
    )
    
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        init=False,
    )
    
    products: Mapped[List["Product"]] = relationship(
        "Product",
        secondary=product_categories,
        back_populates="categories",
        init=False,
    )
```

---

## Relationships và Foreign Keys

### 1. One-to-Many Relationship

```python
# Parent Model
class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    
    # One-to-many: Một user có nhiều orders
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        init=False,
    )

# Child Model
class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    # Foreign key reference
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Back reference
    user: Mapped["User"] = relationship(
        "User",
        back_populates="orders",
        lazy="selectin",
        init=False,
    )
```

### 2. Many-to-Many Relationship

```python
# Association table
user_roles = Table(
    'user_roles',
    Base.metadata,
    mapped_column('user_id', Integer, ForeignKey('users.id')),
    mapped_column('role_id', Integer, ForeignKey('roles.id')),
    # Composite primary key
    PrimaryKeyConstraint('user_id', 'role_id'),
    # Additional constraints
    UniqueConstraint('user_id', 'role_id', name='unique_user_role'),
)

class User(Base):
    # ... other fields
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
        init=False,
    )

class Role(Base):
    # ... other fields
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        lazy="selectin",
        init=False,
    )
```

### 3. Association Object Pattern (Advanced Many-to-Many)

```python
class OrderProduct(Base, TimestampMixin):
    """Association object với additional data"""
    __tablename__ = "order_products"
    
    # Composite primary key
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        primary_key=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        primary_key=True,
    )
    
    # Additional fields trong association
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal('0.00'),
    )
    
    # Relationships
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="order_products",
        init=False,
    )
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="order_products",
        init=False,
    )

class Order(Base):
    # ... other fields
    order_products: Mapped[List["OrderProduct"]] = relationship(
        "OrderProduct",
        back_populates="order",
        cascade="all, delete-orphan",
        init=False,
    )
    
    # Convenient property để access products directly
    @property
    def products(self) -> List["Product"]:
        return [op.product for op in self.order_products]
```

---

## Schema Design Pattern

### 1. Layered Schema Architecture

```python
# src/app/schemas/product/product_schemas.py
from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Annotated, Optional, List
from decimal import Decimal
from datetime import datetime

# Base schemas
class ProductBase(BaseModel):
    """Base product fields"""
    name: Annotated[str, Field(min_length=1, max_length=255)]
    sku: Annotated[str, Field(min_length=1, max_length=100)]
    price: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    description: Optional[str] = None
    stock_quantity: Annotated[int, Field(ge=0)] = 0

# Create schemas
class ProductCreate(ProductBase):
    """Schema for creating product"""
    model_config = ConfigDict(extra="forbid")
    
    brand_id: Optional[int] = None
    supplier_id: Optional[int] = None
    category_ids: List[int] = []

class ProductCreateInternal(ProductCreate):
    """Internal schema with system fields"""
    created_by_user_id: int

# Update schemas
class ProductUpdate(BaseModel):
    """Schema for updating product"""
    model_config = ConfigDict(extra="forbid")
    
    name: Optional[str] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None
    stock_quantity: Optional[int] = None
    brand_id: Optional[int] = None
    supplier_id: Optional[int] = None

class ProductUpdateInternal(ProductUpdate):
    """Internal update schema"""
    updated_at: datetime
    updated_by_user_id: int

# Read schemas
class ProductRead(BaseModel):
    """Basic product read schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    sku: str
    price: Decimal
    description: Optional[str]
    stock_quantity: int
    created_at: datetime
    updated_at: datetime

class ProductDetail(ProductRead):
    """Detailed product schema with relationships"""
    brand: Optional["BrandRead"] = None
    supplier: Optional["SupplierRead"] = None
    categories: List["CategoryRead"] = []
    
    @computed_field
    @property
    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0
    
    @computed_field
    @property
    def stock_status(self) -> str:
        if self.stock_quantity == 0:
            return "out_of_stock"
        elif self.stock_quantity < 10:
            return "low_stock"
        return "in_stock"

# Nested schemas
class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str

class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    logo_url: Optional[str] = None

# List schemas với pagination
class ProductList(BaseModel):
    """Product list với metadata"""
    items: List[ProductRead]
    total: int
    page: int
    size: int
    pages: int
    
    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
    
    @computed_field
    @property
    def has_prev(self) -> bool:
        return self.page > 1
```

### 2. Advanced Validation Patterns

```python
from pydantic import validator, root_validator, Field
from typing import Any, Dict

class ProductCreateAdvanced(ProductBase):
    """Advanced product creation với custom validation"""
    
    @validator('sku')
    def validate_sku_format(cls, v):
        """Validate SKU format"""
        import re
        if not re.match(r'^[A-Z]{2,3}-\d{4,6}$', v):
            raise ValueError('SKU must follow format: XX-1234 or XXX-123456')
        return v
    
    @validator('price')
    def validate_price_range(cls, v):
        """Validate price trong reasonable range"""
        if v > Decimal('999999.99'):
            raise ValueError('Price cannot exceed 999,999.99')
        return v
    
    @root_validator
    def validate_stock_price_relationship(cls, values):
        """Complex validation across multiple fields"""
        price = values.get('price')
        stock = values.get('stock_quantity', 0)
        
        # Expensive items should have lower stock
        if price and price > Decimal('1000.00') and stock > 100:
            raise ValueError(
                'High-value items (>$1000) should not have stock >100'
            )
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Premium Laptop",
                "sku": "LAP-001234",
                "price": "1299.99",
                "description": "High-performance laptop",
                "stock_quantity": 50,
                "brand_id": 1,
                "category_ids": [1, 2]
            }
        }
```

---

## Service Layer Architecture

### 1. Base Service Pattern

```python
# src/app/services/base.py
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from ..core.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service với common CRUD operations"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def create(
        self,
        db: AsyncSession,
        obj_in: CreateSchemaType,
        **kwargs
    ) -> ModelType:
        """Create new object"""
        obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in
        obj_data.update(kwargs)
        
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(
        self,
        db: AsyncSession,
        id: int,
        load_relationships: bool = False
    ) -> Optional[ModelType]:
        """Get object by ID"""
        query = select(self.model).where(self.model.id == id)
        
        if load_relationships:
            # Dynamic relationship loading
            query = self._add_relationship_loading(query)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get multiple objects với filtering và pagination"""
        query = select(self.model)
        
        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply ordering
        if order_by:
            query = self._apply_ordering(query, order_by)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update(
        self,
        db: AsyncSession,
        id: int,
        obj_in: UpdateSchemaType,
        **kwargs
    ) -> Optional[ModelType]:
        """Update object"""
        update_data = {}
        
        if hasattr(obj_in, 'model_dump'):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = {k: v for k, v in obj_in.items() if v is not None}
        
        update_data.update(kwargs)
        
        if not update_data:
            return await self.get(db, id)
        
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )
        
        result = await db.execute(query)
        await db.commit()
        return result.scalar_one_or_none()
    
    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Hard delete object"""
        query = delete(self.model).where(self.model.id == id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    
    async def soft_delete(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Soft delete object (if model supports it)"""
        if not hasattr(self.model, 'is_deleted'):
            raise NotImplementedError("Model doesn't support soft delete")
        
        return await self.update(
            db, id, 
            {"is_deleted": True, "deleted_at": datetime.now(UTC)}
        )
    
    # Helper methods
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query"""
        for field, value in filters.items():
            if hasattr(self.model, field):
                if isinstance(value, list):
                    query = query.where(getattr(self.model, field).in_(value))
                else:
                    query = query.where(getattr(self.model, field) == value)
        return query
    
    def _apply_ordering(self, query, order_by: str):
        """Apply ordering to query"""
        if order_by.startswith('-'):
            field = order_by[1:]
            if hasattr(self.model, field):
                query = query.order_by(getattr(self.model, field).desc())
        else:
            if hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by))
        return query
```

### 2. Specialized Service Implementation

```python
# src/app/services/product/product_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from decimal import Decimal

from ..base import BaseService
from ...models.product.product_model import Product, Category
from ...schemas.product.product_schemas import ProductCreate, ProductUpdate
from ...core.exceptions import NotFoundError, ValidationError

class ProductService(BaseService[Product, ProductCreate, ProductUpdate]):
    """Specialized product service"""
    
    def __init__(self):
        super().__init__(Product)
    
    async def create_with_categories(
        self,
        db: AsyncSession,
        product_in: ProductCreate,
        current_user_id: int
    ) -> Product:
        """Create product với categories"""
        # Extract category IDs
        category_ids = product_in.category_ids
        product_data = product_in.model_dump(exclude={'category_ids'})
        
        # Create product
        product = Product(**product_data, created_by_user_id=current_user_id)
        
        # Add categories if provided
        if category_ids:
            categories_query = select(Category).where(Category.id.in_(category_ids))
            result = await db.execute(categories_query)
            categories = result.scalars().all()
            
            if len(categories) != len(category_ids):
                raise ValidationError("Some categories not found")
            
            product.categories = categories
        
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product
    
    async def search_products(
        self,
        db: AsyncSession,
        query: str,
        category_id: Optional[int] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        in_stock_only: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Advanced product search"""
        # Base query với relationships
        base_query = select(Product).options(
            selectinload(Product.brand),
            selectinload(Product.categories)
        )
        
        # Text search
        if query:
            search_filter = or_(
                Product.name.ilike(f"%{query}%"),
                Product.description.ilike(f"%{query}%"),
                Product.sku.ilike(f"%{query}%")
            )
            base_query = base_query.where(search_filter)
        
        # Category filter
        if category_id:
            base_query = base_query.join(Product.categories).where(
                Category.id == category_id
            )
        
        # Price range
        if min_price:
            base_query = base_query.where(Product.price >= min_price)
        if max_price:
            base_query = base_query.where(Product.price <= max_price)
        
        # Stock filter
        if in_stock_only:
            base_query = base_query.where(Product.stock_quantity > 0)
        
        # Only active products
        base_query = base_query.where(Product.is_deleted == False)
        
        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination và execute
        products_query = base_query.offset(skip).limit(limit)
        result = await db.execute(products_query)
        products = result.scalars().all()
        
        return {
            "products": products,
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }
    
    async def get_low_stock_products(
        self,
        db: AsyncSession,
        threshold: int = 10
    ) -> List[Product]:
        """Get products với low stock"""
        query = select(Product).where(
            and_(
                Product.stock_quantity <= threshold,
                Product.stock_quantity > 0,
                Product.is_deleted == False
            )
        ).order_by(Product.stock_quantity.asc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_stock(
        self,
        db: AsyncSession,
        product_id: int,
        quantity_change: int,
        operation: str = "add"  # "add" or "subtract"
    ) -> Product:
        """Update product stock với validation"""
        product = await self.get(db, product_id)
        if not product:
            raise NotFoundError("Product not found")
        
        if operation == "add":
            new_quantity = product.stock_quantity + quantity_change
        elif operation == "subtract":
            new_quantity = product.stock_quantity - quantity_change
        else:
            raise ValidationError("Invalid operation")
        
        if new_quantity < 0:
            raise ValidationError("Insufficient stock")
        
        product.stock_quantity = new_quantity
        await db.commit()
        await db.refresh(product)
        return product
    
    async def get_product_analytics(
        self,
        db: AsyncSession,
        product_id: int
    ) -> Dict[str, Any]:
        """Get product analytics data"""
        # This would integrate với order system
        # Placeholder implementation
        product = await self.get(db, product_id, load_relationships=True)
        if not product:
            raise NotFoundError("Product not found")
        
        # Mock analytics - trong real app sẽ query từ orders, reviews, etc.
        return {
            "product": product,
            "total_sold": 0,  # Would query from orders
            "revenue": Decimal('0.00'),
            "average_rating": 0.0,  # Would query from reviews
            "view_count": 0,  # Would track từ analytics service
            "conversion_rate": 0.0
        }

# Service instance
product_service = ProductService()
```

---

## API Controller Best Practices

### 1. Advanced Controller Pattern

```python
# src/app/api/v1/products/product_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from typing import Annotated, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from ....core.db.database import async_get_db
from ....services.product.product_service import product_service
from ....schemas.product.product_schemas import (
    ProductCreate, ProductUpdate, ProductRead, ProductDetail, ProductList
)
from ....api.dependencies import get_current_user, get_current_superuser
from ....models.user import User
from ....core.exceptions import NotFoundError, ValidationError
from ....core.responses import create_response

router = APIRouter(prefix="/products", tags=["products"])

@router.post(
    "/",
    response_model=ProductDetail,
    status_code=201,
    summary="Create new product",
    description="Create a new product với categories"
)
async def create_product(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    product_in: ProductCreate,
    current_user: Annotated[User, Depends(get_current_superuser)]
) -> ProductDetail:
    """
    Create new product:
    
    - **name**: Product name (required)
    - **sku**: Stock keeping unit (required, unique)
    - **price**: Product price (required, > 0)
    - **description**: Product description (optional)
    - **stock_quantity**: Initial stock (default: 0)
    - **brand_id**: Brand ID (optional)
    - **category_ids**: List of category IDs
    """
    try:
        product = await product_service.create_with_categories(
            db, product_in, current_user.id
        )
        return ProductDetail.model_validate(product)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/",
    response_model=ProductList,
    summary="List products với filtering và search"
)
async def list_products(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    skip: Annotated[int, Query(ge=0, description="Skip items")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Limit items")] = 20,
    search: Annotated[Optional[str], Query(description="Search term")] = None,
    category_id: Annotated[Optional[int], Query(description="Category filter")] = None,
    min_price: Annotated[Optional[Decimal], Query(ge=0, description="Min price")] = None,
    max_price: Annotated[Optional[Decimal], Query(gt=0, description="Max price")] = None,
    in_stock_only: Annotated[bool, Query(description="Show only in-stock items")] = False,
) -> ProductList:
    """
    List products với advanced filtering:
    
    - **search**: Search trong name, description, SKU
    - **category_id**: Filter by category
    - **min_price** & **max_price**: Price range filter
    - **in_stock_only**: Show only products với stock > 0
    - **skip** & **limit**: Pagination
    """
    result = await product_service.search_products(
        db=db,
        query=search or "",
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        skip=skip,
        limit=limit
    )
    
    return ProductList(
        items=[ProductRead.model_validate(p) for p in result["products"]],
        total=result["total"],
        page=result["page"],
        size=result["size"],
        pages=result["pages"]
    )

@router.get(
    "/{product_id}",
    response_model=ProductDetail,
    summary="Get product by ID"
)
async def get_product(
    product_id: Annotated[int, Path(description="Product ID", gt=0)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> ProductDetail:
    """Get detailed product information by ID"""
    product = await product_service.get(db, product_id, load_relationships=True)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductDetail.model_validate(product)

@router.put(
    "/{product_id}",
    response_model=ProductDetail,
    summary="Update product"
)
async def update_product(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    product_id: Annotated[int, Path(gt=0)],
    product_update: ProductUpdate,
    current_user: Annotated[User, Depends(get_current_superuser)]
) -> ProductDetail:
    """Update product information"""
    try:
        product = await product_service.update(
            db, product_id, product_update, updated_by_user_id=current_user.id
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return ProductDetail.model_validate(product)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch(
    "/{product_id}/stock",
    response_model=ProductRead,
    summary="Update product stock"
)
async def update_product_stock(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    product_id: Annotated[int, Path(gt=0)],
    quantity_change: Annotated[int, Body(description="Quantity to add/subtract")],
    operation: Annotated[str, Body(regex="^(add|subtract)$")] = "add",
    current_user: Annotated[User, Depends(get_current_superuser)]
) -> ProductRead:
    """
    Update product stock:
    
    - **quantity_change**: Number to add or subtract
    - **operation**: "add" hoặc "subtract"
    """
    try:
        product = await product_service.update_stock(
            db, product_id, quantity_change, operation
        )
        return ProductRead.model_validate(product)
    except (NotFoundError, ValidationError) as e:
        status_code = 404 if isinstance(e, NotFoundError) else 400
        raise HTTPException(status_code=status_code, detail=str(e))

@router.get(
    "/analytics/low-stock",
    response_model=List[ProductRead],
    summary="Get low stock products"
)
async def get_low_stock_products(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    threshold: Annotated[int, Query(ge=1, le=100)] = 10,
    current_user: Annotated[User, Depends(get_current_superuser)]
) -> List[ProductRead]:
    """Get products với stock below threshold"""
    products = await product_service.get_low_stock_products(db, threshold)
    return [ProductRead.model_validate(p) for p in products]

@router.delete(
    "/{product_id}",
    status_code=204,
    summary="Delete product"
)
async def delete_product(
    product_id: Annotated[int, Path(gt=0)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[User, Depends(get_current_superuser)],
    hard_delete: Annotated[bool, Query(description="Permanently delete")] = False
) -> None:
    """Delete product (soft delete by default)"""
    try:
        if hard_delete:
            success = await product_service.delete(db, product_id)
        else:
            product = await product_service.soft_delete(db, product_id)
            success = product is not None
        
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Bulk operations
@router.post(
    "/bulk/import",
    response_model=dict,
    summary="Bulk import products"
)
async def bulk_import_products(
    products: List[ProductCreate],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[User, Depends(get_current_superuser)]
) -> dict:
    """Bulk import products từ list"""
    results = {"success": 0, "failed": 0, "errors": []}
    
    for i, product_data in enumerate(products):
        try:
            await product_service.create_with_categories(
                db, product_data, current_user.id
            )
            results["success"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Row {i+1}: {str(e)}")
    
    return results
```

---

## Advanced Query Patterns

### 1. Complex Filtering và Sorting

```python
# src/app/services/advanced_queries.py
from sqlalchemy import select, func, case, text, and_, or_
from sqlalchemy.orm import aliased, contains_eager
from typing import Dict, Any, List, Optional

class AdvancedQueryService:
    """Service for complex database queries"""
    
    async def get_products_with_stats(
        self,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get products với calculated statistics"""
        
        # Subquery for order statistics
        OrderProduct = aliased("OrderProduct")  # Assume this exists
        order_stats = (
            select(
                OrderProduct.product_id,
                func.sum(OrderProduct.quantity).label("total_sold"),
                func.sum(OrderProduct.quantity * OrderProduct.unit_price).label("total_revenue"),
                func.count(OrderProduct.order_id).label("order_count")
            )
            .group_by(OrderProduct.product_id)
            .subquery()
        )
        
        # Main query với joins
        query = (
            select(
                Product.id,
                Product.name,
                Product.price,
                Product.stock_quantity,
                Brand.name.label("brand_name"),
                func.coalesce(order_stats.c.total_sold, 0).label("total_sold"),
                func.coalesce(order_stats.c.total_revenue, 0).label("total_revenue"),
                func.coalesce(order_stats.c.order_count, 0).label("order_count"),
                # Calculated fields
                case(
                    (Product.stock_quantity > 50, "high"),
                    (Product.stock_quantity > 10, "medium"),
                    else_="low"
                ).label("stock_level"),
                # Performance score calculation
                (
                    func.coalesce(order_stats.c.total_sold, 0) * 0.4 +
                    func.coalesce(order_stats.c.order_count, 0) * 0.3 +
                    (Product.stock_quantity / 100.0) * 0.3
                ).label("performance_score")
            )
            .select_from(
                Product
                .outerjoin(Brand, Product.brand_id == Brand.id)
                .outerjoin(order_stats, Product.id == order_stats.c.product_id)
            )
            .where(Product.is_deleted == False)
        )
        
        # Apply dynamic filters
        if filters:
            if "brand_ids" in filters:
                query = query.where(Product.brand_id.in_(filters["brand_ids"]))
            
            if "min_performance_score" in filters:
                having_clause = text(f"performance_score >= {filters['min_performance_score']}")
                query = query.having(having_clause)
        
        result = await db.execute(query)
        return [dict(row._mapping) for row in result]
    
    async def get_category_hierarchy_with_counts(
        self,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get category hierarchy với product counts"""
        
        # Recursive CTE for category hierarchy
        cte = (
            select(
                Category.id,
                Category.name,
                Category.parent_id,
                func.cast(Category.name, String).label("path"),
                func.cast(0, Integer).label("level")
            )
            .where(Category.parent_id.is_(None))
            .cte(name="category_hierarchy", recursive=True)
        )
        
        cte_recursive = (
            select(
                Category.id,
                Category.name,
                Category.parent_id,
                (cte.c.path + " > " + Category.name).label("path"),
                (cte.c.level + 1).label("level")
            )
            .select_from(
                Category.join(cte, Category.parent_id == cte.c.id)
            )
        )
        
        cte = cte.union_all(cte_recursive)
        
        # Join với product counts
        product_counts = (
            select(
                func.unnest(func.array_agg(Category.id)).label("category_id"),
                func.count(Product.id).label("product_count")
            )
            .select_from(
                Product.join(
                    product_categories,
                    Product.id == product_categories.c.product_id
                ).join(
                    Category,
                    product_categories.c.category_id == Category.id
                )
            )
            .where(Product.is_deleted == False)
            .group_by(Product.id)
            .subquery()
        )
        
        final_query = (
            select(
                cte.c.id,
                cte.c.name,
                cte.c.parent_id,
                cte.c.path,
                cte.c.level,
                func.coalesce(product_counts.c.product_count, 0).label("product_count")
            )
            .select_from(
                cte.outerjoin(
                    product_counts,
                    cte.c.id == product_counts.c.category_id
                )
            )
            .order_by(cte.c.path)
        )
        
        result = await db.execute(final_query)
        return [dict(row._mapping) for row in result]
    
    async def search_products_advanced(
        self,
        db: AsyncSession,
        search_term: str,
        filters: Dict[str, Any]
    ) -> List[Product]:
        """Advanced full-text search với ranking"""
        
        # Create search vector (PostgreSQL specific)
        search_query = text("""
            SELECT p.*, 
                   ts_rank(
                       to_tsvector('english', 
                           coalesce(p.name, '') || ' ' || 
                           coalesce(p.description, '') || ' ' ||
                           coalesce(b.name, '')
                       ),
                       plainto_tsquery('english', :search_term)
                   ) as search_rank
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE to_tsvector('english', 
                      coalesce(p.name, '') || ' ' || 
                      coalesce(p.description, '') || ' ' ||
                      coalesce(b.name, '')
                  ) @@ plainto_tsquery('english', :search_term)
            AND p.is_deleted = false
            ORDER BY search_rank DESC
            LIMIT 50
        """)
        
        result = await db.execute(search_query, {"search_term": search_term})
        
        # Convert to Product objects (simplified)
        products = []
        for row in result:
            product = Product()
            for key, value in row._mapping.items():
                if hasattr(product, key) and key != 'search_rank':
                    setattr(product, key, value)
            products.append(product)
        
        return products
```

---

## Error Handling và Validation

### 1. Custom Exception System

```python
# src/app/core/exceptions.py
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class AppException(Exception):
    """Base application exception"""
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppException):
    """Validation related errors"""
    pass

class NotFoundError(AppException):
    """Resource not found errors"""
    pass

class DuplicateError(AppException):
    """Duplicate resource errors"""
    pass

class PermissionError(AppException):
    """Permission related errors"""
    pass

class BusinessRuleError(AppException):
    """Business logic violations"""
    pass

# Exception handlers
async def app_exception_handler(request, exc: AppException):
    """Global exception handler"""
    status_map = {
        ValidationError: status.HTTP_400_BAD_REQUEST,
        NotFoundError: status.HTTP_404_NOT_FOUND,
        DuplicateError: status.HTTP_409_CONFLICT,
        PermissionError: status.HTTP_403_FORBIDDEN,
        BusinessRuleError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    
    status_code = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "details": exc.details,
                "type": exc.__class__.__name__
            }
        }
    )
```

### 2. Advanced Validation Patterns

```python
# src/app/core/validators.py
from typing import Any, Callable, List, Optional
from pydantic import validator
from decimal import Decimal
import re

class ValidationRules:
    """Collection of reusable validation rules"""
    
    @staticmethod
    def validate_price(value: Decimal) -> Decimal:
        """Validate price rules"""
        if value <= 0:
            raise ValueError("Price must be greater than 0")
        if value > Decimal('999999.99'):
            raise ValueError("Price cannot exceed 999,999.99")
        return value
    
    @staticmethod
    def validate_sku(value: str) -> str:
        """Validate SKU format"""
        if not re.match(r'^[A-Z]{2,3}-\d{4,8}$', value):
            raise ValueError(
                "SKU must follow format: XX-1234 or XXX-12345678"
            )
        return value.upper()
    
    @staticmethod
    def validate_email(value: str) -> str:
        """Enhanced email validation"""
        email_regex = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        if not email_regex.match(value):
            raise ValueError("Invalid email format")
        return value.lower()
    
    @staticmethod
    def validate_phone(value: str) -> str:
        """Phone number validation"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', value)
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError("Phone number must be 10-15 digits")
        return digits_only

# Custom validator decorators
def business_rule_validator(rule_func: Callable) -> Callable:
    """Decorator for business rule validation"""
    def decorator(cls, v, values, **kwargs):
        try:
            return rule_func(v, values)
        except Exception as e:
            raise ValueError(f"Business rule violation: {str(e)}")
    return decorator

# Example usage in schema
class ProductCreateAdvanced(BaseModel):
    name: str
    sku: str
    price: Decimal
    cost: Optional[Decimal] = None
    
    # Apply validation rules
    _validate_price = validator('price', allow_reuse=True)(
        ValidationRules.validate_price
    )
    
    _validate_sku = validator('sku', allow_reuse=True)(
        ValidationRules.validate_sku
    )
    
    @business_rule_validator
    def validate_profit_margin(cost: Decimal, values: Dict[str, Any]) -> Decimal:
        """Ensure minimum profit margin"""
        price = values.get('price')
        if price and cost:
            margin = (price - cost) / price
            if margin < Decimal('0.1'):  # 10% minimum margin
                raise ValueError("Profit margin must be at least 10%")
        return cost
    
    @root_validator
    def validate_business_rules(cls, values):
        """Complex business rule validation"""
        name = values.get('name', '')
        price = values.get('price')
        
        # Luxury items rule
        if 'luxury' in name.lower() and price and price < Decimal('100.00'):
            raise ValueError("Luxury items must be priced above $100")
        
        return values
```

---

## Performance Optimization

### 1. Query Optimization Strategies

```python
# src/app/core/database_optimizations.py
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
import time
import logging

logger = logging.getLogger(__name__)

# Query performance monitoring
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries"""
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time"""
    total = time.time() - context._query_start_time
    if total > 0.5:  # Log queries taking > 500ms
        logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")

# Optimized query patterns
class OptimizedQueries:
    """Collection of optimized query patterns"""
    
    @staticmethod
    async def get_products_with_minimal_joins(
        db: AsyncSession,
        limit: int = 100
    ) -> List[Product]:
        """Optimized product query với selective loading"""
        
        # Use selectinload for better performance với relationships
        query = (
            select(Product)
            .options(
                selectinload(Product.brand),  # Separate query, better than joinedload
                selectinload(Product.categories),
                # Don't load reviews by default (use lazy loading)
            )
            .where(Product.is_deleted == False)
            .limit(limit)
        )
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def bulk_update_products(
        db: AsyncSession,
        updates: Dict[int, Dict[str, Any]]
    ) -> int:
        """Efficient bulk update"""
        
        # Use bulk update instead of individual updates
        if not updates:
            return 0
        
        cases = []
        product_ids = list(updates.keys())
        
        # Build CASE statements for each field
        for field in ['price', 'stock_quantity']:  # Example fields
            case_stmt = case(
                *[(Product.id == pid, updates[pid].get(field, getattr(Product, field))) 
                  for pid in product_ids if field in updates[pid]],
                else_=getattr(Product, field)
            )
            cases.append({field: case_stmt})
        
        if cases:
            update_stmt = (
                update(Product)
                .where(Product.id.in_(product_ids))
                .values(**{k: v for case in cases for k, v in case.items()})
            )
            
            result = await db.execute(update_stmt)
            await db.commit()
            return result.rowcount
        
        return 0
    
    @staticmethod
    async def get_paginated_results_optimized(
        db: AsyncSession,
        query: select,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Optimized pagination với cursor-based option"""
        
        # For large datasets, use cursor-based pagination
        if page * size > 10000:  # Switch to cursor-based for large offsets
            # Implement cursor-based pagination
            # This is more efficient for large datasets
            pass
        
        # Standard offset-based pagination
        offset = (page - 1) * size
        
        # Get total count efficiently
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        paginated_query = query.offset(offset).limit(size)
        result = await db.execute(paginated_query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }

# Database connection pooling configuration
class DatabaseConfig:
    """Optimized database configuration"""
    
    @staticmethod
    def get_engine_config():
        """Return optimized engine configuration"""
        return {
            "pool_size": 20,  # Connection pool size
            "max_overflow": 30,  # Additional connections
            "pool_pre_ping": True,  # Verify connections
            "pool_recycle": 3600,  # Recycle connections every hour
            "echo": False,  # Don't log all queries in production
            "future": True,  # Use SQLAlchemy 2.0 style
            # Connection arguments
            "connect_args": {
                "server_settings": {
                    "application_name": "fastapi_app",
                    "jit": "off",  # Disable JIT for consistent performance
                },
                "command_timeout": 60,
            }
        }

# Caching layer
from functools import wraps
import json
import hashlib

def cache_result(expire_time: int = 300):
    """Decorator để cache query results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Try to get from cache (implement cache backend - Redis, etc.)
            # cached_result = await cache_backend.get(cache_key)
            # if cached_result:
            #     return json.loads(cached_result)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            # await cache_backend.setex(cache_key, expire_time, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator
```

### 2. API Performance Patterns

```python
# src/app/core/performance.py
from fastapi import BackgroundTasks
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
    
    async def parallel_database_calls(
        self,
        db: AsyncSession,
        calls: List[tuple]  # List of (function, args, kwargs)
    ) -> List[Any]:
        """Execute multiple database calls in parallel"""
        tasks = []
        for func, args, kwargs in calls:
            task = asyncio.create_task(func(db, *args, **kwargs))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def background_data_processing(
        self,
        background_tasks: BackgroundTasks,
        data: List[Dict[str, Any]]
    ):
        """Process data in background"""
        background_tasks.add_task(self._process_data_heavy, data)
    
    def _process_data_heavy(self, data: List[Dict[str, Any]]):
        """Heavy data processing trong background"""
        # Example: Generate reports, send emails, etc.
        pass
    
    async def batch_process_items(
        self,
        items: List[Any],
        process_func: callable,
        batch_size: int = 100
    ) -> List[Any]:
        """Process items in batches để avoid memory issues"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[process_func(item) for item in batch],
                return_exceptions=True
            )
            results.extend(batch_results)
        
        return results

# Response caching middleware
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """Cache GET responses"""
    
    def __init__(self, app, cache_time: int = 300):
        super().__init__(app)
        self.cache_time = cache_time
        self.cache = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Generate cache key
        cache_key = f"{request.url.path}:{str(request.query_params)}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_time:
                return Response(
                    content=cached_data["body"],
                    status_code=cached_data["status_code"],
                    headers=cached_data["headers"]
                )
        
        # Execute request
        response = await call_next(request)
        
        # Cache successful responses
        if 200 <= response.status_code < 300:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            self.cache[cache_key] = (
                {
                    "body": body,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                },
                time.time()
            )
            
            return Response(
                content=body,
                status_code=response.status_code,
                headers=response.headers
            )
        
        return response
```

---

## Tổng Kết

Hướng dẫn này cover các aspects chính của việc xây dựng model và API phức tạp:

### Key Takeaways:

1. **Model Design**: Sử dụng mixins, proper relationships, và dataclass configuration
2. **Schema Patterns**: Layered schemas với validation và computed fields  
3. **Service Layer**: Generic base service với specialized implementations
4. **API Controllers**: RESTful design với proper error handling
5. **Advanced Queries**: Complex filtering, joins, và aggregations
6. **Performance**: Query optimization, caching, và async patterns

### Best Practices:

- ✅ Separation of concerns (Model/Schema/Service/Controller)
- ✅ Proper error handling và validation
- ✅ Performance optimization từ đầu
- ✅ Comprehensive documentation
- ✅ Type hints everywhere
- ✅ Async/await patterns
- ✅ Proper relationship loading strategies
- ✅ Caching và background tasks

Áp dụng các patterns này sẽ giúp bạn build được APIs scalable và maintainable! 🚀