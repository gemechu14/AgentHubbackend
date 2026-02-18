# Agent API - Frontend Integration Guide

## Overview

This guide provides everything you need to integrate the Agent API endpoints into your frontend application.

## Base URL

All endpoints are prefixed with `/agents`

## Authentication

All endpoints require authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## API Endpoints

### 1. Create Agent

**Endpoint:** `POST /agents/{account_id}`

**Description:** Create a new agent for an account

**Required Role:** OWNER, ADMIN, or MEMBER

**Request Body:**

```typescript
interface AgentCreate {
  name: string;                    // Required, 1-255 characters
  description?: string;             // Optional
  status?: string;                  // Optional, default: "active" (active, inactive, pending)
  model_type?: string;              // Optional
  api_key?: string;                 // Optional
  system_instructions?: string;      // Optional
  connection_type: "POWERBI" | "DB"; // Required
  connection_config: PowerBIConfig | DBConfig; // Required, see below
}

// For POWERBI connection
interface PowerBIConfig {
  tenant_id: string;
  client_id: string;
  workspace_id: string;
  dataset_id: string;
  client_secret: string;
}

// For DB connection
interface DBConfig {
  host: string;
  username: string;
  database: string;
  password: string;
  port: number;
  database_type: string;  // e.g., "postgresql", "mysql", "mongodb"
}
```

**Example Request (POWERBI):**

```typescript
const createPowerBIAgent = async (accountId: string) => {
  const response = await fetch(`/agents/${accountId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      name: "Sales Analytics Agent",
      description: "Agent for analyzing sales data from PowerBI",
      status: "active",
      model_type: "gpt-4",
      api_key: "sk-...",
      system_instructions: "You are a helpful assistant for sales analytics.",
      connection_type: "POWERBI",
      connection_config: {
        tenant_id: "12345678-1234-1234-1234-123456789012",
        client_id: "87654321-4321-4321-4321-210987654321",
        workspace_id: "workspace-123",
        dataset_id: "dataset-456",
        client_secret: "your-client-secret"
      }
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to create agent');
  }
  
  return await response.json();
};
```

**Example Request (DB):**

```typescript
const createDBAgent = async (accountId: string) => {
  const response = await fetch(`/agents/${accountId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      name: "Database Query Agent",
      description: "Agent for querying PostgreSQL database",
      status: "active",
      model_type: "gpt-4",
      api_key: "sk-...",
      system_instructions: "You are a database query assistant.",
      connection_type: "DB",
      connection_config: {
        host: "localhost",
        username: "dbuser",
        database: "mydb",
        password: "dbpassword",
        port: 5432,
        database_type: "postgresql"
      }
    })
  });
  
  return await response.json();
};
```

**Response:**

```typescript
interface AgentOut {
  id: string;                       // UUID
  name: string;
  description: string | null;
  status: string;
  model_type: string | null;
  api_key: string | null;
  system_instructions: string | null;
  connection_type: "POWERBI" | "DB";
  connection_config: Record<string, any>;
  account_id: string;              // UUID
  created_by: string | null;        // UUID
  created_at: string;               // ISO 8601 datetime
  updated_at: string | null;        // ISO 8601 datetime
}
```

---

### 2. List Agents

**Endpoint:** `GET /agents/{account_id}?skip=0&limit=100`

**Description:** Get all agents for an account with pagination

**Required Role:** OWNER, ADMIN, MEMBER, or VIEWER

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 100, max: 1000)

**Example Request:**

```typescript
const listAgents = async (accountId: string, skip = 0, limit = 100) => {
  const response = await fetch(
    `/agents/${accountId}?skip=${skip}&limit=${limit}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  return await response.json();
};
```

**Response:**

```typescript
interface AgentListResponse {
  agents: AgentOut[];
  total: number;
}
```

---

### 3. Get Single Agent

**Endpoint:** `GET /agents/{account_id}/{agent_id}`

**Description:** Get details of a specific agent

**Required Role:** OWNER, ADMIN, MEMBER, or VIEWER

**Example Request:**

```typescript
const getAgent = async (accountId: string, agentId: string) => {
  const response = await fetch(
    `/agents/${accountId}/${agentId}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Agent not found');
  }
  
  return await response.json();
};
```

**Response:** `AgentOut` (same as Create Agent response)

---

### 4. Update Agent

**Endpoint:** `PATCH /agents/{account_id}/{agent_id}`

**Description:** Update an existing agent (only provided fields will be updated)

**Required Role:** OWNER, ADMIN, or MEMBER

**Request Body:** (All fields optional)

```typescript
interface AgentUpdate {
  name?: string;
  description?: string;
  status?: string;
  model_type?: string;
  api_key?: string;
  system_instructions?: string;
  connection_type?: "POWERBI" | "DB";
  connection_config?: PowerBIConfig | DBConfig;
}
```

**Example Request:**

```typescript
const updateAgent = async (
  accountId: string, 
  agentId: string, 
  updates: Partial<AgentUpdate>
) => {
  const response = await fetch(
    `/agents/${accountId}/${agentId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify(updates)
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to update agent');
  }
  
  return await response.json();
};

// Example usage
await updateAgent(accountId, agentId, {
  status: "inactive",
  description: "Updated description"
});
```

**Response:** `AgentOut`

---

### 5. Delete Agent

**Endpoint:** `DELETE /agents/{account_id}/{agent_id}`

**Description:** Delete an agent

**Required Role:** OWNER, ADMIN, or MEMBER

**Example Request:**

```typescript
const deleteAgent = async (accountId: string, agentId: string) => {
  const response = await fetch(
    `/agents/${accountId}/${agentId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to delete agent');
  }
  
  return await response.json();
};
```

**Response:**

```typescript
{
  ok: true,
  message: "Agent deleted successfully"
}
```

---

## Error Handling

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid PowerBI config: ..."
}
```

### 401 Unauthorized
```json
{
  "detail": "Missing or invalid Authorization header"
}
```

### 403 Forbidden
```json
{
  "detail": "Not a member of this account"
}
```
or
```json
{
  "detail": "Insufficient role"
}
```

### 404 Not Found
```json
{
  "detail": "Agent not found"
}
```

### Example Error Handling:

```typescript
const handleApiError = async (response: Response) => {
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'An error occurred');
  }
  return response.json();
};

// Usage
try {
  const agent = await createPowerBIAgent(accountId);
} catch (error) {
  console.error('Error:', error.message);
  // Handle error in UI
}
```

---

## React Hook Example

```typescript
import { useState, useEffect } from 'react';

interface UseAgentsProps {
  accountId: string;
  accessToken: string;
}

export const useAgents = ({ accountId, accessToken }: UseAgentsProps) => {
  const [agents, setAgents] = useState<AgentOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/agents/${accountId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch agents');
      
      const data = await response.json();
      setAgents(data.agents);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const createAgent = async (agentData: AgentCreate) => {
    try {
      const response = await fetch(`/agents/${accountId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(agentData)
      });
      
      if (!response.ok) throw new Error('Failed to create agent');
      
      const newAgent = await response.json();
      setAgents(prev => [newAgent, ...prev]);
      return newAgent;
    } catch (err) {
      throw err;
    }
  };

  const updateAgent = async (agentId: string, updates: Partial<AgentUpdate>) => {
    try {
      const response = await fetch(`/agents/${accountId}/${agentId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(updates)
      });
      
      if (!response.ok) throw new Error('Failed to update agent');
      
      const updatedAgent = await response.json();
      setAgents(prev => 
        prev.map(agent => agent.id === agentId ? updatedAgent : agent)
      );
      return updatedAgent;
    } catch (err) {
      throw err;
    }
  };

  const deleteAgent = async (agentId: string) => {
    try {
      const response = await fetch(`/agents/${accountId}/${agentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to delete agent');
      
      setAgents(prev => prev.filter(agent => agent.id !== agentId));
    } catch (err) {
      throw err;
    }
  };

  useEffect(() => {
    if (accountId && accessToken) {
      fetchAgents();
    }
  }, [accountId, accessToken]);

  return {
    agents,
    loading,
    error,
    createAgent,
    updateAgent,
    deleteAgent,
    refetch: fetchAgents
  };
};
```

---

## TypeScript Type Definitions

```typescript
// Connection Types
type ConnectionType = "POWERBI" | "DB";

// PowerBI Configuration
interface PowerBIConfig {
  tenant_id: string;
  client_id: string;
  workspace_id: string;
  dataset_id: string;
  client_secret: string;
}

// Database Configuration
interface DBConfig {
  host: string;
  username: string;
  database: string;
  password: string;
  port: number;
  database_type: string;
}

// Agent Models
interface AgentCreate {
  name: string;
  description?: string;
  status?: string;
  model_type?: string;
  api_key?: string;
  system_instructions?: string;
  connection_type: ConnectionType;
  connection_config: PowerBIConfig | DBConfig;
}

interface AgentUpdate {
  name?: string;
  description?: string;
  status?: string;
  model_type?: string;
  api_key?: string;
  system_instructions?: string;
  connection_type?: ConnectionType;
  connection_config?: PowerBIConfig | DBConfig;
}

interface AgentOut {
  id: string;
  name: string;
  description: string | null;
  status: string;
  model_type: string | null;
  api_key: string | null;
  system_instructions: string | null;
  connection_type: ConnectionType;
  connection_config: Record<string, any>;
  account_id: string;
  created_by: string | null;
  created_at: string;
  updated_at: string | null;
}

interface AgentListResponse {
  agents: AgentOut[];
  total: number;
}
```

---

## Form Example (React)

```typescript
import { useState } from 'react';

const AgentForm = ({ accountId, accessToken, onSuccess }: Props) => {
  const [formData, setFormData] = useState<AgentCreate>({
    name: '',
    description: '',
    status: 'active',
    connection_type: 'POWERBI',
    connection_config: {
      tenant_id: '',
      client_id: '',
      workspace_id: '',
      dataset_id: '',
      client_secret: ''
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch(`/agents/${accountId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }
      
      const agent = await response.json();
      onSuccess?.(agent);
    } catch (error) {
      console.error('Error creating agent:', error);
    }
  };

  const handleConnectionTypeChange = (type: ConnectionType) => {
    setFormData(prev => ({
      ...prev,
      connection_type: type,
      connection_config: type === 'POWERBI' 
        ? {
            tenant_id: '',
            client_id: '',
            workspace_id: '',
            dataset_id: '',
            client_secret: ''
          }
        : {
            host: '',
            username: '',
            database: '',
            password: '',
            port: 5432,
            database_type: 'postgresql'
          }
    }));
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Agent Name"
        value={formData.name}
        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
        required
      />
      
      <textarea
        placeholder="Description"
        value={formData.description}
        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
      />
      
      <select
        value={formData.connection_type}
        onChange={(e) => handleConnectionTypeChange(e.target.value as ConnectionType)}
      >
        <option value="POWERBI">PowerBI</option>
        <option value="DB">Database</option>
      </select>
      
      {formData.connection_type === 'POWERBI' ? (
        <>
          <input
            type="text"
            placeholder="Tenant ID"
            value={(formData.connection_config as PowerBIConfig).tenant_id}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              connection_config: {
                ...prev.connection_config as PowerBIConfig,
                tenant_id: e.target.value
              }
            }))}
          />
          {/* Add other PowerBI fields */}
        </>
      ) : (
        <>
          <input
            type="text"
            placeholder="Host"
            value={(formData.connection_config as DBConfig).host}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              connection_config: {
                ...prev.connection_config as DBConfig,
                host: e.target.value
              }
            }))}
          />
          {/* Add other DB fields */}
        </>
      )}
      
      <button type="submit">Create Agent</button>
    </form>
  );
};
```

---

## Notes

1. **Security**: The `api_key` field in responses may contain sensitive data. Consider masking it in the UI or omitting it from responses in production.

2. **Connection Config Validation**: The API validates connection configs based on the `connection_type`. Make sure to provide all required fields for the selected connection type.

3. **Pagination**: When listing agents, use the `skip` and `limit` parameters for pagination. The response includes a `total` count for implementing pagination controls.

4. **Role-Based Access**: Different endpoints require different roles. Ensure your UI reflects the user's permissions appropriately.

5. **Error Messages**: All error responses follow the format `{ "detail": "error message" }`. Display these to users appropriately.

---

## Swagger Documentation

For interactive API documentation, visit:
- Swagger UI: `/gibberish-xyz-123`
- Look for the "agents" tag in the Swagger interface






