# First Time Chat Flow - What Happens When You Ask Your First Question

## Overview

When you ask your first question in a chat, here's the step-by-step flow:

## Step-by-Step Flow

### Step 1: Create a Chat (Required First)

**Before you can ask a question, you need to create a chat conversation.**

```typescript
// Create a new chat
POST /chats/{account_id}/{agent_id}
{
  "title": "New Chat"  // Optional - defaults to "New Chat"
}
```

**Response:**
```json
{
  "id": "chat-uuid",
  "title": "New Chat",
  "agent_id": "agent-uuid",
  "user_id": "user-uuid",
  "account_id": "account-uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**What happens:**
- ✅ A new chat record is created in the database
- ✅ Chat title is set to "New Chat" (or your provided title)
- ✅ Chat is linked to the agent, user, and account
- ✅ Chat ID is returned for use in subsequent requests

---

### Step 2: Send Your First Message

**Now you can send your first question:**

```typescript
// Send first message
POST /chats/{account_id}/{agent_id}/{chat_id}/messages
{
  "content": "What are the top 10 products by sales?"
}
```

**What happens behind the scenes:**

1. **User Message is Stored**
   - Your question is saved as a `ChatMessage` with `role: "user"`
   - Stored in the database immediately

2. **Chat Title Auto-Update** (First Message Only)
   - If chat title is still "New Chat", it gets automatically updated
   - New title = first 50 characters of your message
   - Example: "What are the top 10 products by sales?" → "What are the top 10 products by sales?"
   - If message is longer than 50 chars, it gets truncated with "..."

3. **AI Processing**
   - Your question is sent to the Power BI chat service
   - The service:
     - Connects to Power BI using agent's credentials
     - Loads/caches the schema (first time only, then cached)
     - Decides: DESCRIBE (answer from schema) or QUERY (execute DAX)
     - Processes your question and generates a response

4. **Assistant Message is Stored**
   - AI response is saved as a `ChatMessage` with `role: "assistant"`
   - Includes metadata:
     - `action`: "DESCRIBE", "QUERY", or "ERROR"
     - `final_dax`: The DAX query used (if QUERY action)
     - `dax_attempts`: All DAX queries attempted (if multiple tries)
     - `resolution_note`: Any value resolution/typo corrections
     - `error`: Error message if something went wrong

5. **Chat Updated**
   - `updated_at` timestamp is refreshed
   - Both messages are now in the database

**Response:**
```json
{
  "message": {
    "id": "message-uuid",
    "chat_id": "chat-uuid",
    "role": "assistant",
    "content": "The top 10 products by sales are:\n\n1. Product A - $50,000\n2. Product B - $45,000\n...",
    "action": "QUERY",
    "final_dax": "EVALUATE TOPN(10, ...)",
    "dax_attempts": "[\"EVALUATE TOPN(10, ...)\"]",
    "resolution_note": "",
    "error": null,
    "created_at": "2024-01-01T00:00:01Z"
  },
  "chat": {
    "id": "chat-uuid",
    "title": "What are the top 10 products by sales?",  // Auto-updated!
    "updated_at": "2024-01-01T00:00:01Z"
  }
}
```

---

## Complete Example Flow

### Frontend Implementation Example

```typescript
// 1. User selects an agent and wants to start chatting
const agentId = "agent-uuid";
const accountId = "account-uuid";

// 2. Create a new chat (first time only)
const newChat = await fetch(`/chats/${accountId}/${agentId}`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ title: "New Chat" })
}).then(r => r.json());

console.log("Chat created:", newChat.id);
// Chat title: "New Chat"

// 3. User types and sends first message
const firstMessage = "What are the top 10 products by sales?";

const response = await fetch(
  `/chats/${accountId}/${agentId}/${newChat.id}/messages`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ content: firstMessage })
  }
).then(r => r.json());

console.log("AI Response:", response.message.content);
console.log("Chat title updated to:", response.chat.title);
// Chat title: "What are the top 10 products by sales?" (auto-updated!)

// 4. Continue conversation - just send more messages
const secondMessage = "What about last month?";

const response2 = await fetch(
  `/chats/${accountId}/${agentId}/${newChat.id}/messages`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ content: secondMessage })
  }
).then(r => r.json());
```

---

## Important Points

### ✅ What You Need to Do

1. **Create chat first** - You cannot send a message without a chat ID
2. **Provide chat_id** - Every message requires the chat ID
3. **Handle the response** - The response includes both the message and updated chat

### 🤖 What Happens Automatically

1. **Chat title auto-update** - Only on the first message if title is "New Chat"
2. **Message storage** - Both user and assistant messages are automatically stored
3. **Schema caching** - Power BI schema is cached after first load (per workspace+dataset)
4. **Error handling** - Errors are stored as assistant messages with `action: "ERROR"`

### 📝 Chat Title Behavior

- **First message**: If title is "New Chat", it auto-updates to first 50 chars of message
- **Subsequent messages**: Title doesn't change automatically (you can update manually)
- **Manual update**: Use `PATCH /chats/{account_id}/{agent_id}/{chat_id}` to change title anytime

---

## UI Flow Recommendations

### Option 1: Auto-Create Chat on First Message (Recommended)

```typescript
async function sendMessage(agentId: string, accountId: string, content: string, chatId?: string) {
  // If no chatId, create a new chat first
  if (!chatId) {
    const newChat = await createChat(accountId, agentId);
    chatId = newChat.id;
  }
  
  // Then send the message
  const response = await sendMessageToChat(accountId, agentId, chatId, content);
  
  return { chatId, response };
}
```

### Option 2: Explicit Chat Creation

```typescript
// User clicks "New Chat" button
const chat = await createChat(accountId, agentId, "My Analysis");

// User types and sends message
const response = await sendMessage(accountId, agentId, chat.id, "What are the top products?");
```

---

## Error Scenarios

### If Agent Doesn't Exist
```json
{
  "detail": "Agent not found"
}
```
**Solution:** Verify the agent_id is correct and belongs to the account

### If Chat Doesn't Exist
```json
{
  "detail": "Chat not found"
}
```
**Solution:** Create the chat first before sending messages

### If Agent is Not POWERBI Type
```json
{
  "detail": "Chat messages only supported for POWERBI agents. This agent has type: DB"
}
```
**Solution:** Only POWERBI agents support chat messages currently

### If OpenAI API Key Missing
```json
{
  "detail": "OpenAI API key is required. Set it in the agent's api_key field or OPENAI_API_KEY environment variable."
}
```
**Solution:** Set the OpenAI API key in the agent configuration or environment

---

## Summary

**First Time Flow:**
1. ✅ Create chat → Get `chat_id`
2. ✅ Send first message → Chat title auto-updates
3. ✅ Continue conversation → Just send more messages to same `chat_id`

**Key Points:**
- Chat must exist before sending messages
- First message auto-updates chat title
- All messages are stored permanently
- Schema is cached after first load (fast subsequent queries)






