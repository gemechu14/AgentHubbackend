# Frontend Chat Integration Guide

This guide provides everything you need to integrate the ChatGPT-like chat system into your frontend application.

## Overview

The chat system allows users to have multiple conversation threads (chats) with each agent. Each chat stores all messages persistently, similar to ChatGPT's interface.

## Base URL

All endpoints are prefixed with `/chats`

## Authentication

All endpoints require authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## API Endpoints

### 1. Create a New Chat

**Endpoint:** `POST /chats/{account_id}/{agent_id}`

**Description:** Create a new chat conversation for an agent.

**Request Body:**
```typescript
interface ChatCreate {
  title?: string;  // Optional, defaults to "New Chat"
}
```

**Response:** `ChatOut`
```typescript
interface ChatOut {
  id: string;                    // UUID
  title: string;
  agent_id: string;              // UUID
  user_id: string;               // UUID
  account_id: string;            // UUID
  created_at: string;            // ISO 8601 datetime
  updated_at: string;            // ISO 8601 datetime
  message_count?: number;         // Number of messages (when listing)
}
```

**Example Request:**
```typescript
const createChat = async (
  accountId: string,
  agentId: string,
  title?: string
) => {
  const response = await fetch(
    `/chats/${accountId}/${agentId}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ title })
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to create chat');
  }
  
  return await response.json();
};
```

---

### 2. List All Chats for an Agent

**Endpoint:** `GET /chats/{account_id}/{agent_id}?skip=0&limit=100`

**Description:** Get all chat conversations for a specific agent with pagination.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 100, max: 1000)

**Response:** `ChatListOut`
```typescript
interface ChatListOut {
  chats: ChatOut[];
  total: number;
}
```

**Example Request:**
```typescript
const listChats = async (
  accountId: string,
  agentId: string,
  skip = 0,
  limit = 100
) => {
  const response = await fetch(
    `/chats/${accountId}/${agentId}?skip=${skip}&limit=${limit}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  return await response.json();
};
```

---

### 3. Get a Specific Chat with Messages

**Endpoint:** `GET /chats/{account_id}/{agent_id}/{chat_id}`

**Description:** Get a specific chat conversation with all its messages in chronological order.

**Response:** `ChatWithMessagesOut`
```typescript
interface ChatMessageOut {
  id: string;                    // UUID
  chat_id: string;               // UUID
  role: "user" | "assistant";
  content: string;
  action?: string;               // "DESCRIBE", "QUERY", "ERROR"
  dax_attempts?: string;         // JSON string array
  final_dax?: string;
  resolution_note?: string;
  error?: string;
  created_at: string;            // ISO 8601 datetime
}

interface ChatWithMessagesOut {
  id: string;
  title: string;
  agent_id: string;
  user_id: string;
  account_id: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessageOut[];
}
```

**Example Request:**
```typescript
const getChat = async (
  accountId: string,
  agentId: string,
  chatId: string
) => {
  const response = await fetch(
    `/chats/${accountId}/${agentId}/${chatId}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Chat not found');
  }
  
  return await response.json();
};
```

---

### 4. Update Chat Title

**Endpoint:** `PATCH /chats/{account_id}/{agent_id}/{chat_id}`

**Description:** Update the title of a chat conversation.

**Request Body:**
```typescript
interface ChatUpdate {
  title?: string;
}
```

**Response:** `ChatOut`

**Example Request:**
```typescript
const updateChatTitle = async (
  accountId: string,
  agentId: string,
  chatId: string,
  newTitle: string
) => {
  const response = await fetch(
    `/chats/${accountId}/${agentId}/${chatId}`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ title: newTitle })
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to update chat title');
  }
  
  return await response.json();
};
```

---

### 5. Delete a Chat

**Endpoint:** `DELETE /chats/{account_id}/{agent_id}/{chat_id}`

**Description:** Delete a chat conversation and all its messages. This action cannot be undone.

**Response:**
```typescript
{
  ok: true;
  message: "Chat deleted successfully";
}
```

**Example Request:**
```typescript
const deleteChat = async (
  accountId: string,
  agentId: string,
  chatId: string
) => {
  const response = await fetch(
    `/chats/${accountId}/${agentId}/${chatId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to delete chat');
  }
  
  return await response.json();
};
```

---

### 6. Send a Message (Most Important!)

**Endpoint:** `POST /chats/{account_id}/{agent_id}/{chat_id}/messages`

**Description:** Send a message in a chat and get an AI response. This endpoint:
1. Stores the user's message
2. Processes it through the agent's chat service (Power BI)
3. Stores the assistant's response
4. Returns both messages

**Request Body:**
```typescript
interface MessageCreate {
  content: string;  // Required, min length: 1
}
```

**Response:** `MessageResponse`
```typescript
interface MessageResponse {
  message: ChatMessageOut;  // The assistant's response
  chat: ChatOut;            // Updated chat object
}
```

**Example Request:**
```typescript
const sendMessage = async (
  accountId: string,
  agentId: string,
  chatId: string,
  content: string
) => {
  const response = await fetch(
    `/chats/${accountId}/${agentId}/${chatId}/messages`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ content })
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to send message');
  }
  
  return await response.json();
};
```

---

## Complete TypeScript Types

```typescript
// Request Types
interface ChatCreate {
  title?: string;
}

interface ChatUpdate {
  title?: string;
}

interface MessageCreate {
  content: string;
}

// Response Types
interface ChatOut {
  id: string;
  title: string;
  agent_id: string;
  user_id: string;
  account_id: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

interface ChatMessageOut {
  id: string;
  chat_id: string;
  role: "user" | "assistant";
  content: string;
  action?: "DESCRIBE" | "QUERY" | "ERROR";
  dax_attempts?: string;
  final_dax?: string;
  resolution_note?: string;
  error?: string;
  created_at: string;
}

interface ChatWithMessagesOut {
  id: string;
  title: string;
  agent_id: string;
  user_id: string;
  account_id: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessageOut[];
}

interface ChatListOut {
  chats: ChatOut[];
  total: number;
}

interface MessageResponse {
  message: ChatMessageOut;
  chat: ChatOut;
}
```

---

## Complete React/TypeScript Example

```typescript
import { useState, useEffect } from 'react';

interface ChatHookProps {
  accountId: string;
  agentId: string;
  accessToken: string;
}

export const useChat = ({ accountId, agentId, accessToken }: ChatHookProps) => {
  const [chats, setChats] = useState<ChatOut[]>([]);
  const [currentChat, setCurrentChat] = useState<ChatWithMessagesOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // List all chats
  const loadChats = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/chats/${accountId}/${agentId}?skip=0&limit=100`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        }
      );
      const data: ChatListOut = await response.json();
      setChats(data.chats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chats');
    } finally {
      setLoading(false);
    }
  };

  // Create a new chat
  const createChat = async (title?: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `/chats/${accountId}/${agentId}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ title })
        }
      );
      const newChat: ChatOut = await response.json();
      setChats(prev => [newChat, ...prev]);
      return newChat;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create chat');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Load a specific chat with messages
  const loadChat = async (chatId: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `/chats/${accountId}/${agentId}/${chatId}`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        }
      );
      const chat: ChatWithMessagesOut = await response.json();
      setCurrentChat(chat);
      return chat;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chat');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Send a message
  const sendMessage = async (chatId: string, content: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `/chats/${accountId}/${agentId}/${chatId}/messages`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send message');
      }

      const data: MessageResponse = await response.json();
      
      // Update current chat with new messages
      if (currentChat && currentChat.id === chatId) {
        setCurrentChat(prev => {
          if (!prev) return null;
          return {
            ...prev,
            messages: [
              ...prev.messages,
              // Add user message (you might need to fetch the full chat)
              data.message
            ],
            updated_at: data.chat.updated_at
          };
        });
      }

      // Reload chats to update message_count
      await loadChats();
      
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Update chat title
  const updateChatTitle = async (chatId: string, newTitle: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `/chats/${accountId}/${agentId}/${chatId}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ title: newTitle })
        }
      );
      const updatedChat: ChatOut = await response.json();
      setChats(prev => prev.map(chat => 
        chat.id === chatId ? updatedChat : chat
      ));
      if (currentChat && currentChat.id === chatId) {
        setCurrentChat(prev => prev ? { ...prev, title: newTitle } : null);
      }
      return updatedChat;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update title');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Delete a chat
  const deleteChat = async (chatId: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `/chats/${accountId}/${agentId}/${chatId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to delete chat');
      }

      setChats(prev => prev.filter(chat => chat.id !== chatId));
      if (currentChat && currentChat.id === chatId) {
        setCurrentChat(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete chat');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    chats,
    currentChat,
    loading,
    error,
    loadChats,
    createChat,
    loadChat,
    sendMessage,
    updateChatTitle,
    deleteChat
  };
};
```

---

## UI Flow Recommendations

### 1. Chat List Sidebar
- Display all chats for the selected agent
- Show chat title and last message preview
- Show message count or last updated time
- Allow creating new chat with a "+" button
- Allow renaming chats (double-click or edit button)
- Allow deleting chats (with confirmation)

### 2. Chat Interface
- Display messages in chronological order
- Show user messages on the right, assistant messages on the left
- Display loading state while sending message
- Show error messages if something goes wrong
- Auto-scroll to bottom when new messages arrive
- Display metadata (DAX queries, resolution notes) in a collapsible section

### 3. Message Input
- Text input at the bottom
- Send button (or Enter key)
- Disable input while message is being sent
- Show typing indicator while waiting for response

---

## Error Handling

All endpoints may return the following error responses:

```typescript
// 400 Bad Request
{
  "detail": "Error message"
}

// 403 Forbidden
{
  "detail": "Account ID mismatch" | "Insufficient permissions"
}

// 404 Not Found
{
  "detail": "Agent not found" | "Chat not found"
}

// 500 Internal Server Error
{
  "detail": "Internal server error"
}
```

**Example Error Handling:**
```typescript
try {
  const response = await sendMessage(accountId, agentId, chatId, message);
  // Handle success
} catch (error) {
  if (error instanceof Error) {
    // Display error.message to user
    console.error('Error:', error.message);
  }
}
```

---

## Important Notes

1. **Chat Title Auto-Generation**: The chat title is automatically generated from the first message (first 50 characters). You can update it later using the PATCH endpoint.

2. **Message Ordering**: Messages are returned in chronological order (oldest first). You may want to reverse this for display (newest at bottom).

3. **Real-time Updates**: The current implementation doesn't include WebSocket support. You'll need to poll or refetch the chat after sending a message to get the latest state.

4. **Pagination**: When listing chats, use pagination for better performance if there are many chats.

5. **Agent Type**: Currently, only agents with `connection_type = "POWERBI"` support chat messages.

---

## Quick Start Checklist

- [ ] Set up API client with authentication
- [ ] Create TypeScript interfaces/types
- [ ] Implement chat list component
- [ ] Implement chat message component
- [ ] Implement message input component
- [ ] Add error handling
- [ ] Add loading states
- [ ] Test create chat flow
- [ ] Test send message flow
- [ ] Test update/delete chat flow
- [ ] Add UI polish (animations, styling)

---

## Example Usage Flow

```typescript
// 1. User selects an agent
const agentId = "agent-uuid-here";
const accountId = "account-uuid-here";

// 2. Load all chats for this agent
const { chats } = await listChats(accountId, agentId);

// 3. User creates a new chat (or selects existing)
const newChat = await createChat(accountId, agentId, "My New Chat");

// 4. Load the chat with messages
const chat = await loadChat(accountId, agentId, newChat.id);

// 5. User sends a message
const response = await sendMessage(
  accountId,
  agentId,
  newChat.id,
  "What are the top 10 products by sales?"
);

// 6. Display the response
console.log(response.message.content); // AI's answer
console.log(response.message.final_dax); // DAX query used (if QUERY action)
```

---

For questions or issues, contact the backend team or refer to the API documentation at `/gibberish-xyz-123` (Swagger UI).

