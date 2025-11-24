# Hướng dẫn Authentication và lấy thông tin User hiện tại

## Tổng quan
Authentication trong FastAPI được triển khai sử dụng JWT (JSON Web Token) để xác thực người dùng và lấy thông tin user hiện tại đang call API.

## Kiến trúc Authentication

### 1. Cấu trúc Files

```
src/app/
├── core/
│   ├── auth.py          # Authentication dependencies
│   ├── security.py      # JWT token utilities
│   └── config.py        # Security settings
├── api/v1/
│   ├── articles.py      # API endpoints với auth
│   └── auth.py          # Login/logout endpoints
└── models/
    └── user.py          # User model
```

### 2. Authentication Dependencies (core/auth.py)

Tạo các dependency functions để lấy thông tin user hiện tại:

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.core.config import settings
from app.core.db.session import async_get_db
from app.crud.user import user_crud
from app.models.user import User

# HTTP Bearer token scheme
security = HTTPBearer()

async def get_current_user(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = await user_crud.get(db, id=user_id)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current active user (not disabled)"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user

async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
```

## Cách sử dụng trong API Endpoints

### 1. Import Dependencies

```python
from typing import Annotated
from fastapi import Depends
from app.core.auth import get_current_active_user, get_current_superuser
from app.models.user import User
```

### 2. Sử dụng trong API Functions

#### Lấy User ID hiện tại:

```python
@router.post("/", response_model=ArticleResponseSimple, status_code=201)
async def create_article(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    article_in: ArticleCreate,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ArticleResponseSimple:
    """Create new article"""
    # Lấy ID của user hiện tại
    user_id = current_user.id
    
    # Tạo article với author_id = user_id hiện tại
    article = await article_crud.create(
        db, 
        obj_in=article_in, 
        author_id=user_id
    )
    return ArticleResponseSimple.model_validate(article)
```

#### Kiểm tra quyền ownership:

```python
@router.put("/{article_id}", response_model=ArticleResponseSimple)
async def update_article(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    article_id: int,
    article_in: ArticleUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ArticleResponseSimple:
    """Update article"""
    # Lấy article từ database
    article = await article_crud.get(db, id=article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Kiểm tra ownership: chỉ author hoặc superuser mới được update
    if article.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update article
    updated_article = await article_crud.update(db, db_obj=article, obj_in=article_in)
    return ArticleResponseSimple.model_validate(updated_article)
```

#### Endpoint chỉ dành cho Superuser:

```python
@router.delete("/admin/{user_id}", status_code=204)
async def admin_delete_user(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user_id: int,
    current_user: Annotated[User, Depends(get_current_superuser)]  # Chỉ superuser
) -> None:
    """Admin delete user - superuser only"""
    success = await user_crud.delete(db, id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
```

## Các loại Authentication Dependencies

### 1. `get_current_user`
- Lấy user từ JWT token
- Không kiểm tra trạng thái active
- Sử dụng khi cần user info cơ bản

### 2. `get_current_active_user` 
- Lấy user từ JWT token
- Kiểm tra user phải active (is_active=True)
- **Sử dụng phổ biến nhất** cho các API thông thường

### 3. `get_current_superuser`
- Lấy user từ JWT token  
- Kiểm tra user phải là superuser (is_superuser=True)
- Sử dụng cho admin endpoints

## Quy trình Authentication

### 1. Client gửi request với Bearer token:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. FastAPI dependency system:
1. `HTTPBearer()` extract token từ Authorization header
2. `get_current_user()` decode JWT token và lấy user_id
3. Query database để lấy User object
4. `get_current_active_user()` kiểm tra user.is_active
5. Trả về User object cho API endpoint

### 3. API endpoint sử dụng user info:
```python
# Lấy user ID
user_id = current_user.id

# Lấy thông tin user khác
user_email = current_user.email
user_name = current_user.full_name
is_admin = current_user.is_superuser
```

## Ví dụ thực tế

### Article API với Authentication:

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db.session import async_get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.crud.article import article_crud
from app.schemas.article import ArticleCreate, ArticleResponseSimple

router = APIRouter(prefix="/articles", tags=["articles"])

@router.post("/", response_model=ArticleResponseSimple, status_code=201)
async def create_article(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    article_in: ArticleCreate,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ArticleResponseSimple:
    """Create new article"""
    # Tự động gán author_id = current_user.id
    article = await article_crud.create(
        db, 
        obj_in=article_in, 
        author_id=current_user.id
    )
    return ArticleResponseSimple.model_validate(article)

@router.get("/my-articles", response_model=list[ArticleResponseSimple])
async def get_my_articles(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> list[ArticleResponseSimple]:
    """Get articles của user hiện tại"""
    articles = await article_crud.get_by_author(db, author_id=current_user.id)
    return [ArticleResponseSimple.model_validate(article) for article in articles]
```

## Error Handling

### 1. Token không hợp lệ:
```json
{
    "detail": "Could not validate credentials",
    "status_code": 401
}
```

### 2. User không active:
```json
{
    "detail": "Inactive user", 
    "status_code": 400
}
```

### 3. Không đủ quyền:
```json
{
    "detail": "Not enough permissions",
    "status_code": 403
}
```

## Best Practices

### 1. Luôn sử dụng `get_current_active_user`
- Đảm bảo user đang active
- Tránh inactive users call API

### 2. Kiểm tra ownership khi cần:
```python
if resource.owner_id != current_user.id and not current_user.is_superuser:
    raise HTTPException(status_code=403, detail="Not enough permissions")
```

### 3. Sử dụng Type Hints:
```python
current_user: Annotated[User, Depends(get_current_active_user)]
```

### 4. Tách riêng admin endpoints:
```python
# Public endpoint
@router.get("/articles")
async def get_articles(): ...

# User endpoint  
@router.post("/articles")
async def create_article(current_user: Annotated[User, Depends(get_current_active_user)]): ...

# Admin endpoint
@router.delete("/admin/articles/{id}")
async def admin_delete_article(current_user: Annotated[User, Depends(get_current_superuser)]): ...
```

## Kết luận

Với cách triển khai này, bạn có thể:
- **Lấy ID user hiện tại**: `current_user.id`
- **Kiểm tra quyền truy cập**: So sánh `current_user.id` với owner của resource
- **Phân quyền admin**: Sử dụng `get_current_superuser` dependency
- **Bảo mật endpoint**: Tự động reject các request không có token hợp lệ

Mỗi API call sẽ tự động extract user information từ JWT token và cung cấp `current_user` object để sử dụng trong business logic.