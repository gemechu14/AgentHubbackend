# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(
    title=settings.app_name,
    docs_url="/gibberish-xyz-123",             # new Swagger UI path
    redoc_url=None,                            # disable ReDoc if you don't need it
    openapi_url="/gibberish-xyz-123/openapi.json"  # OpenAPI JSON path
)

# CORS (open for now; tighten to specific origins later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.smartschema.io", "https://www.app.smartschema.io", "http://localhost:3000","http://localhost:3001","https://smartschema.io", "https://www.smartschema.io"],              # e.g., ["http://localhost:3000", "https://your-frontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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