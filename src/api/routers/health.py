from typing import Annotated

from fastapi import APIRouter, Depends

from src.config.settings import Settings, get_settings
from src.models.schemas import HealthResponse
from src.services.analyzer import WebsiteAnalyzerService
from src.api.dependencies import get_analyzer_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    analyzer: Annotated[WebsiteAnalyzerService, Depends(get_analyzer_service)],
) -> HealthResponse:
    """Check the health status of the API and its dependencies."""
    services_status = {"openai": "unknown"}
    
    # Check OpenAI connectivity
    try:
        # Simple test to check if OpenAI is accessible
        await analyzer.openai_client.models.list()
        services_status["openai"] = "healthy"
    except Exception:
        services_status["openai"] = "unhealthy"
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        services=services_status,
    )


@router.get("/readiness")
async def readiness_check(
    analyzer: Annotated[WebsiteAnalyzerService, Depends(get_analyzer_service)],
) -> dict[str, str]:
    """Check if the service is ready to handle requests."""
    # Perform any initialization checks here
    return {"status": "ready"}