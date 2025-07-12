from typing import Annotated

from fastapi import Depends, Header

from src.config.settings import Settings, get_settings
from src.services.analyzer import WebsiteAnalyzerService
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Cached service instance
_analyzer_service: WebsiteAnalyzerService | None = None


async def get_analyzer_service(
    settings: Annotated[Settings, Depends(get_settings)]
) -> WebsiteAnalyzerService:
    """Get or create the analyzer service instance."""
    global _analyzer_service
    
    if _analyzer_service is None:
        logger.info("Creating new analyzer service instance")
        _analyzer_service = WebsiteAnalyzerService(settings)
    
    return _analyzer_service


async def get_request_id(
    x_request_id: Annotated[str | None, Header()] = None,
) -> str:
    """Extract or generate request ID from headers."""
    if x_request_id:
        return x_request_id
    
    # Generate a new request ID if not provided
    import uuid
    return f"req_{uuid.uuid4().hex[:12]}"