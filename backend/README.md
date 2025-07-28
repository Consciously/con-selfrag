# Backend - FastAPI + Ollama Service

This is the backend service for the con-llm-container-base project, providing a FastAPI-based REST API for interacting with Ollama LLM models.

## Features

- **FastAPI REST API** with automatic OpenAPI documentation
- **Ollama Integration** for local LLM model inference
- **Prometheus Metrics** for monitoring and observability
- **Health Checks** for Kubernetes readiness/liveness probes
- **Async Operations** for optimal performance
- **Production Ready** with proper error handling and logging

## Quick Start

```bash
# Install dependencies
uv venv
uv pip install -e ".[dev]"

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - API information and status
- `POST /ask` - Simple conversational interface
- `POST /generate` - Advanced text generation
- `GET /models` - List available models
- `GET /health` - Comprehensive health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

## Development

```bash
# Code formatting
uv run black .

# Linting
uv run ruff check .

# Testing
uv run pytest -v
```

## Configuration

Configure via environment variables (see `.env.example` in project root):

- `OLLAMA_HOST` - Ollama service URL
- `DEFAULT_MODEL` - Default LLM model to use
- `LOG_LEVEL` - Logging verbosity
- `API_TIMEOUT` - Request timeout in seconds

## Docker

```bash
# Build image
docker build -t con-llm-backend .

# Run container
docker run -p 8000:8000 -e OLLAMA_HOST=http://ollama:11434 con-llm-backend
```

For complete documentation, see the main project README.md.
