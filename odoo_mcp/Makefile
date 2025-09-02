.PHONY: help install test test-unit test-integration test-e2e lint format type-check security clean pre-commit

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install dependencies with uv
	uv pip install -e ".[dev]"
	uv pip list

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install
	pre-commit install --hook-type commit-msg

test:  ## Run all tests
	uv run pytest

test-unit:  ## Run unit tests only
	uv run pytest tests/unit -v

test-integration:  ## Run integration tests only
	uv run pytest tests/integration -v -m integration

test-e2e:  ## Run end-to-end tests only
	uv run pytest tests/e2e -v -m e2e

test-cov:  ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=html --cov-report=term

lint:  ## Run ruff linter
	uv run ruff check src tests --fix

format:  ## Format code with ruff
	uv run ruff format src tests

type-check:  ## Run mypy type checker
	uv run mypy src tests

security:  ## Run security checks
	uv run safety check

clean:  ## Clean up generated files
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

pre-commit:  ## Run pre-commit on all files
	pre-commit run --all-files

check-all: lint type-check security test  ## Run all checks

dev-setup: install pre-commit-install  ## Complete development setup
