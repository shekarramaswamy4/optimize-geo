"""Simplified performance tests for LumaRank."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from src.config.settings import Settings
from src.models.schemas import CompanyInfo
from src.services.analyzer import WebsiteAnalyzerService
from tests.fixtures.test_data import SAMPLE_COMPANY_ANALYSIS


class TestBasicPerformance:
    """Basic performance tests."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent requests."""
        settings = Settings(
            openai_api_key="test-key",
            environment="testing",
            http_timeout=5,
        )
        
        service = WebsiteAnalyzerService(settings)
        
        # Mock the clients
        service.http_client = AsyncMock()
        service.http_client.get = AsyncMock(return_value=MagicMock(
            content=b"<html><body>Test</body></html>",
            raise_for_status=MagicMock()
        ))
        service.http_client.aclose = AsyncMock()
        
        # Test concurrent fetches
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
        
        start_time = time.time()
        tasks = [service.fetch_website_content(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Should complete all requests
        assert len(results) == 3
        assert all(isinstance(r, str) for r in results)
        
        # Should be reasonably fast
        assert end_time - start_time < 2.0
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_api_response_time(self, client: AsyncClient):
        """Test basic API response time."""
        with patch("src.api.routers.health.get_analyzer_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.openai_client.models.list = AsyncMock(return_value=MagicMock())
            mock_get_service.return_value = mock_service
            
            start_time = time.time()
            response = await client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            # Health check should be fast
            assert end_time - start_time < 2.0  # Allow more time for mocked health check
    
    def test_model_validation_speed(self):
        """Test Pydantic model validation is fast."""
        data = SAMPLE_COMPANY_ANALYSIS
        
        start_time = time.time()
        for _ in range(100):
            company = CompanyInfo(**data)
        end_time = time.time()
        
        # Should create 100 models quickly
        assert end_time - start_time < 0.1
    
    @pytest.mark.asyncio
    async def test_service_cleanup(self):
        """Test service cleanup."""
        settings = Settings(
            openai_api_key="test-key",
            environment="testing",
        )
        
        service = WebsiteAnalyzerService(settings)
        service.http_client = AsyncMock()
        service.http_client.aclose = AsyncMock()
        
        await service.close()
        
        # Should call cleanup
        service.http_client.aclose.assert_called_once()