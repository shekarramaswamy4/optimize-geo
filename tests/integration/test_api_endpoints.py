"""Clean integration tests for API endpoints with proper dependency injection."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.main import app
from src.api.dependencies import get_analyzer_service
from src.config.settings import get_settings, Settings
from src.models.schemas import CompanyInfo, QuestionType, SearchQuestion, TestResult
from tests.fixtures.test_data import SAMPLE_COMPANY_ANALYSIS, SAMPLE_QUESTIONS


# Override settings for all tests
def get_test_settings():
    return Settings(
        openai_api_key="test-api-key",
        environment="testing",
        rate_limit_enabled=False,
        enable_metrics=False,
    )


# Create mock analyzer service
def get_mock_analyzer_service():
    mock_service = AsyncMock()
    
    # Mock fetch_website_content
    mock_service.fetch_website_content = AsyncMock(return_value="Website content")
    
    # Mock analyze_content
    mock_service.analyze_content = AsyncMock(
        return_value=CompanyInfo(**SAMPLE_COMPANY_ANALYSIS)
    )
    
    # Mock generate_search_questions
    questions = {
        "company_specific": [
            SearchQuestion(
                question=q["question"],
                question_type=QuestionType.COMPANY_SPECIFIC,
                intent=q["intent"]
            ) for q in SAMPLE_QUESTIONS["company_specific"]
        ],
        "problem_based": [
            SearchQuestion(
                question=q["question"],
                question_type=QuestionType.PROBLEM_BASED,
                intent=q["intent"]
            ) for q in SAMPLE_QUESTIONS["problem_based"]
        ],
    }
    mock_service.generate_search_questions = AsyncMock(return_value=questions)
    
    # Mock test_all_questions
    test_results = [
        TestResult(
            question="Test question",
            question_type=QuestionType.COMPANY_SPECIFIC,
            response="Test response",
            score=2,
            scoring_reason="Good response",
            mentions_company=True
        )
    ]
    mock_service.test_all_questions = AsyncMock(return_value=(test_results, 0.85))
    
    # Mock close
    mock_service.close = AsyncMock()
    
    # Mock OpenAI client for health check
    mock_service.openai_client = MagicMock()
    mock_service.openai_client.models.list = AsyncMock(return_value=MagicMock())
    
    return mock_service


# Override dependencies
app.dependency_overrides[get_settings] = get_test_settings
app.dependency_overrides[get_analyzer_service] = get_mock_analyzer_service


@pytest.fixture
def test_client():
    """Create test client with overridden dependencies."""
    with TestClient(app) as client:
        yield client


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_endpoint_success(self, test_client):
        """Test successful health check."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["openai"] == "healthy"
    
    def test_readiness_endpoint(self, test_client):
        """Test readiness endpoint."""
        response = test_client.get("/readiness")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}


class TestAnalyzerEndpoints:
    """Test analyzer API endpoints."""
    
    def test_analyze_endpoint_success(self, test_client):
        """Test successful website analysis."""
        response = test_client.post(
            "/api/v1/analyze",
            json={"website_url": "https://example.com"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["company_info"]["name"] == "TechCorp"
        assert data["success_rate"] == 0.85
        assert "questions" in data
        assert "test_results" in data
    
    def test_quick_analyze_endpoint(self, test_client):
        """Test quick analysis endpoint."""
        response = test_client.post(
            "/api/v1/analyze/quick",
            json={"website_url": "https://example.com"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["test_results"] is None
    
    def test_test_questions_endpoint(self, test_client):
        """Test the test-questions endpoint."""
        response = test_client.post(
            "/api/v1/test-questions",
            json={
                "company_name": "TechCorp",
                "questions": [
                    {
                        "question": "What is TechCorp?",
                        "question_type": "company_specific",
                        "intent": "Learn about company",
                    }
                ],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["success_rate"] == 0.85
        assert data["metadata"]["test_only"] is True
    
    def test_invalid_url_validation(self, test_client):
        """Test validation error for invalid URL."""
        response = test_client.post(
            "/api/v1/analyze",
            json={"website_url": "not-a-url"},
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_missing_required_fields(self, test_client):
        """Test validation error for missing fields."""
        response = test_client.post(
            "/api/v1/analyze",
            json={},
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint returns API info."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data