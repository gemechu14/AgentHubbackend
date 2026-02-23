from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import current_user, require_role_for_account
from app.models.auth_models import User, Account, Role, Membership
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
    DBTestConnectionRequest,
    PowerBIChatRequest,
    PowerBIChatResponse,
    AgentChatRequest,
    AgentChatResponse,
)
from app.core.security import now_utc
from app.services.powerbi_service import check_connection, execute_dax, get_schema_dax, get_powerbi_token
from app.services.powerbi_chat import chat_with_powerbi
from app.services.db_chat import chat_with_db, check_db_connection
from app.models.agent_credentials import AgentCredential
from app.schemas.agent_launch import AgentCredentialCreate, AgentCredentialOut, AgentCredentialToggleRequest, AgentCredentialThemeUpdate
from app.core.config import settings
from app.core.security import sha256, now_utc
import secrets
from datetime import timedelta
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
    "/test-db-connection",
    response_model=ConnectionCheckResponse,
    summary="Test DB connection (standalone)",
    description="""
    Test database connection with provided credentials.
    
    This endpoint allows you to test database connectivity without creating an agent.
    Simply provide all required database credentials in the request body.
    
    This endpoint:
    - Attempts to connect to the database using the provided credentials
    - Retrieves table information to verify connectivity
    - Returns connection status and basic database information
    
    No authentication required (public endpoint for testing).
    """,
)
def test_db_connection_standalone(
    body: DBTestConnectionRequest,
):
    """Test database connection with provided credentials."""
    try:
        result = check_db_connection(
            database_type=body.database_type,
            host=body.host,
            port=body.port,
            database=body.database,
            username=body.username,
            password=body.password,
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
    
    # Custom tone settings are only used for POWERBI agents
    # For DB agents, we silently ignore custom tone settings and set them to default values
    
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
        # Only set custom tone for POWERBI agents (for DB agents, always use default/None)
        custom_tone_schema_enabled=body.custom_tone_schema_enabled or False if body.connection_type == ConnectionTypeEnum.POWERBI else False,
        custom_tone_rows_enabled=body.custom_tone_rows_enabled or False if body.connection_type == ConnectionTypeEnum.POWERBI else False,
        custom_tone_schema=body.custom_tone_schema if body.connection_type == ConnectionTypeEnum.POWERBI else None,
        custom_tone_rows=body.custom_tone_rows if body.connection_type == ConnectionTypeEnum.POWERBI else None,
        # Recommended questions for embed widget (stored as JSON array)
        recommended_questions=body.recommended_questions,
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
    user, verified_account_id, caller_role = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Query agents
    query = db.query(Agent).filter(Agent.account_id == account_id)
    
    # Filter by manage_agent_ids for MEMBER/VIEWER roles
    # OWNER/ADMIN see all agents regardless of manage_agent_ids
    if caller_role in (Role.MEMBER, Role.VIEWER):
        # Get user's membership to check manage_agent_ids
        membership = db.query(Membership).filter(
            Membership.account_id == account_id,
            Membership.user_id == user.id
        ).first()
        
        if membership and membership.manage_agent_ids:
            # Filter to only show assigned agents
            agent_ids = [UUID(str(aid)) for aid in membership.manage_agent_ids]
            query = query.filter(Agent.id.in_(agent_ids))
        # If manage_agent_ids is None or empty, show all agents (backward compatibility)
    
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
    user, verified_account_id, caller_role = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check access for MEMBER/VIEWER roles
    # OWNER/ADMIN can access any agent
    if caller_role in (Role.MEMBER, Role.VIEWER):
        membership = db.query(Membership).filter(
            Membership.account_id == account_id,
            Membership.user_id == user.id
        ).first()
        
        if membership and membership.manage_agent_ids:
            # Check if agent_id is in their assigned list
            agent_ids = [str(UUID(str(aid))) for aid in membership.manage_agent_ids]
            if str(agent_id) not in agent_ids:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to this agent"
                )
        # If manage_agent_ids is None or empty, allow access (backward compatibility)
    
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
    
    # Determine the connection type (new or existing)
    connection_type = ConnectionTypeEnum(update_data.get("connection_type", agent.connection_type.value))
    
    # Handle connection config validation if connection_type or connection_config is being updated
    if "connection_type" in update_data or "connection_config" in update_data:
        connection_config = update_data.get("connection_config", agent.connection_config)
        validated_config = validate_connection_config(connection_type, connection_config)
        update_data["connection_config"] = validated_config
        if "connection_type" in update_data:
            update_data["connection_type"] = ConnectionType(connection_type.value)
    
    # Custom tone settings are only used for POWERBI agents
    # For DB agents, we silently ignore custom tone settings and clear them
    if connection_type != ConnectionTypeEnum.POWERBI:
        # If switching to DB or already DB, clear custom tone settings
        if agent.connection_type == ConnectionType.POWERBI and connection_type == ConnectionTypeEnum.DB:
            # Switching from POWERBI to DB - clear custom tone
            update_data["custom_tone_schema_enabled"] = False
            update_data["custom_tone_rows_enabled"] = False
            update_data["custom_tone_schema"] = None
            update_data["custom_tone_rows"] = None
        elif "custom_tone_schema_enabled" in update_data or "custom_tone_rows_enabled" in update_data or "custom_tone_schema" in update_data or "custom_tone_rows" in update_data:
            # DB agent trying to set custom tone - silently ignore and clear
            update_data["custom_tone_schema_enabled"] = False
            update_data["custom_tone_rows_enabled"] = False
            update_data["custom_tone_schema"] = None
            update_data["custom_tone_rows"] = None
    
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
    
    # Delete agent (cascade will handle related records if tables exist)
    # Handle case where agent_credentials table might not exist
    try:
        db.delete(agent)
        db.commit()
    except Exception as e:
        db.rollback()
        # If error is due to missing agent_credentials table, delete using raw SQL
        if "agent_credentials" in str(e).lower() or "does not exist" in str(e).lower():
            # Delete directly using SQL to avoid relationship loading
            db.execute(delete(Agent).where(Agent.id == agent_id))
            db.commit()
        else:
            raise
    
    return {"ok": True, "message": "Agent deleted successfully"}


@router.post(
    "/{account_id}/{agent_id}/credentials",
    response_model=AgentCredentialOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create client credentials for agent embed",
    description="""
    Create credentials for embedding an agent widget.
    
    These credentials are used with the /embed/launch endpoint to generate
    secure launch tokens for the agent chatbot widget.
    
    Requires OWNER, ADMIN, or MEMBER role for the account.
    """,
)
def create_agent_credentials(
    account_id: UUID,
    agent_id: UUID,
    body: AgentCredentialCreate,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER})),
    db: Session = Depends(get_db),
):
    """Create credentials for agent embed widget."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Verify agent exists and belongs to account
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Verify agent_id in body matches path parameter
    if body.agent_id != agent_id:
        raise HTTPException(status_code=400, detail="Agent ID mismatch")
    
    # Check if credential already exists (only one per agent)
    credential = db.query(AgentCredential).filter(
        AgentCredential.agent_id == agent_id
    ).first()
    
    # Default theme configuration
    default_theme = {
        "primary": "#0F172A",
        "accent": "#3B82F6",
        "background": "#F8FAFC",
        "surface": "#FFFFFF",
        "textPrimary": "#0F172A",
        "border": "#E2E8F0",
        "success": "#22C55E"
    }
    
    if credential:
        # Update existing credential (ensure it's active and account matches)
        credential.account_id = account_id
        credential.is_active = True
        # Set default theme if not already set
        if not credential.theme:
            credential.theme = default_theme
    else:
        # Create new credential with default theme
        credential = AgentCredential(
            agent_id=agent_id,
            account_id=account_id,
            is_active=True,
            theme=default_theme
        )
        db.add(credential)
    
    db.commit()
    db.refresh(credential)
    
    # Generate embed_url if credential is active
    embed_url = None
    if credential.is_active:
        # Generate new token and store in credential
        raw_token = secrets.token_urlsafe(32).rstrip('=')
        token_hash = sha256(raw_token)
        
        # Store token in credential
        credential.token_hash = token_hash
        credential.raw_token = raw_token
        db.commit()
        
        # Build embed URL with token as query parameter
        embed_url = f"{settings.app_base_url}/embed/chatbot?token={raw_token}"
    
    return AgentCredentialOut.from_orm(credential, embed_url=embed_url)


@router.get(
    "/{account_id}/{agent_id}/credentials",
    response_model=List[AgentCredentialOut],
    summary="List credentials for an agent",
    description="""
    Get credential for an agent (only one per agent).
    
    Requires OWNER, ADMIN, or MEMBER role for the account.
    """,
)
def list_agent_credentials(
    account_id: UUID,
    agent_id: UUID,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER})),
    db: Session = Depends(get_db),
):
    """Get credential for an agent (only one per agent)."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Verify agent exists and belongs to account
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get credential (only one per agent)
    credential = db.query(AgentCredential).filter(
        AgentCredential.agent_id == agent_id,
        AgentCredential.account_id == account_id
    ).first()
    
    if not credential:
        return []
    
    # Check if there's a token for this agent
    embed_url = None
    if credential.is_active:
        # Check if credential has a token
        if credential.token_hash and credential.raw_token:
            embed_url = f"{settings.app_base_url}/embed/chatbot?token={credential.raw_token}"
    
    return [AgentCredentialOut.from_orm(credential, embed_url=embed_url)]


@router.delete(
    "/{account_id}/{agent_id}/credentials/{credential_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete agent credentials",
    description="""
    Delete credentials for an agent.
    
    Any existing launch tokens using these credentials will no longer work.
    
    Requires OWNER, ADMIN, or MEMBER role for the account.
    """,
)
def delete_agent_credentials(
    account_id: UUID,
    agent_id: UUID,
    credential_id: UUID,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER})),
    db: Session = Depends(get_db),
):
    """Delete agent credentials."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Verify agent exists and belongs to account
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get credential
    credential = db.query(AgentCredential).filter(
        AgentCredential.id == credential_id,
        AgentCredential.agent_id == agent_id,
        AgentCredential.account_id == account_id
    ).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    db.delete(credential)
    db.commit()
    
    return {"ok": True, "message": "Credential deleted successfully"}


@router.patch(
    "/{account_id}/{agent_id}/credentials/{credential_id}/toggle",
    response_model=AgentCredentialOut,
    summary="Toggle embed status",
    description="""
    Enable or disable embed launch for an agent.
    
    When disabled (is_active=False), the embed launch endpoint will reject requests
    and existing tokens will not validate.
    
    Requires OWNER, ADMIN, or MEMBER role for the account.
    """,
)
def toggle_agent_credential_status(
    account_id: UUID,
    agent_id: UUID,
    credential_id: UUID,
    body: AgentCredentialToggleRequest,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER})),
    db: Session = Depends(get_db),
):
    """Toggle embed status for agent credentials."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Verify agent exists and belongs to account
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get credential
    credential = db.query(AgentCredential).filter(
        AgentCredential.id == credential_id,
        AgentCredential.agent_id == agent_id,
        AgentCredential.account_id == account_id
    ).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    # Update status
    credential.is_active = body.is_active
    db.commit()
    db.refresh(credential)
    
    # Generate embed_url if credential is now active
    embed_url = None
    if credential.is_active:
        # Generate new token and store in credential
        raw_token = secrets.token_urlsafe(32).rstrip('=')
        token_hash = sha256(raw_token)
        
        # Store token in credential
        credential.token_hash = token_hash
        credential.raw_token = raw_token
        db.commit()
        
        # Build embed URL with token as query parameter
        embed_url = f"{settings.app_base_url}/embed/chatbot?token={raw_token}"
    
    return AgentCredentialOut.from_orm(credential, embed_url=embed_url)


@router.patch(
    "/{account_id}/{agent_id}/credentials/{credential_id}/theme",
    response_model=AgentCredentialOut,
    summary="Update embed widget theme",
    description="""
    Update the theme configuration for an agent's embed widget.
    
    The theme object should contain color values for:
    - primary: Brand color
    - accent: Buttons & actions color
    - background: Chat body background
    - surface: Input & cards background
    - textPrimary: Main text color
    - border: Separators color
    - success: Online status color (optional)
    
    Requires OWNER, ADMIN, or MEMBER role for the account.
    """,
)
def update_agent_credential_theme(
    account_id: UUID,
    agent_id: UUID,
    credential_id: UUID,
    body: AgentCredentialThemeUpdate,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER})),
    db: Session = Depends(get_db),
):
    """Update theme configuration for agent embed widget."""
    user, verified_account_id, _ = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Get credential
    credential = db.query(AgentCredential).filter(
        AgentCredential.id == credential_id,
        AgentCredential.agent_id == agent_id,
        AgentCredential.account_id == account_id
    ).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    # Update theme
    credential.theme = body.theme
    db.commit()
    db.refresh(credential)
    
    # Generate embed_url if credential is active
    embed_url = None
    if credential.is_active and credential.raw_token:
        embed_url = f"{settings.app_base_url}/embed/chatbot?token={credential.raw_token}"
    
    return AgentCredentialOut.from_orm(credential, embed_url=embed_url)


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
    response_model=AgentChatResponse,
    summary="Chat with agent",
    description="""
    Ask questions about your data using natural language.
    
    This endpoint implements the full chat-on-data functionality:
    - For PowerBI agents: Understands natural language questions, decides whether to answer from schema (DESCRIBE) or execute DAX queries (QUERY), handles typos and value resolution automatically, executes DAX queries with automatic error correction
    - For DB agents: Understands natural language questions, generates SQL queries, executes them, and returns conversational answers
    
    Returns conversational, human-friendly answers.
    
    The agent uses OpenAI to understand questions and generate queries (DAX for PowerBI, SQL for DB).
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def chat_with_agent(
    account_id: UUID,
    agent_id: UUID,
    body: AgentChatRequest,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Chat with agent (supports both PowerBI and DB connection types)."""
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
    
    # Get OpenAI API key from agent's api_key field or environment
    openai_api_key = agent.api_key or os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key is required. Set it in the agent's api_key field or OPENAI_API_KEY environment variable."
        )
    
    # Route to appropriate chat service based on connection type
    if agent.connection_type == ConnectionType.POWERBI:
        # Extract Power BI config
        try:
            config = PowerBIConfig(**agent.connection_config)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Power BI configuration: {str(e)}"
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
                model_type=agent.model_type,
                custom_tone_schema_enabled=agent.custom_tone_schema_enabled or False,
                custom_tone_rows_enabled=agent.custom_tone_rows_enabled or False,
                custom_tone_schema=agent.custom_tone_schema,
                custom_tone_rows=agent.custom_tone_rows,
            )
            # Convert PowerBI result to unified response format
            return AgentChatResponse(
                answer=result.get("answer", ""),
                resolution_note=result.get("resolution_note", ""),
                action=result.get("action", "ERROR"),
                dax_attempts=result.get("dax_attempts", []),
                final_dax=result.get("final_dax", ""),
                sql_attempts=[],
                final_sql="",
                error=result.get("error"),
            )
        except Exception as e:
            return AgentChatResponse(
                answer=f"An error occurred while processing your question: {str(e)}",
                resolution_note="",
                action="ERROR",
                dax_attempts=[],
                final_dax="",
                sql_attempts=[],
                final_sql="",
                error=str(e),
            )
    
    elif agent.connection_type == ConnectionType.DB:
        # Extract DB config
        try:
            config = DBConfig(**agent.connection_config)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid DB configuration: {str(e)}"
            )
        
        # Chat with DB (always uses default tone, custom tone is only for PowerBI)
        try:
            result = chat_with_db(
                question=body.question,
                database_type=config.database_type,
                host=config.host,
                port=config.port,
                database=config.database,
                username=config.username,
                password=config.password,
                openai_api_key=openai_api_key,
                model_type=agent.model_type,
                custom_tone_schema_enabled=False,
                custom_tone_rows_enabled=False,
                custom_tone_schema=None,
                custom_tone_rows=None,
            )
            # Convert DB result to unified response format
            return AgentChatResponse(
                answer=result.get("answer", ""),
                resolution_note=result.get("resolution_note", ""),
                action=result.get("action", "ERROR"),
                dax_attempts=[],
                final_dax="",
                sql_attempts=result.get("sql_attempts", []),
                final_sql=result.get("final_sql", ""),
                error=result.get("error"),
            )
        except Exception as e:
            return AgentChatResponse(
                answer=f"An error occurred while processing your question: {str(e)}",
                resolution_note="",
                action="ERROR",
                dax_attempts=[],
                final_dax="",
                sql_attempts=[],
                final_sql="",
                error=str(e),
            )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Chat not supported for connection type: {agent.connection_type.value}"
        )

