from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Query, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db
from app.models.agent import Agent, ConnectionType
from app.schemas.agent import PowerBIConfig, DBConfig
from app.services.powerbi_chat import chat_with_powerbi
from app.services.db_chat import chat_with_db
import os

router = APIRouter(prefix="/embed", tags=["embed"])


class EmbedChatRequest(BaseModel):
    question: str


@router.get("/widget/{agent_id}", response_class=HTMLResponse)
async def embed_widget(
    agent_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Returns HTML chatbot widget for iframe embedding.
    
    This widget allows users to chat with an agent without authentication.
    Chat messages are NOT stored in the database (non-persistent).
    
    Usage:
        <iframe src="https://your-backend.com/embed/widget/{agent_id}" 
                width="100%" height="600px" frameborder="0"></iframe>
    """
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        # Return error page instead of raising exception
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Agent Not Found</title>
                <style>
                    body { margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #f5f5f5; }
                    .error { background: white; padding: 20px; border-radius: 8px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>Agent Not Found</h2>
                    <p>The requested agent does not exist or is not available.</p>
                </div>
            </body>
            </html>
            """,
            status_code=404
        )
    
    # Only support POWERBI agents
    if agent.connection_type != ConnectionType.POWERBI:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Agent Not Supported</title>
                <style>
                    body { margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #f5f5f5; }
                    .error { background: white; padding: 20px; border-radius: 8px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>Agent Not Supported</h2>
                    <p>This agent type does not support chat functionality.</p>
                </div>
            </body>
            </html>
            """,
            status_code=400
        )
    
    # Get base URL for API calls
    base_url = str(request.base_url).rstrip('/')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat with {agent.name}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: #f5f5f5;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            
            .chat-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .chat-header h2 {{
                font-size: 18px;
                font-weight: 600;
            }}
            
            .chat-header p {{
                font-size: 12px;
                opacity: 0.9;
                margin-top: 4px;
            }}
            
            .chat-messages {{
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            
            .message {{
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
                animation: fadeIn 0.3s ease-in;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .message.user {{
                background: #667eea;
                color: white;
                align-self: flex-end;
                border-bottom-right-radius: 4px;
            }}
            
            .message.assistant {{
                background: white;
                color: #333;
                align-self: flex-start;
                border-bottom-left-radius: 4px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }}
            
            .message.error {{
                background: #fee;
                color: #c33;
                border: 1px solid #fcc;
            }}
            
            .message.loading {{
                background: #f0f0f0;
                color: #666;
                font-style: italic;
            }}
            
            .chat-input-container {{
                background: white;
                padding: 16px 20px;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 12px;
            }}
            
            .chat-input {{
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 24px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }}
            
            .chat-input:focus {{
                border-color: #667eea;
            }}
            
            .send-button {{
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 24px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }}
            
            .send-button:hover:not(:disabled) {{
                background: #5568d3;
            }}
            
            .send-button:disabled {{
                background: #ccc;
                cursor: not-allowed;
            }}
            
            .empty-state {{
                text-align: center;
                color: #999;
                padding: 40px 20px;
            }}
            
            .empty-state h3 {{
                font-size: 18px;
                margin-bottom: 8px;
            }}
            
            .empty-state p {{
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="chat-header">
            <h2>{agent.name}</h2>
            <p>{agent.description or 'Ask me anything about your data'}</p>
        </div>
        
        <div class="chat-messages" id="messages">
            <div class="empty-state">
                <h3>👋 Hello!</h3>
                <p>Start a conversation by asking a question below.</p>
            </div>
        </div>
        
        <div class="chat-input-container">
            <input 
                type="text" 
                class="chat-input" 
                id="messageInput" 
                placeholder="Type your question here..."
                autocomplete="off"
            />
            <button class="send-button" id="sendButton">Send</button>
        </div>
        
        <script>
            const agentId = '{agent_id}';
            const baseUrl = '{base_url}';
            const messagesContainer = document.getElementById('messages');
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            
            // Remove empty state when first message is sent
            let isEmpty = true;
            
            // Add message to chat
            function addMessage(content, role, isError = false) {{
                if (isEmpty) {{
                    messagesContainer.innerHTML = '';
                    isEmpty = false;
                }}
                
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${{role}} ${{isError ? 'error' : ''}}`;
                messageDiv.textContent = content;
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                return messageDiv;
            }}
            
            // Add loading message
            function addLoadingMessage() {{
                if (isEmpty) {{
                    messagesContainer.innerHTML = '';
                    isEmpty = false;
                }}
                
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'message assistant loading';
                loadingDiv.textContent = 'Thinking...';
                loadingDiv.id = 'loading-message';
                messagesContainer.appendChild(loadingDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                return loadingDiv;
            }}
            
            // Remove loading message
            function removeLoadingMessage() {{
                const loading = document.getElementById('loading-message');
                if (loading) {{
                    loading.remove();
                }}
            }}
            
            // Send message
            async function sendMessage() {{
                const message = messageInput.value.trim();
                if (!message) return;
                
                // Disable input
                messageInput.disabled = true;
                sendButton.disabled = true;
                
                // Add user message
                addMessage(message, 'user');
                messageInput.value = '';
                
                // Add loading message
                addLoadingMessage();
                
                try {{
                    const response = await fetch(`${{baseUrl}}/embed/chat/${{agentId}}`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ question: message }})
                    }});
                    
                    const data = await response.json();
                    
                    removeLoadingMessage();
                    
                    if (response.ok) {{
                        // Add assistant response
                        addMessage(data.answer || 'No response received.', 'assistant');
                        
                        // Notify parent window
                        if (window.parent !== window) {{
                            window.parent.postMessage({{
                                type: 'chat-response',
                                agent_id: agentId,
                                question: message,
                                answer: data.answer,
                                action: data.action
                            }}, '*');
                        }}
                    }} else {{
                        // Show error
                        addMessage(data.detail || 'An error occurred. Please try again.', 'assistant', true);
                    }}
                }} catch (error) {{
                    removeLoadingMessage();
                    addMessage('Failed to send message. Please check your connection and try again.', 'assistant', true);
                    console.error('Error:', error);
                }} finally {{
                    // Re-enable input
                    messageInput.disabled = false;
                    sendButton.disabled = false;
                    messageInput.focus();
                }}
            }}
            
            // Event listeners
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    sendMessage();
                }}
            }});
            
            // Notify parent when ready
            if (window.parent !== window) {{
                window.parent.postMessage({{
                    type: 'widget-ready',
                    agent_id: agentId,
                    agent_name: '{agent.name}'
                }}, '*');
            }}
            
            // Listen for messages from parent
            window.addEventListener('message', (event) => {{
                if (event.data.type === 'send-message' && event.data.agent_id === agentId) {{
                    messageInput.value = event.data.message || '';
                    sendMessage();
                }}
            }});
            
            // Focus input on load
            messageInput.focus();
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.post(
    "/chat/{agent_id}",
    summary="Chat with agent (non-persistent)",
    description="""
    Send a message to an agent and get a response.
    
    This endpoint is designed for embed widgets and does NOT store messages in the database.
    It's a stateless chat endpoint that processes questions and returns answers immediately.
    
    Can be used with or without token authentication.
    """,
)
async def embed_chat(
    agent_id: UUID,
    body: EmbedChatRequest,
    token: Optional[str] = Query(None, description="Optional launch token for validation"),
    db: Session = Depends(get_db),
):
    """
    Non-persistent chat endpoint for embed widget.
    Messages are NOT stored in the database.
    """
    # Get agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if agent is active
    if agent.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Agent is not active. Current status: {agent.status}"
        )
    
    # Get OpenAI API key from agent's api_key field or environment
    openai_api_key = agent.api_key or os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key is required. Set it in the agent's api_key field or OPENAI_API_KEY environment variable."
        )
    
    # Route to appropriate chat service based on connection type
    try:
        if agent.connection_type == ConnectionType.POWERBI:
            # Extract Power BI config
            try:
                config = PowerBIConfig(**agent.connection_config)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid Power BI configuration: {str(e)}"
                )
            
            # Chat with Power BI (non-persistent - no database storage)
            result = chat_with_powerbi(
                question=body.question,
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
            
            return {
                "answer": result.get("answer", ""),
                "resolution_note": result.get("resolution_note", ""),
                "action": result.get("action", "DESCRIBE"),
                "dax_attempts": result.get("dax_attempts", []),
                "final_dax": result.get("final_dax", ""),
                "error": result.get("error"),
            }
        
        elif agent.connection_type == ConnectionType.DB:
            # Extract DB config
            try:
                config = DBConfig(**agent.connection_config)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid DB configuration: {str(e)}"
                )
            
            # Chat with DB (non-persistent - no database storage)
            result = chat_with_db(
                question=body.question,
                database_type=config.database_type,
                host=config.host,
                port=config.port,
                database=config.database,
                username=config.username,
                password=config.password,
                openai_api_key=openai_api_key,
                custom_tone_schema_enabled=agent.custom_tone_schema_enabled or False,
                custom_tone_rows_enabled=agent.custom_tone_rows_enabled or False,
                custom_tone_schema=agent.custom_tone_schema,
                custom_tone_rows=agent.custom_tone_rows,
            )
            
            return {
                "answer": result.get("answer", ""),
                "resolution_note": result.get("resolution_note", ""),
                "action": result.get("action", "DESCRIBE"),
                "dax_attempts": result.get("sql_attempts", []),  # Map SQL to DAX field for compatibility
                "final_dax": result.get("final_sql", ""),  # Map SQL to DAX field for compatibility
                "error": result.get("error"),
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Chat not supported for connection type: {agent.connection_type.value}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "answer": f"An error occurred while processing your question: {str(e)}",
            "resolution_note": "",
            "action": "ERROR",
            "dax_attempts": [],
            "final_dax": "",
            "error": str(e),
        }


@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot_frontend_page(request: Request, db: Session = Depends(get_db)):
    """
    Frontend page that extracts token from URL query parameter and loads the chatbot widget.
    This page validates the token and embeds the widget iframe.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat with Agent</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                background: #f5f5f5;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .container {
                width: 100%;
                max-width: 900px;
                height: 100vh;
                background: white;
                display: flex;
                flex-direction: column;
            }
            
            .loading {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                gap: 20px;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .error {
                padding: 40px;
                text-align: center;
                color: #c33;
            }
            
            .error h2 {
                margin-bottom: 10px;
            }
            
            iframe {
                width: 100%;
                height: 100%;
                border: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Loading chatbot...</p>
            </div>
            <div id="error" class="error" style="display: none;">
                <h2>Error</h2>
                <p id="errorMessage"></p>
            </div>
            <iframe id="chatWidget" style="display: none;"></iframe>
        </div>
        
        <script>
            // Extract token from URL query parameter
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');
            
            const loadingDiv = document.getElementById('loading');
            const errorDiv = document.getElementById('error');
            const errorMessage = document.getElementById('errorMessage');
            const chatWidget = document.getElementById('chatWidget');
            
            if (!token) {
                loadingDiv.style.display = 'none';
                errorDiv.style.display = 'block';
                errorMessage.textContent = 'No token provided in URL';
            } else {
                // Validate token with backend
                fetch(`/embed/validate-token?token=${encodeURIComponent(token)}`)
                    .then(res => {
                        if (!res.ok) {
                            return res.json().then(data => {
                                throw new Error(data.detail || 'Token validation failed');
                            });
                        }
                        return res.json();
                    })
                    .then(data => {
                        // Token is valid, load the widget
                        const baseUrl = window.location.origin;
                        chatWidget.src = `${baseUrl}/embed/widget/${data.agent_id}?token=${encodeURIComponent(token)}`;
                        loadingDiv.style.display = 'none';
                        chatWidget.style.display = 'block';
                    })
                    .catch(err => {
                        loadingDiv.style.display = 'none';
                        errorDiv.style.display = 'block';
                        errorMessage.textContent = err.message || 'Failed to validate token';
                    });
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

