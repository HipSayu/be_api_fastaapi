# 🧪 DEMO TEST CHAT API

## 🚀 Hướng dẫn Test Chat System

### 1. 🔑 Đăng nhập để lấy Access Token

```bash
# POST /api/v1/login
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@example.com",
    "password": "admin123"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. 💬 Tạo Conversation mới

```bash
# POST /api/v1/conversations
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Daily Standup",
    "description": "Daily team sync up discussion",
    "conversation_type": "group",
    "metadata": {
      "avatar": "team-avatar.jpg",
      "settings": {
        "notifications": true,
        "auto_archive": false
      }
    }
  }'

# Response:
{
  "id": 1,
  "title": "Team Daily Standup",
  "description": "Daily team sync up discussion",
  "conversation_type": "group",
  "created_by": 1,
  "metadata": {...},
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### 3. 👥 Lấy danh sách Conversations của user

```bash
# GET /api/v1/conversations
curl -X GET "http://localhost:8000/api/v1/conversations?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response:
[
  {
    "id": 1,
    "title": "Team Daily Standup",
    "description": "Daily team sync up discussion",
    "conversation_type": "group",
    "created_by": 1,
    "created_at": "2024-01-01T10:00:00Z"
  }
]
```

### 4. 📋 Lấy chi tiết Conversation với Members

```bash
# GET /api/v1/conversations/{id}
curl -X GET "http://localhost:8000/api/v1/conversations/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response:
{
  "id": 1,
  "title": "Team Daily Standup",
  "members": [
    {
      "id": 1,
      "user_id": 1,
      "role": "owner",
      "joined_at": "2024-01-01T10:00:00Z",
      "is_active": true
    }
  ]
}
```

### 5. ➕ Thêm member vào Conversation

```bash
# POST /api/v1/conversations/{id}/members/{user_id}
curl -X POST "http://localhost:8000/api/v1/conversations/1/members/2?role=member" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response: 201 Created
```

### 6. ✉️ Gửi tin nhắn

```bash
# POST /api/v1/conversations/{id}/messages
curl -X POST "http://localhost:8000/api/v1/conversations/1/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Good morning team! Ready for standup? 🚀",
    "metadata": {
      "type": "text",
      "mentions": [],
      "attachments": []
    }
  }'

# Response:
{
  "id": 1,
  "conversation_id": 1,
  "sender_id": 1,
  "content": "Good morning team! Ready for standup? 🚀",
  "reply_to": null,
  "metadata": {...},
  "created_at": "2024-01-01T10:30:00Z",
  "edited_at": null
}
```

### 7. 💬 Reply tin nhắn

```bash
# POST /api/v1/conversations/{id}/messages (với reply_to)
curl -X POST "http://localhost:8000/api/v1/conversations/1/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Yes! Let me share yesterday'\''s progress 📊",
    "reply_to": 1,
    "metadata": {
      "type": "reply"
    }
  }'

# Response:
{
  "id": 2,
  "conversation_id": 1,
  "sender_id": 2,
  "content": "Yes! Let me share yesterday's progress 📊",
  "reply_to": 1,
  "created_at": "2024-01-01T10:32:00Z"
}
```

### 8. 📜 Lấy danh sách tin nhắn

```bash
# GET /api/v1/conversations/{id}/messages
curl -X GET "http://localhost:8000/api/v1/conversations/1/messages?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response:
[
  {
    "id": 1,
    "conversation_id": 1,
    "sender_id": 1,
    "content": "Good morning team! Ready for standup? 🚀",
    "reply_to": null,
    "created_at": "2024-01-01T10:30:00Z",
    "sender": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com"
    }
  },
  {
    "id": 2,
    "conversation_id": 1,
    "sender_id": 2,
    "content": "Yes! Let me share yesterday's progress 📊",
    "reply_to": 1,
    "created_at": "2024-01-01T10:32:00Z",
    "sender": {
      "id": 2,
      "username": "user2",
      "email": "user2@example.com"
    }
  }
]
```

### 9. ✏️ Chỉnh sửa tin nhắn

```bash
# PUT /api/v1/conversations/{id}/messages/{message_id}
curl -X PUT "http://localhost:8000/api/v1/conversations/1/messages/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Good morning team! Ready for standup? 🚀 (Updated with agenda)",
    "metadata": {
      "type": "text",
      "edited": true
    }
  }'

# Response:
{
  "id": 1,
  "conversation_id": 1,
  "content": "Good morning team! Ready for standup? 🚀 (Updated with agenda)",
  "created_at": "2024-01-01T10:30:00Z",
  "edited_at": "2024-01-01T10:35:00Z"
}
```

### 10. 🔍 Tìm kiếm tin nhắn

```bash
# GET /api/v1/conversations/{id}/messages/search
curl -X GET "http://localhost:8000/api/v1/conversations/1/messages/search?q=standup&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response:
[
  {
    "id": 1,
    "content": "Good morning team! Ready for standup? 🚀 (Updated with agenda)",
    "sender": {
      "username": "admin"
    },
    "created_at": "2024-01-01T10:30:00Z"
  }
]
```

### 11. 🔢 Đếm tin nhắn

```bash
# GET /api/v1/conversations/{id}/messages/count
curl -X GET "http://localhost:8000/api/v1/conversations/1/messages/count" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response:
{
  "count": 2
}
```

### 12. 🗑️ Xóa tin nhắn

```bash
# DELETE /api/v1/conversations/{id}/messages/{message_id}
curl -X DELETE "http://localhost:8000/api/v1/conversations/1/messages/2" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response: 204 No Content
```

### 13. 👑 Cập nhật role member (chỉ admin/owner)

```bash
# PATCH /api/v1/conversations/{id}/members/{user_id}/role
curl -X PATCH "http://localhost:8000/api/v1/conversations/1/members/2/role?new_role=admin" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response: 200 OK
```

### 14. 🚪 Rời khỏi conversation

```bash
# POST /api/v1/conversations/{id}/leave
curl -X POST "http://localhost:8000/api/v1/conversations/1/leave" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response: 204 No Content
```

### 15. 🗑️ Xóa conversation (chỉ owner)

```bash
# DELETE /api/v1/conversations/{id}
curl -X DELETE "http://localhost:8000/api/v1/conversations/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response: 204 No Content
```

---

## 🧪 Test Scenarios Nâng cao

### Scenario 1: Group Chat Workflow

```python
# Python test script
import requests
import json

base_url = "http://localhost:8000/api/v1"
token = "YOUR_ACCESS_TOKEN"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Tạo group chat
conversation_data = {
    "title": "Product Planning Q1",
    "description": "Planning for Q1 product roadmap",
    "conversation_type": "group"
}
response = requests.post(f"{base_url}/conversations", 
                        headers=headers, 
                        json=conversation_data)
conversation = response.json()
conversation_id = conversation["id"]

# 2. Thêm team members
user_ids = [2, 3, 4, 5]  # Team member IDs
for user_id in user_ids:
    requests.post(f"{base_url}/conversations/{conversation_id}/members/{user_id}",
                 headers=headers,
                 params={"role": "member"})

# 3. Gửi welcome message
welcome_msg = {
    "content": "Welcome to Q1 planning! Let's discuss our roadmap 🗺️",
    "metadata": {
        "type": "announcement",
        "priority": "high"
    }
}
requests.post(f"{base_url}/conversations/{conversation_id}/messages",
             headers=headers,
             json=welcome_msg)

# 4. Simulate conversation
messages = [
    "What are our top priorities for Q1?",
    "I think we should focus on mobile app improvements",
    "Agree! User retention is critical",
    "Should we include the new analytics dashboard?"
]

for content in messages:
    msg_data = {"content": content}
    requests.post(f"{base_url}/conversations/{conversation_id}/messages",
                 headers=headers, 
                 json=msg_data)

print(f"Created conversation {conversation_id} with {len(messages)} messages")
```

### Scenario 2: Message Threading

```python
# Test reply chain
base_message = {
    "content": "What's everyone's availability for sprint planning?"
}
response = requests.post(f"{base_url}/conversations/{conversation_id}/messages",
                        headers=headers, json=base_message)
parent_message_id = response.json()["id"]

# Replies
replies = [
    "I'm free Monday 2-4 PM",
    "Tuesday morning works for me", 
    "Wednesday is best for me",
    "Let's go with Monday 2 PM then!"
]

for reply_content in replies:
    reply_data = {
        "content": reply_content,
        "reply_to": parent_message_id
    }
    requests.post(f"{base_url}/conversations/{conversation_id}/messages",
                 headers=headers, json=reply_data)

# Get replies
replies_response = requests.get(
    f"{base_url}/conversations/{conversation_id}/messages/{parent_message_id}/replies",
    headers=headers
)
print(f"Parent message has {len(replies_response.json())} replies")
```

### Scenario 3: Error Handling Test

```python
# Test các error cases
def test_unauthorized_access():
    # No token
    response = requests.get(f"{base_url}/conversations")
    assert response.status_code == 401
    
def test_forbidden_access():
    # Try to access conversation user is not member of
    response = requests.get(f"{base_url}/conversations/999", headers=headers)
    assert response.status_code == 404 or response.status_code == 403
    
def test_invalid_data():
    # Empty title
    invalid_data = {"title": "", "conversation_type": "group"}
    response = requests.post(f"{base_url}/conversations", 
                           headers=headers, json=invalid_data)
    assert response.status_code == 422
    
def test_edit_others_message():
    # Try to edit message from another user
    response = requests.put(f"{base_url}/conversations/{conversation_id}/messages/1",
                          headers=headers, 
                          json={"content": "Hacked message"})
    assert response.status_code == 403

# Run tests
test_unauthorized_access()
test_forbidden_access() 
test_invalid_data()
print("All error handling tests passed! ✅")
```

---

## 📊 Performance Testing

### Load Test với nhiều messages

```python
import concurrent.futures
import time

def send_bulk_messages(conversation_id, count=100):
    start_time = time.time()
    
    def send_message(i):
        msg_data = {
            "content": f"Bulk message #{i} - performance test",
            "metadata": {"batch": True, "index": i}
        }
        response = requests.post(
            f"{base_url}/conversations/{conversation_id}/messages",
            headers=headers, 
            json=msg_data
        )
        return response.status_code == 201
    
    # Parallel sending
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_message, i) for i in range(count)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    success_count = sum(results)
    
    print(f"Sent {success_count}/{count} messages in {end_time - start_time:.2f}s")
    print(f"Rate: {success_count / (end_time - start_time):.2f} messages/second")

# Test với 100 messages
send_bulk_messages(conversation_id, 100)
```

---

## 🔍 Debugging Tips

### 1. Check Database State

```sql
-- Check conversations
SELECT id, title, conversation_type, created_by, deleted 
FROM conversations;

-- Check members
SELECT cm.*, u.username 
FROM conversation_members cm 
JOIN users u ON cm.user_id = u.id
WHERE conversation_id = 1;

-- Check messages
SELECT m.id, m.content, m.reply_to, u.username as sender, m.created_at
FROM messages m
JOIN users u ON m.sender_id = u.id  
WHERE conversation_id = 1
ORDER BY created_at;
```

### 2. Check Logs

```bash
# FastAPI logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f app
```

### 3. Monitor Performance

```python
# Add timing middleware
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

## 🎯 Next Steps

1. **Real-time Testing**: Implement WebSocket connections
2. **File Upload**: Test attachment functionality  
3. **Push Notifications**: Mobile app integration
4. **Analytics**: Track message patterns and user engagement
5. **Stress Testing**: Handle thousands of concurrent users

Bây giờ bạn có thể test toàn bộ chat system! 🚀