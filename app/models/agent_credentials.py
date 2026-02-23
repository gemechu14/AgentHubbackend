from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    
    # Token fields (moved from agent_launch_tokens table)
    token_hash = Column(String(128), nullable=True, index=True)  # Hash of the launch token
    raw_token = Column(String(200), nullable=True)  # Raw token to build embed URLs
    
    # Theme configuration for embed widget (stored as JSON)
    theme = Column(JSONB, nullable=True)  # Custom theme colors for the embed widget
    
    # Relationships
    agent = relationship("Agent", backref="credentials", lazy="select", passive_deletes=True)
    account = relationship("Account", backref="agent_credentials")


