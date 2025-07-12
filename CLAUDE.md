# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Set required environment variable
export OPENAI_API_KEY='your-api-key-here'
```

### Running the Application

**Web Server (API)**:
```bash
# Using run script
poetry run python scripts/run_server.py

# Using uvicorn directly
poetry run uvicorn src.main:app --reload

# Production mode with multiple workers
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**CLI Interface**:
```bash
# Analyze default website
poetry run website-analyzer https://spacetil.com

# Analyze specific website with options
poetry run website-analyzer https://example.com --company-name "Example Corp" --no-test
```

### Development Commands
```bash
# Run tests
poetry run pytest                         # Run all tests
poetry run pytest tests/unit -v          # Run unit tests only
poetry run pytest tests/integration -v   # Run integration tests only
poetry run pytest --cov=src --cov-report=html  # With coverage

# Using Makefile shortcuts
make test-unit        # Run unit tests
make test-integration # Run integration tests
make test-all        # Run all tests with coverage
make coverage        # Generate HTML coverage report

# Code formatting and linting
poetry run black src tests    # Format code
poetry run ruff src tests     # Lint code
poetry run mypy src          # Type checking

# Run all quality checks
make check  # Runs lint, type-check, and tests
```

### Testing
The project has comprehensive test coverage:
- **Unit Tests** (`tests/unit/`): Test individual components
- **Integration Tests** (`tests/integration/`): Test API endpoints and workflows
- **Performance Tests** (`tests/test_performance.py`): Test performance characteristics
- **Test Fixtures** (`tests/fixtures/`): Reusable test data and mocks

Run specific test files:
```bash
poetry run pytest tests/unit/test_analyzer_service.py -v
poetry run pytest tests/integration/test_api_endpoints.py::TestAnalyzerEndpoints -v
```

## Architecture

Production-grade website analyzer built with FastAPI, async support, and modern Python practices.

### Tech Stack
- **Framework**: FastAPI + Uvicorn (async ASGI server)
- **Package Management**: Poetry
- **AI Integration**: OpenAI GPT models via async client
- **Validation**: Pydantic v2 for request/response models
- **Logging**: Structlog with JSON formatting
- **HTTP Client**: HTTPX for async web requests
- **CLI**: Rich for beautiful terminal output

### Core Components

1. **`src/services/analyzer.py`** - Main business logic service
   - Async WebsiteAnalyzerService class
   - Methods for content fetching, analysis, question generation, and scoring
   - Retry logic with exponential backoff
   - Comprehensive error handling

2. **`src/main.py`** - FastAPI application
   - Production-ready with lifespan management
   - Global exception handlers
   - Middleware for request tracking and rate limiting
   - Prometheus metrics support

3. **`src/api/routers/`** - API endpoints
   - `analyzer.py`: Main analysis endpoints
   - `health.py`: Health and readiness checks

4. **`src/models/schemas.py`** - Pydantic models
   - Request/response validation
   - Type-safe data structures
   - Automatic OpenAPI documentation

5. **`src/config/settings.py`** - Configuration management
   - Environment-based settings with Pydantic
   - Validation and type safety
   - Feature flags and tunables

6. **`src/cli.py`** - Modern CLI interface
   - Async command-line tool
   - Rich formatting and progress indicators
   - Multiple output formats

### Analysis Workflow

1. **Fetch** - Downloads website content using BeautifulSoup
2. **Analyze** - Extracts company info (description, ICP, features, pricing) via OpenAI
3. **Generate** - Creates two types of search questions:
   - Company-specific (with company name)
   - Problem-based (generic solution searches)
4. **Test** - Queries OpenAI with each question
5. **Score** - Evaluates responses:
   - Company questions: Quality score (0-2)
   - Problem questions: Company mention score (0-2)

### Key Design Patterns

- **Shared Library Pattern** - Core logic in `website_analyzer_lib.py` used by multiple interfaces
- **Environment-based Configuration** - Uses environment variables for settings
- **Error Handling** - Comprehensive try-catch blocks with informative messages
- **Modular Methods** - Each analysis step is a separate method for flexibility

### API Response Format

All API responses follow this structure:
```json
{
  "company_info": {...},
  "questions": {...},
  "test_results": {...},
  "success_rate": 0.75,
  "error": null
}
```

### Important Notes

- Requires active internet connection for website fetching and OpenAI API calls
- Some websites may block automated requests
- OpenAI API costs apply for each analysis
- No authentication implemented - API is open