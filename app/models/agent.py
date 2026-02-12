from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class ConnectionType(str, Enum):
    POWERBI = "POWERBI"
    DB = "DB"


class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active")  # e.g., "active", "inactive", "pending"
    model_type = Column(String(100), nullable=True)  # modelType
    api_key = Column(String(500), nullable=True)  # Apikey (encrypted in production)
    system_instructions = Column(Text, nullable=True)  # Systeminstructions
    connection_type = Column(SAEnum(ConnectionType), nullable=False)  # connectiontype
    
    # Connection-specific data stored as JSONB
    # For POWERBI: tenantID, ClientID, Workspace ID, Dataset ID, clientsecret
    # For DB: host, username, database, password, port, databasetype
    connection_config = Column(JSONB, nullable=False)
    
    # Foreign keys
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    account = relationship("Account", backref="agents")
    creator = relationship("User", backref="created_agents")


