# Embeddable Chatbot Widget - Frontend Integration Guide

This guide shows how to embed the agent chatbot widget into any website using an iframe.

## Overview

The embed widget allows you to add a chatbot interface to any website. The widget:
- ✅ Requires **NO authentication** - works for public websites
- ✅ **Does NOT store chat messages** - completely stateless
- ✅ Fully responsive and mobile-friendly
- ✅ Supports PostMessage API for parent-child communication
- ✅ Works with any agent that has `connection_type = POWERBI`

## Quick Start

### Basic Embedding

Simply add an iframe to your HTML:

```html
<iframe 
    src="https://your-backend.com/embed/widget/{agent_id}" 
    width="100%" 
    height="600px" 
    frameborder="0"
    title="Chat with Agent">
</iframe>
```

**Replace:**
- `https://your-backend.com` with your backend URL
- `{agent_id}` with the actual agent UUID

### Example

```html
<iframe 
    src="https://api.example.com/embed/widget/123e4567-e89b-12d3-a456-426614174000" 
    width="100%" 
    height="600px" 
    frameborder="0">
</iframe>
```

---

## Responsive Embedding

For a responsive iframe that adapts to screen size:

```html
<div style="position: relative; padding-bottom: 75%; height: 0; overflow: hidden; max-width: 100%;">
    <iframe 
        src="https://your-backend.com/embed/widget/{agent_id}" 
        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;"
        title="Chat with Agent">
    </iframe>
</div>
```

---

## API Endpoints

### 1. Get Widget HTML

**Endpoint:** `GET /embed/widget/{agent_id}`

**Description:** Returns the HTML widget for iframe embedding.

**Parameters:**
- `agent_id` (path): UUID of the agent

**Response:** HTML page with embedded chatbot

**Example:**
```
GET https://your-backend.com/embed/widget/123e4567-e89b-12d3-a456-426614174000
```

---

### 2. Chat Endpoint (Non-Persistent)

**Endpoint:** `POST /embed/chat/{agent_id}`

**Description:** Send a message to an agent and get a response. Messages are NOT stored.

**Request Body:**
```json
{
  "question": "What are the top 10 products by sales?"
}
```

**Response:**
```json
{
  "answer": "The top 10 products by sales are...",
  "resolution_note": "",
  "action": "QUERY",
  "dax_attempts": ["EVALUATE TOPN(10, ...)"],
  "final_dax": "EVALUATE TOPN(10, ...)",
  "error": null
}
```

**Example:**
```bash
curl -X POST "https://your-backend.com/embed/chat/{agent_id}" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top products?"}'
```

---

## PostMessage API Communication

The widget supports two-way communication with the parent page using the PostMessage API.

### Widget → Parent (Widget sends to parent)

The widget sends these message types:

#### 1. Widget Ready
Sent when the widget is loaded and ready:

```javascript
{
  type: 'widget-ready',
  agent_id: 'uuid',
  agent_name: 'Agent Name'
}
```

#### 2. Chat Response
Sent when a chat response is received:

```javascript
{
  type: 'chat-response',
  agent_id: 'uuid',
  question: 'User question',
  answer: 'AI response',
  action: 'QUERY' | 'DESCRIBE' | 'ERROR'
}
```

### Parent → Widget (Parent sends to widget)

The parent can send these message types:

#### 1. Send Message
Programmatically send a message to the widget:

```javascript
{
  type: 'send-message',
  agent_id: 'uuid',
  message: 'Question text'
}
```

---

## Complete Integration Example

### HTML Page with Widget

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Website with Chatbot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .chat-container {
            margin-top: 40px;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }
        iframe {
            width: 100%;
            height: 600px;
            border: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to My Website</h1>
        <p>Ask our AI assistant anything about your data!</p>
        
        <div class="chat-container">
            <iframe 
                id="chatWidget"
                src="https://your-backend.com/embed/widget/123e4567-e89b-12d3-a456-426614174000"
                title="Chat with Agent">
            </iframe>
        </div>
    </div>
    
    <script>
        const agentId = '123e4567-e89b-12d3-a456-426614174000';
        const iframe = document.getElementById('chatWidget');
        
        // Listen for messages from widget
        window.addEventListener('message', (event) => {
            // Verify origin for security (in production)
            // if (event.origin !== 'https://your-backend.com') return;
            
            const data = event.data;
            
            if (data.type === 'widget-ready') {
                console.log('Widget loaded:', data.agent_name);
                // Widget is ready, you can now interact with it
            }
            
            if (data.type === 'chat-response') {
                console.log('Chat response received:', data.answer);
                // Handle chat response
                // You could log it, display it elsewhere, etc.
            }
        });
        
        // Example: Send a message to widget programmatically
        function sendMessageToWidget(message) {
            iframe.contentWindow.postMessage({
                type: 'send-message',
                agent_id: agentId,
                message: message
            }, '*'); // In production, use specific origin
        }
        
        // Example usage:
        // sendMessageToWidget('What are the top products?');
    </script>
</body>
</html>
```

---

## React Integration Example

```tsx
import React, { useEffect, useRef } from 'react';

interface ChatWidgetProps {
  agentId: string;
  backendUrl: string;
  height?: string;
}

const ChatWidget: React.FC<ChatWidgetProps> = ({ 
  agentId, 
  backendUrl, 
  height = '600px' 
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Verify origin in production
      // if (event.origin !== backendUrl) return;
      
      const data = event.data;
      
      if (data.type === 'widget-ready') {
        console.log('Widget ready:', data.agent_name);
      }
      
      if (data.type === 'chat-response') {
        console.log('Response:', data.answer);
        // Handle response
      }
    };
    
    window.addEventListener('message', handleMessage);
    
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [backendUrl]);
  
  const sendMessage = (message: string) => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({
        type: 'send-message',
        agent_id: agentId,
        message: message
      }, '*');
    }
  };
  
  return (
    <div style={{ width: '100%', border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden' }}>
      <iframe
        ref={iframeRef}
        src={`${backendUrl}/embed/widget/${agentId}`}
        width="100%"
        height={height}
        frameBorder="0"
        title="Chat with Agent"
        style={{ border: 'none' }}
      />
    </div>
  );
};

// Usage
function App() {
  return (
    <div>
      <h1>My Website</h1>
      <ChatWidget 
        agentId="123e4567-e89b-12d3-a456-426614174000"
        backendUrl="https://your-backend.com"
        height="700px"
      />
    </div>
  );
}
```

---

## Vue.js Integration Example

```vue
<template>
  <div class="chat-widget-container">
    <iframe
      ref="chatWidget"
      :src="widgetUrl"
      width="100%"
      height="600px"
      frameborder="0"
      title="Chat with Agent"
    />
  </div>
</template>

<script>
export default {
  name: 'ChatWidget',
  props: {
    agentId: {
      type: String,
      required: true
    },
    backendUrl: {
      type: String,
      required: true
    }
  },
  computed: {
    widgetUrl() {
      return `${this.backendUrl}/embed/widget/${this.agentId}`;
    }
  },
  mounted() {
    window.addEventListener('message', this.handleMessage);
  },
  beforeUnmount() {
    window.removeEventListener('message', this.handleMessage);
  },
  methods: {
    handleMessage(event) {
      // Verify origin in production
      // if (event.origin !== this.backendUrl) return;
      
      const data = event.data;
      
      if (data.type === 'widget-ready') {
        console.log('Widget ready:', data.agent_name);
        this.$emit('ready', data);
      }
      
      if (data.type === 'chat-response') {
        console.log('Response:', data.answer);
        this.$emit('response', data);
      }
    },
    sendMessage(message) {
      if (this.$refs.chatWidget?.contentWindow) {
        this.$refs.chatWidget.contentWindow.postMessage({
          type: 'send-message',
          agent_id: this.agentId,
          message: message
        }, '*');
      }
    }
  }
};
</script>
```

---

## Styling Customization

The widget has a built-in modern design, but you can customize the iframe container:

```html
<style>
  .custom-chat-container {
    width: 100%;
    max-width: 500px;
    margin: 0 auto;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }
  
  .custom-chat-container iframe {
    width: 100%;
    height: 600px;
    border: none;
  }
</style>

<div class="custom-chat-container">
  <iframe 
    src="https://your-backend.com/embed/widget/{agent_id}"
    title="Chat">
  </iframe>
</div>
```

---

## Security Considerations

### 1. Origin Verification

Always verify the message origin in production:

```javascript
window.addEventListener('message', (event) => {
  // Only accept messages from your backend
  if (event.origin !== 'https://your-backend.com') {
    return;
  }
  
  // Process message
  const data = event.data;
  // ...
});
```

### 2. HTTPS in Production

Always use HTTPS in production for secure communication.

### 3. Agent ID Validation

The widget validates that:
- Agent exists
- Agent is active
- Agent type is POWERBI
- Agent has valid configuration

### 4. CORS Configuration

The backend allows embedding from any origin. In production, you may want to restrict this:

```python
# In main.py - restrict to specific domains
allow_origins=["https://yourdomain.com", "https://www.yourdomain.com"]
```

---

## Error Handling

The widget handles errors gracefully:

### Agent Not Found
If the agent doesn't exist, the widget displays:
```
Agent Not Found
The requested agent does not exist or is not available.
```

### Agent Not Supported
If the agent type is not POWERBI:
```
Agent Not Supported
This agent type does not support chat functionality.
```

### Network Errors
If the chat request fails, the widget displays:
```
Failed to send message. Please check your connection and try again.
```

---

## Features

✅ **No Authentication Required** - Public access
✅ **Non-Persistent** - Messages are not stored
✅ **Real-time Chat** - Instant responses
✅ **Mobile Responsive** - Works on all devices
✅ **PostMessage API** - Two-way communication
✅ **Error Handling** - Graceful error messages
✅ **Loading States** - Visual feedback during processing
✅ **Modern UI** - Clean, professional design

---

## Limitations

1. **No Chat History** - Messages are not stored or persisted
2. **No Authentication** - Anyone with the agent ID can use it
3. **Power BI Only** - Only works with POWERBI connection type agents
4. **Agent Must Be Active** - Inactive agents won't work

---

## Testing

### Test the Widget

1. Get an agent ID from your backend
2. Create an HTML file with the iframe
3. Open it in a browser
4. Test sending messages

### Test PostMessage Communication

```javascript
// In browser console on parent page
const iframe = document.querySelector('iframe');

// Listen for messages
window.addEventListener('message', (e) => {
  console.log('Received:', e.data);
});

// Send message to widget
iframe.contentWindow.postMessage({
  type: 'send-message',
  agent_id: 'your-agent-id',
  message: 'Test message'
}, '*');
```

---

## Troubleshooting

### Widget Not Loading

1. Check that the agent ID is correct
2. Verify the backend URL is accessible
3. Check browser console for errors
4. Ensure CORS is properly configured

### Messages Not Sending

1. Check network tab for API calls
2. Verify agent is active
3. Check that agent has valid Power BI configuration
4. Ensure OpenAI API key is set

### PostMessage Not Working

1. Verify origin in message handler
2. Check that iframe is fully loaded
3. Ensure message format is correct
4. Check browser console for errors

---

## Quick Reference

### Widget URL Format
```
https://your-backend.com/embed/widget/{agent_id}
```

### Chat API Endpoint
```
POST https://your-backend.com/embed/chat/{agent_id}
Body: { "question": "Your question" }
```

### Message Types

**From Widget:**
- `widget-ready` - Widget loaded
- `chat-response` - Chat response received

**To Widget:**
- `send-message` - Send message programmatically

---

## Support

For issues or questions:
1. Check the browser console for errors
2. Verify agent configuration
3. Test the chat API endpoint directly
4. Contact backend team for assistance

---

**Ready to embed!** Just add the iframe to your website and start chatting! 🚀






