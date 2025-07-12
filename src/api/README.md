# API Layer

This directory contains the FastAPI-based API layer for LumaRank, including authentication, routing, middleware, and dependency injection.

## Architecture

The API layer follows FastAPI best practices with clear separation of concerns:

```
api/
├── __init__.py
├── auth.py              # Authentication and session management
├── dependencies.py      # FastAPI dependency injection
├── middleware.py        # Custom middleware (logging, tracking)
└── routers/            # API endpoint definitions
    ├── __init__.py
    ├── analyzer.py      # SEO analysis endpoints
    └── health.py        # Health check endpoints
```

## Authentication

### Header-Based Authentication

The API uses header-based authentication with three required headers:

```
x-email: user@example.com      # User's email address
x-auth-id: user_123            # WorkOS user ID
x-entity-id: entity_456        # Organization/entity ID
```

### Session Context

Every authenticated request has access to a complete session context:

```python
class SessionContext(BaseModel):
    user: UserContext          # User details
    entity: EntityContext      # Organization details
    membership: MembershipContext  # User's role in organization
    request_id: str           # Unique request identifier
```

### Authentication Flow

1. **Header Validation**: Checks for required headers
2. **User Lookup**: Finds user by email and auth_id
3. **WorkOS Integration**: Creates user from WorkOS if not found
4. **Entity Validation**: Verifies entity exists
5. **Membership Check**: Ensures user has access to entity
6. **Context Creation**: Builds complete session context

### Using Authentication in Endpoints

```python
from src.api.auth import get_session_context, require_session
from src.core.auth import SessionContext

@router.post("/endpoint", dependencies=[Depends(require_session)])
async def my_endpoint(
    session: Annotated[SessionContext, Depends(get_session_context)],
):
    # Access user info
    user_id = session.user.id
    user_email = session.user.email
    
    # Access entity info
    entity_id = session.entity.id
    entity_name = session.entity.name
    
    # Check user role
    if session.membership.role == "admin":
        # Admin-only logic
```

## API Endpoints

### Analyzer Endpoints (`/api/v1`)

#### `POST /api/v1/analyze`
Full website analysis with SEO scoring:
- Fetches website content
- Extracts company information
- Generates search questions
- Tests questions and calculates scores
- Stores results in MongoDB

**Request:**
```json
{
  "website_url": "https://example.com",
  "company_name": "Example Corp",  // Optional override
  "test_questions": true           // Optional, default true
}
```

**Response:**
```json
{
  "request_id": "req_123",
  "status": "completed",
  "company_info": {
    "name": "Example Corp",
    "description": "...",
    "ideal_customer_profile": "...",
    "key_features": ["..."]
  },
  "questions": {
    "company_specific": [...],
    "problem_based": [...]
  },
  "test_results": [...],
  "success_rate": 0.85,
  "metadata": {...}
}
```

#### `POST /api/v1/analyze/quick`
Quick analysis without question testing:
- Same as full analysis but skips testing phase
- Faster response time
- No success_rate or test_results

#### `POST /api/v1/test-questions`
Test pre-generated questions:
- Tests custom questions without website analysis
- Useful for re-testing or custom question sets

**Request:**
```json
{
  "company_name": "Example Corp",
  "questions": [
    {
      "question": "What is Example Corp?",
      "question_type": "company_specific",
      "intent": "Learn about company"
    }
  ]
}
```

### Health Endpoints

#### `GET /health`
Comprehensive health check with dependency status:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "openai": "healthy",
    "postgres": "healthy",
    "mongo": "healthy"
  },
  "version": "1.0.0",
  "environment": "production"
}
```

#### `GET /readiness`
Simple readiness probe for Kubernetes:

```json
{
  "status": "ready"
}
```

## Middleware

### Request Tracking Middleware
- Adds unique request ID to every request
- Logs request/response details
- Tracks request duration
- Adds request ID to response headers

### Error Handling
Global exception handlers for:
- `WebsiteAnalyzerError`: Domain-specific errors
- `ValidationError`: Request validation errors
- `Exception`: Unexpected errors

All errors return consistent format:
```json
{
  "error_code": "ERROR_CODE",
  "message": "Human readable message",
  "details": {...},
  "request_id": "req_123"
}
```

## Dependencies

### Database Sessions
```python
from src.api.dependencies import get_postgres_db

def my_endpoint(db: Session = Depends(get_postgres_db)):
    # Use database session
```

### Service Instances
```python
from src.api.dependencies import get_analyzer_service

def my_endpoint(
    analyzer: WebsiteAnalyzerService = Depends(get_analyzer_service)
):
    # Use analyzer service
```

### Request Context
```python
from src.api.dependencies import get_request_id

def my_endpoint(request_id: str = Depends(get_request_id)):
    # Access request ID
```

## Rate Limiting

When enabled via settings, the API implements rate limiting:
- Default: 100 requests per minute per IP
- Configurable via environment variables
- Returns 429 status when exceeded

## CORS Configuration

CORS is configured for production use:
- Allowed origins from environment config
- Credentials supported
- Standard HTTP methods allowed
- Authorization headers allowed

## Metrics and Monitoring

### Prometheus Metrics (when enabled)
- Request count by endpoint
- Request duration histograms
- Error rates by type
- Active request gauge

### Structured Logging
All logs include:
- Request ID for tracing
- User and entity context
- Operation details
- Error information

## Security Best Practices

1. **Authentication Required**: All business endpoints require authentication
2. **Input Validation**: Pydantic models validate all inputs
3. **SQL Injection Protection**: SQLAlchemy ORM prevents injection
4. **Error Handling**: Never expose internal details in errors
5. **Rate Limiting**: Prevents abuse and DoS
6. **CORS**: Properly configured for production

## Testing

### Unit Tests
```python
# Test individual components
tests/unit/test_auth.py
tests/unit/test_dependencies.py
```

### Integration Tests
```python
# Test full request flow
tests/integration/test_api_endpoints.py
```

### Testing with Authentication
```python
# Override session dependency in tests
from src.api.auth import get_session_context

app.dependency_overrides[get_session_context] = mock_session_context
```

## Local Development

### Running the API
```bash
# Development with auto-reload
poetry run uvicorn src.main:app --reload

# Production mode
poetry run python scripts/run_server.py
```

### Testing Endpoints
```bash
# With httpie
http POST localhost:8000/api/v1/analyze \
  x-email:user@example.com \
  x-auth-id:user_123 \
  x-entity-id:entity_456 \
  website_url=https://example.com

# With curl
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "x-email: user@example.com" \
  -H "x-auth-id: user_123" \
  -H "x-entity-id: entity_456" \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://example.com"}'
```

## API Documentation

FastAPI automatically generates OpenAPI documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Performance Considerations

1. **Async Operations**: All I/O operations are async
2. **Connection Pooling**: Database connections are pooled
3. **Request Timeout**: Configurable timeout for external calls
4. **Streaming**: Large responses can be streamed
5. **Caching**: Response caching headers when appropriate

## Error Codes

Standard error codes used by the API:

- `FETCH_ERROR`: Failed to fetch website
- `PARSE_ERROR`: Failed to parse website content
- `ANALYSIS_ERROR`: Failed to analyze content
- `OPENAI_ERROR`: OpenAI API error
- `VALIDATION_ERROR`: Request validation failed
- `AUTH_ERROR`: Authentication failed
- `PERMISSION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `INTERNAL_ERROR`: Unexpected server error