.PHONY: help install test test-unit test-integration test-performance test-all coverage lint format type-check clean run-server run-cli docker-build docker-run db-up db-down db-migrate db-rollback db-reset db-shell

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies with Poetry
	poetry install

test: ## Run all tests
	poetry run pytest tests -v

test-unit: ## Run unit tests only
	poetry run pytest tests/unit -v

test-integration: ## Run integration tests only
	poetry run pytest tests/integration -v

test-performance: ## Run performance tests only
	poetry run pytest tests/test_performance.py -v

test-all: ## Run all tests with coverage
	poetry run pytest tests -v --cov=src --cov-report=term-missing --cov-report=html

coverage: ## Generate coverage report
	poetry run pytest tests --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint: ## Run linting checks
	poetry run ruff src tests
	poetry run black --check src tests

format: ## Format code with Black
	poetry run black src tests

type-check: ## Run type checking with mypy
	poetry run mypy src

clean: ## Clean up cache and build files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache

run-server: ## Run the FastAPI server
	poetry run python scripts/run_server.py

run-cli: ## Run the CLI with default website
	poetry run lumarank

docker-build: ## Build Docker image
	docker build -t lumarank .

docker-run: ## Run Docker container
	docker run -p 8000:8000 -e OPENAI_API_KEY=$(OPENAI_API_KEY) lumarank

prod-up: ## Start production environment (web + postgres)
	docker-compose --profile prod up -d

prod-down: ## Stop production environment
	docker-compose --profile prod down

prod-logs: ## View production logs
	docker-compose --profile prod logs -f

# Database commands
db-up: ## Start all database containers (PostgreSQL + MongoDB)
	docker-compose up -d postgres mongo
	@echo "Waiting for databases to be ready..."
	@sleep 5

db-down: ## Stop all database containers
	docker-compose down postgres mongo

postgres-up: ## Start only PostgreSQL
	docker-compose up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 5

mongo-up: ## Start only MongoDB
	docker-compose up -d mongo
	@echo "Waiting for MongoDB to be ready..."
	@sleep 5

db-migrate: ## Run database migrations
	poetry run alembic upgrade head

db-rollback: ## Rollback last migration
	poetry run alembic downgrade -1

db-reset: ## Reset database (drop all tables and re-run migrations)
	poetry run alembic downgrade base
	poetry run alembic upgrade head

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U lumarank -d lumarank_db

mongo-shell: ## Open MongoDB shell
	docker-compose exec mongo mongosh -u admin -p admin_password --authenticationDatabase admin lumarank

db-test-up: ## Start test database containers (PostgreSQL + MongoDB)
	docker-compose --profile test up -d postgres_test mongo_test
	@echo "Waiting for test databases to be ready..."
	@sleep 5

db-test-down: ## Stop test database containers
	docker-compose --profile test down

# Development shortcuts
dev: install ## Setup development environment
	poetry run pre-commit install

check: lint type-check test ## Run all checks (lint, type-check, test)

ci: check ## Run CI pipeline locally
	@echo "✅ All CI checks passed!"