# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import atexit

from app.core.config import settings
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.api.routes.schemas import router as schemas_router
from app.api.routes.auth import router as auth_router
from app.api.routes.accounts import router as accounts_router
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.stripe_webhook import router as stripe_webhook_router
from app.api.routes.public_plans import router as public_plans_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.mapper import router as mapper_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.contact import router as contact_router
from app.api.routes.surveys import router as surveys_router
from app.api.routes.survey_public import router as survey_public_router
from app.api.routes.agents import router as agents_router
from app.api.routes.chats import router as chats_router
from app.api.routes.embed import router as embed_router
from app.api.routes.agent_launch import router as agent_launch_router

app = FastAPI(
    title=settings.app_name,
    docs_url="/gibberish-xyz-123",             # new Swagger UI path
    redoc_url=None,                            # disable ReDoc if you don't need it
    openapi_url="/gibberish-xyz-123/openapi.json"  # OpenAPI JSON path
)

# CORS - Allow embedding from any origin for embed widget
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for embed widget (can be restricted in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers for iframe embedding
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Allow embedding in iframes from any origin
    # Note: X-Frame-Options doesn't support ALLOWALL, so we remove it and use CSP instead
    # In production, you may want to restrict frame-ancestors to specific domains
    if "/embed/" in str(request.url.path):
        # Only allow iframe embedding for embed routes
        # Remove X-Frame-Options if it exists (MutableHeaders doesn't have pop)
        if "X-Frame-Options" in response.headers:
            del response.headers["X-Frame-Options"]
        response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

# Routers
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(schemas_router)
app.include_router(subscriptions_router)
app.include_router(stripe_webhook_router)
app.include_router(public_plans_router)
app.include_router(integrations_router)
app.include_router(mapper_router)
app.include_router(dashboard_router)
app.include_router(contact_router)
app.include_router(surveys_router)
app.include_router(survey_public_router)
app.include_router(agents_router)
app.include_router(chats_router)
app.include_router(embed_router)
app.include_router(agent_launch_router)

# Start pipeline scheduler on app startup
@app.on_event("startup")
def startup_event():
    """Start pipeline scheduler when app starts."""
    try:
        start_scheduler()
    except Exception as e:
        print(f"Warning: Failed to start pipeline scheduler: {e}")

# Stop scheduler on app shutdown
@app.on_event("shutdown")
def shutdown_event():
    """Stop pipeline scheduler when app shuts down."""
    try:
        stop_scheduler()
    except Exception as e:
        print(f"Warning: Failed to stop pipeline scheduler: {e}")

# Also register shutdown handler for graceful exit
atexit.register(stop_scheduler)

@app.get("/health")
def health():
    return {"ok": True}