from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging
from app.api.routes import auth, agents, tasks, conversations, tools, billing
from app.tools.base import tool_registry
from app.tools.builtin import register_builtin_tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    setup_logging()
    logger = structlog.get_logger()
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Register built-in tools
    register_builtin_tools()
    logger.info("Built-in tools registered", tool_count=len(tool_registry.tools))
    
    logger.info("CogniVerve-AI backend started", version="1.0.0")
    
    yield
    
    # Shutdown
    logger.info("CogniVerve-AI backend shutting down")


app = FastAPI(
    title="CogniVerve-AI API",
    description="Open-source AI agent platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "cogniverve-ai-backend",
        "version": "1.0.0"
    }


# API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["Conversations"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger = structlog.get_logger()
    logger.error("Unhandled exception", 
                path=request.url.path, 
                method=request.method, 
                error=str(exc))
    
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

