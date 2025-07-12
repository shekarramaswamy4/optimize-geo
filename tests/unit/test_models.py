"""Unit tests for Pydantic models and schemas."""

import pytest
from pydantic import ValidationError

from src.models.schemas import (
    AnalysisResponse,
    AnalysisStatus,
    AnalyzeRequest,
    CompanyInfo,
    ErrorResponse,
    HealthResponse,
    QuestionType,
    SearchQuestion,
    TestQuestionsRequest,
    TestResult,
)


class TestCompanyInfo:
    """Test CompanyInfo model."""
    
    def test_valid_company_info(self):
        """Test creating valid company info."""
        data = {
            "name": "TechCorp",
            "description": "A tech company",
            "ideal_customer_profile": "Enterprises",
            "key_features": ["Feature 1", "Feature 2"],
            "pricing_info": "$100/month",
            "industry": "Technology",
        }
        
        company = CompanyInfo(**data)
        assert company.name == "TechCorp"
        assert len(company.key_features) == 2
        assert company.pricing_info == "$100/month"
    
    def test_optional_fields(self):
        """Test company info with optional fields."""
        data = {
            "name": "TechCorp",
            "description": "A tech company",
            "ideal_customer_profile": "Enterprises",
        }
        
        company = CompanyInfo(**data)
        assert company.key_features == []
        assert company.pricing_info is None
        assert company.industry is None
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            CompanyInfo(name="TechCorp")
        
        errors = exc_info.value.errors()
        assert len(errors) == 2  # description and ideal_customer_profile missing


class TestSearchQuestion:
    """Test SearchQuestion model."""
    
    def test_valid_question(self):
        """Test creating valid search question."""
        question = SearchQuestion(
            question="What is TechCorp?",
            question_type=QuestionType.COMPANY_SPECIFIC,
            intent="Learn about company",
        )
        
        assert question.question == "What is TechCorp?"
        assert question.question_type == QuestionType.COMPANY_SPECIFIC
    
    def test_question_whitespace_validation(self):
        """Test question whitespace is stripped."""
        question = SearchQuestion(
            question="  What is TechCorp?  ",
            question_type=QuestionType.COMPANY_SPECIFIC,
            intent="Learn",
        )
        
        assert question.question == "What is TechCorp?"
    
    def test_empty_question_validation(self):
        """Test validation error for empty question."""
        with pytest.raises(ValidationError) as exc_info:
            SearchQuestion(
                question="   ",
                question_type=QuestionType.COMPANY_SPECIFIC,
                intent="Learn",
            )
        
        errors = exc_info.value.errors()
        assert "Question cannot be empty" in str(errors[0])


class TestTestResult:
    """Test TestResult model."""
    
    def test_valid_test_result(self):
        """Test creating valid test result."""
        result = TestResult(
            question="What is TechCorp?",
            question_type=QuestionType.COMPANY_SPECIFIC,
            response="TechCorp is a cloud provider",
            score=2,
            scoring_reason="Good response",
            mentions_company=True,
        )
        
        assert result.score == 2
        assert result.mentions_company is True
    
    def test_score_validation(self):
        """Test score must be between 0 and 2."""
        # Test score too high
        with pytest.raises(ValidationError):
            TestResult(
                question="Test",
                question_type=QuestionType.COMPANY_SPECIFIC,
                response="Response",
                score=3,
                scoring_reason="Reason",
                mentions_company=True,
            )
        
        # Test negative score
        with pytest.raises(ValidationError):
            TestResult(
                question="Test",
                question_type=QuestionType.COMPANY_SPECIFIC,
                response="Response",
                score=-1,
                scoring_reason="Reason",
                mentions_company=True,
            )


class TestAnalyzeRequest:
    """Test AnalyzeRequest model."""
    
    def test_valid_request(self):
        """Test creating valid analyze request."""
        request = AnalyzeRequest(
            website_url="https://example.com",
            company_name="Example Corp",
            test_questions=True,
        )
        
        assert str(request.website_url) == "https://example.com/"
        assert request.company_name == "Example Corp"
        assert request.test_questions is True
    
    def test_default_values(self):
        """Test default values for optional fields."""
        request = AnalyzeRequest(website_url="https://example.com")
        
        assert request.company_name is None
        assert request.test_questions is True
    
    def test_invalid_url(self):
        """Test validation error for invalid URL."""
        with pytest.raises(ValidationError):
            AnalyzeRequest(website_url="not-a-url")


class TestTestQuestionsRequest:
    """Test TestQuestionsRequest model."""
    
    def test_valid_request(self, sample_questions):
        """Test creating valid test questions request."""
        questions = sample_questions["company_specific"][:2]
        
        request = TestQuestionsRequest(
            company_name="TechCorp",
            questions=questions,
        )
        
        assert request.company_name == "TechCorp"
        assert len(request.questions) == 2
    
    def test_empty_questions_validation(self):
        """Test validation error for empty questions list."""
        with pytest.raises(ValidationError) as exc_info:
            TestQuestionsRequest(
                company_name="TechCorp",
                questions=[],
            )
        
        errors = exc_info.value.errors()
        assert "At least one question must be provided" in str(errors[0])


class TestAnalysisResponse:
    """Test AnalysisResponse model."""
    
    def test_valid_response(self, sample_company_info, sample_questions):
        """Test creating valid analysis response."""
        response = AnalysisResponse(
            request_id="req_123",
            status=AnalysisStatus.COMPLETED,
            company_info=sample_company_info,
            questions=sample_questions,
            success_rate=0.85,
        )
        
        assert response.request_id == "req_123"
        assert response.status == AnalysisStatus.COMPLETED
        assert response.success_rate == 0.85
        assert response.test_results is None
    
    def test_success_rate_validation(self, sample_company_info, sample_questions):
        """Test success rate must be between 0 and 1."""
        with pytest.raises(ValidationError):
            AnalysisResponse(
                request_id="req_123",
                status=AnalysisStatus.COMPLETED,
                company_info=sample_company_info,
                questions=sample_questions,
                success_rate=1.5,  # Invalid: > 1
            )


class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_valid_error_response(self):
        """Test creating valid error response."""
        error = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "website_url"},
            request_id="req_123",
        )
        
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field"] == "website_url"
        assert error.request_id == "req_123"
    
    def test_default_values(self):
        """Test default values for error response."""
        error = ErrorResponse(
            error_code="ERROR",
            message="Something went wrong",
        )
        
        assert error.details == {}
        assert error.request_id is None
        assert error.timestamp is not None


class TestHealthResponse:
    """Test HealthResponse model."""
    
    def test_valid_health_response(self):
        """Test creating valid health response."""
        health = HealthResponse(
            status="healthy",
            version="1.0.0",
            environment="production",
            services={"openai": "healthy", "database": "healthy"},
        )
        
        assert health.status == "healthy"
        assert health.version == "1.0.0"
        assert health.services["openai"] == "healthy"
        assert health.timestamp is not None