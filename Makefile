# con-selfrag Development Makefile
# Docker-first development workflow commands

.PHONY: help dev up down lint format test clean build logs shell

# Default target
help:
	@echo "con-selfrag Development Commands"
	@echo "==============================="
	@echo ""
	@echo "Development:"
	@echo "  make dev      - Start development environment"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make restart  - Restart all services"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint     - Run all code quality checks"
	@echo "  make format   - Auto-format code"
	@echo "  make test     - Run all tests"
	@echo "  make check    - Run lint + test"
	@echo ""
	@echo "Utility:"
	@echo "  make logs     - Show logs for all services"
	@echo "  make build    - Rebuild all images"
	@echo "  make clean    - Clean up containers and volumes"
	@echo "  make shell    - Open shell in dev container"
	@echo ""

# Development environment
dev:
	@echo "Starting development environment..."
	docker compose up -d
	@echo "Services started! Access API at http://localhost:8080"
	@echo "Run 'make logs' to view logs"

up:
	@echo "Starting all services..."
	docker compose up -d

restart:
	@echo "Restarting all services..."
	docker compose restart

down:
	@echo "Stopping all services..."
	docker compose down

# Code quality commands
lint:
	@echo "Running code quality checks..."
	docker compose --profile dev run --rm lint

format:
	@echo "Auto-formatting code..."
	docker compose --profile dev run --rm lint sh -c "black . && isort . && ruff check --fix ."

test:
	@echo "Running tests..."
	docker compose --profile dev run --rm lint pytest test_*.py -v

check: lint test
	@echo "All checks completed!"

# Individual linting tools
black:
	@echo "Running Black formatting..."
	docker compose --profile dev run --rm lint black --check --diff .

ruff:
	@echo "Running Ruff linting..."
	docker compose --profile dev run --rm lint ruff check .

isort:
	@echo "Running import sorting..."
	docker compose --profile dev run --rm lint isort --check-only --diff .

mypy:
	@echo "Running type checking..."
	docker compose --profile dev run --rm lint mypy app/

# Utility commands
logs:
	@echo "Showing logs... (Ctrl+C to exit)"
	docker compose logs -f

build:
	@echo "Rebuilding images..."
	docker compose build --no-cache

clean:
	@echo "Cleaning up containers and volumes..."
	docker compose down -v
	docker system prune -f

shell:
	@echo "Opening shell in dev container..."
	docker compose --profile dev run --rm lint sh

# CI/CD helpers
ci-lint:
	@echo "Running CI linting..."
	docker compose --profile dev run --rm lint

# Quick development cycle
dev-cycle: format test
	@echo "Development cycle complete!"

# Watch mode (requires additional tools)
watch:
	@echo "Starting file watcher..."
	@echo "Install entr for file watching: brew install entr (macOS) or apt-get install entr (Ubuntu)"
	@find backend -name "*.py" | entr -r make dev-cycle

# Database utilities
reset-db:
	@echo "Resetting database..."
	docker compose down
	docker volume rm con-selfrag_postgres-data || true
	docker compose up -d postgres

# Health checks
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8080/health && echo "✓ API healthy" || echo "✗ API unhealthy"
	@curl -f http://localhost:6333/health && echo "✓ Qdrant healthy" || echo "✗ Qdrant unhealthy"
	@curl -f http://localhost:5432 && echo "✓ PostgreSQL healthy" || echo "✗ PostgreSQL unhealthy"
	@redis-cli -h localhost ping && echo "✓ Redis healthy" || echo "✗ Redis unhealthy"
