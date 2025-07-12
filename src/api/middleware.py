import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logging import clear_request_context, get_logger, set_request_context

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set request context for logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        
        # Store request ID in request state
        request.state.request_id = request_id
        
        # Set request context for logging
        set_request_context(request_id=request_id)
        
        # Extract user info if available
        user_email = request.headers.get("x-email")
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
            user_email=user_email,
        )
        
        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration * 1000, 2),
            )
            raise
        finally:
            # Clear request context
            clear_request_context()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Get client identifier
        client_id = request.client.host if request.client else "unknown"
        
        # Clean up old requests
        current_time = time.time()
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if current_time - req_time < 60
            ]
        
        # Check rate limit
        if client_id in self.requests and len(self.requests[client_id]) >= self.requests_per_minute:
            logger.warning("Rate limit exceeded", client_id=client_id)
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                headers={"Retry-After": "60"},
                media_type="application/json",
            )
        
        # Record request
        if client_id not in self.requests:
            self.requests[client_id] = []
        self.requests[client_id].append(current_time)
        
        return await call_next(request)