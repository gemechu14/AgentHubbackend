# Frontend Power BI Testing Guide

This guide provides code examples for testing the Power BI connection and schema endpoints from the frontend.

## Endpoints

### 1. Test Power BI Connection
**POST** `/agents/test-connection`

### 2. Get Power BI Schema
**POST** `/agents/get-schema`

## Base URL
```
http://localhost:8000  (or your backend URL)
```

## Request Body Schema

Both endpoints use the same request body structure:

```typescript
interface PowerBITestRequest {
  tenant_id: string;
  client_id: string;
  workspace_id: string;
  dataset_id: string;
  client_secret: string;
}
```

## Frontend Code Examples

### React/TypeScript with Fetch API

```typescript
// types.ts
export interface PowerBITestRequest {
  tenant_id: string;
  client_id: string;
  workspace_id: string;
  dataset_id: string;
  client_secret: string;
}

export interface ConnectionCheckResponse {
  connected: boolean;
  message: string;
  workspace_id?: string;
  dataset_id?: string;
  table_count?: number;
  error?: string;
}

export interface SchemaResponse {
  success: boolean;
  message: string;
  data?: {
    tables?: any[];
    columns?: any[];
    relationships?: any[];
    measures?: any[];
  };
  error?: string;
}

// services/powerbiService.ts
const API_BASE_URL = 'http://localhost:8000'; // or your backend URL

export const testPowerBIConnection = async (
  credentials: PowerBITestRequest
): Promise<ConnectionCheckResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/agents/test-connection`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Connection test failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Power BI connection test error:', error);
    throw error;
  }
};

export const getPowerBISchema = async (
  credentials: PowerBITestRequest
): Promise<SchemaResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/agents/get-schema`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Schema retrieval failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Power BI schema retrieval error:', error);
    throw error;
  }
};
```

### React Component Example

```tsx
// components/PowerBITest.tsx
import React, { useState } from 'react';
import { testPowerBIConnection, getPowerBISchema } from '../services/powerbiService';
import type { PowerBITestRequest, ConnectionCheckResponse, SchemaResponse } from '../types';

const PowerBITest: React.FC = () => {
  const [credentials, setCredentials] = useState<PowerBITestRequest>({
    tenant_id: '',
    client_id: '',
    workspace_id: '',
    dataset_id: '',
    client_secret: '',
  });

  const [connectionResult, setConnectionResult] = useState<ConnectionCheckResponse | null>(null);
  const [schemaResult, setSchemaResult] = useState<SchemaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTestConnection = async () => {
    setLoading(true);
    setError(null);
    setConnectionResult(null);

    try {
      const result = await testPowerBIConnection(credentials);
      setConnectionResult(result);
    } catch (err: any) {
      setError(err.message || 'Failed to test connection');
    } finally {
      setLoading(false);
    }
  };

  const handleGetSchema = async () => {
    setLoading(true);
    setError(null);
    setSchemaResult(null);

    try {
      const result = await getPowerBISchema(credentials);
      setSchemaResult(result);
    } catch (err: any) {
      setError(err.message || 'Failed to get schema');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Power BI Connection Tester</h1>

      <div style={{ marginBottom: '20px' }}>
        <h2>Credentials</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <input
            type="text"
            placeholder="Tenant ID"
            value={credentials.tenant_id}
            onChange={(e) => setCredentials({ ...credentials, tenant_id: e.target.value })}
            style={{ padding: '8px' }}
          />
          <input
            type="text"
            placeholder="Client ID"
            value={credentials.client_id}
            onChange={(e) => setCredentials({ ...credentials, client_id: e.target.value })}
            style={{ padding: '8px' }}
          />
          <input
            type="text"
            placeholder="Workspace ID"
            value={credentials.workspace_id}
            onChange={(e) => setCredentials({ ...credentials, workspace_id: e.target.value })}
            style={{ padding: '8px' }}
          />
          <input
            type="text"
            placeholder="Dataset ID"
            value={credentials.dataset_id}
            onChange={(e) => setCredentials({ ...credentials, dataset_id: e.target.value })}
            style={{ padding: '8px' }}
          />
          <input
            type="password"
            placeholder="Client Secret"
            value={credentials.client_secret}
            onChange={(e) => setCredentials({ ...credentials, client_secret: e.target.value })}
            style={{ padding: '8px' }}
          />
        </div>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button onClick={handleTestConnection} disabled={loading}>
          {loading ? 'Testing...' : 'Test Connection'}
        </button>
        <button onClick={handleGetSchema} disabled={loading}>
          {loading ? 'Loading...' : 'Get Schema'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '10px', backgroundColor: '#fee', color: '#c00', marginBottom: '20px' }}>
          Error: {error}
        </div>
      )}

      {connectionResult && (
        <div style={{ marginBottom: '20px' }}>
          <h2>Connection Result</h2>
          <div style={{
            padding: '15px',
            backgroundColor: connectionResult.connected ? '#efe' : '#fee',
            borderRadius: '5px'
          }}>
            <p><strong>Status:</strong> {connectionResult.connected ? '✅ Connected' : '❌ Failed'}</p>
            <p><strong>Message:</strong> {connectionResult.message}</p>
            {connectionResult.table_count !== undefined && (
              <p><strong>Table Count:</strong> {connectionResult.table_count}</p>
            )}
            {connectionResult.error && (
              <p><strong>Error:</strong> {connectionResult.error}</p>
            )}
          </div>
        </div>
      )}

      {schemaResult && (
        <div>
          <h2>Schema Result</h2>
          <div style={{
            padding: '15px',
            backgroundColor: schemaResult.success ? '#efe' : '#fee',
            borderRadius: '5px',
            marginBottom: '20px'
          }}>
            <p><strong>Status:</strong> {schemaResult.success ? '✅ Success' : '❌ Failed'}</p>
            <p><strong>Message:</strong> {schemaResult.message}</p>
            {schemaResult.error && (
              <p><strong>Error:</strong> {schemaResult.error}</p>
            )}
          </div>

          {schemaResult.data && (
            <div>
              <h3>Schema Data</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div>
                  <h4>Tables ({schemaResult.data.tables?.length || 0})</h4>
                  <pre style={{ 
                    backgroundColor: '#f5f5f5', 
                    padding: '10px', 
                    overflow: 'auto',
                    maxHeight: '200px',
                    fontSize: '12px'
                  }}>
                    {JSON.stringify(schemaResult.data.tables?.slice(0, 5), null, 2)}
                    {schemaResult.data.tables && schemaResult.data.tables.length > 5 && '...'}
                  </pre>
                </div>
                <div>
                  <h4>Columns ({schemaResult.data.columns?.length || 0})</h4>
                  <pre style={{ 
                    backgroundColor: '#f5f5f5', 
                    padding: '10px', 
                    overflow: 'auto',
                    maxHeight: '200px',
                    fontSize: '12px'
                  }}>
                    {JSON.stringify(schemaResult.data.columns?.slice(0, 5), null, 2)}
                    {schemaResult.data.columns && schemaResult.data.columns.length > 5 && '...'}
                  </pre>
                </div>
                <div>
                  <h4>Measures ({schemaResult.data.measures?.length || 0})</h4>
                  <pre style={{ 
                    backgroundColor: '#f5f5f5', 
                    padding: '10px', 
                    overflow: 'auto',
                    maxHeight: '200px',
                    fontSize: '12px'
                  }}>
                    {JSON.stringify(schemaResult.data.measures?.slice(0, 5), null, 2)}
                    {schemaResult.data.measures && schemaResult.data.measures.length > 5 && '...'}
                  </pre>
                </div>
                <div>
                  <h4>Relationships ({schemaResult.data.relationships?.length || 0})</h4>
                  <pre style={{ 
                    backgroundColor: '#f5f5f5', 
                    padding: '10px', 
                    overflow: 'auto',
                    maxHeight: '200px',
                    fontSize: '12px'
                  }}>
                    {JSON.stringify(schemaResult.data.relationships?.slice(0, 5), null, 2)}
                    {schemaResult.data.relationships && schemaResult.data.relationships.length > 5 && '...'}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PowerBITest;
```

### Axios Example

```typescript
// services/powerbiService.ts (Axios version)
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const testPowerBIConnection = async (credentials: PowerBITestRequest) => {
  const response = await api.post<ConnectionCheckResponse>(
    '/agents/test-connection',
    credentials
  );
  return response.data;
};

export const getPowerBISchema = async (credentials: PowerBITestRequest) => {
  const response = await api.post<SchemaResponse>(
    '/agents/get-schema',
    credentials
  );
  return response.data;
};
```

### Vanilla JavaScript Example

```javascript
// Test Connection
async function testPowerBIConnection(credentials) {
  try {
    const response = await fetch('http://localhost:8000/agents/test-connection', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Connection test failed');
    }

    const result = await response.json();
    console.log('Connection Result:', result);
    return result;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Get Schema
async function getPowerBISchema(credentials) {
  try {
    const response = await fetch('http://localhost:8000/agents/get-schema', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Schema retrieval failed');
    }

    const result = await response.json();
    console.log('Schema Result:', result);
    return result;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Usage Example
const credentials = {
  tenant_id: 'e174b7cc-406a-4fff-b1d5-6a43601ab563',
  client_id: 'c04e88c4-5c70-4e5f-a7ca-a5e1a55e1cc1',
  workspace_id: '1f941dcd-6778-4237-bcf3-bc03e233b052',
  dataset_id: 'fd37215d-b1ac-44a0-8c90-535e6c000a98',
  client_secret: 'nWT8Q~BkGQ6-LbzQVnmHlCP3EQmYY1g4_FvEtdg'
};

// Test connection
testPowerBIConnection(credentials)
  .then(result => {
    if (result.connected) {
      console.log('✅ Connected! Table count:', result.table_count);
    } else {
      console.log('❌ Connection failed:', result.message);
    }
  })
  .catch(error => console.error('Error:', error));

// Get schema
getPowerBISchema(credentials)
  .then(result => {
    if (result.success) {
      console.log('✅ Schema retrieved!');
      console.log('Tables:', result.data.tables);
      console.log('Columns:', result.data.columns);
      console.log('Measures:', result.data.measures);
      console.log('Relationships:', result.data.relationships);
    } else {
      console.log('❌ Schema retrieval failed:', result.message);
    }
  })
  .catch(error => console.error('Error:', error));
```

## Example Request Body

```json
{
  "tenant_id": "e174b7cc-406a-4fff-b1d5-6a43601ab563",
  "client_id": "c04e88c4-5c70-4e5f-a7ca-a5e1a55e1cc1",
  "workspace_id": "1f941dcd-6778-4237-bcf3-bc03e233b052",
  "dataset_id": "fd37215d-b1ac-44a0-8c90-535e6c000a98",
  "client_secret": "nWT8Q~BkGQ6-LbzQVnmHlCP3EQmYY1g4_FvEtdg"
}
```

## Example Responses

### Connection Check Success Response
```json
{
  "connected": true,
  "message": "Successfully connected to Power BI",
  "workspace_id": "1f941dcd-6778-4237-bcf3-bc03e233b052",
  "dataset_id": "fd37215d-b1ac-44a0-8c90-535e6c000a98",
  "table_count": 10,
  "error": null
}
```

### Schema Success Response
```json
{
  "success": true,
  "message": "Schema retrieved successfully",
  "data": {
    "tables": [
      {
        "Name": "Sales",
        "Table": "Sales"
      }
    ],
    "columns": [
      {
        "Table": "Sales",
        "Name": "Amount",
        "DataType": "Double"
      }
    ],
    "measures": [
      {
        "Table": "Sales",
        "Name": "Total Sales",
        "Expression": "SUM(Sales[Amount])"
      }
    ],
    "relationships": [
      {
        "FromTable": "Sales",
        "FromColumn": "ProductID",
        "ToTable": "Products",
        "ToColumn": "ID"
      }
    ]
  },
  "error": null
}
```

## Testing with cURL

```bash
# Test Connection
curl -X POST "http://localhost:8000/agents/test-connection" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "e174b7cc-406a-4fff-b1d5-6a43601ab563",
    "client_id": "c04e88c4-5c70-4e5f-a7ca-a5e1a55e1cc1",
    "workspace_id": "1f941dcd-6778-4237-bcf3-bc03e233b052",
    "dataset_id": "fd37215d-b1ac-44a0-8c90-535e6c000a98",
    "client_secret": "nWT8Q~BkGQ6-LbzQVnmHlCP3EQmYY1g4_FvEtdg"
  }'

# Get Schema
curl -X POST "http://localhost:8000/agents/get-schema" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "e174b7cc-406a-4fff-b1d5-6a43601ab563",
    "client_id": "c04e88c4-5c70-4e5f-a7ca-a5e1a55e1cc1",
    "workspace_id": "1f941dcd-6778-4237-bcf3-bc03e233b052",
    "dataset_id": "fd37215d-b1ac-44a0-8c90-535e6c000a98",
    "client_secret": "nWT8Q~BkGQ6-LbzQVnmHlCP3EQmYY1g4_FvEtdg"
  }'
```

## Notes

- Both endpoints are **public** (no authentication required) for testing purposes
- Make sure your backend is running on the correct port
- Replace `localhost:8000` with your actual backend URL
- The `client_secret` should be kept secure in production
- These endpoints use the same authentication logic as `final.py`

