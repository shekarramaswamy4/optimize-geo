from typing import Any, Optional


class WebsiteAnalyzerError(Exception):
    """Base exception for LumaRank application."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        self.details = details or {}


class ValidationError(WebsiteAnalyzerError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class WebsiteFetchError(WebsiteAnalyzerError):
    """Raised when website fetching fails."""
    
    def __init__(self, url: str, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            message=f"Failed to fetch website {url}: {message}",
            error_code="WEBSITE_FETCH_ERROR",
            status_code=502,
            details={"url": url, **(details or {})},
        )


class OpenAIError(WebsiteAnalyzerError):
    """Raised when OpenAI API calls fail."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            message=f"OpenAI API error: {message}",
            error_code="OPENAI_ERROR",
            status_code=502,
            details=details,
        )


class RateLimitError(WebsiteAnalyzerError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None) -> None:
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details=details,
        )


class AuthenticationError(WebsiteAnalyzerError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(WebsiteAnalyzerError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class NotFoundError(WebsiteAnalyzerError):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class ServiceUnavailableError(WebsiteAnalyzerError):
    """Raised when a service is temporarily unavailable."""
    
    def __init__(self, service: str, message: Optional[str] = None) -> None:
        super().__init__(
            message=message or f"Service '{service}' is temporarily unavailable",
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service},
        )