# 🎯 HƯỚNG DẪN ĐƠN GIẢN: TỪ MODEL ĐẾN API

## ⚠️ QUY TẮC QUAN TRỌNG ĐỂ TRÁNH LỖI

### 1. **Relationship Configuration - ĐƠN GIẢN LÀ TỐT NHẤT**

```python
# ✅ ĐÚNG - Đơn giản, ít lỗi
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    
    # Relationship đơn giản nhất
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author"
    )

class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Relationship đơn giản
    author: Mapped["User"] = relationship(
        back_populates="posts"
    )

# ❌ SAI - Quá phức tạp, dễ lỗi
class User(Base):
    posts: Mapped[list["Post"]] = relationship(
        "Post",  # ❌ Không cần string name
        back_populates="author",
        foreign_keys="Post.author_id",  # ❌ Không cần
        lazy="selectinload",  # ❌ Để mặc định
        init=False  # ✅ Cái này OK
    )
```
### 2. **Import Models - QUAN TRỌNG**

```python
# 📁 models/__init__.py - PHẢI import đầy đủ
from .user import User
from .post import Post
from .chats import Message, Conversations  # Import chat models

# 📁 models/chats/__init__.py - PHẢI có file này
from .messages import Message
from .conversations import Conversations
from .conversation_members import ConversationMembers

__all__ = ["Message", "Conversations", "ConversationMembers"]
```

### 3. **Foreign Key - CHỈ CẦN CƠ BẢN**

```python
# ✅ ĐÚNG
sender_id: Mapped[int] = mapped_column(
    ForeignKey("users.id"),
    nullable=False
)

# ❌ SAI - Thừa thãi
sender_id: Mapped[int] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
    nullable=False,
    index=True,  # SQLAlchemy tự tạo index cho FK
)
```

---

## 📝 QUY TRÌNH 5 BƯỚC: TỪ MODEL ĐẾN API

### **BƯỚC 1: Tạo Model**

```python
# 📁 src/app/models/note.py
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, UTC
from ..core.db.database import Base

class Note(Base):
    __tablename__ = "notes"
    
    # 1️⃣ Columns - các cột trong database
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    
    # 2️⃣ Foreign Key - liên kết với bảng khác
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    
    # 3️⃣ Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default_factory=lambda: datetime.now(UTC)
    )
    
    # 4️⃣ Relationship - ĐỪNG overthink, càng đơn giản càng tốt
    owner: Mapped["User"] = relationship(back_populates="notes")
```

**Cập nhật User model:**
```python
# 📁 src/app/models/user.py
class User(Base):
    # ... existing fields ...
    
    # Thêm relationship
    notes: Mapped[list["Note"]] = relationship(back_populates="owner")
```

**Import vào models/__init__.py:**
```python
# 📁 src/app/models/__init__.py
from .note import Note  # Thêm dòng này
```

### **BƯỚC 2: Tạo Schema**

```python
# 📁 src/app/schemas/note.py
from pydantic import BaseModel
from datetime import datetime

# 1️⃣ Base Schema - các field chung
class NoteBase(BaseModel):
    title: str
    content: str

# 2️⃣ Create Schema - để tạo mới
class NoteCreate(NoteBase):
    pass  # Không cần user_id, lấy từ current_user

# 3️⃣ Update Schema - để update (tất cả optional)
class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None

# 4️⃣ Read Schema - response từ API
class NoteRead(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}  # Quan trọng!
```

### **BƯỚC 3: Tạo CRUD**

```python
# 📁 src/app/crud/crud_note.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.note import Note
from ..schemas.note import NoteCreate, NoteUpdate

class NoteCRUD:
    
    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: NoteCreate, 
        user_id: int
    ) -> Note:
        """Tạo note mới"""
        note = Note(
            title=obj_in.title,
            content=obj_in.content,
            user_id=user_id
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note
    
    async def get(self, db: AsyncSession, id: int) -> Note | None:
        """Lấy note theo ID"""
        result = await db.execute(
            select(Note).where(Note.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(
        self, 
        db: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[Note]:
        """Lấy tất cả notes của user"""
        result = await db.execute(
            select(Note)
            .where(Note.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Note, 
        obj_in: NoteUpdate
    ) -> Note:
        """Update note"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """Xóa note"""
        note = await self.get(db, id)
        if note:
            await db.delete(note)
            await db.commit()
            return True
        return False

# Singleton instance
crud_note = NoteCRUD()
```

### **BƯỚC 4: Tạo API Endpoints**

```python
# 📁 src/app/api/v1/notes.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...api.dependencies import get_current_user
from ...crud.crud_note import crud_note
from ...schemas.note import NoteCreate, NoteRead, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    note_in: NoteCreate,
) -> NoteRead:
    """Tạo note mới"""
    note = await crud_note.create(
        db=db, 
        obj_in=note_in, 
        user_id=current_user["id"]
    )
    return NoteRead.model_validate(note)


@router.get("/", response_model=list[NoteRead])
async def get_my_notes(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
) -> list[NoteRead]:
    """Lấy tất cả notes của user hiện tại"""
    notes = await crud_note.get_by_user(
        db=db, 
        user_id=current_user["id"], 
        skip=skip, 
        limit=limit
    )
    return [NoteRead.model_validate(note) for note in notes]


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    note_id: int,
) -> NoteRead:
    """Lấy chi tiết note"""
    note = await crud_note.get(db=db, id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Kiểm tra quyền sở hữu
    if note.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return NoteRead.model_validate(note)


@router.put("/{note_id}", response_model=NoteRead)
async def update_note(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    note_id: int,
    note_in: NoteUpdate,
) -> NoteRead:
    """Update note"""
    note = await crud_note.get(db=db, id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    if note.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_note = await crud_note.update(db=db, db_obj=note, obj_in=note_in)
    return NoteRead.model_validate(updated_note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    note_id: int,
):
    """Xóa note"""
    note = await crud_note.get(db=db, id=note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    if note.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await crud_note.delete(db=db, id=note_id)
```

### **BƯỚC 5: Register Router**

```python
# 📁 src/app/api/v1/__init__.py
from fastapi import APIRouter
from .notes import router as notes_router  # Thêm dòng này

router = APIRouter()

# Register routers
router.include_router(notes_router)  # Thêm dòng này
# ... other routers ...
```

---

## 🔧 MIGRATION DATABASE

```bash
# 1. Tạo migration
cd src
alembic revision --autogenerate -m "Add notes table"

# 2. Apply migration
alembic upgrade head
```

---

## 📊 RELATIONSHIPS - CÁC LOẠI QUAN HỆ

### **1:N (One-to-Many) - MỘT USER CÓ NHIỀU NOTES**

```python
# User Model (One side)
class User(Base):
    notes: Mapped[list["Note"]] = relationship(back_populates="owner")

# Note Model (Many side)
class Note(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    owner: Mapped["User"] = relationship(back_populates="notes")
```

### **N:N (Many-to-Many) - USER CÓ NHIỀU ROLES**

```python
# Association Table
from sqlalchemy import Table, Column, Integer, ForeignKey

user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# User Model
class User(Base):
    roles: Mapped[list["Role"]] = relationship(
        secondary=user_roles,
        back_populates="users"
    )

# Role Model
class Role(Base):
    users: Mapped[list["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles"
    )
```

### **1:1 (One-to-One) - USER CÓ MỘT PROFILE**

```python
# User Model
class User(Base):
    profile: Mapped["UserProfile"] = relationship(
        back_populates="user",
        uselist=False  # Quan trọng cho 1:1
    )

# UserProfile Model
class UserProfile(Base):
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True  # Đảm bảo 1:1
    )
    user: Mapped["User"] = relationship(back_populates="profile")
```

### **Self-Referencing - COMMENT REPLY COMMENT**

```python
class Comment(Base):
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id"))
    
    # Parent comment
    parent: Mapped["Comment | None"] = relationship(
        remote_side=[id],  # Chỉ định side nào là remote
        back_populates="replies"
    )
    
    # Child comments
    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent"
    )
```

---

## ⚡ EAGER LOADING - LOAD RELATIONSHIPS

```python
from sqlalchemy.orm import selectinload, joinedload

# Trong CRUD method
async def get_with_owner(self, db: AsyncSession, id: int) -> Note | None:
    """Lấy note kèm thông tin owner"""
    result = await db.execute(
        select(Note)
        .options(selectinload(Note.owner))  # Load relationship
        .where(Note.id == id)
    )
    return result.scalar_one_or_none()
```

---

## 🎯 CHECKLIST KHI TẠO FEATURE MỚI

- [ ] ✅ Model đã có trong `models/__init__.py`
- [ ] ✅ Relationship đơn giản, không dùng `lazy=`, `foreign_keys=`
- [ ] ✅ Schema có đầy đủ: Base, Create, Update, Read
- [ ] ✅ Schema Read có `model_config = {"from_attributes": True}`
- [ ] ✅ CRUD có đầy đủ: create, get, get_multi, update, delete
- [ ] ✅ API endpoints kiểm tra quyền sở hữu
- [ ] ✅ Router đã register trong `api/v1/__init__.py`
- [ ] ✅ Migration đã chạy

---

## 🐛 TROUBLESHOOTING

### Lỗi: `'Message' is not defined`
**Nguyên nhân:** Model chưa được import vào `models/__init__.py`
**Fix:**
```python
# models/__init__.py
from .chats import Message  # Thêm import
```

### Lỗi: `Can't create Index on table`
**Nguyên nhân:** Cú pháp sai trong model (dấu phẩy thừa)
**Fix:**
```python
# ❌ SAI
field: Mapped[bool] = (mapped_column(default=False),)

# ✅ ĐÚNG
field: Mapped[bool] = mapped_column(default=False)
```

### Lỗi: `foreign_keys='Model.field' failed to locate`
**Nguyên nhân:** Không nên dùng string trong `foreign_keys`
**Fix:**
```python
# ❌ SAI
relationship("Model", foreign_keys="Model.field_id")

# ✅ ĐÚNG - bỏ foreign_keys
relationship(back_populates="field")
```

---

## 💡 LỜI KHUYÊN

1. **ĐỪNG phức tạp hóa relationships** - SQLAlchemy đủ thông minh
2. **LUÔN kiểm tra import** trong `__init__.py`
3. **SỬ DỤNG default SQLAlchemy behavior** - đừng config quá nhiều
4. **TEST từng bước** - đừng viết hết rồi mới chạy
5. **ĐỌC lỗi kỹ** - SQLAlchemy error messages rất chi tiết

---

Quy trình này đã test và hoạt động ổn định. Nếu gặp lỗi, hãy:
1. Kiểm tra imports trong `__init__.py`
2. Đơn giản hóa relationships
3. Xóa các tham số không cần thiết
