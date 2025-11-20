# 📝 THỰC HÀNH: TẠO FEATURE "NOTES" 

## 🎯 Mục tiêu: Tạo hệ thống ghi chú cá nhân

### Yêu cầu tính năng:
- Users có thể tạo/sửa/xóa notes
- Notes có thể có tags để phân loại  
- Tìm kiếm notes theo title/content
- Đánh dấu notes quan trọng (pinned)
- Soft delete với khả năng restore

---

## 🗄️ BƯỚC 1: TẠO DATABASE MODELS

```python
# src/app/models/note.py
from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime, JSON, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum
from ..core.db.database import Base

# Many-to-many relationship table cho tags
note_tags = Table(
    'note_tags',
    Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Note(Base):
    __tablename__ = "notes"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Properties
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Owner
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # Metadata cho formatting, attachments, etc.
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Soft Delete
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notes")
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=note_tags, back_populates="notes")

class Tag(Base):
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color code
    
    # Owner (tags có thể personal hoặc global)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    
    # Relationships  
    user: Mapped[Optional["User"]] = relationship("User", back_populates="tags")
    notes: Mapped[List["Note"]] = relationship("Note", secondary=note_tags, back_populates="tags")
```

### 📋 Cập nhật User Model để add relationships

```python
# Thêm vào src/app/models/user.py
class User(Base):
    # ... existing fields ...
    
    # Thêm relationships mới
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="user")
    tags: Mapped[List["Tag"]] = relationship("Tag", back_populates="user")
```

---

## 📋 BƯỚC 2: TẠO PYDANTIC SCHEMAS

```python
# src/app/schemas/note.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# TAG SCHEMAS
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$", description="Hex color code")

class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    color: Optional[str]
    is_global: bool

# NOTE INPUT SCHEMAS
class NoteCreateBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    content: str = Field(..., min_length=1, description="Note content")
    is_pinned: bool = Field(False, description="Pin note to top")
    is_favorite: bool = Field(False, description="Mark as favorite")
    tag_ids: List[int] = Field([], description="List of tag IDs")
    metadata: Optional[dict] = Field(None, description="Additional metadata")

class NoteCreate(NoteCreateBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    tag_ids: Optional[List[int]] = None
    metadata: Optional[dict] = None

# NOTE OUTPUT SCHEMAS  
class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    content: str
    is_pinned: bool
    is_favorite: bool
    user_id: int
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

class NoteReadWithTags(NoteRead):
    tags: List[TagRead] = []

class NoteReadDetailed(NoteReadWithTags):
    user: "UserRead"

# SEARCH & FILTER SCHEMAS
class NoteFilter(BaseModel):
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    tag_ids: Optional[List[int]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

class NoteSearchQuery(BaseModel):
    q: str = Field(..., min_length=2, description="Search query")
    in_title: bool = Field(True, description="Search in title")
    in_content: bool = Field(True, description="Search in content")

# STATS SCHEMAS
class NoteStats(BaseModel):
    total: int
    pinned: int
    favorites: int
    with_tags: int
    created_today: int
    created_this_week: int
    created_this_month: int
    most_used_tags: List[dict]  # [{"tag": "work", "count": 10}]

# BULK OPERATIONS
class NoteBulkAction(BaseModel):
    note_ids: List[int] = Field(..., min_items=1)
    action: str = Field(..., regex="^(delete|pin|unpin|favorite|unfavorite|add_tag|remove_tag)$")
    tag_id: Optional[int] = None  # Cho add_tag/remove_tag actions
```

---

## 🔧 BƯỚC 3: XÂY DỰNG CRUD OPERATIONS

```python
# src/app/crud/crud_note.py
from typing import List, Optional, Tuple
from sqlalchemy import select, update, and_, or_, desc, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, UTC, timedelta

from ..models.note import Note, Tag, note_tags
from ..schemas.note import NoteCreate, NoteUpdate, NoteFilter, NoteSearchQuery

class NoteCRUD:
    
    async def create(self, db: AsyncSession, *, obj_in: NoteCreate, user_id: int) -> Note:
        """Tạo note mới với tags"""
        # Tạo note
        db_obj = Note(
            title=obj_in.title,
            content=obj_in.content,
            is_pinned=obj_in.is_pinned,
            is_favorite=obj_in.is_favorite,
            user_id=user_id,
            metadata=obj_in.metadata
        )
        db.add(db_obj)
        await db.flush()  # Lấy ID
        
        # Add tags nếu có
        if obj_in.tag_ids:
            await self._add_tags_to_note(db, note_id=db_obj.id, tag_ids=obj_in.tag_ids, user_id=user_id)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: int, user_id: int) -> Optional[Note]:
        """Lấy note theo ID (chỉ của user)"""
        result = await db.execute(
            select(Note).where(
                Note.id == id,
                Note.user_id == user_id,
                Note.deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_with_tags(self, db: AsyncSession, id: int, user_id: int) -> Optional[Note]:
        """Lấy note với tags"""
        result = await db.execute(
            select(Note)
            .options(selectinload(Note.tags))
            .where(
                Note.id == id,
                Note.user_id == user_id,
                Note.deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_user_notes(
        self, 
        db: AsyncSession, 
        user_id: int, 
        *, 
        skip: int = 0, 
        limit: int = 50,
        filters: Optional[NoteFilter] = None,
        order_by: str = "updated_at",
        desc_order: bool = True
    ) -> List[Note]:
        """Lấy notes của user với filtering và sorting"""
        query = select(Note).where(
            Note.user_id == user_id,
            Note.deleted == False
        ).options(selectinload(Note.tags))
        
        # Apply filters
        if filters:
            if filters.is_pinned is not None:
                query = query.where(Note.is_pinned == filters.is_pinned)
            if filters.is_favorite is not None:
                query = query.where(Note.is_favorite == filters.is_favorite)
            if filters.tag_ids:
                query = query.join(note_tags).where(note_tags.c.tag_id.in_(filters.tag_ids))
            if filters.created_after:
                query = query.where(Note.created_at >= filters.created_after)
            if filters.created_before:
                query = query.where(Note.created_at <= filters.created_before)
        
        # Sorting - pinned notes luôn lên đầu
        if order_by == "created_at":
            order_field = Note.created_at
        elif order_by == "updated_at":
            order_field = Note.updated_at
        else:
            order_field = Note.title
            
        if desc_order:
            order_field = desc(order_field)
            
        query = query.order_by(desc(Note.is_pinned), order_field)
        
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def search_notes(
        self, 
        db: AsyncSession, 
        user_id: int, 
        search_query: NoteSearchQuery,
        limit: int = 50
    ) -> List[Note]:
        """Tìm kiếm notes"""
        conditions = []
        
        if search_query.in_title:
            conditions.append(Note.title.ilike(f"%{search_query.q}%"))
        if search_query.in_content:
            conditions.append(Note.content.ilike(f"%{search_query.q}%"))
        
        if not conditions:
            return []
        
        result = await db.execute(
            select(Note)
            .options(selectinload(Note.tags))
            .where(
                and_(
                    Note.user_id == user_id,
                    Note.deleted == False,
                    or_(*conditions)
                )
            )
            .order_by(desc(Note.is_pinned), desc(Note.updated_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Note, obj_in: NoteUpdate, user_id: int) -> Note:
        """Cập nhật note"""
        update_data = obj_in.model_dump(exclude_unset=True, exclude={'tag_ids'})
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(UTC)
        
        # Update tags nếu có
        if obj_in.tag_ids is not None:
            await self._update_note_tags(db, note_id=db_obj.id, tag_ids=obj_in.tag_ids, user_id=user_id)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int, user_id: int) -> bool:
        """Soft delete note"""
        result = await db.execute(
            update(Note)
            .where(Note.id == id, Note.user_id == user_id)
            .values(
                deleted=True, 
                deleted_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
        )
        await db.commit()
        return result.rowcount > 0

    async def restore(self, db: AsyncSession, *, id: int, user_id: int) -> bool:
        """Restore deleted note"""
        result = await db.execute(
            update(Note)
            .where(Note.id == id, Note.user_id == user_id, Note.deleted == True)
            .values(
                deleted=False, 
                deleted_at=None,
                updated_at=datetime.now(UTC)
            )
        )
        await db.commit()
        return result.rowcount > 0

    async def get_deleted_notes(self, db: AsyncSession, user_id: int) -> List[Note]:
        """Lấy notes đã xóa (trash)"""
        result = await db.execute(
            select(Note)
            .where(Note.user_id == user_id, Note.deleted == True)
            .order_by(desc(Note.deleted_at))
        )
        return result.scalars().all()

    async def permanent_delete(self, db: AsyncSession, *, id: int, user_id: int) -> bool:
        """Xóa vĩnh viễn note"""
        # Xóa relationships trước
        await db.execute(
            delete(note_tags).where(note_tags.c.note_id == id)
        )
        
        # Xóa note
        result = await db.execute(
            delete(Note).where(Note.id == id, Note.user_id == user_id)
        )
        await db.commit()
        return result.rowcount > 0

    async def bulk_action(
        self, 
        db: AsyncSession, 
        *, 
        note_ids: List[int], 
        user_id: int, 
        action: str,
        tag_id: Optional[int] = None
    ) -> int:
        """Bulk operations trên notes"""
        base_query = update(Note).where(
            Note.id.in_(note_ids),
            Note.user_id == user_id,
            Note.deleted == False
        )
        
        if action == "delete":
            result = await db.execute(
                base_query.values(
                    deleted=True, 
                    deleted_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
            )
        elif action == "pin":
            result = await db.execute(
                base_query.values(is_pinned=True, updated_at=datetime.now(UTC))
            )
        elif action == "unpin":
            result = await db.execute(
                base_query.values(is_pinned=False, updated_at=datetime.now(UTC))
            )
        elif action == "favorite":
            result = await db.execute(
                base_query.values(is_favorite=True, updated_at=datetime.now(UTC))
            )
        elif action == "unfavorite":
            result = await db.execute(
                base_query.values(is_favorite=False, updated_at=datetime.now(UTC))
            )
        else:
            return 0
            
        await db.commit()
        return result.rowcount

    async def get_stats(self, db: AsyncSession, user_id: int) -> dict:
        """Lấy thống kê notes"""
        # Thời gian tính toán
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        
        # Query tất cả notes
        result = await db.execute(
            select(Note)
            .options(selectinload(Note.tags))
            .where(Note.user_id == user_id, Note.deleted == False)
        )
        notes = result.scalars().all()
        
        # Calculate stats
        stats = {
            "total": len(notes),
            "pinned": sum(1 for note in notes if note.is_pinned),
            "favorites": sum(1 for note in notes if note.is_favorite),
            "with_tags": sum(1 for note in notes if note.tags),
            "created_today": sum(1 for note in notes if note.created_at >= today_start),
            "created_this_week": sum(1 for note in notes if note.created_at >= week_start),
            "created_this_month": sum(1 for note in notes if note.created_at >= month_start),
        }
        
        # Most used tags
        tag_counts = {}
        for note in notes:
            for tag in note.tags:
                tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
        
        stats["most_used_tags"] = [
            {"tag": tag, "count": count} 
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return stats

    # PRIVATE METHODS
    async def _add_tags_to_note(self, db: AsyncSession, note_id: int, tag_ids: List[int], user_id: int):
        """Thêm tags vào note"""
        # Verify tags belong to user hoặc là global
        result = await db.execute(
            select(Tag).where(
                Tag.id.in_(tag_ids),
                or_(Tag.user_id == user_id, Tag.is_global == True)
            )
        )
        valid_tags = result.scalars().all()
        
        # Insert relationships
        for tag in valid_tags:
            await db.execute(
                note_tags.insert().values(note_id=note_id, tag_id=tag.id)
            )

    async def _update_note_tags(self, db: AsyncSession, note_id: int, tag_ids: List[int], user_id: int):
        """Cập nhật tags của note"""
        # Xóa existing relationships
        await db.execute(
            delete(note_tags).where(note_tags.c.note_id == note_id)
        )
        
        # Add new relationships
        if tag_ids:
            await self._add_tags_to_note(db, note_id, tag_ids, user_id)

class TagCRUD:
    
    async def create(self, db: AsyncSession, *, obj_in: TagCreate, user_id: int) -> Tag:
        """Tạo tag mới"""
        db_obj = Tag(
            name=obj_in.name.lower(),  # Normalize to lowercase
            color=obj_in.color,
            user_id=user_id,
            is_global=False
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_user_tags(self, db: AsyncSession, user_id: int) -> List[Tag]:
        """Lấy tags của user + global tags"""
        result = await db.execute(
            select(Tag).where(
                or_(Tag.user_id == user_id, Tag.is_global == True)
            ).order_by(Tag.name)
        )
        return result.scalars().all()

    async def get_by_name(self, db: AsyncSession, name: str, user_id: int) -> Optional[Tag]:
        """Lấy tag theo tên"""
        result = await db.execute(
            select(Tag).where(
                Tag.name == name.lower(),
                or_(Tag.user_id == user_id, Tag.is_global == True)
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, db: AsyncSession, *, id: int, user_id: int) -> bool:
        """Xóa tag (chỉ personal tags)"""
        # Xóa relationships trước
        await db.execute(
            delete(note_tags).where(note_tags.c.tag_id == id)
        )
        
        # Xóa tag
        result = await db.execute(
            delete(Tag).where(Tag.id == id, Tag.user_id == user_id, Tag.is_global == False)
        )
        await db.commit()
        return result.rowcount > 0

# Create instances
crud_note = NoteCRUD()
crud_tag = TagCRUD()
```

---

## 🌐 BƯỚC 4: XÂY DỰNG API ENDPOINTS

```python
# src/app/api/v1/notes.py
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...api.dependencies import get_current_user
from ...crud.crud_note import crud_note, crud_tag
from ...schemas.note import (
    NoteCreate,
    NoteRead,
    NoteUpdate,
    NoteReadWithTags,
    NoteReadDetailed,
    NoteFilter,
    NoteSearchQuery,
    NoteStats,
    NoteBulkAction,
    TagCreate,
    TagRead
)

router = APIRouter(prefix="/notes", tags=["notes"])

# NOTE ENDPOINTS
@router.post("/", response_model=NoteReadWithTags, status_code=status.HTTP_201_CREATED)
async def create_note(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    note_in: NoteCreate,
) -> NoteReadWithTags:
    """Tạo note mới"""
    note = await crud_note.create(
        db=db,
        obj_in=note_in,
        user_id=current_user["id"]
    )
    
    # Get with tags
    note_with_tags = await crud_note.get_with_tags(
        db=db, 
        id=note.id, 
        user_id=current_user["id"]
    )
    return NoteReadWithTags.model_validate(note_with_tags)

@router.get("/", response_model=List[NoteReadWithTags])
async def list_notes(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_pinned: Optional[bool] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    tag_ids: Optional[str] = Query(None, description="Comma-separated tag IDs"),
    order_by: str = Query("updated_at", regex="^(created_at|updated_at|title)$"),
    desc_order: bool = Query(True),
) -> List[NoteReadWithTags]:
    """Lấy danh sách notes với filtering"""
    # Parse tag_ids
    tag_id_list = []
    if tag_ids:
        try:
            tag_id_list = [int(x.strip()) for x in tag_ids.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag_ids format"
            )
    
    filters = NoteFilter(
        is_pinned=is_pinned,
        is_favorite=is_favorite,
        tag_ids=tag_id_list if tag_id_list else None
    )
    
    notes = await crud_note.get_user_notes(
        db=db,
        user_id=current_user["id"],
        skip=skip,
        limit=limit,
        filters=filters,
        order_by=order_by,
        desc_order=desc_order
    )
    return [NoteReadWithTags.model_validate(note) for note in notes]

@router.get("/search", response_model=List[NoteReadWithTags])
async def search_notes(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    q: str = Query(..., min_length=2, description="Search query"),
    in_title: bool = Query(True),
    in_content: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
) -> List[NoteReadWithTags]:
    """Tìm kiếm notes"""
    search_query = NoteSearchQuery(
        q=q,
        in_title=in_title,
        in_content=in_content
    )
    
    notes = await crud_note.search_notes(
        db=db,
        user_id=current_user["id"],
        search_query=search_query,
        limit=limit
    )
    return [NoteReadWithTags.model_validate(note) for note in notes]

@router.get("/stats", response_model=NoteStats)
async def get_note_stats(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> NoteStats:
    """Lấy thống kê notes"""
    stats = await crud_note.get_stats(db=db, user_id=current_user["id"])
    return NoteStats(**stats)

@router.get("/trash", response_model=List[NoteRead])
async def get_deleted_notes(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> List[NoteRead]:
    """Lấy notes đã xóa (trash)"""
    notes = await crud_note.get_deleted_notes(db=db, user_id=current_user["id"])
    return [NoteRead.model_validate(note) for note in notes]

@router.get("/{note_id}", response_model=NoteReadWithTags)
async def get_note(
    *,
    note_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> NoteReadWithTags:
    """Lấy chi tiết note"""
    note = await crud_note.get_with_tags(
        db=db, 
        id=note_id, 
        user_id=current_user["id"]
    )
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return NoteReadWithTags.model_validate(note)

@router.put("/{note_id}", response_model=NoteReadWithTags)
async def update_note(
    *,
    note_id: int,
    note_in: NoteUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> NoteReadWithTags:
    """Cập nhật note"""
    note = await crud_note.get(db=db, id=note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    updated_note = await crud_note.update(
        db=db,
        db_obj=note,
        obj_in=note_in,
        user_id=current_user["id"]
    )
    
    # Get with tags
    note_with_tags = await crud_note.get_with_tags(
        db=db, 
        id=updated_note.id, 
        user_id=current_user["id"]
    )
    return NoteReadWithTags.model_validate(note_with_tags)

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    *,
    note_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Xóa note (soft delete)"""
    success = await crud_note.delete(
        db=db, 
        id=note_id, 
        user_id=current_user["id"]
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

@router.post("/{note_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
async def restore_note(
    *,
    note_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Restore note từ trash"""
    success = await crud_note.restore(
        db=db, 
        id=note_id, 
        user_id=current_user["id"]
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found in trash"
        )

@router.delete("/{note_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanent_delete_note(
    *,
    note_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Xóa vĩnh viễn note"""
    success = await crud_note.permanent_delete(
        db=db, 
        id=note_id, 
        user_id=current_user["id"]
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

@router.post("/bulk-action", response_model=dict)
async def bulk_action_notes(
    *,
    action_data: NoteBulkAction,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Bulk operations trên notes"""
    affected_count = await crud_note.bulk_action(
        db=db,
        note_ids=action_data.note_ids,
        user_id=current_user["id"],
        action=action_data.action,
        tag_id=action_data.tag_id
    )
    
    return {
        "message": f"Successfully {action_data.action} {affected_count} notes",
        "affected_count": affected_count
    }

# TAG ENDPOINTS
@router.get("/tags/", response_model=List[TagRead])
async def list_tags(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> List[TagRead]:
    """Lấy danh sách tags"""
    tags = await crud_tag.get_user_tags(db=db, user_id=current_user["id"])
    return [TagRead.model_validate(tag) for tag in tags]

@router.post("/tags/", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    *,
    tag_in: TagCreate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TagRead:
    """Tạo tag mới"""
    # Check if tag already exists
    existing_tag = await crud_tag.get_by_name(
        db=db, 
        name=tag_in.name, 
        user_id=current_user["id"]
    )
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag already exists"
        )
    
    tag = await crud_tag.create(
        db=db,
        obj_in=tag_in,
        user_id=current_user["id"]
    )
    return TagRead.model_validate(tag)

@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    *,
    tag_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Xóa tag"""
    success = await crud_tag.delete(
        db=db, 
        id=tag_id, 
        user_id=current_user["id"]
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found or cannot delete global tag"
        )
```

---

## 🎯 BƯỚC 5: TÍCH HỢP VÀO APP

### 1. Thêm vào API Router

```python
# src/app/api/v1/__init__.py (thêm import)
from .notes import router as notes_router

# Thêm vào router includes
router.include_router(notes_router)
```

### 2. Tạo Migration

```bash
# Terminal commands
cd d:\Worksapce\base_fast_api
uv run alembic revision --autogenerate -m "Add notes and tags tables"
uv run alembic upgrade head
```

### 3. Test Data Script

```python
# scripts/create_sample_notes.py
import asyncio
from src.app.core.db.database import async_get_db
from src.app.crud.crud_note import crud_note, crud_tag
from src.app.schemas.note import NoteCreate, TagCreate

async def create_sample_data():
    async for db in async_get_db():
        user_id = 1  # Admin user
        
        # Tạo tags
        tags_data = [
            TagCreate(name="work", color="#FF5733"),
            TagCreate(name="personal", color="#33FF57"),
            TagCreate(name="ideas", color="#3357FF"),
            TagCreate(name="todo", color="#FF33F5"),
            TagCreate(name="important", color="#F5FF33"),
        ]
        
        created_tags = []
        for tag_data in tags_data:
            tag = await crud_tag.create(db=db, obj_in=tag_data, user_id=user_id)
            created_tags.append(tag)
        
        # Tạo notes
        notes_data = [
            NoteCreate(
                title="Project Planning Meeting Notes",
                content="Discussion about Q1 goals and roadmap. Key points: 1) Focus on mobile, 2) Improve UX, 3) Add analytics",
                is_pinned=True,
                tag_ids=[created_tags[0].id, created_tags[3].id]  # work, todo
            ),
            NoteCreate(
                title="Book Recommendations",
                content="1. Clean Code by Robert Martin\n2. System Design Interview by Alex Xu\n3. Designing Data-Intensive Applications",
                is_favorite=True,
                tag_ids=[created_tags[1].id]  # personal
            ),
            NoteCreate(
                title="App Feature Ideas",
                content="- Dark mode toggle\n- Export to PDF\n- Voice notes\n- Collaborative editing\n- Mobile app",
                tag_ids=[created_tags[2].id, created_tags[4].id]  # ideas, important
            ),
            NoteCreate(
                title="Grocery List",
                content="- Milk\n- Bread\n- Eggs\n- Chicken\n- Vegetables\n- Fruits",
                tag_ids=[created_tags[1].id, created_tags[3].id]  # personal, todo
            ),
            NoteCreate(
                title="Learning Goals 2024",
                content="1. Master FastAPI and async Python\n2. Learn React Native\n3. Study system design\n4. Improve DevOps skills",
                is_pinned=True,
                is_favorite=True,
                tag_ids=[created_tags[1].id, created_tags[4].id]  # personal, important
            )
        ]
        
        for note_data in notes_data:
            await crud_note.create(db=db, obj_in=note_data, user_id=user_id)
        
        print(f"Created {len(created_tags)} tags and {len(notes_data)} notes")
        break

if __name__ == "__main__":
    asyncio.run(create_sample_data())
```

---

## 🧪 BƯỚC 6: TESTING COMMANDS

```bash
# 1. Tạo note mới
curl -X POST "http://localhost:8000/api/v1/notes/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Note",
    "content": "This is my first note content",
    "is_pinned": true,
    "tag_ids": [1, 2]
  }'

# 2. Lấy danh sách notes
curl -X GET "http://localhost:8000/api/v1/notes/?skip=0&limit=10&is_pinned=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Tìm kiếm notes
curl -X GET "http://localhost:8000/api/v1/notes/search?q=meeting&in_title=true&in_content=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Lấy thống kê
curl -X GET "http://localhost:8000/api/v1/notes/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 5. Bulk action - pin multiple notes
curl -X POST "http://localhost:8000/api/v1/notes/bulk-action" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "note_ids": [1, 2, 3],
    "action": "pin"
  }'

# 6. Tạo tag mới
curl -X POST "http://localhost:8000/api/v1/notes/tags/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "urgent",
    "color": "#FF0000"
  }'

# 7. Lấy danh sách tags
curl -X GET "http://localhost:8000/api/v1/notes/tags/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 TỔNG KẾT: BẠN ĐÃ HỌC ĐƯỢC

### ✅ **Patterns đã áp dụng:**
1. **Many-to-many relationships** (Note ↔ Tag)
2. **Soft delete với restore** functionality
3. **Complex filtering và search** với multiple conditions
4. **Bulk operations** để thao tác nhiều records
5. **Statistics calculation** với aggregation
6. **JSON metadata** cho extensibility
7. **Proper indexing** cho performance
8. **User isolation** (users chỉ thấy data của mình)

### ✅ **Advanced Features:**
- **Tag system** với colors
- **Pinning và favorites** functionality
- **Full-text search** trong title/content
- **Trash/restore** mechanism
- **Bulk actions** (pin/unpin/delete/favorite)
- **Statistics dashboard** data
- **Personal vs global tags**

### ✅ **Best Practices đã follow:**
- **Consistent API design** với proper HTTP methods
- **Proper error handling** với meaningful messages
- **Input validation** với Pydantic
- **Database optimization** với eager loading
- **Security** với user-based filtering
- **Clean code structure** với separation of concerns

### 🚀 **Next Steps cho bạn:**

1. **Implement similar pattern** cho features khác (Events, Projects, etc.)
2. **Add real-time features** với WebSocket
3. **Implement caching** với Redis
4. **Add file attachments** cho notes
5. **Create mobile API** với different schemas
6. **Add audit logging** để track changes
7. **Implement sharing** notes between users

Bây giờ bạn đã có template hoàn chỉnh để tự tạo bất kỳ feature nào! 🎯