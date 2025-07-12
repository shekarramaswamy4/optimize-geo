# LumaRank

A production-grade SEO analyzer that extracts business information and measures search discoverability through AI-generated search questions.

## Features

- 🔍 **Website Analysis**: Extracts company information, features, and pricing from any website
- 🤖 **AI-Powered**: Uses OpenAI GPT models to understand and analyze content
- 📊 **SEO Scoring**: Generates and tests search questions to measure discoverability
- 🚀 **Production-Ready**: Built with FastAPI, async support, and proper error handling
- 📝 **Structured Logging**: JSON logging with request tracking and correlation IDs
- 🐳 **Docker Support**: Ready for containerized deployment
- 📈 **Metrics**: Prometheus metrics endpoint for monitoring
- 🔒 **Rate Limiting**: Built-in rate limiting to prevent abuse

## Tech Stack

- **Framework**: FastAPI with Uvicorn
- **AI**: OpenAI GPT-3.5/GPT-4
- **Package Management**: Poetry
- **Logging**: Structlog with JSON formatting
- **Validation**: Pydantic v2
- **HTTP Client**: HTTPX (async)
- **Web Scraping**: BeautifulSoup4
- **CLI**: Rich for beautiful terminal output

## Installation

### Using Poetry (Recommended)

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Running the API Server

```bash
# Using the run script
python scripts/run_server.py

# Or directly with uvicorn
uvicorn src.main:app --reload

# Or with Poetry
poetry run uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

### Using the CLI

```bash
# Analyze a website
poetry run website-analyzer https://example.com

# With custom company name
poetry run website-analyzer https://example.com --company-name "Example Corp"

# Quick analysis without testing questions
poetry run website-analyzer https://example.com --no-test

# Enable debug logging
poetry run website-analyzer https://example.com --debug
```

### Using Docker

```bash
# For local development (just PostgreSQL)
make db-up
make run-server

# For production (web + PostgreSQL)
make prod-up

# Or build manually
docker build -t lumarank .
docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY lumarank
```

## API Endpoints

### Core Endpoints

- `POST /api/v1/analyze` - Full website analysis with question testing
- `POST /api/v1/analyze/quick` - Quick analysis without testing
- `POST /api/v1/test-questions` - Test pre-generated questions

### Utility Endpoints

- `GET /health` - Health check with dependency status
- `GET /readiness` - Readiness probe
- `GET /metrics` - Prometheus metrics (if enabled)
- `GET /docs` - Interactive API documentation (development only)

### Example API Usage

```bash
# Full analysis
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://example.com"}'

# Quick analysis
curl -X POST http://localhost:8000/api/v1/analyze/quick \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://example.com", "company_name": "Example Corp"}'

# Health check
curl http://localhost:8000/health
```

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# With coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_analyzer.py
```

### Code Quality

```bash
# Format code
poetry run black src tests

# Lint code
poetry run ruff src tests

# Type checking
poetry run mypy src
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

## Project Structure

```
.
├── src/
│   ├── api/           # FastAPI routers and dependencies
│   ├── config/        # Configuration management
│   ├── core/          # Core business logic and exceptions
│   ├── models/        # Pydantic models
│   ├── services/      # Service layer (analyzer)
│   ├── utils/         # Utilities (logging, etc.)
│   ├── cli.py         # CLI application
│   └── main.py        # FastAPI application
├── tests/             # Test suite
├── scripts/           # Utility scripts
├── docker-compose.yml # Docker composition
├── Dockerfile         # Docker configuration
├── pyproject.toml     # Poetry configuration
└── README.md          # This file
```

## Environment Variables

See `.env.example` for all available configuration options. Key variables:

- `OPENAI_API_KEY` - Required OpenAI API key
- `ENVIRONMENT` - Environment (development/staging/production)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `PORT` - Server port (default: 8000)
- `WORKERS` - Number of worker processes (default: 4)

## Monitoring

The application includes:

- Structured JSON logging with request correlation
- Prometheus metrics endpoint at `/metrics`
- Health checks at `/health` and `/readiness`
- Request/response timing and error tracking

## Security Considerations

- Never commit `.env` files or API keys
- Use environment variables for sensitive configuration
- Enable rate limiting in production
- Run as non-root user in containers
- Keep dependencies updated regularly

## License

This project is proprietary and confidential.

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

For major changes, please open an issue first to discuss what you would like to change.