.PHONY: help install test test-unit test-integration test-performance test-all coverage lint format type-check clean run-server run-cli docker-build docker-run

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

# Development shortcuts
dev: install ## Setup development environment
	poetry run pre-commit install

check: lint type-check test ## Run all checks (lint, type-check, test)

ci: check ## Run CI pipeline locally
	@echo "✅ All CI checks passed!"