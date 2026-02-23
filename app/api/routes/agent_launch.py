from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.agent import Agent, ConnectionType
from app.models.agent_credentials import AgentCredential
from app.schemas.agent_launch import AgentLaunchRequest, AgentLaunchResponse, AgentLaunchTokenValidation
from app.core.security import sha256, now_utc
import secrets
from app.core.config import settings

router = APIRouter(prefix="/embed", tags=["embed-launch"])


@router.post("/launch", response_model=AgentLaunchResponse)
async def launch_agent_widget(
    body: AgentLaunchRequest,
    db: Session = Depends(get_db),
):
    """
    Launch endpoint: Generate token and return frontend URL.
    
    Validates agent_id, creates new token (replaces any previous token for this agent),
    and returns URL with token in query parameter.
    
    Note: Generating a new token will replace the previous token for this agent.
    Tokens do not expire.
    """
    
    # 1. Validate agent_id
    try:
        agent_uuid = UUID(body.agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent_id format"
        )
    
    agent = db.query(Agent).filter(
        Agent.id == agent_uuid
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify agent is active
    if agent.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not active. Current status: {agent.status}"
        )
    
    # Check if credential exists, create if missing
    credential = db.query(AgentCredential).filter(
        AgentCredential.agent_id == agent_uuid
    ).first()
    
    if not credential:
        # Auto-create credentials if they don't exist
        credential = AgentCredential(
            agent_id=agent_uuid,
            account_id=agent.account_id,
            is_active=True
        )
        db.add(credential)
        db.commit()
        db.refresh(credential)
    
    if not credential.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Embed is currently disabled for this agent. Please enable it to use embed launch."
        )
    
    # 2. Generate new token and store in credential
    # Generate token (32 bytes = ~43 chars base64, remove padding = ~43 chars)
    raw_token = secrets.token_urlsafe(32).rstrip('=')  # ~43 characters
    token_hash = sha256(raw_token)
    
    # 3. Store token in credential (replaces any previous token)
    credential.token_hash = token_hash
    credential.raw_token = raw_token
    db.commit()
    
    # 4. Build frontend URL with token as query parameter
    frontend_url = f"{settings.app_base_url}/embed/chatbot?token={raw_token}"
    
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
    try:
        # Check token in credential (short random token, not JWT)
        token_hash = sha256(token)
        credential = db.query(AgentCredential).filter(
            AgentCredential.token_hash == token_hash
        ).first()
        
        if not credential:
            raise HTTPException(status_code=401, detail="Token not found")
        
        # Check if credential is active
        if not credential.is_active:
            raise HTTPException(status_code=403, detail="Embed is currently disabled for this agent")
        
        # Get agent
        agent = db.get(Agent, credential.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get recommended questions (ensure it's a list)
        recommended_questions = agent.recommended_questions or []
        if not isinstance(recommended_questions, list):
            recommended_questions = []
        
        return AgentLaunchTokenValidation(
            agent_id=str(agent.id),
            agent_name=agent.name,
            account_id=str(agent.account_id),
            recommended_questions=recommended_questions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

