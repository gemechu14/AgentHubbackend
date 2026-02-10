from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import current_user, require_role_for_account
from app.models.auth_models import User, Account, Role
from app.models.agent import Agent, ConnectionType
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentOut,
    AgentListOut,
    ConnectionTypeEnum,
    PowerBIConfig,
    DBConfig,
    ConnectionCheckResponse,
    SchemaResponse,
    PowerBITestConnectionRequest,
    PowerBIGetSchemaRequest,
    PowerBIChatRequest,
    PowerBIChatResponse,
)
from app.core.security import now_utc
from app.services.powerbi_service import check_connection, execute_dax, get_schema_dax, get_powerbi_token
from app.services.powerbi_chat import chat_with_powerbi
import os

router = APIRouter(prefix="/agents", tags=["agents"])


# ============================================================================
# Standalone test endpoints (must come BEFORE parameterized routes)
# ============================================================================

@router.post(
    "/test-connection",
    response_model=ConnectionCheckResponse,
    summary="Test Power BI connection (standalone)",
    description="""
    Test Power BI connection with provided credentials.
    
    This endpoint allows you to test Power BI connectivity without creating an agent.
    Simply provide all required Power BI credentials in the request body.
    
    This endpoint:
    - Authenticates with Power BI using the provided credentials
    - Executes a simple DAX query to verify connectivity
    - Returns connection status and basic dataset information
    
    No authentication required (public endpoint for testing).
    """,
)
def test_powerbi_connection_standalone(
    body: PowerBITestConnectionRequest,
):
    """Test Power BI connection with provided credentials."""
    try:
        result = check_connection(
            tenant_id=body.tenant_id,
            client_id=body.client_id,
            workspace_id=body.workspace_id,
            dataset_id=body.dataset_id,
            client_secret=body.client_secret,
        )
        return ConnectionCheckResponse(**result)
    except Exception as e:
        return ConnectionCheckResponse(
            connected=False,
            message=f"Connection check failed: {str(e)}",
            error=str(e),
        )


@router.post(
    "/get-schema",
    response_model=SchemaResponse,
    summary="Get Power BI schema (standalone)",
    description="""
    Retrieve schema information from Power BI dataset with provided credentials.
    
    This endpoint allows you to retrieve Power BI schema without creating an agent.
    Simply provide all required Power BI credentials in the request body.
    
    This endpoint:
    - Authenticates with Power BI using the provided credentials
    - Executes DAX queries to get tables, columns, relationships, and measures
    - Returns comprehensive schema information
    
    No authentication required (public endpoint for testing).
    """,
)
def get_powerbi_schema_standalone(
    body: PowerBIGetSchemaRequest,
):
    """Get Power BI schema with provided credentials."""
    try:
        # Get token
        token = get_powerbi_token(
            tenant_id=body.tenant_id,
            client_id=body.client_id,
            client_secret=body.client_secret,
        )
        
        # Get schema DAX queries
        schema_queries = get_schema_dax(
            workspace_id=body.workspace_id,
            dataset_id=body.dataset_id,
        )
        
        # Execute all schema queries
        schema_data = {}
        for key, dax_query in schema_queries.items():
            try:
                result = execute_dax(
                    token=token,
                    workspace_id=body.workspace_id,
                    dataset_id=body.dataset_id,
                    dax_query=dax_query,
                )
                # Extract rows from first table
                rows = (
                    result.get("results", [{}])[0]
                    .get("tables", [{}])[0]
                    .get("rows", [])
                )
                schema_data[key] = rows
            except Exception as e:
                schema_data[key] = {"error": str(e)}
        
        return SchemaResponse(
            success=True,
            message="Schema retrieved successfully",
            data=schema_data,
        )
    except Exception as e:
        return SchemaResponse(
            success=False,
            message=f"Schema retrieval failed: {str(e)}",
            error=str(e),
        )


# ============================================================================
# Helper functions
# ============================================================================

def validate_connection_config(connection_type: ConnectionTypeEnum, config: dict) -> dict:
    """Validate connection config based on connection type."""
    if connection_type == ConnectionTypeEnum.POWERBI:
        try:
            PowerBIConfig(**config)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid PowerBI config: {str(e)}"
            )
        return config
    elif connection_type == ConnectionTypeEnum.DB:
        try:
            DBConfig(**config)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid DB config: {str(e)}"
            )
        return config
    else:
        raise HTTPException(status_code=400, detail="Invalid connection_type")


@router.post(
    "/{account_id}",
    response_model=AgentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="""
    Create a new agent for the specified account.
    
    **Connection Types:**
    - **POWERBI**: Requires `tenant_id`, `client_id`, `workspace_id`, `dataset_id`, `client_secret`
    - **DB**: Requires `host`, `username`, `database`, `password`, `port`, `database_type`
    
    Requires OWNER, ADMIN, or MEMBER role for the account.
    """,
)
def create_agent(
    account_id: UUID,
    body: AgentCreate,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER})),
    db: Session = Depends(get_db),
):
    """Create a new agent."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Validate connection config
    validated_config = validate_connection_config(body.connection_type, body.connection_config)
    
    # Create agent
    agent = Agent(
        name=body.name,
        description=body.description,
        status=body.status,
        model_type=body.model_type,
        api_key=body.api_key,
        system_instructions=body.system_instructions,
        connection_type=ConnectionType(body.connection_type.value),
        connection_config=validated_config,
        account_id=account_id,
        created_by=user.id,
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return agent


@router.get(
    "/{account_id}",
    response_model=AgentListOut,
    summary="List all agents for an account",
    description="""
    Get all agents for the specified account.
    
    Supports pagination with `skip` and `limit` query parameters.
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def list_agents(
    account_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """List all agents for an account."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Query agents
    query = db.query(Agent).filter(Agent.account_id == account_id)
    total = query.count()
    agents = query.order_by(Agent.created_at.desc()).offset(skip).limit(limit).all()
    
    return AgentListOut(agents=agents, total=total)


@router.get(
    "/{account_id}/{agent_id}",
    response_model=AgentOut,
    summary="Get a specific agent",
    description="""
    Get details of a specific agent by ID.
    
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def get_agent(
    account_id: UUID,
    agent_id: UUID,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Get a specific agent."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.patch(
    "/{account_id}/{agent_id}",
    response_model=AgentOut,
    summary="Update an agent",
    description="""
    Update an existing agent. Only provided fields will be updated.
    
    If `connection_type` or `connection_config` is updated, the config will be validated.
    
    Requires OWNER, ADMIN, or MEMBER role for the account.
    """,
)
def update_agent(
    account_id: UUID,
    agent_id: UUID,
    body: AgentUpdate,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER})),
    db: Session = Depends(get_db),
):
    """Update an agent."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update fields
    update_data = body.model_dump(exclude_unset=True)
    
    # Handle connection config validation if connection_type or connection_config is being updated
    if "connection_type" in update_data or "connection_config" in update_data:
        connection_type = ConnectionTypeEnum(update_data.get("connection_type", agent.connection_type.value))
        connection_config = update_data.get("connection_config", agent.connection_config)
        validated_config = validate_connection_config(connection_type, connection_config)
        update_data["connection_config"] = validated_config
        if "connection_type" in update_data:
            update_data["connection_type"] = ConnectionType(connection_type.value)
    
    # Update model fields
    for field, value in update_data.items():
        if hasattr(agent, field):
            setattr(agent, field, value)
    
    agent.updated_at = now_utc()
    db.commit()
    db.refresh(agent)
    
    return agent


@router.delete(
    "/{account_id}/{agent_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an agent",
    description="""
    Delete an agent by ID.
    
    Requires OWNER, ADMIN, or MEMBER role for the account.
    """,
)
def delete_agent(
    account_id: UUID,
    agent_id: UUID,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER})),
    db: Session = Depends(get_db),
):
    """Delete an agent."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    
    return {"ok": True, "message": "Agent deleted successfully"}


@router.post(
    "/{account_id}/{agent_id}/check-connection",
    response_model=ConnectionCheckResponse,
    summary="Check Power BI connection",
    description="""
    Test the Power BI connection for an agent.
    
    This endpoint:
    - Authenticates with Power BI using the agent's credentials
    - Executes a simple DAX query to verify connectivity
    - Returns connection status and basic dataset information
    
    Only works for agents with connection_type = POWERBI.
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def check_powerbi_connection(
    account_id: UUID,
    agent_id: UUID,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Check Power BI connection for an agent."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Get agent
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Only support POWERBI connection type
    if agent.connection_type != ConnectionType.POWERBI:
        raise HTTPException(
            status_code=400,
            detail=f"Connection check only supported for POWERBI agents. This agent has type: {agent.connection_type.value}"
        )
    
    # Extract Power BI config
    try:
        config = PowerBIConfig(**agent.connection_config)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Power BI configuration: {str(e)}"
        )
    
    # Check connection
    try:
        result = check_connection(
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            workspace_id=config.workspace_id,
            dataset_id=config.dataset_id,
            client_secret=config.client_secret,
        )
        return ConnectionCheckResponse(**result)
    except Exception as e:
        return ConnectionCheckResponse(
            connected=False,
            message=f"Connection check failed: {str(e)}",
            error=str(e),
        )


@router.post(
    "/{account_id}/{agent_id}/get-schema",
    response_model=SchemaResponse,
    summary="Get Power BI schema",
    description="""
    Retrieve schema information from Power BI dataset.
    
    This endpoint:
    - Authenticates with Power BI using the agent's credentials
    - Executes DAX queries to get tables, columns, relationships, and measures
    - Returns comprehensive schema information
    
    Only works for agents with connection_type = POWERBI.
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def get_powerbi_schema(
    account_id: UUID,
    agent_id: UUID,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Get Power BI schema for an agent."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Get agent
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Only support POWERBI connection type
    if agent.connection_type != ConnectionType.POWERBI:
        raise HTTPException(
            status_code=400,
            detail=f"Schema retrieval only supported for POWERBI agents. This agent has type: {agent.connection_type.value}"
        )
    
    # Extract Power BI config
    try:
        config = PowerBIConfig(**agent.connection_config)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Power BI configuration: {str(e)}"
        )
    
    # Get schema
    try:
        # Get token
        token = get_powerbi_token(
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )
        
        # Get schema DAX queries
        schema_queries = get_schema_dax(
            workspace_id=config.workspace_id,
            dataset_id=config.dataset_id,
        )
        
        # Execute all schema queries
        schema_data = {}
        for key, dax_query in schema_queries.items():
            try:
                result = execute_dax(
                    token=token,
                    workspace_id=config.workspace_id,
                    dataset_id=config.dataset_id,
                    dax_query=dax_query,
                )
                # Extract rows from first table
                rows = (
                    result.get("results", [{}])[0]
                    .get("tables", [{}])[0]
                    .get("rows", [])
                )
                schema_data[key] = rows
            except Exception as e:
                schema_data[key] = {"error": str(e)}
        
        return SchemaResponse(
            success=True,
            message="Schema retrieved successfully",
            data=schema_data,
        )
    except Exception as e:
        return SchemaResponse(
            success=False,
            message=f"Schema retrieval failed: {str(e)}",
            error=str(e),
        )


@router.post(
    "/{account_id}/{agent_id}/chat",
    response_model=PowerBIChatResponse,
    summary="Chat with Power BI agent",
    description="""
    Ask questions about your Power BI data using natural language.
    
    This endpoint implements the full chat-on-data functionality:
    - Understands natural language questions
    - Decides whether to answer from schema (DESCRIBE) or execute DAX queries (QUERY)
    - Handles typos and value resolution automatically
    - Executes DAX queries with automatic error correction
    - Returns conversational, human-friendly answers
    
    The agent uses OpenAI to understand questions and generate DAX queries.
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def chat_with_agent(
    account_id: UUID,
    agent_id: UUID,
    body: PowerBIChatRequest,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Chat with Power BI agent."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Get agent
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Only support POWERBI connection type
    if agent.connection_type != ConnectionType.POWERBI:
        raise HTTPException(
            status_code=400,
            detail=f"Chat only supported for POWERBI agents. This agent has type: {agent.connection_type.value}"
        )
    
    # Extract Power BI config
    try:
        config = PowerBIConfig(**agent.connection_config)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Power BI configuration: {str(e)}"
        )
    
    # Get OpenAI API key from agent's api_key field or environment
    openai_api_key = agent.api_key or os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key is required. Set it in the agent's api_key field or OPENAI_API_KEY environment variable."
        )
    
    # Chat with Power BI (schema is automatically cached internally)
    try:
        result = chat_with_powerbi(
            question=body.question,
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            workspace_id=config.workspace_id,
            dataset_id=config.dataset_id,
            client_secret=config.client_secret,
            openai_api_key=openai_api_key,
        )
        return PowerBIChatResponse(**result)
    except Exception as e:
        return PowerBIChatResponse(
            answer=f"An error occurred while processing your question: {str(e)}",
            resolution_note="",
            action="ERROR",
            dax_attempts=[],
            final_dax="",
            error=str(e),
        )

