# Frontend Integration Guide - Agent Chatbot Launch System

## Overview

The launch system allows you to securely embed agent chatbots using `client_id`, `client_secret`, and `agent_id`. It generates short-lived tokens for secure access.

---

## Step 1: Create Client Credentials

First, create client credentials for an agent in your database:

```python
from app.models.agent_credentials import AgentCredential
from uuid import uuid4

# Create credential
credential = AgentCredential(
    agent_id=agent_id,  # UUID of your agent
    client_id="your-client-id",  # Unique client ID
    client_secret="your-client-secret",  # Secret key
    account_id=account_id,  # Account that owns the agent
    is_active=True
)
db.add(credential)
db.commit()
```

---

## Step 2: Launch Endpoint

**Endpoint:** `POST /embed/launch`

**Request:**
```json
{
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "agent_id": "agent-uuid"
}
```

**Response:**
```json
{
  "frontend_url": "https://your-backend.com/embed/chatbot#<token>"
}
```

**Example:**
```javascript
async function getChatbotUrl() {
  const response = await fetch('https://your-backend.com/embed/launch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      client_id: 'your-client-id',
      client_secret: 'your-client-secret',
      agent_id: 'agent-uuid'
    })
  });
  
  const data = await response.json();
  return data.frontend_url;
}
```

---

## Step 3: Embed in HTML

### Option A: Direct iframe (Recommended)

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Website</title>
</head>
<body>
  <h1>Chat with our AI Assistant</h1>
  
  <button id="openChat">Open Chat</button>
  
  <div id="backdrop" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,.4); align-items:center; justify-content:center;">
    <div style="background:#fff; position:relative; padding:8px; border-radius:8px; width:90%; max-width:900px; height:90vh;">
      <button onclick="closeChat()" style="position:absolute; top:8px; right:8px; background:none; border:none; font-size:24px; cursor:pointer;">✕</button>
      <iframe id="chatFrame" width="100%" height="100%" style="border:0" sandbox="allow-scripts allow-top-navigation-by-user-activation"></iframe>
    </div>
  </div>
  
  <script>
    async function openChat() {
      try {
        // Get launch URL
        const url = await getChatbotUrl();
        
        // Load in iframe
        document.getElementById('chatFrame').src = url;
        document.getElementById('backdrop').style.display = 'flex';
      } catch (error) {
        alert('Failed to open chat: ' + error.message);
      }
    }
    
    function closeChat() {
      document.getElementById('chatFrame').src = 'about:blank';
      document.getElementById('backdrop').style.display = 'none';
    }
    
    document.getElementById('openChat').onclick = openChat;
  </script>
</body>
</html>
```

### Option B: Always Visible Widget

```html
<iframe 
  id="chatWidget"
  width="100%" 
  height="600px" 
  frameborder="0"
  sandbox="allow-scripts allow-top-navigation-by-user-activation">
</iframe>

<script>
  async function loadChat() {
    const url = await getChatbotUrl();
    document.getElementById('chatWidget').src = url;
  }
  
  loadChat();
</script>
```

---

## Step 4: React Integration

```tsx
import React, { useState, useEffect } from 'react';

interface ChatWidgetProps {
  clientId: string;
  clientSecret: string;
  agentId: string;
  backendUrl: string;
}

const ChatWidget: React.FC<ChatWidgetProps> = ({ 
  clientId, 
  clientSecret, 
  agentId, 
  backendUrl 
}) => {
  const [chatUrl, setChatUrl] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const launchChat = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/embed/launch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          client_id: clientId,
          client_secret: clientSecret,
          agent_id: agentId
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to launch chat');
      }
      
      const data = await response.json();
      setChatUrl(data.frontend_url);
      setIsOpen(true);
    } catch (error) {
      console.error('Error launching chat:', error);
      alert('Failed to open chat');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <button onClick={launchChat} disabled={loading}>
        {loading ? 'Loading...' : 'Open Chat'}
      </button>
      
      {isOpen && chatUrl && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            position: 'relative',
            padding: '8px',
            borderRadius: '8px',
            width: '90%',
            maxWidth: '900px',
            height: '90vh'
          }}>
            <button 
              onClick={() => setIsOpen(false)}
              style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer'
              }}
            >
              ✕
            </button>
            <iframe
              src={chatUrl}
              width="100%"
              height="100%"
              style={{ border: 'none' }}
              sandbox="allow-scripts allow-top-navigation-by-user-activation"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatWidget;
```

---

## Step 5: Vue.js Integration

```vue
<template>
  <div>
    <button @click="launchChat" :disabled="loading">
      {{ loading ? 'Loading...' : 'Open Chat' }}
    </button>
    
    <div v-if="isOpen && chatUrl" class="chat-modal">
      <div class="chat-container">
        <button @click="closeChat" class="close-btn">✕</button>
        <iframe
          :src="chatUrl"
          width="100%"
          height="100%"
          frameborder="0"
          sandbox="allow-scripts allow-top-navigation-by-user-activation"
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatWidget',
  props: {
    clientId: String,
    clientSecret: String,
    agentId: String,
    backendUrl: String
  },
  data() {
    return {
      chatUrl: null,
      isOpen: false,
      loading: false
    };
  },
  methods: {
    async launchChat() {
      this.loading = true;
      try {
        const response = await fetch(`${this.backendUrl}/embed/launch`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            client_id: this.clientId,
            client_secret: this.clientSecret,
            agent_id: this.agentId
          })
        });
        
        const data = await response.json();
        this.chatUrl = data.frontend_url;
        this.isOpen = true;
      } catch (error) {
        console.error('Error:', error);
        alert('Failed to open chat');
      } finally {
        this.loading = false;
      }
    },
    closeChat() {
      this.isOpen = false;
      this.chatUrl = null;
    }
  }
};
</script>

<style scoped>
.chat-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.chat-container {
  background: white;
  position: relative;
  padding: 8px;
  border-radius: 8px;
  width: 90%;
  max-width: 900px;
  height: 90vh;
}

.close-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  z-index: 10;
}
</style>
```

---

## API Reference

### Launch Endpoint

**POST** `/embed/launch`

**Request Body:**
```typescript
{
  client_id: string;
  client_secret: string;
  agent_id: string;  // UUID
}
```

**Response:**
```typescript
{
  frontend_url: string;  // URL with token in fragment
}
```

**Errors:**
- `401` - Invalid client_id or client_secret
- `404` - Agent not found
- `400` - Agent not active or invalid type

### Validate Token Endpoint

**GET** `/embed/validate-token?token=<token>`

**Response:**
```typescript
{
  agent_id: string;
  agent_name: string;
  account_id: string;
  credential_id: string;
}
```

---

## Security Notes

1. **Token TTL**: Tokens expire after 5 minutes (configurable)
2. **Single-Use**: Tokens can only be used once
3. **HTTPS Required**: Always use HTTPS in production
4. **Client Secret**: Store securely, never expose in frontend code
5. **Origin Validation**: Consider restricting CORS in production

---

## Quick Start Checklist

1. ✅ Create `AgentCredential` in database
2. ✅ Get `client_id`, `client_secret`, and `agent_id`
3. ✅ Call `/embed/launch` endpoint
4. ✅ Get `frontend_url` with token
5. ✅ Embed in iframe
6. ✅ Test the widget

---

## Example Complete Flow

```javascript
// 1. Launch chat
const response = await fetch('https://your-backend.com/embed/launch', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    client_id: 'your-client-id',
    client_secret: 'your-client-secret',
    agent_id: 'agent-uuid'
  })
});

const { frontend_url } = await response.json();
// frontend_url = "https://your-backend.com/embed/chatbot#<token>"

// 2. Embed in iframe
const iframe = document.createElement('iframe');
iframe.src = frontend_url;
iframe.width = '100%';
iframe.height = '600px';
iframe.frameBorder = '0';
iframe.sandbox = 'allow-scripts allow-top-navigation-by-user-activation';
document.body.appendChild(iframe);
```

---

## Troubleshooting

**Token validation fails:**
- Check token is in URL fragment (after #)
- Verify token hasn't expired (5 minutes)
- Ensure token hasn't been used before

**Agent not found:**
- Verify agent_id is correct
- Check agent belongs to same account as credential
- Ensure agent status is "active"

**Chat not working:**
- Verify agent type is POWERBI
- Check agent has valid Power BI configuration
- Ensure OpenAI API key is set

---

**Ready to embed!** Use the launch endpoint to get a secure token URL, then embed it in your website! 🚀








