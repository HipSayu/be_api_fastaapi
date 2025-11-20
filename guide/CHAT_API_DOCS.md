# Chat System API Documentation

## 🚀 Tổng quan hệ thống Chat

Hệ thống chat bao gồm 3 component chính:
- **Conversations**: Quản lý cuộc hội thoại 
- **ConversationMembers**: Quản lý thành viên trong cuộc hội thoại
- **Messages**: Quản lý tin nhắn

## 📊 Database Models

### Conversations Table
```sql
conversations:
- id (Primary Key)
- title (varchar)
- description (text, nullable) 
- conversation_type (enum: private, group, channel)
- created_by (Foreign Key -> users.id)
- metadata (jsonb, nullable)
- created_at, updated_at
- deleted (boolean, default=False)
```

### ConversationMembers Table  
```sql
conversation_members:
- id (Primary Key)
- conversation_id (Foreign Key -> conversations.id)
- user_id (Foreign Key -> users.id)
- role (enum: owner, admin, member)
- joined_at (timestamp)
- left_at (timestamp, nullable)
- is_active (boolean, default=True)
```

### Messages Table
```sql
messages:
- id (Primary Key)
- conversation_id (Foreign Key -> conversations.id)
- sender_id (Foreign Key -> users.id)
- content (text)
- reply_to (Foreign Key -> messages.id, nullable)
- metadata (jsonb, nullable)  # Cho file attachments, images, etc.
- created_at, edited_at (timestamps)
- deleted (boolean, default=False)
```

## 🔐 Authentication & Permissions

Tất cả endpoints yêu cầu JWT authentication:
```
Authorization: Bearer <access_token>
```

### Permission Levels:
- **Member**: Có thể đọc tin nhắn, gửi tin nhắn
- **Admin**: Member + quản lý thành viên, chỉnh sửa conversation
- **Owner**: Admin + xóa conversation

## 🛠️ API Endpoints

### 💬 Conversations

#### `POST /api/v1/conversations`
Tạo conversation mới
```json
{
  "title": "Team Discussion",
  "description": "Daily standup chat",
  "conversation_type": "group", 
  "metadata": {}
}
```

#### `GET /api/v1/conversations`
Lấy danh sách conversations của user
- Query params: `skip=0`, `limit=20`

#### `GET /api/v1/conversations/{id}`
Lấy thông tin conversation với danh sách members

#### `PUT /api/v1/conversations/{id}`
Cập nhật conversation (chỉ admin/owner)

#### `DELETE /api/v1/conversations/{id}`
Xóa conversation (chỉ owner)

#### `POST /api/v1/conversations/{id}/members/{user_id}`
Thêm member vào conversation (chỉ admin/owner)
- Query param: `role=member|admin`

#### `DELETE /api/v1/conversations/{id}/members/{user_id}`
Xóa member khỏi conversation (chỉ admin/owner)

#### `PATCH /api/v1/conversations/{id}/members/{user_id}/role`
Cập nhật role của member (chỉ admin/owner)
- Query param: `new_role=member|admin`

#### `POST /api/v1/conversations/{id}/leave`
Rời khỏi conversation

### 💬 Messages

#### `POST /api/v1/conversations/{id}/messages`
Gửi tin nhắn mới
```json
{
  "content": "Hello world!",
  "reply_to": 123,  // Optional: reply to message
  "metadata": {}    // Optional: attachments, etc.
}
```

#### `GET /api/v1/conversations/{id}/messages`
Lấy danh sách tin nhắn
- Query params: `skip=0`, `limit=50`, `before_message_id=456`

#### `GET /api/v1/conversations/{id}/messages/{message_id}`
Lấy chi tiết tin nhắn

#### `PUT /api/v1/conversations/{id}/messages/{message_id}`
Chỉnh sửa tin nhắn (chỉ người gửi)
```json
{
  "content": "Updated message content"
}
```

#### `DELETE /api/v1/conversations/{id}/messages/{message_id}`
Xóa tin nhắn (chỉ người gửi)

#### `GET /api/v1/conversations/{id}/messages/{message_id}/replies`
Lấy danh sách reply của tin nhắn

#### `GET /api/v1/conversations/{id}/messages/search`
Tìm kiếm tin nhắn
- Query param: `q=search_term`, `limit=20`

#### `GET /api/v1/conversations/{id}/messages/count`
Lấy tổng số tin nhắn trong conversation

## 📝 Response Schemas

### ConversationRead
```json
{
  "id": 1,
  "title": "Team Discussion",
  "description": "Daily standup chat",
  "conversation_type": "group",
  "created_by": 1,
  "metadata": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### ConversationWithMembers
```json
{
  "id": 1,
  "title": "Team Discussion",
  "members": [
    {
      "id": 1,
      "user_id": 1,
      "role": "owner",
      "joined_at": "2024-01-01T00:00:00Z",
      "is_active": true
    }
  ]
}
```

### MessageWithSender
```json
{
  "id": 1,
  "conversation_id": 1,
  "sender_id": 1,
  "content": "Hello world!",
  "reply_to": null,
  "metadata": {},
  "created_at": "2024-01-01T00:00:00Z",
  "edited_at": null,
  "sender": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

## 🔧 CRUD Operations Implemented

### ConversationCRUD
- ✅ `create()` - Tạo conversation mới với owner
- ✅ `get()` - Lấy conversation theo ID  
- ✅ `get_with_members()` - Lấy conversation với danh sách members
- ✅ `get_user_conversations()` - Lấy conversations của user
- ✅ `update()` - Cập nhật conversation
- ✅ `delete()` - Soft delete conversation

### ConversationMemberCRUD
- ✅ `add_user_to_conversation()` - Thêm user vào conversation
- ✅ `remove_user_from_conversation()` - Xóa user khỏi conversation  
- ✅ `get_member()` - Lấy thông tin member
- ✅ `get_conversation_members()` - Lấy danh sách members
- ✅ `update_user_role()` - Cập nhật role của user
- ✅ `is_user_in_conversation()` - Kiểm tra user có trong conversation
- ✅ `get_member_count()` - Đếm số members

### MessageCRUD
- ✅ `create()` - Tạo tin nhắn mới
- ✅ `get()` - Lấy tin nhắn theo ID
- ✅ `get_with_sender()` - Lấy tin nhắn với thông tin người gửi
- ✅ `get_conversation_messages()` - Lấy tin nhắn trong conversation
- ✅ `update()` - Chỉnh sửa tin nhắn
- ✅ `delete()` - Soft delete tin nhắn
- ✅ `get_replies()` - Lấy replies của tin nhắn
- ✅ `search_messages()` - Tìm kiếm tin nhắn
- ✅ `get_message_count()` - Đếm tin nhắn
- ✅ `check_user_can_edit()` - Kiểm tra quyền edit

## 🚀 Next Steps

1. **WebSocket Support**: Thêm real-time messaging
2. **File Attachments**: Upload/download files trong tin nhắn  
3. **Message Reactions**: Like, emoji reactions
4. **Typing Indicators**: Hiển thị khi người dùng đang gõ
5. **Message Threading**: Organize replies better
6. **Push Notifications**: Thông báo tin nhắn mới
7. **Message Encryption**: End-to-end encryption
8. **Admin Panel**: Quản lý conversations trong admin interface

## 🧪 Testing

Sử dụng FastAPI docs tại `http://localhost:8000/docs` để test các endpoints.

### Test Flow:
1. Login để lấy access token
2. Tạo conversation mới
3. Thêm members vào conversation  
4. Gửi tin nhắn
5. Test reply, edit, delete messages
6. Test search và pagination