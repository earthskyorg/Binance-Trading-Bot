.PHONY: help install install-dev test test-cov lint format clean build docker-build docker-run docs

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e .[dev]
	pre-commit install

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=binance_trading_bot --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	pytest -m unit

test-integration: ## Run integration tests only
	pytest -m integration

lint: ## Run linting checks
	flake8 binance_trading_bot tests
	mypy binance_trading_bot

format: ## Format code with black and isort
	black binance_trading_bot tests
	isort binance_trading_bot tests

format-check: ## Check code formatting
	black --check binance_trading_bot tests
	isort --check-only binance_trading_bot tests

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	python -m build

docker-build: ## Build Docker image
	docker build -t binance-trading-bot .

docker-run: ## Run Docker container
	docker run --rm -it \
		-e BINANCE_API_KEY=$$BINANCE_API_KEY \
		-e BINANCE_API_SECRET=$$BINANCE_API_SECRET \
		binance-trading-bot

docker-compose-up: ## Start services with docker-compose
	docker-compose up -d

docker-compose-down: ## Stop services with docker-compose
	docker-compose down

docker-compose-logs: ## View docker-compose logs
	docker-compose logs -f

docs: ## Build documentation
	sphinx-build -b html docs docs/_build/html

docs-serve: ## Serve documentation locally
	cd docs/_build/html && python -m http.server 8000

security: ## Run security checks
	safety check
	bandit -r binance_trading_bot/

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

validate-config: ## Validate configuration
	python -m binance_trading_bot.main --validate-config

dry-run: ## Run bot in dry-run mode
	python -m binance_trading_bot.main --dry-run

setup-env: ## Setup development environment
	python -m venv venv
	@echo "Activate virtual environment with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
	@echo "Then run: make install-dev"

check-all: format-check lint test ## Run all checks (format, lint, test)

ci: check-all security ## Run CI pipeline locally
