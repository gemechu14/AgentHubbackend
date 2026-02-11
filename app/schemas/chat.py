from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime


# Request schemas
class ChatCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Chat title (defaults to 'New Chat')")
    agent_id: UUID = Field(..., description="Agent ID this chat belongs to")


class ChatUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Chat title")


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Message content")


# Response schemas
class ChatMessageOut(BaseModel):
    model_config: ConfigDict = ConfigDict(from_attributes=True)
    
    id: UUID
    chat_id: UUID
    role: str  # "user" or "assistant"
    content: str
    action: Optional[str] = None
    dax_attempts: Optional[str] = None  # JSON string
    final_dax: Optional[str] = None
    resolution_note: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime


class ChatOut(BaseModel):
    model_config: ConfigDict = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    agent_id: UUID
    user_id: UUID
    account_id: UUID
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = Field(None, description="Number of messages in this chat")


class ChatWithMessagesOut(BaseModel):
    model_config: ConfigDict = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    agent_id: UUID
    user_id: UUID
    account_id: UUID
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageOut] = Field(default_factory=list)


class ChatListOut(BaseModel):
    chats: List[ChatOut]
    total: int


# Message response schema
class MessageResponse(BaseModel):
    message: ChatMessageOut
    chat: ChatOut

