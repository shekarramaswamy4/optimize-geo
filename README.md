# LumaRank

A production-grade SEO analysis platform that helps businesses understand and improve their search engine discoverability through AI-powered insights.

## Overview

LumaRank analyzes websites to extract business information and measures search discoverability by:
- Extracting company details, features, and pricing from websites
- Generating targeted search questions potential customers might ask
- Testing those questions to measure how well the company appears in search results
- Providing actionable SEO insights and scoring

## Architecture

### Tech Stack

- **Backend Framework**: FastAPI with async/await support
- **Databases**: 
  - PostgreSQL (users, entities, memberships) with SQLAlchemy ORM
  - MongoDB (crawl data, analysis results) with PyMongo
- **AI Integration**: OpenAI GPT models for content analysis
- **Authentication**: Header-based with WorkOS integration
- **Package Management**: Poetry
- **Testing**: Pytest with 95%+ coverage
- **Deployment**: Docker with multi-stage builds

### Key Features

- **Multi-tenant Architecture**: Support for multiple organizations (entities)
- **Session-based Auth**: Complete session context with user, entity, and membership
- **Automatic User Provisioning**: Creates users from WorkOS on first access
- **Production-ready**: Structured logging, error handling, rate limiting, metrics
- **Comprehensive Testing**: Unit, integration, and performance tests

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- MongoDB 6+
- Poetry (for dependency management)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd optimize-geo
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up databases**
   ```bash
   # Start databases with Docker
   docker-compose up -d
   
   # Run PostgreSQL migrations
   poetry run alembic upgrade head
   ```

5. **Run the application**
   ```bash
   # Development server
   poetry run uvicorn src.main:app --reload
   
   # Production server
   poetry run python scripts/run_server.py
   ```

## Configuration

### Environment Variables

See `.env.example` for all configuration options. Key variables:

```bash
# Database URLs
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
MONGO_URL=mongodb://localhost:27017
MONGO_DATABASE=lumarank

# Authentication
WORKOS_API_KEY=sk_live_...
WORKOS_CLIENT_ID=client_...

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## API Usage

### Authentication

All API endpoints require three authentication headers:
- `x-email`: User's email address
- `x-auth-id`: WorkOS user ID
- `x-entity-id`: Organization/entity ID

### Core Endpoints

#### Analyze Website
```bash
POST /api/v1/analyze
{
  "website_url": "https://example.com",
  "company_name": "Example Corp",  # Optional
  "test_questions": true           # Optional, default true
}
```

#### Quick Analysis (No Testing)
```bash
POST /api/v1/analyze/quick
{
  "website_url": "https://example.com"
}
```

#### Test Pre-generated Questions
```bash
POST /api/v1/test-questions
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

### Health & Monitoring

- `GET /health` - Service health with dependency status
- `GET /readiness` - Kubernetes readiness probe
- `GET /metrics` - Prometheus metrics (if enabled)

## Development

### Project Structure

```
.
├── src/
│   ├── api/              # API routes and middleware
│   │   ├── routers/      # Endpoint definitions
│   │   ├── auth.py       # Authentication logic
│   │   └── middleware.py # Request tracking, logging
│   ├── config/           # Configuration management
│   ├── core/             # Core business logic
│   │   ├── auth.py       # Auth models and context
│   │   └── workos_client.py # WorkOS integration
│   ├── database/         # Database layer
│   │   ├── postgres/     # PostgreSQL models and connection
│   │   └── mongo/        # MongoDB models and repositories
│   ├── models/           # Pydantic schemas
│   ├── services/         # Business logic services
│   ├── utils/            # Utilities (logging, etc.)
│   ├── cli.py           # CLI interface
│   └── main.py          # FastAPI application
├── tests/               # Test suite
├── migrations/          # Alembic migrations
├── scripts/             # Utility scripts
└── docker-compose.yml   # Local development setup
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Run specific test file
poetry run pytest tests/unit/test_analyzer_service.py

# Run with verbose output
poetry run pytest -v
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

### Database Migrations

```bash
# Create new migration
poetry run alembic revision -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1
```

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t lumarank .

# Run with environment file
docker run --env-file .env -p 8000:8000 lumarank

# Using docker-compose
docker-compose up
```

### Production Deployment

The application includes:
- Multi-stage Docker builds for smaller images
- Health checks for container orchestration
- Prometheus metrics for monitoring
- Structured JSON logging
- Graceful shutdown handling

## Security

- **Authentication**: Header-based with WorkOS integration
- **Authorization**: Role-based access control (member, admin, owner)
- **Data Isolation**: Multi-tenant with entity-based data separation
- **API Security**: Rate limiting, CORS configuration
- **Secret Management**: All secrets via environment variables

## Monitoring & Observability

- **Structured Logging**: JSON logs with correlation IDs
- **Metrics**: Prometheus metrics endpoint
- **Health Checks**: Detailed health status with dependencies
- **Request Tracking**: Unique request IDs for tracing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

Proprietary - All rights reserved