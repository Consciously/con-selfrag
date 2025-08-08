# FastAPI Endpoint Documentation

<!--
# =============================================================================
# Project: Selfrag
# Module: Memory Service (Phase 3)
# File: backend/API_DOCUMENTATION.md (Memory Section)
# Purpose: Documentation of memory endpoints /memory/*
# Owner: Core Platform (RAG + Memory)
# Status: Draft (Phase 3) | Created: 2025-08-08
# Notes: Keep Agents out. Coordinator only routes. No external tools.
# =============================================================================
-->

## Memory Service (Phase 3 Draft)

Memory endpoints provide persistent conversational (episodic) and semantic (fact) storage. Content is redacted server‑side prior to persistence.

### Endpoints

| Method | Path                   | Description                         |
| ------ | ---------------------- | ----------------------------------- |
| POST   | `/memory/log`          | Log a chat turn (episodic memory)   |
| POST   | `/memory/retrieve`     | Retrieve recent turns for a session |
| POST   | `/memory/facts`        | Create a semantic fact/note         |
| GET    | `/memory/facts/{id}`   | Get a fact by id                    |
| POST   | `/memory/facts/search` | Text search (ILIKE) over facts      |
| PATCH  | `/memory/facts/{id}`   | Update a fact                       |
| DELETE | `/memory/facts/{id}`   | Delete a fact                       |

### Request Examples

Log turn:

```json
{
	"session_id": "sess_123",
	"role": "user",
	"content": "My email is user@example.com"
}
```

Create fact:

```json
{
	"title": "Project Deadline",
	"body": "Deadline is 2025-09-01",
	"tags": ["proj"]
}
```

Search facts:

```json
{ "query": "deadline", "limit": 10 }
```

### Response Snippets

Turn (retrieve):

```json
{
	"id": "…",
	"session_id": "sess_123",
	"role": "user",
	"content": "My email is [REDACTED_EMAIL]",
	"created_at": "2025-08-08T12:00:00Z"
}
```

Fact:

```json
{
	"id": "…",
	"title": "Project Deadline",
	"body": "Deadline is 2025-09-01",
	"created_at": "…",
	"updated_at": "…"
}
```

### Redaction

Patterns removed: emails, IPv4 addresses, `sk-*` API keys, JWT-like tokens. Content returned from APIs is already redacted.

### Limits & Performance

- Turn retrieval default 10 (max 100)
- Fact search default 20 (max 100)
- Simple ILIKE search (embedding/vector search arrives Phase 4/5)

### Future (Phase 4/5)

- Embedding generation & vector similarity
- Hybrid semantic + episodic retrieval
- Advanced redaction / PII classification pipeline

## Overview

This FastAPI application provides a clean, extensible foundation for building AI-powered applications. It includes three primary endpoints for Milestone 1: `/health`, `/ingest`, and `/query`.

## Quick Start

### Starting the Server

```bash
cd backend
python -m app.main
```

The server will start on `http://localhost:8000` with interactive documentation available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing the Endpoints

```bash
# Run the test script
python test_endpoints.py
```

## Endpoints Reference

### 1. Health Check - `/health`

**Method**: `GET`
**Tags**: Health & Monitoring

Comprehensive health check that verifies service status and LocalAI connectivity.

#### Response

```json
{
	"status": "healthy",
	"localai_connected": true,
	"timestamp": "2024-01-15T10:30:00Z",
	"version": "1.0.0"
}
```

#### Usage Example

```bash
curl -X GET http://localhost:8000/health
```

### 2. Content Ingestion - `/ingest`

**Method**: `POST`
**Tags**: Data Management

Ingest content into the system for future querying and retrieval.

#### Request Body

```json
{
	"content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
	"source": "user_input",
	"metadata": {
		"type": "text",
		"language": "en",
		"tags": ["api", "python"],
		"author": "user"
	}
}
```

#### Response

```json
{
	"id": "doc_abc123",
	"status": "success",
	"timestamp": "2024-01-15T10:30:00Z",
	"content_length": 85
}
```

#### Usage Examples

**Basic ingestion**:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Python is a programming language.",
    "source": "manual_input"
  }'
```

**With metadata**:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Machine learning is a subset of artificial intelligence.",
    "source": "documentation",
    "metadata": {
      "category": "ai",
      "difficulty": "beginner",
      "tags": ["ml", "ai"]
    }
  }'
```

### 3. Content Query - `/query`

**Method**: `POST`
**Tags**: Data Management

Query ingested content using natural language search.

#### Request Body

```json
{
	"query": "What is FastAPI?",
	"limit": 5,
	"filters": {
		"source": "user_input",
		"tags": ["python"]
	}
}
```

#### Response

```json
{
	"query": "What is FastAPI?",
	"results": [
		{
			"id": "doc_abc123",
			"content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
			"relevance_score": 0.95,
			"metadata": {
				"tags": ["api", "python"],
				"source": "user_input"
			}
		}
	],
	"total_results": 1,
	"query_time_ms": 45
}
```

#### Usage Examples

**Simple query**:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?"
  }'
```

**With filters**:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "web frameworks",
    "limit": 3,
    "filters": {
      "tags": ["python"],
      "source": "documentation"
    }
  }'
```

## Health Monitoring Endpoints

### Liveness Probe - `/health/live`

**Method**: `GET`
**Purpose**: Kubernetes liveness probe

```bash
curl -X GET http://localhost:8000/health/live
```

### Readiness Probe - `/health/ready`

**Method**: `GET`
**Purpose**: Kubernetes readiness probe

```bash
curl -X GET http://localhost:8000/health/ready
```

## Python Client Examples

### Basic Usage

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
health = requests.get(f"{BASE_URL}/health").json()
print(f"Service status: {health['status']}")

# Ingest content
ingest_response = requests.post(
    f"{BASE_URL}/ingest",
    json={
        "content": "FastAPI is awesome!",
        "source": "python_client",
        "metadata": {"type": "review"}
    }
).json()
print(f"Ingested document ID: {ingest_response['id']}")

# Query content
query_response = requests.post(
    f"{BASE_URL}/query",
    json={
        "query": "What do you think about FastAPI?",
        "limit": 5
    }
).json()

for result in query_response['results']:
    print(f"Relevant content: {result['content']}")
    print(f"Relevance score: {result['relevance_score']}")
```

### Async Client Example

```python
import asyncio
import aiohttp

async def test_endpoints():
    async with aiohttp.ClientSession() as session:
        # Health check
        async with session.get("http://localhost:8000/health") as resp:
            health = await resp.json()
            print(f"Health: {health['status']}")

        # Ingest content
        async with session.post(
            "http://localhost:8000/ingest",
            json={"content": "Async example", "source": "async_client"}
        ) as resp:
            ingest = await resp.json()
            print(f"Ingested: {ingest['id']}")

asyncio.run(test_endpoints())
```

## CLI Usage

### Using curl

Create a simple CLI script:

```bash
#!/bin/bash
# save as test_api.sh

echo "Testing FastAPI endpoints..."

# Health check
echo "Health:"
curl -s http://localhost:8000/health | jq .

# Ingest
echo -e "\nIngest:"
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "CLI test content", "source": "cli"}' | jq .

# Query
echo -e "\nQuery:"
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test content"}' | jq .
```

## Error Handling

All endpoints return consistent error responses:

```json
{
	"error": "ValidationError",
	"message": "Invalid request format",
	"detail": "temperature must be between 0.0 and 2.0",
	"timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting & Security

- **CORS**: Configured to allow cross-origin requests
- **Validation**: All inputs validated with Pydantic
- **Error Handling**: Comprehensive error responses with debugging info
- **Logging**: Request/response logging for monitoring

## Next Steps

The current implementation uses placeholder logic. For production:

1. **Database Integration**: Connect to vector database (Qdrant/Weaviate)
2. **Embedding Generation**: Generate embeddings for semantic search
3. **Hybrid Search**: Combine semantic and keyword search
4. **Caching**: Implement Redis caching for performance
5. **Authentication**: Add API key or JWT authentication
6. **Rate Limiting**: Implement rate limiting per user/IP

## Testing

Run the included test script:

```bash
cd backend
python test_endpoints.py
```

This will test all endpoints and provide usage examples.
