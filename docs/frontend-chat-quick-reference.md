# Chat API Quick Reference

## Base URL
```
/chats
```

## Authentication
```
Authorization: Bearer <access_token>
```

## Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chats/{account_id}/{agent_id}` | Create new chat |
| GET | `/chats/{account_id}/{agent_id}` | List all chats |
| GET | `/chats/{account_id}/{agent_id}/{chat_id}` | Get chat with messages |
| PATCH | `/chats/{account_id}/{agent_id}/{chat_id}` | Update chat title |
| DELETE | `/chats/{account_id}/{agent_id}/{chat_id}` | Delete chat |
| POST | `/chats/{account_id}/{agent_id}/{chat_id}/messages` | Send message |

## cURL Examples

### 1. Create Chat
```bash
curl -X POST "https://api.example.com/chats/{account_id}/{agent_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My New Chat"}'
```

### 2. List Chats
```bash
curl -X GET "https://api.example.com/chats/{account_id}/{agent_id}?skip=0&limit=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Get Chat with Messages
```bash
curl -X GET "https://api.example.com/chats/{account_id}/{agent_id}/{chat_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Update Chat Title
```bash
curl -X PATCH "https://api.example.com/chats/{account_id}/{agent_id}/{chat_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'
```

### 5. Delete Chat
```bash
curl -X DELETE "https://api.example.com/chats/{account_id}/{agent_id}/{chat_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Send Message (Most Important!)
```bash
curl -X POST "https://api.example.com/chats/{account_id}/{agent_id}/{chat_id}/messages" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "What are the top 10 products by sales?"}'
```

## Response Examples

### Chat Object
```json
{
  "id": "uuid",
  "title": "Sales Analysis",
  "agent_id": "uuid",
  "user_id": "uuid",
  "account_id": "uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "message_count": 5
}
```

### Message Object
```json
{
  "id": "uuid",
  "chat_id": "uuid",
  "role": "assistant",
  "content": "The top 10 products by sales are...",
  "action": "QUERY",
  "final_dax": "EVALUATE TOPN(10, ...)",
  "resolution_note": "",
  "error": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Send Message Response
```json
{
  "message": {
    "id": "uuid",
    "chat_id": "uuid",
    "role": "assistant",
    "content": "AI response here...",
    "action": "QUERY",
    "final_dax": "EVALUATE ...",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "chat": {
    "id": "uuid",
    "title": "Sales Analysis",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

## Error Responses

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `400` - Bad Request (invalid data)
- `403` - Forbidden (permission denied)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

