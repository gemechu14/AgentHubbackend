from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Chat(Base):
    """Chat conversation model - represents a single chat session with an agent."""
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False, default="New Chat")
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", backref="chats")
    user = relationship("User", backref="chats")
    account = relationship("Account", backref="chats")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """Chat message model - represents a single message in a chat conversation."""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    
    # Metadata (for assistant messages)
    action = Column(String(50), nullable=True)  # "DESCRIBE", "QUERY", "ERROR"
    dax_attempts = Column(Text, nullable=True)  # JSON array of DAX queries attempted
    final_dax = Column(Text, nullable=True)  # Final DAX query that succeeded
    resolution_note = Column(Text, nullable=True)  # Note about value resolution/typo correction
    error = Column(Text, nullable=True)  # Error message if any
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, server_default=func.now())
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")

