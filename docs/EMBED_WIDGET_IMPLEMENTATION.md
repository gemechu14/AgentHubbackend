# Embeddable Chatbot Widget - Implementation Complete ✅

## What Was Implemented

A complete embeddable iframe chatbot widget system that allows users to embed agent chatbots into any website without authentication. Chat messages are **NOT stored** (non-persistent).

---

## 🎯 Key Features

✅ **Agent-Level Embedding** - Each agent has its own embeddable widget
✅ **No Authentication Required** - Public access, works on any website
✅ **Non-Persistent Chat** - Messages are NOT stored in database
✅ **Fully Responsive** - Mobile-friendly design
✅ **PostMessage API** - Two-way communication between widget and parent page
✅ **Modern UI** - Clean, professional chatbot interface
✅ **Error Handling** - Graceful error messages
✅ **Real-time Responses** - Instant AI-powered answers

---

## 📁 Files Created/Modified

### New Files:
1. **`app/api/routes/embed.py`** - Embed widget routes and chat endpoint
2. **`docs/frontend-embed-widget.md`** - Complete frontend integration guide

### Modified Files:
1. **`app/main.py`** - Added embed router and security headers

---

## 🔌 API Endpoints

### 1. Widget HTML Endpoint
```
GET /embed/widget/{agent_id}
```
Returns HTML page with embedded chatbot interface.

**Example:**
```
https://your-backend.com/embed/widget/123e4567-e89b-12d3-a456-426614174000
```

### 2. Chat Endpoint (Non-Persistent)
```
POST /embed/chat/{agent_id}
```
Sends a message to agent and returns response. Messages are NOT stored.

**Request:**
```json
{
  "question": "What are the top 10 products by sales?"
}
```

**Response:**
```json
{
  "answer": "The top 10 products are...",
  "action": "QUERY",
  "final_dax": "EVALUATE TOPN(10, ...)",
  "error": null
}
```

---

## 🚀 How to Use

### Basic Embedding

Simply add an iframe to any HTML page:

```html
<iframe 
    src="https://your-backend.com/embed/widget/{agent_id}" 
    width="100%" 
    height="600px" 
    frameborder="0">
</iframe>
```

### Responsive Embedding

```html
<div style="position: relative; padding-bottom: 75%; height: 0; overflow: hidden;">
    <iframe 
        src="https://your-backend.com/embed/widget/{agent_id}" 
        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;">
    </iframe>
</div>
```

---

## 📡 PostMessage API

### Widget → Parent Communication

**Widget Ready:**
```javascript
{
  type: 'widget-ready',
  agent_id: 'uuid',
  agent_name: 'Agent Name'
}
```

**Chat Response:**
```javascript
{
  type: 'chat-response',
  agent_id: 'uuid',
  question: 'User question',
  answer: 'AI response',
  action: 'QUERY' | 'DESCRIBE' | 'ERROR'
}
```

### Parent → Widget Communication

**Send Message:**
```javascript
{
  type: 'send-message',
  agent_id: 'uuid',
  message: 'Question text'
}
```

### Example Usage

```javascript
// Listen for messages from widget
window.addEventListener('message', (event) => {
  if (event.data.type === 'widget-ready') {
    console.log('Widget loaded:', event.data.agent_name);
  }
  
  if (event.data.type === 'chat-response') {
    console.log('Response:', event.data.answer);
  }
});

// Send message to widget
iframe.contentWindow.postMessage({
  type: 'send-message',
  agent_id: 'your-agent-id',
  message: 'What are the top products?'
}, '*');
```

---

## 🔒 Security Features

1. **CORS Configuration** - Allows embedding from any origin (can be restricted)
2. **Content Security Policy** - Allows iframe embedding
3. **Agent Validation** - Verifies agent exists, is active, and has valid config
4. **Error Handling** - Graceful error messages for invalid agents

---

## ⚙️ Configuration

### Backend Requirements

1. **Agent Must Exist** - Agent ID must be valid
2. **Agent Must Be Active** - Status must be "active"
3. **Agent Type** - Must be `POWERBI` connection type
4. **OpenAI API Key** - Must be set in agent config or environment

### Security Headers

The backend automatically adds security headers for embed routes:
- `Content-Security-Policy: frame-ancestors *` - Allows embedding
- CORS configured to allow all origins (for embed widget)

---

## 🎨 Widget Features

- **Modern UI** - Gradient header, smooth animations
- **Message Bubbles** - User messages (right, blue), Assistant messages (left, white)
- **Loading States** - "Thinking..." indicator
- **Error Handling** - Red error messages for failures
- **Auto-scroll** - Automatically scrolls to latest message
- **Keyboard Support** - Enter key to send message
- **Empty State** - Welcome message when no messages

---

## 📋 Requirements

### Agent Requirements:
- ✅ Agent must exist in database
- ✅ Agent status must be "active"
- ✅ Agent connection_type must be "POWERBI"
- ✅ Agent must have valid Power BI configuration
- ✅ OpenAI API key must be set (in agent or environment)

### Backend Requirements:
- ✅ FastAPI application running
- ✅ Database connection
- ✅ Power BI service configured
- ✅ OpenAI API key available

---

## 🧪 Testing

### Test Widget Embedding

1. Get an agent ID:
   ```bash
   GET /agents/{account_id}
   ```

2. Create test HTML:
   ```html
   <iframe src="http://localhost:8000/embed/widget/{agent_id}"></iframe>
   ```

3. Open in browser and test chatting

### Test API Directly

```bash
curl -X POST "http://localhost:8000/embed/chat/{agent_id}" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top products?"}'
```

---

## 📚 Documentation

Complete documentation available in:
- **`docs/frontend-embed-widget.md`** - Full frontend integration guide
  - HTML examples
  - React integration
  - Vue.js integration
  - PostMessage API examples
  - Security considerations
  - Troubleshooting

---

## 🔄 Differences from Regular Chat

| Feature | Regular Chat (`/chats/*`) | Embed Widget (`/embed/*`) |
|---------|---------------------------|----------------------------|
| **Authentication** | Required | Not required |
| **Message Storage** | Stored in database | Not stored |
| **Chat History** | Persistent | No history |
| **Multiple Chats** | Yes, per agent | Single session |
| **Chat Management** | Create, list, update, delete | N/A |
| **Use Case** | Internal app | Public websites |

---

## 🎯 Use Cases

1. **Public Websites** - Embed chatbot on marketing sites
2. **Customer Support** - Add to help pages
3. **Product Demos** - Showcase AI capabilities
4. **Landing Pages** - Interactive data exploration
5. **Documentation Sites** - Help users query data

---

## 🚨 Important Notes

1. **No Authentication** - Anyone with agent ID can use it
2. **No Message Storage** - All messages are ephemeral
3. **Power BI Only** - Only works with POWERBI agents
4. **Agent Must Be Active** - Inactive agents won't work
5. **Public Access** - Consider rate limiting in production

---

## ✅ Implementation Checklist

- [x] Create embed routes (`app/api/routes/embed.py`)
- [x] Add widget HTML endpoint
- [x] Add non-persistent chat endpoint
- [x] Add security headers to main.py
- [x] Add CORS configuration
- [x] Register embed router
- [x] Create frontend documentation
- [x] Test widget embedding
- [x] Test chat functionality

---

## 🎉 Ready to Use!

The embed widget is fully implemented and ready to use. Simply:

1. Get an agent ID
2. Add iframe to your website
3. Start chatting!

**Example:**
```html
<iframe 
    src="https://your-backend.com/embed/widget/your-agent-id" 
    width="100%" 
    height="600px">
</iframe>
```

---

## 📞 Support

For questions or issues:
1. Check `docs/frontend-embed-widget.md` for detailed guide
2. Verify agent configuration
3. Test API endpoints directly
4. Check browser console for errors

---

**Implementation Complete! 🚀**


