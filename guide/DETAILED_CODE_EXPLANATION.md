# 📚 HƯỚNG DẪN CHI TIẾT HỆ THỐNG CHAT

## 🏗️ KIẾN TRÚC TỔNG QUAN

### 📁 Cấu trúc thư mục
```
src/app/
├── models/chats/           # 🗄️ Database Models (SQLAlchemy)
│   ├── conversations.py    # Model cho conversations
│   ├── conversation_members.py  # Model cho members
│   └── messages.py         # Model cho messages
├── schemas/chats/          # 📋 Pydantic Schemas (API Input/Output)
│   ├── conversation.py     # Schemas cho conversations
│   ├── conversation_member.py   # Schemas cho members  
│   ├── message.py          # Schemas cho messages
│   └── __init__.py         # Exports
├── crud/chats/             # 🔧 CRUD Operations (Database Logic)
│   ├── crud_conversation.py     # CRUD cho conversations
│   ├── crud_conversation_member.py  # CRUD cho members
│   ├── crud_message.py     # CRUD cho messages
│   └── __init__.py         # Exports
└── api/                    # 🌐 API Layer
    ├── chat_dependencies.py    # Permission & Access Control
    └── v1/
        ├── conversations.py     # Conversation endpoints
        └── messages.py          # Message endpoints
```

### 🔄 Luồng hoạt động tổng quát
```
User Request → API Endpoint → Dependencies → CRUD → Database → Response
     ↓              ↓              ↓           ↓        ↓         ↓
1. HTTP Request  2. Validate   3. Check     4. Query  5. SQL    6. JSON
   + JWT Token     Schema        Permissions   Logic    Execute   Response
```

---

## 🗄️ DATABASE MODELS (models/chats/)

### 1. conversations.py - Model Conversation
```python
class Conversation(Base):
    __tablename__ = "conversations"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic Info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Conversation Type: private (1-1), group (nhiều người), channel (broadcast)
    conversation_type: Mapped[ConversationType] = mapped_column(
        Enum(ConversationType), default=ConversationType.PRIVATE
    )
    
    # Owner (người tạo conversation)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Metadata JSON cho mở rộng (settings, configs, etc.)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Soft Delete Pattern
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_conversations")
    members: Mapped[List["ConversationMember"]] = relationship(
        "ConversationMember", back_populates="conversation"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation"  
    )
```

**💡 Giải thích:**
- `ConversationType`: Enum định nghĩa loại conversation (private/group/channel)
- `created_by`: Foreign key tới users.id, xác định chủ sở hữu
- `metadata`: JSON field linh hoạt cho tính năng tương lai (avatar, settings, etc.)
- `deleted`: Soft delete - không xóa thật khỏi DB, chỉ đánh dấu
- **Relationships**: Kết nối với User, ConversationMember, Message

### 2. conversation_members.py - Model Member
```python
class ConversationMember(Base):
    __tablename__ = "conversation_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign Keys
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Role System: owner > admin > member
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole), default=MemberRole.MEMBER
    )
    
    # Lifecycle Tracking
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="conversation_memberships")
```

**💡 Giải thích:**
- `role`: Enum quyền hạn (owner/admin/member), phân quyền chức năng
- `joined_at/left_at`: Tracking thời gian tham gia/rời khỏi
- `is_active`: Trạng thái thành viên (có thể tạm khóa không xóa)
- **Composite Key**: (conversation_id, user_id) đảm bảo unique

### 3. messages.py - Model Message  
```python
class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign Keys
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Reply Feature - Self-referencing FK
    reply_to: Mapped[Optional[int]] = mapped_column(ForeignKey("messages.id"), nullable=True)
    
    # Metadata cho attachments, files, images, etc.
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(UTC))
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Soft Delete
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages")
    
    # Self-referencing relationship cho replies
    parent_message: Mapped[Optional["Message"]] = relationship("Message", remote_side=[id])
```

**💡 Giải thích:**
- `reply_to`: Self-referencing FK cho threading messages
- `metadata`: Chứa attachments, file info, emoji reactions, etc.
- `edited_at`: Track khi message được chỉnh sửa
- `parent_message`: Relationship để lấy message gốc khi reply

---

## 📋 PYDANTIC SCHEMAS (schemas/chats/)

### 1. conversation.py - Schemas cho API
```python
# INPUT SCHEMAS (Request)
class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    conversation_type: ConversationType = ConversationType.PRIVATE
    metadata: Optional[dict] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[dict] = None

# OUTPUT SCHEMAS (Response)  
class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str]
    conversation_type: ConversationType
    created_by: int
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

class ConversationWithMembers(ConversationRead):
    members: List[ConversationMemberRead]
```

**💡 Giải thích:**
- **Create**: Dữ liệu cần thiết để tạo conversation mới
- **Update**: Cho phép update một số field (không có conversation_type)
- **Read**: Dữ liệu trả về client, bao gồm timestamps
- **WithMembers**: Extend Read + danh sách members (join table)
- `Field()`: Validation rules (min_length, max_length, etc.)

### 2. message.py - Message Schemas
```python
class MessageCreate(BaseModel):
    conversation_id: int
    content: str = Field(..., min_length=1, max_length=10000)
    reply_to: Optional[int] = None
    metadata: Optional[dict] = None

class MessageUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    metadata: Optional[dict] = None

class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    conversation_id: int
    sender_id: int
    content: str
    reply_to: Optional[int]
    metadata: Optional[dict]
    created_at: datetime
    edited_at: Optional[datetime]

class MessageWithSender(MessageRead):
    sender: UserRead  # Nested schema với thông tin người gửi
```

**💡 Giải thích:**
- **Create**: conversation_id set từ URL path, content required
- **Update**: Chỉ cho phép sửa content và metadata
- **WithSender**: Include thông tin user gửi tin nhắn (JOIN query)
- `reply_to`: Optional field cho threading messages

---

## 🔧 CRUD OPERATIONS (crud/chats/)

### 1. crud_conversation.py - Business Logic cho Conversations

```python
class ConversationCRUD:
    
    async def create(self, db: AsyncSession, *, obj_in: ConversationCreate, owner_id: int) -> Conversation:
        """
        🏗️ TẠO CONVERSATION MỚI
        
        Luồng:
        1. Tạo conversation với owner_id
        2. Tự động thêm owner vào members với role="owner"
        3. Commit transaction
        4. Return conversation object
        """
        db_obj = Conversation(
            title=obj_in.title,
            description=obj_in.description,
            conversation_type=obj_in.conversation_type,
            created_by=owner_id,
            metadata=obj_in.metadata
        )
        db.add(db_obj)
        await db.flush()  # Lấy ID trước khi commit
        
        # Tự động thêm owner vào members
        member = ConversationMember(
            conversation_id=db_obj.id,
            user_id=owner_id,
            role=MemberRole.OWNER
        )
        db.add(member)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_user_conversations(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20) -> List[Conversation]:
        """
        📋 LẤY CONVERSATIONS CỦA USER
        
        Luồng:
        1. JOIN conversations với conversation_members
        2. Filter theo user_id và is_active=True
        3. Sắp xếp theo updated_at DESC (mới nhất trước)
        4. Pagination với skip/limit
        """
        result = await db.execute(
            select(Conversation)
            .join(ConversationMember)
            .where(
                and_(
                    ConversationMember.user_id == user_id,
                    ConversationMember.is_active == True,
                    Conversation.deleted == False
                )
            )
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
```

**💡 Giải thích luồng CREATE:**
1. **Input Validation**: Pydantic schema đã validate
2. **Create Object**: Tạo Conversation instance 
3. **Flush**: Lấy ID mà chưa commit (cho foreign key)
4. **Auto-membership**: Thêm creator làm owner
5. **Transaction**: Commit cả 2 operations atomically

### 2. crud_conversation_member.py - Quản lý Members

```python
class ConversationMemberCRUD:
    
    async def add_user_to_conversation(self, db: AsyncSession, conversation_id: int, user_id: int, role: str = "member") -> ConversationMember:
        """
        ➕ THÊM USER VÀO CONVERSATION
        
        Luồng:
        1. Kiểm tra user đã là member chưa
        2. Nếu đã có nhưng is_active=False → reactive
        3. Nếu chưa có → tạo mới
        4. Set joined_at = now, left_at = None
        """
        # Kiểm tra existing membership
        existing = await self.get_member(db, conversation_id=conversation_id, user_id=user_id)
        
        if existing:
            if not existing.is_active:
                # Reactivate membership
                existing.is_active = True
                existing.joined_at = datetime.now(UTC)
                existing.left_at = None
                existing.role = MemberRole(role)
                await db.commit()
                return existing
            else:
                raise ValueError("User is already a member of this conversation")
        
        # Tạo membership mới
        db_obj = ConversationMember(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MemberRole(role)
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def is_user_in_conversation(self, db: AsyncSession, conversation_id: int, user_id: int) -> bool:
        """
        🔍 KIỂM TRA USER CÓ TRONG CONVERSATION KHÔNG
        
        Sử dụng cho permission checking trong dependencies
        """
        result = await db.execute(
            select(ConversationMember).where(
                and_(
                    ConversationMember.conversation_id == conversation_id,
                    ConversationMember.user_id == user_id,
                    ConversationMember.is_active == True
                )
            )
        )
        return result.scalar_one_or_none() is not None
```

**💡 Giải thích Pattern:**
- **Soft Delete/Reactivate**: Không xóa member record, chỉ toggle is_active
- **Timestamp Tracking**: joined_at/left_at để audit trail
- **Role Management**: Enum validation cho role changes

### 3. crud_message.py - Message Operations

```python
class MessageCRUD:
    
    async def create(self, db: AsyncSession, *, obj_in: MessageCreate, sender_id: int) -> Message:
        """
        ✉️ TẠO MESSAGE MỚI
        
        Luồng:
        1. Validate reply_to message exists (nếu có)
        2. Tạo message với sender_id
        3. Cập nhật conversation.updated_at
        """
        # Validate reply_to nếu có
        if obj_in.reply_to:
            parent = await self.get(db, id=obj_in.reply_to)
            if not parent or parent.conversation_id != obj_in.conversation_id:
                raise ValueError("Invalid reply_to message")
        
        db_obj = Message(
            conversation_id=obj_in.conversation_id,
            sender_id=sender_id,
            content=obj_in.content,
            metadata=obj_in.metadata,
            reply_to=obj_in.reply_to
        )
        db.add(db_obj)
        
        # Cập nhật conversation updated_at
        await db.execute(
            update(Conversation)
            .where(Conversation.id == obj_in.conversation_id)
            .values(updated_at=datetime.now(UTC))
        )
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_conversation_messages(self, db: AsyncSession, conversation_id: int, skip: int = 0, limit: int = 50, before_message_id: Optional[int] = None) -> List[Message]:
        """
        📜 LẤY MESSAGES TRONG CONVERSATION
        
        Luồng:
        1. Query messages với conversation_id
        2. Pagination với before_message_id (cursor-based)
        3. Order by created_at DESC → reverse để chronological
        4. Include sender info với selectinload
        """
        query = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.deleted == False
        )
        
        # Cursor-based pagination
        if before_message_id:
            query = query.where(Message.id < before_message_id)
        
        result = await db.execute(
            query
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        messages = result.scalars().all()
        return list(reversed(messages))  # Chronological order

    async def search_messages(self, db: AsyncSession, conversation_id: int, search_term: str, limit: int = 20) -> List[Message]:
        """
        🔍 TÌM KIẾM MESSAGES
        
        Sử dụng ILIKE cho case-insensitive search
        """
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
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
```

**💡 Giải thích Patterns:**
- **Cursor Pagination**: Sử dụng before_message_id thay vì offset (performance tốt hơn)
- **Eager Loading**: selectinload(Message.sender) để avoid N+1 queries
- **Search**: ILIKE cho case-insensitive, có thể upgrade thành full-text search
- **Soft Delete**: Luôn filter deleted=False

---

## 🔐 PERMISSION SYSTEM (api/chat_dependencies.py)

```python
async def check_conversation_access(
    conversation_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> Conversation:
    """
    🛡️ KIỂM TRA QUYỀN TRUY CẬP CONVERSATION
    
    Luồng:
    1. Lấy conversation từ DB (hoặc 404)
    2. Kiểm tra user có là member không
    3. Return conversation nếu có quyền
    4. Raise 403 nếu không có quyền
    """
    conversation = await get_conversation_or_404(conversation_id, db)
    
    # Kiểm tra membership
    is_member = await crud_conversation_member.is_user_in_conversation(
        db, conversation_id=conversation_id, user_id=current_user["id"]
    )
    
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this conversation"
        )
    
    return conversation

async def check_conversation_admin_access(
    conversation_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> Conversation:
    """
    👨‍💼 KIỂM TRA QUYỀN ADMIN
    
    Chỉ owner/admin mới có thể:
    - Thêm/xóa members
    - Chỉnh sửa conversation
    - Xóa conversation (chỉ owner)
    """
    conversation = await get_conversation_or_404(conversation_id, db)
    
    member = await crud_conversation_member.get_member(
        db, conversation_id=conversation_id, user_id=current_user["id"]
    )
    
    if not member or member.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this action"
        )
    
    return conversation
```

**💡 Giải thích Permission Levels:**
- **check_conversation_access**: Basic membership (đọc messages, gửi messages)
- **check_conversation_admin_access**: Admin rights (quản lý members, settings)
- **Owner-only**: Một số actions chỉ owner mới được (delete conversation)

---

## 🌐 API ENDPOINTS (api/v1/)

### 1. conversations.py - Conversation Management

```python
@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    *,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    conversation_in: ConversationCreate,
) -> ConversationRead:
    """
    🏗️ TẠO CONVERSATION MỚI
    
    Luồng xử lý:
    1. JWT Authentication → get_current_user
    2. Validate input → ConversationCreate schema
    3. Business logic → crud_conversation.create
    4. Response → ConversationRead schema
    """
    conversation = await crud_conversation.create(
        db=db, 
        obj_in=conversation_in, 
        owner_id=current_user["id"]
    )
    return ConversationRead.model_validate(conversation)

@router.get("/{conversation_id}", response_model=ConversationWithMembers)
async def get_conversation(
    *,
    conversation_id: int,
    conversation: Annotated[dict, Depends(check_conversation_access)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> ConversationWithMembers:
    """
    📋 LẤY THÔNG TIN CONVERSATION
    
    Dependency chain:
    1. check_conversation_access → verify membership
    2. Nếu pass → lấy conversation với members
    3. Return detailed info
    """
    conversation_with_members = await crud_conversation.get_with_members(
        db=db, 
        id=conversation_id
    )
    return ConversationWithMembers.model_validate(conversation_with_members)
```

### 2. messages.py - Message Management

```python
@router.post("/", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    *,
    conversation_id: int,
    conversation: Annotated[dict, Depends(check_conversation_access)],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    message_in: MessageCreate,
) -> MessageRead:
    """
    ✉️ GỬI MESSAGE MỚI
    
    URL: POST /api/v1/conversations/{conversation_id}/messages
    
    Luồng:
    1. check_conversation_access → verify membership
    2. Override conversation_id từ URL path
    3. Create message với sender_id từ current_user
    4. Return message data
    """
    # Đảm bảo conversation_id khớp với URL
    message_in.conversation_id = conversation_id
    
    message = await crud_message.create(
        db=db,
        obj_in=message_in,
        sender_id=current_user["id"]
    )
    return MessageRead.model_validate(message)

@router.put("/{message_id}", response_model=MessageRead)
async def update_message(
    *,
    conversation_id: int,
    message_id: int,
    conversation: Annotated[dict, Depends(check_conversation_access)],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    message_in: MessageUpdate,
) -> MessageRead:
    """
    ✏️ CHỈNH SỬA MESSAGE
    
    Business Rules:
    1. Chỉ người gửi mới được edit
    2. Conversation membership required
    3. Message phải thuộc conversation
    4. Set edited_at timestamp
    """
    # Kiểm tra ownership
    can_edit = await crud_message.check_user_can_edit(
        db=db,
        message_id=message_id,
        user_id=current_user["id"]
    )
    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own messages"
        )
    
    # Validate message exists trong conversation
    message = await crud_message.get(db=db, id=message_id)
    if not message or message.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    updated_message = await crud_message.update(
        db=db,
        db_obj=message,
        obj_in=message_in
    )
    return MessageRead.model_validate(updated_message)
```

---

## 🔄 LUỒNG HOẠT ĐỘNG CHI TIẾT

### 🚀 Scenario 1: Tạo Conversation và Gửi Message

#### Bước 1: User Login
```
POST /api/v1/login
Body: {"username": "user1", "password": "password"}
Response: {"access_token": "jwt_token", "token_type": "bearer"}
```

#### Bước 2: Tạo Conversation
```
POST /api/v1/conversations
Headers: {"Authorization": "Bearer jwt_token"}
Body: {
  "title": "Team Chat",
  "conversation_type": "group"
}

🔄 Luồng Backend:
1. JWT Middleware → verify token → extract user_id
2. Pydantic validation → ConversationCreate
3. crud_conversation.create():
   - Insert conversations table
   - Insert conversation_members (owner role)
   - Commit transaction
4. Response → ConversationRead
```

#### Bước 3: Thêm Members
```
POST /api/v1/conversations/1/members/2
Headers: {"Authorization": "Bearer jwt_token"}
Query: ?role=member

🔄 Luồng Backend:
1. check_conversation_admin_access():
   - Verify user có admin/owner role
2. crud_conversation_member.add_user_to_conversation():
   - Check existing membership
   - Insert new member record
3. Response: 201 Created
```

#### Bước 4: Gửi Message
```
POST /api/v1/conversations/1/messages  
Headers: {"Authorization": "Bearer jwt_token"}
Body: {
  "content": "Hello team!",
  "reply_to": null
}

🔄 Luồng Backend:
1. check_conversation_access():
   - Verify user is member
2. crud_message.create():
   - Insert messages table
   - Update conversation.updated_at
3. Response → MessageRead
```

### 🔍 Scenario 2: Lấy Messages với Pagination

```
GET /api/v1/conversations/1/messages?skip=0&limit=20&before_message_id=100

🔄 Luồng Backend:
1. check_conversation_access() → verify membership
2. crud_message.get_conversation_messages():
   - SELECT messages WHERE conversation_id=1 AND id < 100
   - ORDER BY created_at DESC LIMIT 20
   - selectinload(sender) → JOIN users
3. Response: List[MessageWithSender]

💡 Cursor Pagination Benefits:
- Performance: Không có offset scan
- Consistency: Kết quả không bị duplicate khi có new messages
- Real-time: Dễ integrate với WebSocket
```

### 🔐 Scenario 3: Permission Check Flow

```
PUT /api/v1/conversations/1/messages/50
Headers: {"Authorization": "Bearer jwt_token"}

🔄 Permission Chain:
1. get_current_user():
   - Verify JWT token
   - Get user từ database
   - Return user dict
   
2. check_conversation_access():
   - Get conversation by ID
   - Check user membership
   - Return conversation or 403
   
3. Business Logic Check:
   - crud_message.check_user_can_edit()
   - Verify message owner
   - Additional validation
   
4. CRUD Operation:
   - Update message content
   - Set edited_at timestamp
   - Return updated message
```

---

## 🚨 ERROR HANDLING PATTERNS

### 1. Validation Errors (422)
```python
# Pydantic auto-validation
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### 2. Authentication Errors (401)
```python
# JWT token invalid/expired
{
  "detail": "User not authenticated."
}
```

### 3. Permission Errors (403)
```python
# Access denied
{
  "detail": "Access denied to this conversation"
}
```

### 4. Not Found Errors (404)
```python
# Resource không tồn tại
{
  "detail": "Conversation not found"
}
```

### 5. Business Logic Errors (400)
```python
# Custom validation
{
  "detail": "User is already a member of this conversation"
}
```

---

## 🎯 PERFORMANCE OPTIMIZATION

### 1. Database Indexing
```sql
-- Conversation queries
CREATE INDEX idx_conversations_created_by ON conversations(created_by);
CREATE INDEX idx_conversations_deleted ON conversations(deleted);

-- Member queries  
CREATE INDEX idx_conversation_members_conversation_id ON conversation_members(conversation_id);
CREATE INDEX idx_conversation_members_user_id ON conversation_members(user_id);
CREATE INDEX idx_conversation_members_active ON conversation_members(is_active);

-- Message queries
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_deleted ON messages(deleted);
CREATE INDEX idx_messages_content_gin ON messages USING gin(to_tsvector('english', content));
```

### 2. Query Optimization
```python
# ✅ Good: Eager loading
messages = await db.execute(
    select(Message)
    .options(selectinload(Message.sender))  # Single query
    .where(Message.conversation_id == conversation_id)
)

# ❌ Bad: N+1 queries
messages = await db.execute(
    select(Message)
    .where(Message.conversation_id == conversation_id)
)
# Sau đó loop qua messages để lấy sender → N queries
```

### 3. Pagination Strategy
```python
# ✅ Cursor-based (efficient)
WHERE id < last_message_id ORDER BY id DESC LIMIT 20

# ❌ Offset-based (slow với large datasets)  
ORDER BY created_at DESC OFFSET 1000 LIMIT 20
```

---

## 🔮 FUTURE ENHANCEMENTS

### 1. Real-time với WebSocket
```python
# WebSocket endpoint cho real-time messages
@router.websocket("/conversations/{conversation_id}/ws")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int):
    # Connection management
    # Message broadcasting
    # Typing indicators
```

### 2. File Attachments
```python
# Message metadata structure
{
  "attachments": [
    {
      "id": "file_123",
      "filename": "document.pdf",
      "size": 1024000,
      "mime_type": "application/pdf",
      "url": "/api/v1/files/file_123"
    }
  ]
}
```

### 3. Message Reactions
```python
# New table: message_reactions
class MessageReaction(Base):
    message_id: int
    user_id: int  
    reaction: str  # "👍", "❤️", "😄"
    created_at: datetime
```

### 4. Full-text Search
```python
# PostgreSQL full-text search
SELECT * FROM messages 
WHERE to_tsvector('english', content) @@ plainto_tsquery('search term')
```

---

## 📊 MONITORING & LOGGING

### 1. Performance Metrics
- Response time per endpoint
- Database query performance
- Memory usage patterns
- Active connections

### 2. Business Metrics  
- Messages sent per day
- Active conversations
- User engagement
- Most used features

### 3. Error Tracking
- Authentication failures
- Permission violations
- Database errors
- API rate limits

Đây là hệ thống chat hoàn chỉnh với architecture rõ ràng, secure, và scalable! 🚀