# Power BI Chat API - Frontend Testing Guide

This guide provides code examples for using the Power BI chat endpoint from the frontend.

## Endpoint

**POST** `/agents/{account_id}/{agent_id}/chat`

## Base URL
```
http://localhost:8000  (or your backend URL)
```

## Authentication
Requires Bearer token in Authorization header:
```
Authorization: Bearer <access_token>
```

## Request Body Schema

```typescript
interface PowerBIChatRequest {
  question: string;                    // Required: User's question about the Power BI data
  openai_api_key?: string;             // Optional: OpenAI API key (can also be in agent.api_key or env)
  schema_cache?: string;              // Optional: Cached schema string (will be fetched if not provided)
}
```

## Response Schema

```typescript
interface PowerBIChatResponse {
  answer: string;                      // AI's answer to the question
  resolution_note: string;             // Note about value resolution/typo correction (if any)
  action: "DESCRIBE" | "QUERY" | "ERROR";  // Action taken
  dax_attempts: string[];              // List of DAX queries attempted (if QUERY action)
  final_dax: string;                   // Final DAX query that succeeded (if QUERY action)
  error?: string;                       // Error message if any
}
```

## Frontend Code Examples

### React/TypeScript with Fetch API

```typescript
// types.ts
export interface PowerBIChatRequest {
  question: string;
  openai_api_key?: string;
  schema_cache?: string;
}

export interface PowerBIChatResponse {
  answer: string;
  resolution_note: string;
  action: "DESCRIBE" | "QUERY" | "ERROR";
  dax_attempts: string[];
  final_dax: string;
  error?: string;
}

// services/powerbiChatService.ts
const API_BASE_URL = 'http://localhost:8000';

export const chatWithPowerBI = async (
  accountId: string,
  agentId: string,
  question: string,
  accessToken: string,
  openaiApiKey?: string,
  schemaCache?: string
): Promise<PowerBIChatResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/agents/${accountId}/${agentId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        question,
        openai_api_key: openaiApiKey,
        schema_cache: schemaCache,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Power BI chat error:', error);
    throw error;
  }
};
```

### React Component Example

```tsx
// components/PowerBIChat.tsx
import React, { useState } from 'react';
import { chatWithPowerBI } from '../services/powerbiChatService';
import type { PowerBIChatResponse } from '../types';

interface PowerBIChatProps {
  accountId: string;
  agentId: string;
  accessToken: string;
  openaiApiKey?: string;
}

const PowerBIChat: React.FC<PowerBIChatProps> = ({ accountId, agentId, accessToken, openaiApiKey }) => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Array<{ question: string; response: PowerBIChatResponse }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schemaCache, setSchemaCache] = useState<string | undefined>(undefined);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const currentQuestion = question;
    setQuestion('');
    setLoading(true);
    setError(null);

    try {
      const response = await chatWithPowerBI(
        accountId,
        agentId,
        currentQuestion,
        accessToken,
        openaiApiKey,
        schemaCache
      );

      // Cache schema for future requests (optional optimization)
      // You could extract schema from a previous response if needed

      setMessages(prev => [...prev, { question: currentQuestion, response }]);
    } catch (err: any) {
      setError(err.message || 'Failed to get response');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h1>Power BI Chat</h1>

      <div style={{ marginBottom: '20px', border: '1px solid #ddd', borderRadius: '8px', padding: '15px' }}>
        <h2>Chat History</h2>
        {messages.length === 0 ? (
          <p style={{ color: '#666' }}>No messages yet. Ask a question to get started!</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {messages.map((msg, idx) => (
              <div key={idx} style={{ borderBottom: '1px solid #eee', paddingBottom: '15px' }}>
                <div style={{ marginBottom: '10px' }}>
                  <strong style={{ color: '#333' }}>You:</strong>
                  <p style={{ margin: '5px 0', color: '#555' }}>{msg.question}</p>
                </div>
                <div>
                  <strong style={{ color: '#333' }}>AI:</strong>
                  {msg.response.resolution_note && (
                    <p style={{ 
                      margin: '5px 0', 
                      padding: '8px', 
                      backgroundColor: '#fff3cd', 
                      borderRadius: '4px',
                      fontSize: '14px'
                    }}>
                      ℹ️ {msg.response.resolution_note}
                    </p>
                  )}
                  <p style={{ margin: '5px 0', color: '#555', whiteSpace: 'pre-wrap' }}>
                    {msg.response.answer}
                  </p>
                  {msg.response.action === 'QUERY' && msg.response.final_dax && (
                    <details style={{ marginTop: '10px' }}>
                      <summary style={{ cursor: 'pointer', color: '#666', fontSize: '14px' }}>
                        View DAX Query
                      </summary>
                      <pre style={{
                        marginTop: '10px',
                        padding: '10px',
                        backgroundColor: '#f5f5f5',
                        borderRadius: '4px',
                        overflow: 'auto',
                        fontSize: '12px'
                      }}>
                        {msg.response.final_dax}
                      </pre>
                    </details>
                  )}
                  {msg.response.error && (
                    <p style={{ color: '#dc3545', fontSize: '14px', marginTop: '5px' }}>
                      ⚠️ Error: {msg.response.error}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div style={{ 
          padding: '10px', 
          backgroundColor: '#fee', 
          color: '#c00', 
          marginBottom: '20px',
          borderRadius: '4px'
        }}>
          Error: {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your Power BI data..."
            style={{ 
              flex: 1, 
              padding: '12px', 
              fontSize: '16px',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
            disabled={loading}
          />
          <button 
            type="submit" 
            disabled={loading || !question.trim()}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              backgroundColor: loading ? '#ccc' : '#0f172a',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>

      <div style={{ marginTop: '20px', fontSize: '14px', color: '#666' }}>
        <p><strong>Example questions:</strong></p>
        <ul>
          <li>"What tables are in this dataset?"</li>
          <li>"Show me the total sales"</li>
          <li>"What columns are in the Sales table?"</li>
          <li>"List the top 10 products by revenue"</li>
        </ul>
      </div>
    </div>
  );
};

export default PowerBIChat;
```

### Axios Example

```typescript
// services/powerbiChatService.ts (Axios version)
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

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
  accessToken: string,
  openaiApiKey?: string,
  schemaCache?: string
) => {
  const response = await api.post<PowerBIChatResponse>(
    `/agents/${accountId}/${agentId}/chat`,
    {
      question,
      openai_api_key: openaiApiKey,
      schema_cache: schemaCache,
    },
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );
  return response.data;
};
```

### Vanilla JavaScript Example

```javascript
async function chatWithPowerBI(accountId, agentId, question, accessToken, openaiApiKey, schemaCache) {
  try {
    const response = await fetch(`http://localhost:8000/agents/${accountId}/${agentId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        question,
        openai_api_key: openaiApiKey,
        schema_cache: schemaCache,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat request failed');
    }

    const result = await response.json();
    console.log('Chat Response:', result);
    return result;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Usage Example
const accountId = 'your-account-uuid';
const agentId = 'your-agent-uuid';
const accessToken = 'your-access-token';
const question = 'What tables are in this dataset?';

chatWithPowerBI(accountId, agentId, question, accessToken)
  .then(result => {
    console.log('Answer:', result.answer);
    if (result.resolution_note) {
      console.log('Note:', result.resolution_note);
    }
    if (result.action === 'QUERY' && result.final_dax) {
      console.log('DAX Query:', result.final_dax);
    }
  })
  .catch(error => console.error('Error:', error));
```

## Example Request

```json
{
  "question": "What tables are in this dataset?",
  "openai_api_key": "sk-...",
  "schema_cache": null
}
```

## Example Responses

### DESCRIBE Action Response
```json
{
  "answer": "Based on the schema, your dataset contains the following tables:\n\n- Sales\n- Products\n- Customers\n- Orders\n\nThese are the main business tables in your Power BI dataset.",
  "resolution_note": "",
  "action": "DESCRIBE",
  "dax_attempts": [],
  "final_dax": "",
  "error": null
}
```

### QUERY Action Response
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

### Response with Typo Resolution
```json
{
  "answer": "Here are the sales for JO-JanX product...",
  "resolution_note": "Interpreting 'Jo janx' as 'JO-JanX'.",
  "action": "QUERY",
  "dax_attempts": [
    "EVALUATE FILTER('Sales', 'Products'[Name] = \"JO-JanX\")"
  ],
  "final_dax": "EVALUATE FILTER('Sales', 'Products'[Name] = \"JO-JanX\")",
  "error": null
}
```

## Testing with cURL

```bash
curl -X POST "http://localhost:8000/agents/{account_id}/{agent_id}/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "question": "What tables are in this dataset?",
    "openai_api_key": "sk-..."
  }'
```

## Features

- **Natural Language Understanding**: Ask questions in plain English
- **Smart Planning**: Automatically decides whether to answer from schema or execute DAX
- **Typo Handling**: Automatically resolves typos in user input (e.g., "Jo janx" → "JO-JanX")
- **Error Correction**: Automatically retries DAX queries with corrections if they fail
- **Conversational Answers**: Returns human-friendly, brief responses
- **Schema Caching**: Optional schema cache to avoid repeated schema fetches

## Notes

- The OpenAI API key can be provided in:
  1. Request body (`openai_api_key`)
  2. Agent's `api_key` field
  3. `OPENAI_API_KEY` environment variable
- Schema is automatically fetched if not provided in `schema_cache`
- The endpoint uses the same chat logic as `final.py`
- Requires authentication (Bearer token)
- Only works for agents with `connection_type = POWERBI`

