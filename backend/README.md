# con-selfrag Backend

FastAPI backend service for the con-selfrag project with Docker-first development workflow and comprehensive CLI interface.

## Features

- FastAPI-based REST API
- Endpoints: `/ingest`, `/query`, `/health`, `/rag`
- OpenAPI documentation at `/docs`
- Modular architecture: `routes/`, `services/`, `models/`
- Environment-based configuration system
- Docker and Compose-ready
- **Complete CLI interface for command-line operations**
- RAG pipeline with vector embeddings and semantic search

## Quick Start

### Option 1: Docker-First Development (Recommended)

1. **Start all services:**

   ```bash
   docker-compose up -d
   ```

2. **Access the API:**

   - API: http://localhost:8080
   - Docs: http://localhost:8080/docs
   - Health: http://localhost:8080/health

3. **Use the CLI:**
   ```bash
   cd backend
   ./setup_cli.sh  # One-time setup
   ./selfrag health
   ./selfrag query "machine learning"
   ```

### Option 2: CLI-First Usage

The CLI can be used independently for all operations:

```bash
cd backend

# Setup CLI
./setup_cli.sh

# Check system health
./selfrag health

# Ingest documents
./selfrag ingest README.md --title "Project Documentation"
./selfrag ingest *.py --tags "code,python"

# Query knowledge base
./selfrag query "how to setup the project"

# Interactive mode
./selfrag chat
```

### Option 3: Local Development with Poetry

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 3: Manual Development Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## CLI Interface

Selfrag includes a comprehensive command-line interface for all operations:

### Setup

```bash
# One-time setup
cd backend
./setup_cli.sh

# Or use directly
python3 selfrag_cli.py --help
```

### Commands

```bash
# Health monitoring
./selfrag health

# Document ingestion
./selfrag ingest document.txt --title "My Document" --tags "important"
./selfrag ingest *.md --type documentation

# Knowledge base queries
./selfrag query "machine learning algorithms"
./selfrag query "API setup" --limit 5 --threshold 0.7

# Interactive chat mode
./selfrag chat

# System statistics
./selfrag stats
```

### Advanced Usage

```bash
# Batch processing
find docs/ -name "*.md" | head -10 | xargs -I {} ./selfrag ingest {} --type docs

# JSON output for scripting
./selfrag query "docker" --format json | jq '.[0].content'

# Custom API endpoint
./selfrag --api-url http://remote:8080 health
```

See `app/cli/README.md` for comprehensive CLI documentation.

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app setup
│   ├── config.py            # Environment configuration
│   ├── routes/              # API routes
│   ├── services/            # Business logic layer
│   ├── models/              # Pydantic models
│   ├── cli/                 # Command-line interface
│   └── database/            # Database connections (preparation)
├── data/                    # (optional for assets)
├── logs/                    # (optional for future logs)
├── selfrag_cli.py          # Standalone CLI script
├── setup_cli.sh            # CLI setup script
├── Dockerfile
├── pyproject.toml
└── README.md
```

## API Endpoints

| Method | Path    | Description              |
| ------ | ------- | ------------------------ |
| GET    | /health | System health check      |
| POST   | /ingest | Document ingestion       |
| POST   | /query  | Natural language queries |
| GET    | /rag    | RAG pipeline operations  |

→ Full details at `/docs`

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

## Next Steps (Phase 2)

- Complete document ingestion implementation
- Add chunking, embedding, storage in Qdrant
- Prepare CLI routing
- Add authentication and rate limiting
- Implement caching layer for performance

## Contributing

- Please use `pyproject.toml` instead of `requirements.txt`
- Formatting via `black` or `ruff`
- Branch name: `feature/<description>`

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
```
