from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AgentCredential(Base):
    """Client credentials for agent embed widget launch - one per agent"""
    __tablename__ = "agent_credentials"
    __table_args__ = (
        UniqueConstraint('agent_id', name='uq_agent_credentials_agent_id'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    agent = relationship("Agent", backref="credentials", lazy="select", passive_deletes=True)
    account = relationship("Account", backref="agent_credentials")


class AgentLaunchToken(Base):
    """Short-lived tokens for agent embed widget"""
    __tablename__ = "agent_launch_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    credential_id = Column(UUID(as_uuid=True), ForeignKey("agent_credentials.id", ondelete="CASCADE"), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    raw_token = Column(String(200), nullable=True)  # Store raw token to build embed URLs (not used for validation)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)  # Single-use: mark when used
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    credential = relationship("AgentCredential")
    agent = relationship("Agent")


