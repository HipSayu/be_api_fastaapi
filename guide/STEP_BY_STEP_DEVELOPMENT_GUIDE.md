# 🚀 HƯỚNG DẪN STEP-BY-STEP: TỪ MODELS ĐẾN API

## 📋 TỔNG QUAN LUỒNG PHÁT TRIỂN

```
1. Models (Database) → 2. Schemas (API) → 3. CRUD (Logic) → 4. API (Endpoints)
        ↓                      ↓                   ↓                ↓
   SQLAlchemy ORM         Pydantic Models      Business Logic    FastAPI Routes
   Table Structure        Input/Output         Database Ops      HTTP Endpoints
```

---

## 🎯 BƯỚC 1: THIẾT KẾ DATABASE MODELS

### 📝 Template cơ bản cho Model

```python
# src/app/models/feature_name.py
from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.db.database import Base

class FeatureName(Base):
    """
    🏗️ TEMPLATE CHO MODEL MỚI
    
    Quy tắc đặt tên:
    - Class: PascalCase (User, Post, Conversation)
    - Table: snake_case (users, posts, conversations)
    - Fields: snake_case (user_id, created_at)
    """
    __tablename__ = "table_name"
    
    # 🔑 Primary Key (bắt buộc)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 📝 Basic Fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 🔗 Foreign Keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # 📊 Enum Fields (nếu cần)
    # status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), default=StatusEnum.ACTIVE)
    
    # 🗂️ JSON Metadata (linh hoạt cho tương lai)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # ⏰ Timestamps (nên có)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # 🗑️ Soft Delete (recommended)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 🔗 Relationships
    user: Mapped["User"] = relationship("User", back_populates="feature_items")
    # children: Mapped[List["ChildModel"]] = relationship("ChildModel", back_populates="parent")
```

### 💡 Ví dụ thực tế: Tạo Feature "Tasks" (Quản lý công việc)

```python
# src/app/models/task.py
from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum
from ..core.db.database import Base

class TaskStatus(PyEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress" 
    REVIEW = "review"
    DONE = "done"

class TaskPriority(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(Base):
    __tablename__ = "tasks"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic Info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status & Priority
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Assignee & Creator
    assigned_to: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Dates
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata cho tags, attachments, etc.
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Soft Delete
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")
    comments: Mapped[List["TaskComment"]] = relationship("TaskComment", back_populates="task")

class TaskComment(Base):
    __tablename__ = "task_comments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="task_comments")
```

---

## 🎯 BƯỚC 2: TẠO PYDANTIC SCHEMAS

### 📝 Template cơ bản cho Schemas

```python
# src/app/schemas/feature_name.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# 📥 INPUT SCHEMAS (cho API requests)
class FeatureCreateBase(BaseModel):
    """Base schema cho Create operations"""
    name: str = Field(..., min_length=1, max_length=255, description="Feature name")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    metadata: Optional[dict] = Field(None, description="Additional metadata")

class FeatureCreate(FeatureCreateBase):
    """Schema cho POST requests - có thể thêm fields specific"""
    pass

class FeatureUpdate(BaseModel):
    """Schema cho PUT/PATCH requests - tất cả fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[dict] = None

# 📤 OUTPUT SCHEMAS (cho API responses)
class FeatureRead(BaseModel):
    """Schema cho GET responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    user_id: int
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

class FeatureReadWithRelations(FeatureRead):
    """Schema với relationships - cho detailed views"""
    user: "UserRead"  # Forward reference
    # children: List["ChildRead"] = []

# 📋 LIST SCHEMAS
class FeatureList(BaseModel):
    """Schema cho paginated lists"""
    items: List[FeatureRead]
    total: int
    page: int
    per_page: int
    total_pages: int
```

### 💡 Ví dụ thực tế: Task Schemas

```python
# src/app/schemas/task.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from ..models.task import TaskStatus, TaskPriority

# INPUT SCHEMAS
class TaskCreateBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    assigned_to: Optional[int] = Field(None, description="User ID to assign task to")
    due_date: Optional[datetime] = Field(None, description="Due date for task")
    metadata: Optional[dict] = Field(None, description="Additional metadata like tags, labels")

class TaskCreate(TaskCreateBase):
    """Schema for creating new task"""
    pass

class TaskUpdate(BaseModel):
    """Schema for updating existing task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    metadata: Optional[dict] = None

class TaskStatusUpdate(BaseModel):
    """Schema for status-only updates"""
    status: TaskStatus

# OUTPUT SCHEMAS
class TaskRead(BaseModel):
    """Basic task information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    assigned_to: Optional[int]
    created_by: int
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

class TaskReadWithUsers(TaskRead):
    """Task with user information"""
    assignee: Optional["UserRead"] = None
    creator: "UserRead"

class TaskReadDetailed(TaskReadWithUsers):
    """Task with all related data"""
    comments: List["TaskCommentRead"] = []

# COMMENT SCHEMAS
class TaskCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class TaskCommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class TaskCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime

class TaskCommentWithUser(TaskCommentRead):
    user: "UserRead"

# FILTER SCHEMAS
class TaskFilter(BaseModel):
    """Schema for filtering tasks"""
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    created_by: Optional[int] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None

# STATS SCHEMAS
class TaskStats(BaseModel):
    """Task statistics"""
    total: int
    by_status: dict[TaskStatus, int]
    by_priority: dict[TaskPriority, int]
    overdue: int
    completed_today: int
```

---

## 🎯 BƯỚC 3: XÂY DỰNG CRUD OPERATIONS

### 📝 Template cơ bản cho CRUD

```python
# src/app/crud/crud_feature.py
from typing import List, Optional
from sqlalchemy import select, update, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, UTC

from ..models.feature import Feature
from ..schemas.feature import FeatureCreate, FeatureUpdate

class FeatureCRUD:
    
    async def create(self, db: AsyncSession, *, obj_in: FeatureCreate, user_id: int) -> Feature:
        """
        ➕ TẠO RECORD MỚI
        
        Pattern:
        1. Tạo object từ input data
        2. Add vào session
        3. Commit + refresh
        4. Return object
        """
        db_obj = Feature(
            name=obj_in.name,
            description=obj_in.description,
            user_id=user_id,
            metadata=obj_in.metadata
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: int) -> Optional[Feature]:
        """
        🔍 LẤY THEO ID
        
        Luôn filter deleted=False cho soft delete
        """
        result = await db.execute(
            select(Feature).where(
                Feature.id == id,
                Feature.deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_with_relations(self, db: AsyncSession, id: int) -> Optional[Feature]:
        """
        🔍 LẤY VỚI RELATIONSHIPS
        
        Sử dụng selectinload để eager load
        """
        result = await db.execute(
            select(Feature)
            .options(
                selectinload(Feature.user),
                selectinload(Feature.children)
            )
            .where(
                Feature.id == id,
                Feature.deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[int] = None
    ) -> List[Feature]:
        """
        📋 LẤY DANH SÁCH VỚI PAGINATION
        
        Có thể filter theo user
        """
        query = select(Feature).where(Feature.deleted == False)
        
        if user_id:
            query = query.where(Feature.user_id == user_id)
        
        result = await db.execute(
            query
            .order_by(desc(Feature.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: Feature, obj_in: FeatureUpdate) -> Feature:
        """
        ✏️ CẬP NHẬT RECORD
        
        Pattern:
        1. Update fields từ input (exclude_unset=True)
        2. Set updated_at
        3. Commit + refresh
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(UTC)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """
        🗑️ SOFT DELETE
        
        Chỉ đánh dấu deleted=True
        """
        result = await db.execute(
            update(Feature)
            .where(Feature.id == id)
            .values(deleted=True, updated_at=datetime.now(UTC))
        )
        await db.commit()
        return result.rowcount > 0

    async def count(self, db: AsyncSession, *, user_id: Optional[int] = None) -> int:
        """
        🔢 ĐẾM SỐ LƯỢNG
        """
        query = select(Feature).where(Feature.deleted == False)
        if user_id:
            query = query.where(Feature.user_id == user_id)
        
        result = await db.execute(query)
        return len(result.scalars().all())

    async def search(self, db: AsyncSession, *, query: str, limit: int = 20) -> List[Feature]:
        """
        🔍 TÌM KIẾM
        
        Search trong name và description
        """
        result = await db.execute(
            select(Feature)
            .where(
                and_(
                    or_(
                        Feature.name.ilike(f"%{query}%"),
                        Feature.description.ilike(f"%{query}%")
                    ),
                    Feature.deleted == False
                )
            )
            .order_by(desc(Feature.updated_at))
            .limit(limit)
        )
        return result.scalars().all()

# Tạo instance để sử dụng
crud_feature = FeatureCRUD()
```

### 💡 Ví dụ thực tế: Task CRUD

```python
# src/app/crud/crud_task.py
from typing import List, Optional
from sqlalchemy import select, update, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, UTC

from ..models.task import Task, TaskComment, TaskStatus, TaskPriority
from ..schemas.task import TaskCreate, TaskUpdate, TaskFilter, TaskCommentCreate

class TaskCRUD:
    
    async def create(self, db: AsyncSession, *, obj_in: TaskCreate, creator_id: int) -> Task:
        """Tạo task mới"""
        db_obj = Task(
            title=obj_in.title,
            description=obj_in.description,
            priority=obj_in.priority,
            assigned_to=obj_in.assigned_to,
            created_by=creator_id,
            due_date=obj_in.due_date,
            metadata=obj_in.metadata
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: int) -> Optional[Task]:
        """Lấy task theo ID"""
        result = await db.execute(
            select(Task).where(
                Task.id == id,
                Task.deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_with_details(self, db: AsyncSession, id: int) -> Optional[Task]:
        """Lấy task với tất cả thông tin liên quan"""
        result = await db.execute(
            select(Task)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.creator),
                selectinload(Task.comments).selectinload(TaskComment.user)
            )
            .where(
                Task.id == id,
                Task.deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_user_tasks(
        self, 
        db: AsyncSession, 
        user_id: int, 
        *, 
        skip: int = 0, 
        limit: int = 50,
        filters: Optional[TaskFilter] = None
    ) -> List[Task]:
        """Lấy tasks của user với filtering"""
        query = select(Task).where(
            and_(
                or_(
                    Task.assigned_to == user_id,
                    Task.created_by == user_id
                ),
                Task.deleted == False
            )
        )
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.where(Task.status == filters.status)
            if filters.priority:
                query = query.where(Task.priority == filters.priority)
            if filters.due_before:
                query = query.where(Task.due_date <= filters.due_before)
            if filters.due_after:
                query = query.where(Task.due_date >= filters.due_after)
        
        result = await db.execute(
            query
            .options(selectinload(Task.assignee), selectinload(Task.creator))
            .order_by(desc(Task.updated_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_status(self, db: AsyncSession, *, task_id: int, status: TaskStatus) -> Optional[Task]:
        """Cập nhật status của task"""
        task = await self.get(db, task_id)
        if not task:
            return None
        
        task.status = status
        if status == TaskStatus.DONE and not task.completed_at:
            task.completed_at = datetime.now(UTC)
        elif status != TaskStatus.DONE:
            task.completed_at = None
            
        task.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(task)
        return task

    async def get_overdue_tasks(self, db: AsyncSession, user_id: Optional[int] = None) -> List[Task]:
        """Lấy tasks quá hạn"""
        query = select(Task).where(
            and_(
                Task.due_date < datetime.now(UTC),
                Task.status != TaskStatus.DONE,
                Task.deleted == False
            )
        )
        
        if user_id:
            query = query.where(
                or_(
                    Task.assigned_to == user_id,
                    Task.created_by == user_id
                )
            )
        
        result = await db.execute(
            query
            .options(selectinload(Task.assignee))
            .order_by(Task.due_date)
        )
        return result.scalars().all()

    async def get_stats(self, db: AsyncSession, user_id: Optional[int] = None) -> dict:
        """Lấy thống kê tasks"""
        base_query = select(Task).where(Task.deleted == False)
        
        if user_id:
            base_query = base_query.where(
                or_(
                    Task.assigned_to == user_id,
                    Task.created_by == user_id
                )
            )
        
        # Total tasks
        total_result = await db.execute(base_query)
        tasks = total_result.scalars().all()
        
        # Calculate stats
        stats = {
            "total": len(tasks),
            "by_status": {},
            "by_priority": {},
            "overdue": 0,
            "completed_today": 0
        }
        
        today = datetime.now(UTC).date()
        
        for task in tasks:
            # By status
            status_key = task.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
            
            # By priority  
            priority_key = task.priority.value
            stats["by_priority"][priority_key] = stats["by_priority"].get(priority_key, 0) + 1
            
            # Overdue
            if task.due_date and task.due_date.date() < today and task.status != TaskStatus.DONE:
                stats["overdue"] += 1
                
            # Completed today
            if task.completed_at and task.completed_at.date() == today:
                stats["completed_today"] += 1
        
        return stats

class TaskCommentCRUD:
    
    async def create(self, db: AsyncSession, *, obj_in: TaskCommentCreate, task_id: int, user_id: int) -> TaskComment:
        """Tạo comment cho task"""
        db_obj = TaskComment(
            task_id=task_id,
            user_id=user_id,
            content=obj_in.content
        )
        db.add(db_obj)
        
        # Update task's updated_at
        await db.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(updated_at=datetime.now(UTC))
        )
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_task_comments(self, db: AsyncSession, task_id: int) -> List[TaskComment]:
        """Lấy comments của task"""
        result = await db.execute(
            select(TaskComment)
            .options(selectinload(TaskComment.user))
            .where(
                TaskComment.task_id == task_id,
                TaskComment.deleted == False
            )
            .order_by(TaskComment.created_at)
        )
        return result.scalars().all()

# Create instances
crud_task = TaskCRUD()
crud_task_comment = TaskCommentCRUD()
```

---

## 🎯 BƯỚC 4: XÂY DỰNG API ENDPOINTS

### 📝 Template cơ bản cho API

```python
# src/app/api/v1/features.py
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...api.dependencies import get_current_user
from ...crud.crud_feature import crud_feature
from ...schemas.feature import (
    FeatureCreate,
    FeatureRead,
    FeatureUpdate,
    FeatureReadWithRelations
)

router = APIRouter(prefix="/features", tags=["features"])

@router.post("/", response_model=FeatureRead, status_code=status.HTTP_201_CREATED)
async def create_feature(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    feature_in: FeatureCreate,
) -> FeatureRead:
    """
    ➕ TẠO FEATURE MỚI
    
    Pattern:
    1. Validate input (Pydantic auto)
    2. Call CRUD create
    3. Return created object
    """
    feature = await crud_feature.create(
        db=db,
        obj_in=feature_in,
        user_id=current_user["id"]
    )
    return FeatureRead.model_validate(feature)

@router.get("/", response_model=List[FeatureRead])
async def list_features(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    my_only: bool = Query(False, description="Show only my features"),
) -> List[FeatureRead]:
    """
    📋 LẤY DANH SÁCH FEATURES
    
    Query parameters:
    - skip, limit: Pagination
    - my_only: Filter theo user
    """
    user_id = current_user["id"] if my_only else None
    features = await crud_feature.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id
    )
    return [FeatureRead.model_validate(feature) for feature in features]

@router.get("/{feature_id}", response_model=FeatureReadWithRelations)
async def get_feature(
    *,
    feature_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> FeatureReadWithRelations:
    """
    🔍 LẤY CHI TIẾT FEATURE
    
    Include relationships
    """
    feature = await crud_feature.get_with_relations(db=db, id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )
    return FeatureReadWithRelations.model_validate(feature)

@router.put("/{feature_id}", response_model=FeatureRead)
async def update_feature(
    *,
    feature_id: int,
    feature_in: FeatureUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> FeatureRead:
    """
    ✏️ CẬP NHẬT FEATURE
    
    Chỉ owner mới được update
    """
    feature = await crud_feature.get(db=db, id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )
    
    # Check ownership
    if feature.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_feature = await crud_feature.update(
        db=db,
        db_obj=feature,
        obj_in=feature_in
    )
    return FeatureRead.model_validate(updated_feature)

@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(
    *,
    feature_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    🗑️ XÓA FEATURE
    
    Soft delete, chỉ owner
    """
    feature = await crud_feature.get(db=db, id=feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )
    
    if feature.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await crud_feature.delete(db=db, id=feature_id)

@router.get("/search", response_model=List[FeatureRead])
async def search_features(
    *,
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> List[FeatureRead]:
    """
    🔍 TÌM KIẾM FEATURES
    """
    features = await crud_feature.search(db=db, query=q, limit=limit)
    return [FeatureRead.model_validate(feature) for feature in features]
```

### 💡 Ví dụ thực tế: Task API

```python
# src/app/api/v1/tasks.py
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...api.dependencies import get_current_user
from ...crud.crud_task import crud_task, crud_task_comment
from ...models.task import TaskStatus, TaskPriority
from ...schemas.task import (
    TaskCreate,
    TaskRead,
    TaskUpdate,
    TaskReadDetailed,
    TaskStatusUpdate,
    TaskFilter,
    TaskStats,
    TaskCommentCreate,
    TaskCommentWithUser
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    task_in: TaskCreate,
) -> TaskRead:
    """Tạo task mới"""
    task = await crud_task.create(
        db=db,
        obj_in=task_in,
        creator_id=current_user["id"]
    )
    return TaskRead.model_validate(task)

@router.get("/", response_model=List[TaskRead])
async def list_tasks(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assigned_to: Optional[int] = Query(None),
) -> List[TaskRead]:
    """Lấy danh sách tasks với filtering"""
    filters = TaskFilter(
        status=status,
        priority=priority,
        assigned_to=assigned_to
    )
    
    tasks = await crud_task.get_user_tasks(
        db=db,
        user_id=current_user["id"],
        skip=skip,
        limit=limit,
        filters=filters
    )
    return [TaskRead.model_validate(task) for task in tasks]

@router.get("/stats", response_model=TaskStats)
async def get_task_stats(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TaskStats:
    """Lấy thống kê tasks của user"""
    stats = await crud_task.get_stats(db=db, user_id=current_user["id"])
    return TaskStats(**stats)

@router.get("/overdue", response_model=List[TaskRead])
async def get_overdue_tasks(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> List[TaskRead]:
    """Lấy tasks quá hạn"""
    tasks = await crud_task.get_overdue_tasks(db=db, user_id=current_user["id"])
    return [TaskRead.model_validate(task) for task in tasks]

@router.get("/{task_id}", response_model=TaskReadDetailed)
async def get_task(
    *,
    task_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TaskReadDetailed:
    """Lấy chi tiết task"""
    task = await crud_task.get_with_details(db=db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check access permission
    if task.assigned_to != current_user["id"] and task.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return TaskReadDetailed.model_validate(task)

@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    *,
    task_id: int,
    task_in: TaskUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TaskRead:
    """Cập nhật task"""
    task = await crud_task.get(db=db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check permission (creator or assignee can edit)
    if task.created_by != current_user["id"] and task.assigned_to != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_task = await crud_task.update(
        db=db,
        db_obj=task,
        obj_in=task_in
    )
    return TaskRead.model_validate(updated_task)

@router.patch("/{task_id}/status", response_model=TaskRead)
async def update_task_status(
    *,
    task_id: int,
    status_update: TaskStatusUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TaskRead:
    """Cập nhật status của task"""
    task = await crud_task.get(db=db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.assigned_to != current_user["id"] and task.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    updated_task = await crud_task.update_status(
        db=db,
        task_id=task_id,
        status=status_update.status
    )
    return TaskRead.model_validate(updated_task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    *,
    task_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Xóa task (chỉ creator)"""
    task = await crud_task.get(db=db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creator can delete task"
        )
    
    await crud_task.delete(db=db, id=task_id)

# TASK COMMENTS ENDPOINTS
@router.post("/{task_id}/comments", response_model=TaskCommentWithUser, status_code=status.HTTP_201_CREATED)
async def create_task_comment(
    *,
    task_id: int,
    comment_in: TaskCommentCreate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TaskCommentWithUser:
    """Thêm comment cho task"""
    # Verify task exists and user has access
    task = await crud_task.get(db=db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.assigned_to != current_user["id"] and task.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    comment = await crud_task_comment.create(
        db=db,
        obj_in=comment_in,
        task_id=task_id,
        user_id=current_user["id"]
    )
    
    # Get comment with user info
    comment_with_user = await crud_task_comment.get_with_user(db=db, id=comment.id)
    return TaskCommentWithUser.model_validate(comment_with_user)

@router.get("/{task_id}/comments", response_model=List[TaskCommentWithUser])
async def get_task_comments(
    *,
    task_id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> List[TaskCommentWithUser]:
    """Lấy comments của task"""
    # Verify access
    task = await crud_task.get(db=db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.assigned_to != current_user["id"] and task.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    comments = await crud_task_comment.get_task_comments(db=db, task_id=task_id)
    return [TaskCommentWithUser.model_validate(comment) for comment in comments]
```

---

## 🎯 BƯỚC 5: TÍCH HỢP VÀO MAIN APP

### 1. Cập nhật Models trong __init__.py

```python
# src/app/models/__init__.py
from .user import User
from .post import Post
from .task import Task, TaskComment  # ← Thêm models mới
# ... other imports

__all__ = [
    "User",
    "Post", 
    "Task",        # ← Export
    "TaskComment", # ← Export
    # ... others
]
```

### 2. Thêm vào API Router

```python
# src/app/api/v1/__init__.py
from fastapi import APIRouter

from .login import router as login_router
from .users import router as users_router
from .tasks import router as tasks_router  # ← Import router mới

router = APIRouter(prefix="/v1")

# Include existing routers
router.include_router(login_router)
router.include_router(users_router)
router.include_router(tasks_router)  # ← Add router
```

### 3. Tạo Migration

```bash
# Terminal command
cd d:\Worksapce\base_fast_api
uv run alembic revision --autogenerate -m "Add tasks and task_comments tables"
uv run alembic upgrade head
```

---

## 🎯 BƯỚC 6: TESTING VÀ VALIDATION

### 1. Tạo Test Data

```python
# scripts/create_sample_tasks.py
import asyncio
from src.app.core.db.database import async_get_db
from src.app.crud.crud_task import crud_task
from src.app.schemas.task import TaskCreate
from src.app.models.task import TaskPriority

async def create_sample_tasks():
    async for db in async_get_db():
        sample_tasks = [
            TaskCreate(
                title="Setup project environment",
                description="Install dependencies and configure dev environment",
                priority=TaskPriority.HIGH,
                assigned_to=1
            ),
            TaskCreate(
                title="Write API documentation", 
                description="Document all API endpoints with examples",
                priority=TaskPriority.MEDIUM,
                assigned_to=1
            ),
            TaskCreate(
                title="Code review",
                description="Review pull requests from team",
                priority=TaskPriority.LOW
            )
        ]
        
        for task_data in sample_tasks:
            await crud_task.create(db=db, obj_in=task_data, creator_id=1)
        
        print(f"Created {len(sample_tasks)} sample tasks")
        break

if __name__ == "__main__":
    asyncio.run(create_sample_tasks())
```

### 2. Test Endpoints

```bash
# Test tạo task
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Task",
    "description": "Task description",
    "priority": "high",
    "assigned_to": 1
  }'

# Test lấy danh sách  
curl -X GET "http://localhost:8000/api/v1/tasks?status=todo&priority=high" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test stats
curl -X GET "http://localhost:8000/api/v1/tasks/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 TỔNG KẾT: CHECKLIST PHÁT TRIỂN FEATURE

### ✅ Phase 1: Database Design
- [ ] Thiết kế ERD (Entity Relationship Diagram)
- [ ] Tạo Models với SQLAlchemy
- [ ] Định nghĩa Relationships
- [ ] Thêm Indexes và Constraints
- [ ] Tạo Enums cho status fields

### ✅ Phase 2: API Contracts  
- [ ] Thiết kế Input Schemas (Create, Update)
- [ ] Thiết kế Output Schemas (Read, List)
- [ ] Định nghĩa Validation Rules
- [ ] Tạo Filter và Search Schemas
- [ ] Documentation strings

### ✅ Phase 3: Business Logic
- [ ] Implement CRUD operations
- [ ] Thêm Business Rules và Validation
- [ ] Error Handling
- [ ] Performance Optimization (eager loading)
- [ ] Search và Filtering logic

### ✅ Phase 4: API Layer
- [ ] Tạo FastAPI Router
- [ ] Implement CRUD endpoints
- [ ] Add Authentication Dependencies
- [ ] Permission Checking
- [ ] Input Validation và Error Responses

### ✅ Phase 5: Integration & Testing
- [ ] Add to main app router
- [ ] Create database migrations
- [ ] Write test data scripts
- [ ] Manual testing với curl/Postman
- [ ] Performance testing

### ✅ Phase 6: Documentation & Deployment
- [ ] API documentation
- [ ] Code comments
- [ ] User guide
- [ ] Deploy to staging
- [ ] Monitoring setup

---

## 🚀 PATTERNS VÀ BEST PRACTICES

### 1. 🏗️ Architecture Patterns

```python
# MVC Pattern trong FastAPI
Models (SQLAlchemy) → Controllers (FastAPI routes) → Views (Pydantic schemas)

# Repository Pattern 
class BaseRepository:
    def __init__(self, model):
        self.model = model
    
    async def create(self, db: AsyncSession, obj_in: BaseModel):
        # Common create logic
        pass
```

### 2. 🔒 Security Patterns

```python
# Permission Decorators
def require_permission(permission: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Check permission logic
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@router.get("/admin-only")
@require_permission("admin")
async def admin_endpoint():
    pass
```

### 3. 📊 Performance Patterns

```python
# Caching Pattern
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_user_permissions(user_id: int):
    # Expensive operation
    pass

# Bulk Operations
async def bulk_create_tasks(db: AsyncSession, tasks_data: List[TaskCreate]):
    db_objs = [Task(**task.model_dump()) for task in tasks_data]
    db.add_all(db_objs)
    await db.commit()
```

### 4. 🔄 Event Patterns

```python
# Event Handlers
from sqlalchemy.event import listen

@listen(Task, 'after_update')  
def task_updated(mapper, connection, target):
    # Send notification
    # Update search index
    # Log activity
    pass
```

Với hướng dẫn này, bạn có thể tự viết bất kỳ feature nào theo pattern chuẩn! 🎯