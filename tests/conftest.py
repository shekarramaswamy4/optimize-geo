"""Pytest configuration and fixtures."""

import json
import os
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, Response

# Set test environment variables before importing app
os.environ["OPENAI_API_KEY"] = "test-api-key"
os.environ["ENVIRONMENT"] = "testing"

from src.config.settings import Settings
from src.main import app
from src.models.schemas import CompanyInfo, QuestionType, SearchQuestion
from src.services.analyzer import WebsiteAnalyzerService
from tests.fixtures.test_data import (
    SAMPLE_COMPANY_ANALYSIS,
    SAMPLE_OPENAI_RESPONSES,
    SAMPLE_QUESTIONS,
    SAMPLE_WEBSITE_HTML,
    SAMPLE_WEBSITE_TEXT,
)


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        openai_api_key="test-api-key",
        environment="testing",
        log_level="DEBUG",
        rate_limit_enabled=False,
        enable_metrics=False,
    )


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Create mock OpenAI client."""
    mock_client = MagicMock()
    
    # Mock chat completions
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps(SAMPLE_COMPANY_ANALYSIS)))
    ]
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
    mock_client.models.list = AsyncMock(return_value=MagicMock())
    
    return mock_client


@pytest.fixture
def mock_httpx_response() -> MagicMock:
    """Create mock HTTPX response."""
    mock_response = MagicMock()
    mock_response.content = SAMPLE_WEBSITE_HTML.encode()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.raise_for_status = MagicMock()
    return mock_response


@pytest_asyncio.fixture
async def analyzer_service(test_settings: Settings, mock_openai_client: MagicMock, mock_httpx_response: MagicMock) -> AsyncGenerator[WebsiteAnalyzerService, None]:
    """Create test analyzer service with mocks."""
    service = WebsiteAnalyzerService(test_settings)
    service.openai_client = mock_openai_client
    
    # Mock HTTP client
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_httpx_response)
    mock_http_client.aclose = AsyncMock()
    service.http_client = mock_http_client
    
    yield service


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    # Override both settings and analyzer service for testing
    with patch("src.api.dependencies.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            openai_api_key="test-api-key",
            environment="testing",
            rate_limit_enabled=False,
            enable_metrics=False,
        )
        
        # Also patch the analyzer service globally
        with patch("src.api.dependencies._analyzer_service", None):
            async with AsyncClient(app=app, base_url="http://test") as ac:
                yield ac


@pytest.fixture
def sample_company_info() -> CompanyInfo:
    """Create sample company info."""
    return CompanyInfo(**SAMPLE_COMPANY_ANALYSIS)


@pytest.fixture
def sample_questions() -> dict[str, list[SearchQuestion]]:
    """Create sample questions."""
    questions = {
        "company_specific": [],
        "problem_based": [],
    }
    
    for q in SAMPLE_QUESTIONS["company_specific"]:
        questions["company_specific"].append(
            SearchQuestion(
                question=q["question"],
                question_type=QuestionType.COMPANY_SPECIFIC,
                intent=q["intent"],
            )
        )
    
    for q in SAMPLE_QUESTIONS["problem_based"]:
        questions["problem_based"].append(
            SearchQuestion(
                question=q["question"],
                question_type=QuestionType.PROBLEM_BASED,
                intent=q["intent"],
            )
        )
    
    return questions


@pytest.fixture
def mock_openai_responses() -> dict[str, str]:
    """Get mock OpenAI responses."""
    return SAMPLE_OPENAI_RESPONSES


@pytest.fixture
def mock_successful_analysis() -> dict[str, Any]:
    """Create a complete successful analysis response."""
    return {
        "request_id": "test_123",
        "status": "completed",
        "company_info": SAMPLE_COMPANY_ANALYSIS,
        "questions": SAMPLE_QUESTIONS,
        "test_results": [
            {
                "question": "What are TechCorp cloud infrastructure reviews?",
                "question_type": "company_specific",
                "response": SAMPLE_OPENAI_RESPONSES["company_specific_good"],
                "score": 2,
                "scoring_reason": "Comprehensive and relevant response",
                "mentions_company": True,
            }
        ],
        "success_rate": 0.85,
        "metadata": {"website_url": "https://techcorp.com"},
    }


# Pytest plugins configuration
pytest_plugins = ["pytest_asyncio"]