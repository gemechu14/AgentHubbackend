from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import os

from app.api.deps import get_db
from app.api.deps_auth import current_user, require_role_for_account
from app.models.auth_models import User, Account, Role, Membership
from app.models.agent import Agent, ConnectionType
from app.models.chat import Chat, ChatMessage
from app.schemas.chat import (
    ChatCreate,
    ChatUpdate,
    ChatOut,
    ChatWithMessagesOut,
    ChatListOut,
    ChatMessageOut,
    MessageCreate,
    MessageUpdate,
    MessageResponse,
)
from app.schemas.agent import PowerBIConfig
from app.services.powerbi_chat import chat_with_powerbi
from app.core.security import now_utc

router = APIRouter(prefix="/chats", tags=["chats"])


def check_agent_access(
    db: Session,
    user_id: UUID,
    account_id: UUID,
    agent_id: UUID,
    caller_role: Role
) -> None:
    """Check if user has access to agent. Raises HTTPException if not."""
    # OWNER/ADMIN can access any agent
    if caller_role in (Role.OWNER, Role.ADMIN):
        return
    
    # MEMBER/VIEWER: check manage_agent_ids
    membership = db.query(Membership).filter(
        Membership.account_id == account_id,
        Membership.user_id == user_id
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


# ============================================================================
# Chat Management Endpoints
# ============================================================================

@router.post(
    "/{account_id}/{agent_id}",
    response_model=ChatOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat",
    description="""
    Create a new chat conversation for an agent.
    
    Each chat represents a separate conversation thread. You can create multiple
    chats per agent, similar to ChatGPT's conversation history.
    
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def create_chat(
    account_id: UUID,
    agent_id: UUID,
    body: ChatCreate,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Create a new chat."""
    user, verified_account_id, caller_role = tup
    
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
    
    # Check agent access
    check_agent_access(db, user.id, account_id, agent_id, caller_role)
    
    # Create chat
    chat = Chat(
        title=body.title or "New Chat",
        agent_id=agent_id,
        user_id=user.id,
        account_id=account_id,
    )
    
    db.add(chat)
    db.commit()
    db.refresh(chat)
    
    return chat


@router.get(
    "/{account_id}/{agent_id}",
    response_model=ChatListOut,
    summary="List all chats for an agent",
    description="""
    Get all chat conversations for a specific agent.
    
    Supports pagination with `skip` and `limit` query parameters.
    Returns chats ordered by most recently updated first.
    
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def list_chats(
    account_id: UUID,
    agent_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """List all chats for an agent."""
    user, verified_account_id, caller_role = tup
    
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
    
    # Check agent access
    check_agent_access(db, user.id, account_id, agent_id, caller_role)
    
    # Query chats - filter by user_id so users only see their own chats
    query = db.query(Chat).filter(
        Chat.agent_id == agent_id,
        Chat.account_id == account_id,
        Chat.user_id == user.id  # Only show chats created by the current user
    )
    
    total = query.count()
    chats = query.order_by(Chat.updated_at.desc()).offset(skip).limit(limit).all()
    
    # Add message count to each chat
    chat_list = []
    for chat in chats:
        message_count = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.chat_id == chat.id
        ).scalar()
        chat_dict = ChatOut.model_validate(chat).model_dump()
        chat_dict["message_count"] = message_count
        chat_list.append(ChatOut(**chat_dict))
    
    return ChatListOut(chats=chat_list, total=total)


@router.get(
    "/{account_id}/{agent_id}/{chat_id}",
    response_model=ChatWithMessagesOut,
    summary="Get a specific chat with messages",
    description="""
    Get a specific chat conversation with all its messages.
    
    Returns the chat metadata along with all messages in chronological order.
    
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def get_chat(
    account_id: UUID,
    agent_id: UUID,
    chat_id: UUID,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Get a specific chat with messages."""
    user, verified_account_id, caller_role = tup
    
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
    
    # Check agent access
    check_agent_access(db, user.id, account_id, agent_id, caller_role)
    
    # Get chat with messages - ensure user can only access their own chats
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.agent_id == agent_id,
        Chat.account_id == account_id,
        Chat.user_id == user.id  # Only allow access to own chats
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.chat_id == chat_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return ChatWithMessagesOut(
        id=chat.id,
        title=chat.title,
        agent_id=chat.agent_id,
        user_id=chat.user_id,
        account_id=chat.account_id,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        messages=[ChatMessageOut.model_validate(msg) for msg in messages],
    )


@router.patch(
    "/{account_id}/{agent_id}/{chat_id}",
    response_model=ChatOut,
    summary="Update chat title",
    description="""
    Update the title of a chat conversation.
    
    Only the title can be updated. All other fields are read-only.
    
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def update_chat(
    account_id: UUID,
    agent_id: UUID,
    chat_id: UUID,
    body: ChatUpdate,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Update chat title."""
    user, verified_account_id, caller_role = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Check agent access
    check_agent_access(db, user.id, account_id, agent_id, caller_role)
    
    # Get chat - ensure user can only access their own chats
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.agent_id == agent_id,
        Chat.account_id == account_id,
        Chat.user_id == user.id  # Only allow access to own chats
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Update title if provided
    if body.title is not None:
        chat.title = body.title
        chat.updated_at = now_utc()
    
    db.commit()
    db.refresh(chat)
    
    return chat


@router.delete(
    "/{account_id}/{agent_id}/{chat_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a chat",
    description="""
    Delete a chat conversation and all its messages.
    
    This action cannot be undone. All messages in the chat will be permanently deleted.
    
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def delete_chat(
    account_id: UUID,
    agent_id: UUID,
    chat_id: UUID,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Delete a chat."""
    user, verified_account_id, caller_role = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Check agent access
    check_agent_access(db, user.id, account_id, agent_id, caller_role)
    
    # Get chat - ensure user can only access their own chats
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.agent_id == agent_id,
        Chat.account_id == account_id,
        Chat.user_id == user.id  # Only allow access to own chats
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Delete chat (messages will be cascade deleted)
    db.delete(chat)
    db.commit()
    
    return {"ok": True, "message": "Chat deleted successfully"}


# ============================================================================
# Message Endpoints
# ============================================================================

@router.post(
    "/{account_id}/{agent_id}/{chat_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message in a chat",
    description="""
    Send a message in a chat conversation and get an AI response.
    
    This endpoint:
    1. Stores the user's message
    2. Processes it through the agent's chat service (Power BI chat)
    3. Stores the assistant's response
    4. Returns both messages
    
    The chat title will be automatically updated based on the first message if it's still "New Chat".
    
    Only works for agents with connection_type = POWERBI.
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def send_message(
    account_id: UUID,
    agent_id: UUID,
    chat_id: UUID,
    body: MessageCreate,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Send a message in a chat and get AI response."""
    user, verified_account_id, caller_role = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Check agent access
    check_agent_access(db, user.id, account_id, agent_id, caller_role)
    
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
            detail=f"Chat messages only supported for POWERBI agents. This agent has type: {agent.connection_type.value}"
        )
    
    # Get chat - ensure user can only access their own chats
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.agent_id == agent_id,
        Chat.account_id == account_id,
        Chat.user_id == user.id  # Only allow access to own chats
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
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
    
    # Store user message
    user_message = ChatMessage(
        chat_id=chat_id,
        role="user",
        content=body.content,
    )
    db.add(user_message)
    db.flush()  # Flush to get the message ID
    
    # Update chat title if it's still "New Chat" and this is the first message
    if chat.title == "New Chat":
        # Use first 50 characters of the message as title
        title = body.content[:50].strip()
        if len(body.content) > 50:
            title += "..."
        chat.title = title
        chat.updated_at = now_utc()
    
    # Chat with Power BI
    try:
        result = chat_with_powerbi(
            question=body.content,
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            workspace_id=config.workspace_id,
            dataset_id=config.dataset_id,
            client_secret=config.client_secret,
            openai_api_key=openai_api_key,
            custom_tone_schema_enabled=agent.custom_tone_schema_enabled or False,
            custom_tone_rows_enabled=agent.custom_tone_rows_enabled or False,
            custom_tone_schema=agent.custom_tone_schema,
            custom_tone_rows=agent.custom_tone_rows,
        )
        
        # Store assistant message
        assistant_message = ChatMessage(
            chat_id=chat_id,
            role="assistant",
            content=result.get("answer", ""),
            action=result.get("action"),
            dax_attempts=json.dumps(result.get("dax_attempts", [])) if result.get("dax_attempts") else None,
            final_dax=result.get("final_dax"),
            resolution_note=result.get("resolution_note"),
            error=result.get("error"),
        )
        db.add(assistant_message)
        
        # Update chat updated_at
        chat.updated_at = now_utc()
        
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
        db.refresh(chat)
        
        return MessageResponse(
            message=ChatMessageOut.model_validate(assistant_message),
            chat=ChatOut.model_validate(chat),
        )
        
    except Exception as e:
        # Store error message
        error_message = ChatMessage(
            chat_id=chat_id,
            role="assistant",
            content=f"An error occurred while processing your question: {str(e)}",
            action="ERROR",
            error=str(e),
        )
        db.add(error_message)
        chat.updated_at = now_utc()
        db.commit()
        db.refresh(error_message)
        db.refresh(chat)
        
        return MessageResponse(
            message=ChatMessageOut.model_validate(error_message),
            chat=ChatOut.model_validate(chat),
        )


@router.patch(
    "/{account_id}/{agent_id}/{chat_id}/messages/{message_id}",
    response_model=ChatMessageOut,
    summary="Update a message",
    description="""
    Update the content of a message in a chat.
    
    Currently, only user messages (questions) can be updated. 
    Assistant messages cannot be edited.
    
    Note: Updating a user message does NOT automatically regenerate the assistant response.
    You would need to delete the old assistant response and send a new message to get a new answer.
    
    Requires OWNER, ADMIN, MEMBER, or VIEWER role for the account.
    """,
)
def update_message(
    account_id: UUID,
    agent_id: UUID,
    chat_id: UUID,
    message_id: UUID,
    body: MessageUpdate,
    tup = Depends(require_role_for_account({Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER})),
    db: Session = Depends(get_db),
):
    """Update a message in a chat."""
    user, verified_account_id, caller_role = tup
    
    # Verify account_id matches
    if verified_account_id != account_id:
        raise HTTPException(status_code=403, detail="Account ID mismatch")
    
    # Check agent access
    check_agent_access(db, user.id, account_id, agent_id, caller_role)
    
    # Verify agent exists and belongs to account
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.account_id == account_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Verify chat exists and belongs to account - ensure user can only access their own chats
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.agent_id == agent_id,
        Chat.account_id == account_id,
        Chat.user_id == user.id  # Only allow access to own chats
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get message
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.chat_id == chat_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only allow updating user messages (not assistant messages)
    if message.role != "user":
        raise HTTPException(
            status_code=400,
            detail="Only user messages can be updated. Assistant messages cannot be edited."
        )
    
    # Update message content
    message.content = body.content
    
    # Update chat updated_at
    chat.updated_at = now_utc()
    
    db.commit()
    db.refresh(message)
    
    return ChatMessageOut.model_validate(message)

