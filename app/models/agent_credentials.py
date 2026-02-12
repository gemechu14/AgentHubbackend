from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AgentCredential(Base):
    """Client credentials for agent embed widget launch"""
    __tablename__ = "agent_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(255), unique=True, nullable=False, index=True)
    client_secret = Column(String(255), nullable=False)  # Store hashed in production
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    agent = relationship("Agent", backref="credentials")
    account = relationship("Account", backref="agent_credentials")


class AgentLaunchToken(Base):
    """Short-lived tokens for agent embed widget"""
    __tablename__ = "agent_launch_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    credential_id = Column(UUID(as_uuid=True), ForeignKey("agent_credentials.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)  # Single-use: mark when used
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    credential = relationship("AgentCredential")
    agent = relationship("Agent")

