# Power BI Chat Feature - Frontend Integration Guide

Complete guide for integrating the Power BI chat-on-data feature into your frontend application.

## Overview

The chat feature allows users to ask natural language questions about their Power BI data and get intelligent, conversational answers. The system automatically:
- Understands questions in plain English
- Decides whether to answer from schema or execute DAX queries
- Handles typos and value resolution
- Executes DAX with automatic error correction
- Returns human-friendly answers

## API Endpoint

**POST** `/agents/{account_id}/{agent_id}/chat`

### Authentication
Requires Bearer token:
```
Authorization: Bearer <access_token>
```

### Request Body
```typescript
{
  "question": "string"  // User's question about the Power BI data
}
```

**Note:** 
- `openai_api_key` is automatically retrieved from the agent's `api_key` field
- `schema_cache` is handled internally (no need to pass it)

### Response
```typescript
{
  "answer": "string",                    // AI's conversational answer
  "resolution_note": "string",          // Note about typo/value resolution (if any)
  "action": "DESCRIBE" | "QUERY" | "ERROR",
  "dax_attempts": string[],             // DAX queries attempted (if QUERY)
  "final_dax": "string",                // Final successful DAX (if QUERY)
  "error": string | null
}
```

## Complete React/TypeScript Implementation

### 1. Types Definition

```typescript
// types/powerbi.ts
export interface PowerBIChatRequest {
  question: string;
}

export interface PowerBIChatResponse {
  answer: string;
  resolution_note: string;
  action: "DESCRIBE" | "QUERY" | "ERROR";
  dax_attempts: string[];
  final_dax: string;
  error?: string;
}

export interface ChatMessage {
  id: string;
  question: string;
  response: PowerBIChatResponse;
  timestamp: Date;
}
```

### 2. Service Layer

```typescript
// services/powerbiChatService.ts
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const chatWithPowerBI = async (
  accountId: string,
  agentId: string,
  question: string,
  accessToken: string
): Promise<PowerBIChatResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/agents/${accountId}/${agentId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Chat request failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error: any) {
    console.error('Power BI chat error:', error);
    throw error;
  }
};
```

### 3. React Hook for Chat

```typescript
// hooks/usePowerBIChat.ts
import { useState, useCallback } from 'react';
import { chatWithPowerBI } from '../services/powerbiChatService';
import type { ChatMessage, PowerBIChatResponse } from '../types/powerbi';

interface UsePowerBIChatProps {
  accountId: string;
  agentId: string;
  accessToken: string;
}

export const usePowerBIChat = ({ accountId, agentId, accessToken }: UsePowerBIChatProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const response = await chatWithPowerBI(accountId, agentId, question, accessToken);
      
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        question,
        response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, newMessage]);
      return response;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to get response from chat';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [accountId, agentId, accessToken, loading]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearMessages,
  };
};
```

### 4. Complete Chat Component

```tsx
// components/PowerBIChat.tsx
import React, { useState, useRef, useEffect } from 'react';
import { usePowerBIChat } from '../hooks/usePowerBIChat';
import type { ChatMessage } from '../types/powerbi';

interface PowerBIChatProps {
  accountId: string;
  agentId: string;
  accessToken: string;
}

const PowerBIChat: React.FC<PowerBIChatProps> = ({ accountId, agentId, accessToken }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, loading, error, sendMessage, clearMessages } = usePowerBIChat({
    accountId,
    agentId,
    accessToken,
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');

    try {
      await sendMessage(question);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%', 
      maxWidth: '1200px', 
      margin: '0 auto',
      padding: '20px'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px',
        paddingBottom: '15px',
        borderBottom: '2px solid #e5e7eb'
      }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>Power BI Chat</h1>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            style={{
              padding: '8px 16px',
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Clear Chat
          </button>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#fee2e2',
          color: '#991b1b',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '1px solid #fecaca'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        backgroundColor: '#f9fafb',
        borderRadius: '12px',
        marginBottom: '20px',
        minHeight: '400px',
        maxHeight: '600px'
      }}>
        {messages.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            color: '#6b7280', 
            padding: '40px 20px' 
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>💬</div>
            <h3 style={{ margin: '0 0 8px 0', color: '#374151' }}>Start a Conversation</h3>
            <p style={{ margin: 0 }}>Ask questions about your Power BI data in natural language</p>
            <div style={{ marginTop: '24px', textAlign: 'left', display: 'inline-block' }}>
              <p style={{ margin: '8px 0', fontWeight: 500 }}>Example questions:</p>
              <ul style={{ margin: 0, paddingLeft: '20px', color: '#6b7280' }}>
                <li>"What tables are in this dataset?"</li>
                <li>"Show me the total sales"</li>
                <li>"What columns are in the Sales table?"</li>
                <li>"List the top 10 products by revenue"</li>
                <li>"How many customers do we have?"</li>
              </ul>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {messages.map((msg) => (
              <div key={msg.id}>
                {/* User Question */}
                <div style={{ marginBottom: '12px' }}>
                  <div style={{
                    display: 'inline-block',
                    padding: '12px 16px',
                    backgroundColor: '#0f172a',
                    color: 'white',
                    borderRadius: '18px 18px 18px 4px',
                    maxWidth: '80%',
                    wordWrap: 'break-word'
                  }}>
                    <strong style={{ display: 'block', marginBottom: '4px', fontSize: '12px', opacity: 0.9 }}>
                      You
                    </strong>
                    {msg.question}
                  </div>
                </div>

                {/* AI Response */}
                <div style={{ marginBottom: '12px' }}>
                  <div style={{
                    display: 'inline-block',
                    padding: '12px 16px',
                    backgroundColor: 'white',
                    color: '#1f2937',
                    borderRadius: '18px 18px 4px 18px',
                    maxWidth: '80%',
                    wordWrap: 'break-word',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                  }}>
                    <strong style={{ 
                      display: 'block', 
                      marginBottom: '8px', 
                      fontSize: '12px', 
                      color: '#6b7280' 
                    }}>
                      AI Assistant
                    </strong>
                    
                    {/* Resolution Note */}
                    {msg.response.resolution_note && (
                      <div style={{
                        marginBottom: '12px',
                        padding: '8px 12px',
                        backgroundColor: '#fef3c7',
                        borderRadius: '6px',
                        fontSize: '13px',
                        color: '#92400e',
                        border: '1px solid #fde68a'
                      }}>
                        ℹ️ {msg.response.resolution_note}
                      </div>
                    )}

                    {/* Answer */}
                    <div style={{ 
                      whiteSpace: 'pre-wrap',
                      lineHeight: '1.6',
                      marginBottom: msg.response.action === 'QUERY' ? '12px' : '0'
                    }}>
                      {msg.response.answer}
                    </div>

                    {/* DAX Query (Expandable) */}
                    {msg.response.action === 'QUERY' && msg.response.final_dax && (
                      <details style={{ marginTop: '12px' }}>
                        <summary style={{
                          cursor: 'pointer',
                          color: '#6366f1',
                          fontSize: '13px',
                          fontWeight: 500,
                          userSelect: 'none'
                        }}>
                          📊 View DAX Query
                        </summary>
                        <pre style={{
                          marginTop: '8px',
                          padding: '12px',
                          backgroundColor: '#f3f4f6',
                          borderRadius: '6px',
                          overflow: 'auto',
                          fontSize: '12px',
                          fontFamily: 'monospace',
                          border: '1px solid #e5e7eb'
                        }}>
                          {msg.response.final_dax}
                        </pre>
                      </details>
                    )}

                    {/* Error Display */}
                    {msg.response.error && (
                      <div style={{
                        marginTop: '12px',
                        padding: '8px 12px',
                        backgroundColor: '#fee2e2',
                        borderRadius: '6px',
                        fontSize: '13px',
                        color: '#991b1b',
                        border: '1px solid #fecaca'
                      }}>
                        ⚠️ Error: {msg.response.error}
                      </div>
                    )}

                    {/* Action Badge */}
                    <div style={{ 
                      marginTop: '8px', 
                      fontSize: '11px', 
                      color: '#9ca3af' 
                    }}>
                      {msg.response.action === 'DESCRIBE' && '📋 Answered from schema'}
                      {msg.response.action === 'QUERY' && '🔍 Executed DAX query'}
                      {msg.response.action === 'ERROR' && '❌ Error occurred'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={loading ? "Processing..." : "Ask a question about your Power BI data..."}
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px 16px',
              fontSize: '16px',
              border: '2px solid #e5e7eb',
              borderRadius: '12px',
              outline: 'none',
              transition: 'border-color 0.2s',
              backgroundColor: loading ? '#f3f4f6' : 'white'
            }}
            onFocus={(e) => e.target.style.borderColor = '#0f172a'}
            onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            padding: '14px 28px',
            fontSize: '16px',
            fontWeight: 500,
            backgroundColor: loading || !input.trim() ? '#d1d5db' : '#0f172a',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.2s',
            minWidth: '100px'
          }}
        >
          {loading ? (
            <span>
              <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⏳</span>
              {' '}Sending...
            </span>
          ) : (
            'Send'
          )}
        </button>
      </form>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default PowerBIChat;
```

### 5. Usage in Your App

```tsx
// App.tsx or your main component
import React from 'react';
import PowerBIChat from './components/PowerBIChat';

function App() {
  // Get these from your auth context or props
  const accountId = 'your-account-uuid';
  const agentId = 'your-agent-uuid';
  const accessToken = 'your-access-token';

  return (
    <div className="App">
      <PowerBIChat
        accountId={accountId}
        agentId={agentId}
        accessToken={accessToken}
      />
    </div>
  );
}

export default App;
```

## Alternative: Simple Chat Component (Minimal)

```tsx
// components/SimplePowerBIChat.tsx
import React, { useState } from 'react';
import { chatWithPowerBI } from '../services/powerbiChatService';

interface SimplePowerBIChatProps {
  accountId: string;
  agentId: string;
  accessToken: string;
}

const SimplePowerBIChat: React.FC<SimplePowerBIChatProps> = ({
  accountId,
  agentId,
  accessToken,
}) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    setLoading(true);
    try {
      const response = await chatWithPowerBI(accountId, agentId, question, accessToken);
      setAnswer(response.answer);
      if (response.resolution_note) {
        setAnswer(prev => `${response.resolution_note}\n\n${prev}`);
      }
    } catch (error: any) {
      setAnswer(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Ask a Question</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about your Power BI data..."
          style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Ask'}
        </button>
      </form>
      {answer && (
        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
          <strong>Answer:</strong>
          <p style={{ whiteSpace: 'pre-wrap' }}>{answer}</p>
        </div>
      )}
    </div>
  );
};

export default SimplePowerBIChat;
```

## Axios Implementation

```typescript
// services/powerbiChatService.ts (Axios version)
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatWithPowerBI = async (
  accountId: string,
  agentId: string,
  question: string,
  accessToken: string
): Promise<PowerBIChatResponse> => {
  const response = await api.post<PowerBIChatResponse>(
    `/agents/${accountId}/${agentId}/chat`,
    { question },
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );
  return response.data;
};
```

## Example API Call

```typescript
// Example usage
const response = await chatWithPowerBI(
  'account-uuid',
  'agent-uuid',
  'What tables are in this dataset?',
  'your-access-token'
);

console.log(response.answer);        // "Based on the schema, your dataset contains..."
console.log(response.action);       // "DESCRIBE" or "QUERY"
console.log(response.final_dax);    // DAX query if action is "QUERY"
```

## Response Examples

### DESCRIBE Action
```json
{
  "answer": "Based on the schema, your dataset contains the following tables:\n\n- Sales\n- Products\n- Customers",
  "resolution_note": "",
  "action": "DESCRIBE",
  "dax_attempts": [],
  "final_dax": "",
  "error": null
}
```

### QUERY Action
```json
{
  "answer": "The total sales amount is $1,234,567.89.",
  "resolution_note": "",
  "action": "QUERY",
  "dax_attempts": [
    "EVALUATE ROW(\"Result\", SUM('Sales'[Amount]))"
  ],
  "final_dax": "EVALUATE ROW(\"Result\", SUM('Sales'[Amount]))",
  "error": null
}
```

### With Typo Resolution
```json
{
  "answer": "Here are the sales for JO-JanX product...",
  "resolution_note": "Interpreting 'Jo janx' as 'JO-JanX'.",
  "action": "QUERY",
  "dax_attempts": ["..."],
  "final_dax": "...",
  "error": null
}
```

## Styling Tips

### Using Tailwind CSS

```tsx
<div className="flex flex-col h-full max-w-4xl mx-auto p-5">
  <div className="flex-1 overflow-y-auto bg-gray-50 rounded-lg p-5 mb-5">
    {/* Messages */}
  </div>
  <form className="flex gap-2">
    <input 
      className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-slate-900"
      placeholder="Ask a question..."
    />
    <button className="px-6 py-3 bg-slate-900 text-white rounded-xl">
      Send
    </button>
  </form>
</div>
```

### Using Material-UI

```tsx
import { Box, TextField, Button, Paper, Typography } from '@mui/material';

<Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
  <Paper sx={{ flex: 1, overflow: 'auto', p: 2, mb: 2 }}>
    {/* Messages */}
  </Paper>
  <Box sx={{ display: 'flex', gap: 1 }}>
    <TextField
      fullWidth
      placeholder="Ask a question..."
      value={input}
      onChange={(e) => setInput(e.target.value)}
    />
    <Button variant="contained" onClick={handleSubmit}>
      Send
    </Button>
  </Box>
</Box>
```

## Error Handling

```typescript
try {
  const response = await chatWithPowerBI(accountId, agentId, question, accessToken);
  
  if (response.error) {
    // Handle error in response
    console.error('Chat error:', response.error);
  }
  
  // Process successful response
  console.log('Answer:', response.answer);
} catch (error: any) {
  if (error.response) {
    // API error (4xx, 5xx)
    console.error('API Error:', error.response.data);
  } else if (error.request) {
    // Network error
    console.error('Network Error:', error.message);
  } else {
    // Other error
    console.error('Error:', error.message);
  }
}
```

## Best Practices

1. **Loading States**: Always show loading indicators during API calls
2. **Error Handling**: Display user-friendly error messages
3. **Auto-scroll**: Scroll to bottom when new messages arrive
4. **Input Validation**: Prevent empty submissions
5. **Rate Limiting**: Consider debouncing rapid requests
6. **Schema Caching**: The backend handles this automatically, no need to cache on frontend
7. **Accessibility**: Add ARIA labels and keyboard navigation

## Testing

```typescript
// Example test questions to try:
const testQuestions = [
  "What tables are in this dataset?",
  "Show me the total sales",
  "What columns are in the Sales table?",
  "List the top 10 products by revenue",
  "How many customers do we have?",
  "What's the average order value?",
  "Show me sales for product 'JO-JanX'",  // Tests typo resolution
];
```

## Complete Integration Checklist

- [ ] Install dependencies (if using Axios: `npm install axios`)
- [ ] Create types file (`types/powerbi.ts`)
- [ ] Create service file (`services/powerbiChatService.ts`)
- [ ] Create hook (`hooks/usePowerBIChat.ts`)
- [ ] Create chat component (`components/PowerBIChat.tsx`)
- [ ] Add to your app routing/page
- [ ] Test with sample questions
- [ ] Add error handling
- [ ] Style to match your app design
- [ ] Add loading states
- [ ] Test with real agent credentials

## Quick Start

1. Copy the `PowerBIChat` component code
2. Copy the `usePowerBIChat` hook
3. Copy the service function
4. Import and use in your app:

```tsx
<PowerBIChat
  accountId={accountId}
  agentId={agentId}
  accessToken={accessToken}
/>
```

That's it! The chat feature is now integrated.

