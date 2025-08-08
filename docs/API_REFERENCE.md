# SelfRAG API Quick Reference

## Base URL

`http://localhost:8080`

## Authentication

Most endpoints require authentication. Obtain a JWT token via the auth endpoints.

## Core Endpoints

### Health & System

| Method | Endpoint                  | Description            |
| ------ | ------------------------- | ---------------------- |
| `GET`  | `/health/readiness`       | System health check    |
| `GET`  | `/health/metrics`         | Performance metrics    |
| `GET`  | `/health/cache/analytics` | Cache performance data |
| `POST` | `/health/cache/clear`     | Clear all caches       |

### Authentication

| Method | Endpoint            | Description           |
| ------ | ------------------- | --------------------- |
| `POST` | `/v1/auth/register` | Register new user     |
| `POST` | `/v1/auth/login`    | User login            |
| `GET`  | `/v1/auth/me`       | Get current user info |

### Document Management

| Method   | Endpoint             | Description          |
| -------- | -------------------- | -------------------- |
| `POST`   | `/v1/ingest/`        | Ingest new document  |
| `GET`    | `/v1/documents/`     | List documents       |
| `GET`    | `/v1/documents/{id}` | Get document details |
| `DELETE` | `/v1/documents/{id}` | Delete document      |

### Search & Query

| Method | Endpoint                  | Description           |
| ------ | ------------------------- | --------------------- |
| `POST` | `/v1/query/`              | Semantic search       |
| `POST` | `/v1/query/context-aware` | Context-aware search  |
| `GET`  | `/v1/collections/stats`   | Collection statistics |

## Request/Response Examples

### Health Check

```bash
curl -X GET http://localhost:8080/health/readiness
```

**Response:**

```json
{
	"status": "ready",
	"timestamp": "2024-01-15T10:30:00Z",
	"services": {
		"database": { "status": "healthy", "response_time": "8ms" },
		"cache": { "status": "healthy", "response_time": "3ms" },
		"localai": { "status": "healthy", "response_time": "45ms" },
		"qdrant": { "status": "healthy", "response_time": "12ms" }
	}
}
```

### Register User

```bash
curl -X POST http://localhost:8080/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "secure_password",
    "email": "user@example.com"
  }'
```

### Login

```bash
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "secure_password"
  }'
```

**Response:**

```json
{
	"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
	"token_type": "bearer",
	"expires_in": 1800
}
```

### Ingest Document

```bash
curl -X POST http://localhost:8080/v1/ingest/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
    "metadata": {
      "title": "ML Introduction",
      "tags": ["machine-learning", "ai", "introduction"],
      "type": "article",
      "source": "educational",
      "author": "AI Researcher"
    }
  }'
```

**Response:**

```json
{
	"id": "doc_12345678",
	"status": "success",
	"chunks_created": 1,
	"embedding_time_ms": 234,
	"processing_time_ms": 567,
	"metadata": {
		"title": "ML Introduction",
		"tags": ["machine-learning", "ai", "introduction"],
		"type": "article"
	}
}
```

### Semantic Search

```bash
curl -X POST http://localhost:8080/v1/query/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "what is machine learning",
    "limit": 5,
    "threshold": 0.6,
    "filters": {
      "tags": ["machine-learning"],
      "type": "article"
    }
  }'
```

**Response:**

```json
{
	"query": "what is machine learning",
	"results": [
		{
			"id": "chunk_987654321",
			"content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
			"score": 0.923,
			"metadata": {
				"title": "ML Introduction",
				"tags": ["machine-learning", "ai", "introduction"],
				"document_id": "doc_12345678",
				"chunk_index": 0
			}
		}
	],
	"total_results": 1,
	"processing_time_ms": 45,
	"cache_hit": false
}
```

### Context-Aware Search

```bash
curl -X POST http://localhost:8080/v1/query/context-aware \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "deep learning applications",
    "context": "computer vision",
    "limit": 3,
    "threshold": 0.7
  }'
```

### Performance Metrics

```bash
curl -X GET http://localhost:8080/health/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**

```json
{
	"timestamp": "2024-01-15T10:30:00Z",
	"system": {
		"cpu_percent": 23.5,
		"memory_percent": 45.2,
		"disk_usage_percent": 15.8
	},
	"application": {
		"requests_per_second": 45.2,
		"avg_response_time_ms": 89,
		"error_rate_percent": 0.1
	},
	"database": {
		"active_connections": 8,
		"pool_size": 20,
		"avg_query_time_ms": 12
	},
	"cache": {
		"hit_rate_percent": 87.3,
		"l1_utilization_percent": 24.5,
		"l2_memory_usage_mb": 45.2
	}
}
```

### Cache Analytics

```bash
curl -X GET http://localhost:8080/health/cache/analytics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**

```json
{
	"timestamp": "2024-01-15T10:30:00Z",
	"l1_cache": {
		"total_items": 245,
		"valid_items": 243,
		"expired_items": 2,
		"max_size": 1000,
		"utilization": 0.245
	},
	"l2_cache": {
		"used_memory": "15.2MB",
		"used_memory_human": "15.2MB",
		"max_memory": "100MB"
	},
	"metrics": {
		"l1_hits": 1547,
		"l1_misses": 287,
		"l2_hits": 189,
		"l2_misses": 98,
		"sets": 385,
		"errors": 0
	},
	"hit_rates": {
		"l1_hit_rate": 0.847,
		"l2_hit_rate": 0.723,
		"overall_hit_rate": 0.892
	}
}
```

## Error Responses

All endpoints return standardized error responses:

### 400 Bad Request

```json
{
	"detail": "Invalid request format",
	"errors": [
		{
			"field": "content",
			"message": "Content cannot be empty"
		}
	]
}
```

### 401 Unauthorized

```json
{
	"detail": "Invalid or expired token"
}
```

### 404 Not Found

```json
{
	"detail": "Document not found",
	"document_id": "doc_12345678"
}
```

### 500 Internal Server Error

```json
{
	"detail": "Internal server error",
	"error_id": "err_987654321",
	"timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limits

- **General API**: 100 requests per minute per user
- **Search endpoints**: 60 requests per minute per user
- **Ingestion endpoints**: 20 requests per minute per user

## Interactive Documentation

For a complete interactive API documentation with request/response examples:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

These interfaces provide:

- Interactive request testing
- Complete schema documentation
- Authentication testing
- Response format examples
- Error code references
