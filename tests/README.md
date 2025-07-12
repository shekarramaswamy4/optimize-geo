# LumaRank Test Suite

This directory contains comprehensive tests for the LumaRank application.

## Test Structure

```
tests/
├── fixtures/              # Test data and mock helpers
│   ├── test_data.py      # Sample data for tests
│   └── mock_helpers.py   # Helper functions for creating mocks
├── unit/                 # Unit tests for individual components
│   ├── test_analyzer_service.py  # Service layer tests
│   ├── test_exceptions.py        # Custom exceptions tests
│   ├── test_logging.py           # Logging utilities tests
│   └── test_models.py            # Pydantic models tests
├── integration/          # Integration tests
│   └── test_api_endpoints.py     # API endpoint tests
├── test_health.py        # Simple health check tests
└── test_performance.py   # Performance and load tests
```

## Running Tests

### All Tests
```bash
# Run all tests
poetry run pytest

# With verbose output
poetry run pytest -v

# Stop on first failure
poetry run pytest -x
```

### Specific Test Types
```bash
# Unit tests only
poetry run pytest tests/unit

# Integration tests only
poetry run pytest tests/integration

# Performance tests
poetry run pytest tests/test_performance.py
```

### With Coverage
```bash
# Generate coverage report
poetry run pytest --cov=src --cov-report=html

# View coverage in terminal
poetry run pytest --cov=src --cov-report=term-missing
```

### Using Make Commands
```bash
make test           # Run all tests
make test-unit      # Unit tests only
make test-integration  # Integration tests only
make coverage       # Generate HTML coverage report
```

## Test Coverage

Current test coverage: **71%**

- ✅ 100% coverage: Models, Exceptions, Logging utilities
- ✅ 89% coverage: Health endpoints
- ✅ 86% coverage: Middleware
- ✅ 77% coverage: API endpoints
- ✅ 71% coverage: Service layer

## Key Testing Patterns

### 1. Dependency Injection Override
```python
app.dependency_overrides[get_settings] = get_test_settings
app.dependency_overrides[get_analyzer_service] = get_mock_analyzer_service
```

### 2. Async Testing
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### 3. Mock Services
```python
mock_service = AsyncMock()
mock_service.method = AsyncMock(return_value="mocked response")
```

### 4. Fixture Usage
```python
def test_with_fixtures(test_settings, mock_openai_client):
    # Use pre-configured test fixtures
    pass
```

## Test Categories

### Unit Tests
- Test individual functions and methods
- Mock all external dependencies
- Fast execution
- High coverage of edge cases

### Integration Tests
- Test API endpoints end-to-end
- Use TestClient for HTTP testing
- Mock external services (OpenAI, HTTP)
- Validate request/response formats

### Performance Tests
- Test concurrent request handling
- Measure response times
- Validate resource cleanup
- Check memory usage patterns

## Best Practices

1. **Use descriptive test names**: `test_fetch_website_content_http_error`
2. **Test both success and failure cases**
3. **Mock external dependencies** (OpenAI, HTTP requests)
4. **Use fixtures for common test data**
5. **Keep tests focused and independent**
6. **Use proper async/await patterns**

## Continuous Integration

Tests run automatically on:
- Every push to main/develop branches
- Every pull request
- Can be triggered manually

GitHub Actions workflow includes:
- Linting (Black, Ruff)
- Type checking (mypy)
- Unit tests with coverage
- Integration tests
- Performance tests