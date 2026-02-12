from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.api.deps import get_db
from app.models.agent import Agent, ConnectionType
from app.models.agent_credentials import AgentCredential, AgentLaunchToken
from app.schemas.agent_launch import AgentLaunchRequest, AgentLaunchResponse, AgentLaunchTokenValidation
from app.core.security import make_agent_launch_token, decode_jwt, sha256, now_utc
from app.core.config import settings

router = APIRouter(prefix="/embed", tags=["embed-launch"])


@router.post("/launch", response_model=AgentLaunchResponse)
async def launch_agent_widget(
    body: AgentLaunchRequest,
    db: Session = Depends(get_db),
):
    """
    Launch endpoint: Generate short-lived token and return frontend URL.
    
    Validates client_id/client_secret and agent_id, creates single-use token,
    and returns URL with token in fragment.
    """
    
    # 1. Validate credentials
    credential = db.query(AgentCredential).filter(
        AgentCredential.client_id == body.client_id,
        AgentCredential.is_active == True
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client_id"
        )
    
    # Verify client_secret (in production, compare hashed)
    if credential.client_secret != body.client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client_secret"
        )
    
    # 2. Validate agent_id
    try:
        agent_uuid = UUID(body.agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent_id format"
        )
    
    agent = db.query(Agent).filter(
        Agent.id == agent_uuid,
        Agent.account_id == credential.account_id  # Verify agent belongs to same account
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or not accessible"
        )
    
    # Verify agent is active
    if agent.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not active. Current status: {agent.status}"
        )
    
    # Verify agent type is POWERBI
    if agent.connection_type != ConnectionType.POWERBI:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chat only supported for POWERBI agents. This agent has type: {agent.connection_type.value}"
        )
    
    # 3. Generate short-lived token (default 5 minutes)
    token_ttl = settings.launch_token_ttl_seconds
    raw_token = make_agent_launch_token(
        str(agent.id),
        str(credential.id),
        str(credential.account_id),
        ttl_seconds=token_ttl
    )
    token_hash = sha256(raw_token)
    
    # 4. Store token in database (for single-use tracking)
    expires_at = now_utc() + timedelta(seconds=token_ttl)
    launch_token = AgentLaunchToken(
        credential_id=credential.id,
        agent_id=agent.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(launch_token)
    db.commit()
    
    # 5. Build frontend URL with token in fragment
    frontend_url = f"{settings.app_base_url}/embed/chatbot#{raw_token}"
    
    return AgentLaunchResponse(frontend_url=frontend_url)


@router.get("/validate-token", response_model=AgentLaunchTokenValidation)
async def validate_agent_launch_token(
    token: str = Query(..., description="Launch token from URL fragment"),
    db: Session = Depends(get_db),
):
    """
    Validate launch token and return agent details.
    Called by frontend to get agent config.
    """
    import jwt
    
    try:
        # Decode JWT
        payload = decode_jwt(token)
        agent_id = payload.get("agent_id")
        cred_id = payload.get("cred_id")
        
        if not agent_id or not cred_id:
            raise HTTPException(status_code=400, detail="Invalid token payload")
        
        # Check token in database (single-use)
        token_hash = sha256(token)
        launch_token = db.query(AgentLaunchToken).filter(
            AgentLaunchToken.token_hash == token_hash
        ).first()
        
        if not launch_token:
            raise HTTPException(status_code=401, detail="Token not found")
        
        if launch_token.consumed_at:
            raise HTTPException(status_code=401, detail="Token already used")
        
        if launch_token.expires_at < now_utc():
            raise HTTPException(status_code=401, detail="Token expired")
        
        # Mark as consumed (single-use)
        launch_token.consumed_at = now_utc()
        db.commit()
        
        # Get agent
        agent = db.get(Agent, UUID(agent_id))
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return AgentLaunchTokenValidation(
            agent_id=str(agent.id),
            agent_name=agent.name,
            account_id=str(launch_token.credential.account_id),
            credential_id=str(launch_token.credential_id)
        )
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

