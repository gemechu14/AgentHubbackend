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

