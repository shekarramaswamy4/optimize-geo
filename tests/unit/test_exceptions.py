"""Unit tests for custom exceptions."""

import pytest

from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    OpenAIError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
    WebsiteAnalyzerError,
    WebsiteFetchError,
)


class TestWebsiteAnalyzerError:
    """Test WebsiteAnalyzerError base exception."""
    
    def test_basic_exception(self):
        """Test creating basic exception."""
        error = WebsiteAnalyzerError("Something went wrong")
        
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.error_code == "WebsiteAnalyzerError"
        assert error.status_code == 500
        assert error.details == {}
    
    def test_exception_with_all_params(self):
        """Test exception with all parameters."""
        error = WebsiteAnalyzerError(
            message="Custom error",
            error_code="CUSTOM_ERROR",
            status_code=400,
            details={"field": "value"},
        )
        
        assert error.message == "Custom error"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.status_code == 400
        assert error.details == {"field": "value"}


class TestValidationError:
    """Test ValidationError exception."""
    
    def test_validation_error(self):
        """Test validation error creation."""
        error = ValidationError("Invalid input", {"field": "website_url"})
        
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == 400
        assert error.details == {"field": "website_url"}


class TestWebsiteFetchError:
    """Test WebsiteFetchError exception."""
    
    def test_website_fetch_error(self):
        """Test website fetch error creation."""
        error = WebsiteFetchError("https://example.com", "Connection timeout")
        
        assert "Failed to fetch website https://example.com: Connection timeout" in error.message
        assert error.error_code == "WEBSITE_FETCH_ERROR"
        assert error.status_code == 502
        assert error.details["url"] == "https://example.com"
    
    def test_website_fetch_error_with_details(self):
        """Test website fetch error with additional details."""
        error = WebsiteFetchError(
            "https://example.com",
            "Connection timeout",
            {"timeout": 30, "retries": 3},
        )
        
        assert error.details["url"] == "https://example.com"
        assert error.details["timeout"] == 30
        assert error.details["retries"] == 3


class TestOpenAIError:
    """Test OpenAIError exception."""
    
    def test_openai_error(self):
        """Test OpenAI error creation."""
        error = OpenAIError("Rate limit exceeded")
        
        assert error.message == "OpenAI API error: Rate limit exceeded"
        assert error.error_code == "OPENAI_ERROR"
        assert error.status_code == 502
    
    def test_openai_error_with_details(self):
        """Test OpenAI error with details."""
        error = OpenAIError("Invalid API key", {"status": 401})
        
        assert "Invalid API key" in error.message
        assert error.details["status"] == 401


class TestRateLimitError:
    """Test RateLimitError exception."""
    
    def test_rate_limit_error_default(self):
        """Test rate limit error with defaults."""
        error = RateLimitError()
        
        assert error.message == "Rate limit exceeded"
        assert error.error_code == "RATE_LIMIT_ERROR"
        assert error.status_code == 429
        assert error.details == {}
    
    def test_rate_limit_error_with_retry(self):
        """Test rate limit error with retry_after."""
        error = RateLimitError("Too many requests", retry_after=60)
        
        assert error.message == "Too many requests"
        assert error.details["retry_after"] == 60


class TestAuthenticationError:
    """Test AuthenticationError exception."""
    
    def test_authentication_error_default(self):
        """Test authentication error with default message."""
        error = AuthenticationError()
        
        assert error.message == "Authentication failed"
        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.status_code == 401
    
    def test_authentication_error_custom(self):
        """Test authentication error with custom message."""
        error = AuthenticationError("Invalid API key")
        
        assert error.message == "Invalid API key"


class TestAuthorizationError:
    """Test AuthorizationError exception."""
    
    def test_authorization_error_default(self):
        """Test authorization error with default message."""
        error = AuthorizationError()
        
        assert error.message == "Insufficient permissions"
        assert error.error_code == "AUTHORIZATION_ERROR"
        assert error.status_code == 403
    
    def test_authorization_error_custom(self):
        """Test authorization error with custom message."""
        error = AuthorizationError("Admin access required")
        
        assert error.message == "Admin access required"


class TestNotFoundError:
    """Test NotFoundError exception."""
    
    def test_not_found_error(self):
        """Test not found error creation."""
        error = NotFoundError("Analysis", "req_123")
        
        assert error.message == "Analysis with identifier 'req_123' not found"
        assert error.error_code == "NOT_FOUND"
        assert error.status_code == 404
        assert error.details["resource"] == "Analysis"
        assert error.details["identifier"] == "req_123"


class TestServiceUnavailableError:
    """Test ServiceUnavailableError exception."""
    
    def test_service_unavailable_default(self):
        """Test service unavailable with default message."""
        error = ServiceUnavailableError("OpenAI")
        
        assert error.message == "Service 'OpenAI' is temporarily unavailable"
        assert error.error_code == "SERVICE_UNAVAILABLE"
        assert error.status_code == 503
        assert error.details["service"] == "OpenAI"
    
    def test_service_unavailable_custom(self):
        """Test service unavailable with custom message."""
        error = ServiceUnavailableError("Database", "Connection pool exhausted")
        
        assert error.message == "Connection pool exhausted"
        assert error.details["service"] == "Database"