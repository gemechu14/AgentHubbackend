from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class AgentLaunchRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID to launch")


class AgentLaunchResponse(BaseModel):
    frontend_url: str = Field(..., description="Frontend URL with token in fragment")


class AgentLaunchTokenValidation(BaseModel):
    agent_id: str
    agent_name: str
    account_id: str
    status: str = Field(..., description="Agent status (active, inactive, pending)")
    recommended_questions: Optional[list[str]] = Field(None, description="List of recommended questions for the embed widget")


class AgentCredentialCreate(BaseModel):
    agent_id: UUID = Field(..., description="Agent ID to create credentials for")
    name: Optional[str] = Field(None, description="Optional name/description for this credential")


class AgentCredentialOut(BaseModel):
    id: str
    agent_id: str
    account_id: str
    is_active: bool
    created_at: str
    embed_url: Optional[str] = Field(None, description="Current embed URL if a valid token exists. Call /embed/launch to generate a new one.")
    
    @classmethod
    def from_orm(cls, credential: "AgentCredential", embed_url: Optional[str] = None):
        """Convert AgentCredential model to response schema."""
        from datetime import datetime
        return cls(
            id=str(credential.id),
            agent_id=str(credential.agent_id),
            account_id=str(credential.account_id),
            is_active=credential.is_active,
            created_at=credential.created_at.isoformat() if isinstance(credential.created_at, datetime) else str(credential.created_at),
            embed_url=embed_url
        )


class AgentCredentialToggleRequest(BaseModel):
    is_active: bool = Field(..., description="Set to True to enable embed, False to disable")



