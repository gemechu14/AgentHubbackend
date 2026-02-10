# Agent API - Quick Reference

## Base URL
`/agents`

## Authentication
All requests require: `Authorization: Bearer <token>`

## Endpoints Summary

| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| POST | `/agents/{account_id}` | Create agent | OWNER, ADMIN, MEMBER |
| GET | `/agents/{account_id}` | List agents | OWNER, ADMIN, MEMBER, VIEWER |
| GET | `/agents/{account_id}/{agent_id}` | Get agent | OWNER, ADMIN, MEMBER, VIEWER |
| PATCH | `/agents/{account_id}/{agent_id}` | Update agent | OWNER, ADMIN, MEMBER |
| DELETE | `/agents/{account_id}/{agent_id}` | Delete agent | OWNER, ADMIN, MEMBER |

## Request/Response Examples

### Create Agent (POWERBI)
```json
POST /agents/{account_id}
{
  "name": "My Agent",
  "description": "Agent description",
  "status": "active",
  "model_type": "gpt-4",
  "api_key": "sk-...",
  "system_instructions": "You are helpful...",
  "connection_type": "POWERBI",
  "connection_config": {
    "tenant_id": "...",
    "client_id": "...",
    "workspace_id": "...",
    "dataset_id": "...",
    "client_secret": "..."
  }
}
```

### Create Agent (DB)
```json
POST /agents/{account_id}
{
  "name": "DB Agent",
  "connection_type": "DB",
  "connection_config": {
    "host": "localhost",
    "username": "user",
    "database": "mydb",
    "password": "pass",
    "port": 5432,
    "database_type": "postgresql"
  }
}
```

### List Agents Response
```json
{
  "agents": [
    {
      "id": "uuid",
      "name": "Agent Name",
      "status": "active",
      "connection_type": "POWERBI",
      "connection_config": {...},
      "account_id": "uuid",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

## Error Codes
- `400` - Bad Request (invalid data)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient role)
- `404` - Not Found (agent doesn't exist)

## Connection Types

### POWERBI Required Fields:
- `tenant_id`
- `client_id`
- `workspace_id`
- `dataset_id`
- `client_secret`

### DB Required Fields:
- `host`
- `username`
- `database`
- `password`
- `port`
- `database_type`

## Full Documentation
See `docs/frontend-agent-integration.md` for complete integration guide with React examples.

