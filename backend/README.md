# con-selfrag Backend

FastAPI backend service for the con-selfrag project with Docker-first development workflow.

## Quick Start

### Development Environment

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Run code quality checks:**
   ```bash
   docker-compose --profile dev run lint
   ```

3. **Access the API:**
   - API: http://localhost:8080
   - Docs: http://localhost:8080/docs
   - Health: http://localhost:8080/health

### Available Services

| Service | Port | Description |
|---------|------|-------------|
| fastapi-gateway | 8080 | Main FastAPI application |
| qdrant | 6333 | Vector database |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Cache and session store |
| localai | 8081 | Local AI inference |

## Development Workflow

### Docker-First Development

The project uses multi-stage Docker builds to separate development and production environments:

- **Dev stage**: Includes all development tools (black, ruff, mypy, isort, pytest)
- **Runtime stage**: Minimal production image with only runtime dependencies

### Running Code Quality Checks

The lint service runs comprehensive checks:

```bash
# Run all checks
docker-compose --profile dev run lint

# Run specific checks
# Black formatting check
docker-compose --profile dev run lint black --check --diff .

# Ruff linting
docker-compose --profile dev run lint ruff check .

# Import sorting
docker-compose --profile dev run lint isort --check-only --diff .

# Type checking
docker-compose --profile dev run lint mypy app/

# Tests
docker-compose --profile dev run lint pytest test_*.py -v
```

### Auto-fixing Code Issues

```bash
# Auto-format code
docker-compose --profile dev run lint black .
docker-compose --profile dev run lint isort .

# Auto-fix some lint issues
docker-compose --profile dev run lint ruff check --fix .
```

### Local Development with Volume Mounting

For active development with hot-reload:

```bash
# Start with volume mounting for code changes
docker-compose up -d

# Watch logs
docker-compose logs -f fastapi-gateway

# Make code changes - they will be reflected immediately
```

### Manual Development Setup (Alternative)

If you prefer local development:

```bash
# Install dependencies
pip install -e ".[dev]"

# Run linting tools
black --check --diff .
ruff check .
isort --check-only --diff .
mypy app/
pytest test_*.py -v

# Auto-fix
black .
isort .
ruff check --fix .
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure as needed:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Development Tools Configuration

All development tools are pre-configured in `pyproject.toml`:

- **Black**: 88 character line length
- **Ruff**: Comprehensive linting with modern rules
- **MyPy**: Strict type checking
- **isort**: Import sorting compatible with Black
- **pytest**: Async test support

## Testing

### Running Tests

```bash
# Run all tests
docker-compose --profile dev run lint pytest test_*.py -v

# Run specific test file
docker-compose --profile dev run lint pytest test_endpoints.py -v

# Run with coverage (if configured)
docker-compose --profile dev run lint pytest --cov=app test_*.py
```

### Test Structure

- `test_endpoints.py`: API endpoint tests
- Tests use pytest-asyncio for async support
- All external dependencies mocked for isolation

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Backend CI
on: [push, pull_request]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run lint and tests
        run: |
          docker-compose --profile dev run lint
```

### Pre-commit Hooks

Install pre-commit hooks for local development:

```bash
pip install pre-commit
pre-commit install
```

## API Documentation

### Endpoints

- `GET /health` - Health check
- `POST /ingest` - Content ingestion
- `POST /query` - Natural language search

### Interactive Documentation

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- OpenAPI Schema: http://localhost:8080/openapi.json

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8080, 6333, 5432, 6379, 8081 are available
2. **Docker build issues**: Clear build cache: `docker-compose build --no-cache`
3. **Permission issues**: Ensure Docker has proper permissions
4. **Volume issues**: Remove volumes: `docker-compose down -v`

### Debug Mode

```bash
# Run with debug logging
docker-compose up -d
# Check logs
docker-compose logs -f fastapi-gateway
```

### Reset Environment

```bash
# Full reset
docker-compose down -v
docker-compose up --build
