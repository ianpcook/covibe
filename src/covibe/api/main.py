"""Main FastAPI application setup."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from ..models.core import ErrorResponse, ErrorDetail


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Covibe API server")
    yield
    logger.info("Shutting down Covibe API server")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Covibe API",
        description="Agent Personality System - Enhance coding agents with configurable personalities",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    @app.middleware("http")
    async def add_request_id_middleware(request: Request, call_next):
        """Add request ID to all requests."""
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        request_id = getattr(request.state, 'request_id', 'unknown')
        logger.error(f"Unhandled exception in request {request_id}: {exc}")
        
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                suggestions=["Please try again later", "Contact support if the problem persists"]
            ),
            request_id=request_id,
            timestamp=datetime.now()
        )
        
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder(error_response.dict())
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "service": "covibe-api"
        }
    
    # Include routers
    from .personality import router as personality_router
    app.include_router(personality_router)
    
    return app


# Create the app instance
app = create_app()
