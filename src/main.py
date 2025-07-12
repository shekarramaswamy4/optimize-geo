from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from src.api.middleware import RateLimitMiddleware, RequestContextMiddleware
from src.api.routers import analyzer, auth, health
from src.config.settings import get_settings
from src.core.exceptions import WebsiteAnalyzerError
from src.models.schemas import ErrorResponse
from src.utils.logging import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting LumaRank API")
    
    # Startup
    settings = get_settings()
    logger.info(
        "Application started",
        environment=settings.environment,
        debug=settings.debug,
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down LumaRank API")
    
    # Clean up any resources here
    from src.api.dependencies import _analyzer_service
    if _analyzer_service:
        await _analyzer_service.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-grade SEO analyzer API",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Add custom middleware
    app.add_middleware(RequestContextMiddleware)
    
    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.rate_limit_requests,
        )
    
    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(analyzer.router)
    
    # Mount metrics endpoint if enabled
    if settings.enable_metrics:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
    
    # Global exception handler
    @app.exception_handler(WebsiteAnalyzerError)
    async def website_analyzer_exception_handler(
        request: Request, exc: WebsiteAnalyzerError
    ) -> JSONResponse:
        """Handle application-specific exceptions."""
        error_response = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=request.headers.get("X-Request-ID"),
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error("Unhandled exception", error=str(exc), exc_info=True)
        
        error_response = ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            request_id=request.headers.get("X-Request-ID"),
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(),
        )
    
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, Any]:
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "documentation": {
                "openapi": "/docs" if settings.is_development else None,
                "redoc": "/redoc" if settings.is_development else None,
            },
            "endpoints": {
                "health": "/health",
                "analyze": "/api/v1/analyze",
                "quick_analyze": "/api/v1/analyze/quick",
                "test_questions": "/api/v1/test-questions",
            },
        }
    
    return app


# Create the app instance
app = create_app()