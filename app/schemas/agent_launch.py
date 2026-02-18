from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class AgentLaunchRequest(BaseModel):
    client_id: str = Field(..., description="Client ID for authentication")
    client_secret: str = Field(..., description="Client secret for authentication")
    agent_id: str = Field(..., description="Agent ID to launch")


class AgentLaunchResponse(BaseModel):
    frontend_url: str = Field(..., description="Frontend URL with token in fragment")


class AgentLaunchTokenValidation(BaseModel):
    agent_id: str
    agent_name: str
    account_id: str
    credential_id: str


class AgentCredentialCreate(BaseModel):
    agent_id: UUID = Field(..., description="Agent ID to create credentials for")
    name: Optional[str] = Field(None, description="Optional name/description for this credential")


class AgentCredentialOut(BaseModel):
    id: str
    agent_id: str
    client_id: str
    client_secret: str  # Only shown once on creation
    account_id: str
    is_active: bool
    created_at: str
    
    @classmethod
    def from_orm(cls, credential: "AgentCredential"):
        """Convert AgentCredential model to response schema."""
        from datetime import datetime
        return cls(
            id=str(credential.id),
            agent_id=str(credential.agent_id),
            client_id=credential.client_id,
            client_secret=credential.client_secret,
            account_id=str(credential.account_id),
            is_active=credential.is_active,
            created_at=credential.created_at.isoformat() if isinstance(credential.created_at, datetime) else str(credential.created_at)
        )



