from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from enum import Enum
from datetime import datetime


class ConnectionTypeEnum(str, Enum):
    POWERBI = "POWERBI"
    DB = "DB"


# PowerBI connection config
class PowerBIConfig(BaseModel):
    tenant_id: str = Field(..., description="PowerBI Tenant ID")
    client_id: str = Field(..., description="PowerBI Client ID")
    workspace_id: str = Field(..., description="PowerBI Workspace ID")
    dataset_id: str = Field(..., description="PowerBI Dataset ID")
    client_secret: str = Field(..., description="PowerBI Client Secret")


# DB connection config
class DBConfig(BaseModel):
    host: str = Field(..., description="Database host")
    username: str = Field(..., description="Database username")
    database: str = Field(..., description="Database name")
    password: str = Field(..., description="Database password")
    port: int = Field(..., description="Database port")
    database_type: str = Field(..., description="Database type (e.g., postgresql, mysql, etc.)")


# Request schemas
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    status: str = Field(default="active", description="Agent status (active, inactive, pending)")
    model_type: Optional[str] = Field(None, description="Model type")
    api_key: Optional[str] = Field(None, description="API key")
    system_instructions: Optional[str] = Field(None, description="System instructions")
    connection_type: ConnectionTypeEnum = Field(..., description="Connection type: POWERBI or DB")
    
    # Connection config - can be either PowerBI or DB config
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration based on connection_type")
    
    # Custom tone settings for Power BI chat (ONLY for POWERBI agents, not supported for DB agents)
    custom_tone_schema_enabled: Optional[bool] = Field(default=False, description="Enable custom tone for schema-based answers (PowerBI only)")
    custom_tone_rows_enabled: Optional[bool] = Field(default=False, description="Enable custom tone for row-based answers (PowerBI only)")
    custom_tone_schema: Optional[str] = Field(None, description="Custom tone text for schema-based answers (PowerBI only)")
    custom_tone_rows: Optional[str] = Field(None, description="Custom tone text for row-based answers (PowerBI only)")
    
    # Recommended questions for embed widget (array of strings)
    recommended_questions: Optional[list[str]] = Field(None, description="List of recommended questions to display in embed widget")


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    status: Optional[str] = Field(None, description="Agent status")
    model_type: Optional[str] = Field(None, description="Model type")
    api_key: Optional[str] = Field(None, description="API key")
    system_instructions: Optional[str] = Field(None, description="System instructions")
    connection_type: Optional[ConnectionTypeEnum] = Field(None, description="Connection type")
    connection_config: Optional[Dict[str, Any]] = Field(None, description="Connection configuration")
    
    # Custom tone settings for Power BI chat (ONLY for POWERBI agents, not supported for DB agents)
    custom_tone_schema_enabled: Optional[bool] = Field(None, description="Enable custom tone for schema-based answers (PowerBI only)")
    custom_tone_rows_enabled: Optional[bool] = Field(None, description="Enable custom tone for row-based answers (PowerBI only)")
    custom_tone_schema: Optional[str] = Field(None, description="Custom tone text for schema-based answers (PowerBI only)")
    custom_tone_rows: Optional[str] = Field(None, description="Custom tone text for row-based answers (PowerBI only)")
    
    # Recommended questions for embed widget (array of strings)
    recommended_questions: Optional[list[str]] = Field(None, description="List of recommended questions to display in embed widget")


# Response schemas
class AgentOut(BaseModel):
    model_config: ConfigDict = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str]
    status: str
    model_type: Optional[str]
    api_key: Optional[str]  # Consider omitting in production for security
    system_instructions: Optional[str]
    connection_type: str
    connection_config: Dict[str, Any]
    account_id: UUID
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Custom tone settings for Power BI chat (ONLY for POWERBI agents, not supported for DB agents)
    custom_tone_schema_enabled: bool
    custom_tone_rows_enabled: bool
    custom_tone_schema: Optional[str]
    custom_tone_rows: Optional[str]
    
    # Recommended questions for embed widget (array of strings)
    recommended_questions: Optional[list[str]]


class AgentListOut(BaseModel):
    agents: list[AgentOut]
    total: int


# Power BI API response schemas
class ConnectionCheckResponse(BaseModel):
    connected: bool = Field(..., description="Whether the connection is successful")
    message: str = Field(..., description="Connection status message")
    workspace_id: Optional[str] = Field(None, description="Power BI workspace ID")
    dataset_id: Optional[str] = Field(None, description="Power BI dataset ID")
    table_count: Optional[int] = Field(None, description="Number of tables found")
    database_name: Optional[str] = Field(None, description="Database name (for DB connections)")
    host: Optional[str] = Field(None, description="Database host (for DB connections)")
    error: Optional[str] = Field(None, description="Error message if connection failed")


class SchemaResponse(BaseModel):
    success: bool = Field(..., description="Whether the schema retrieval was successful")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Schema data from DAX queries")
    error: Optional[str] = Field(None, description="Error message if retrieval failed")


# Test endpoints request schemas
class PowerBITestConnectionRequest(BaseModel):
    tenant_id: str = Field(..., description="PowerBI Tenant ID")
    client_id: str = Field(..., description="PowerBI Client ID")
    workspace_id: str = Field(..., description="PowerBI Workspace ID")
    dataset_id: str = Field(..., description="PowerBI Dataset ID")
    client_secret: str = Field(..., description="PowerBI Client Secret")


class PowerBIGetSchemaRequest(BaseModel):
    tenant_id: str = Field(..., description="PowerBI Tenant ID")
    client_id: str = Field(..., description="PowerBI Client ID")
    workspace_id: str = Field(..., description="PowerBI Workspace ID")
    dataset_id: str = Field(..., description="PowerBI Dataset ID")
    client_secret: str = Field(..., description="PowerBI Client Secret")


class DBTestConnectionRequest(BaseModel):
    host: str = Field(..., description="Database host")
    username: str = Field(..., description="Database username")
    database: str = Field(..., description="Database name")
    password: str = Field(..., description="Database password")
    port: int = Field(..., description="Database port")
    database_type: str = Field(..., description="Database type (e.g., postgresql, mysql, etc.)")


class PowerBIChatRequest(BaseModel):
    question: str = Field(..., description="User's question about the Power BI data")


class AgentChatRequest(BaseModel):
    question: str = Field(..., description="User's question about the data")


class PowerBIChatResponse(BaseModel):
    answer: str = Field(..., description="AI's answer to the question")
    resolution_note: str = Field(default="", description="Note about value resolution/typo correction")
    action: str = Field(..., description="Action taken: DESCRIBE, QUERY, or ERROR")
    dax_attempts: list[str] = Field(default_factory=list, description="List of DAX queries attempted")
    final_dax: str = Field(default="", description="Final DAX query that succeeded (if QUERY action)")
    error: Optional[str] = Field(None, description="Error message if any")


class AgentChatResponse(BaseModel):
    answer: str = Field(..., description="AI's answer to the question")
    resolution_note: str = Field(default="", description="Note about value resolution/typo correction")
    action: str = Field(..., description="Action taken: DESCRIBE, QUERY, or ERROR")
    dax_attempts: Optional[list[str]] = Field(default_factory=list, description="List of DAX queries attempted (for PowerBI)")
    final_dax: Optional[str] = Field(default="", description="Final DAX query that succeeded (for PowerBI)")
    sql_attempts: Optional[list[str]] = Field(default_factory=list, description="List of SQL queries attempted (for DB)")
    final_sql: Optional[str] = Field(default="", description="Final SQL query that succeeded (for DB)")
    error: Optional[str] = Field(None, description="Error message if any")