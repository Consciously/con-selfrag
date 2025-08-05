"""
Response models for API endpoints.

This module contains all Pydantic models used for API responses.
Each model includes comprehensive OpenAPI documentation and examples.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class GenerateResponse(BaseModel):
    """Response for text generation with metadata."""

    response: str = Field(
        ...,
        description="Generated text content",
        json_schema_extra={
            "example": (
                "Here's a Python function to calculate fibonacci numbers:\n\n"
                "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
            )
        },
    )
    model: str = Field(
        ...,
        description="Model used for generation",
        json_schema_extra={"example": "llama2"},
    )
    done: bool = Field(
        True,
        description="Whether generation is complete",
        json_schema_extra={"example": True},
    )
    total_duration: int | None = Field(
        None,
        description="Total generation time in nanoseconds",
        json_schema_extra={"example": 1234567890},
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
                "model": "llama2",
                "done": True,
                "total_duration": 1234567890,
            }
        }


class AskResponse(BaseModel):
    """Response for conversational question with enhanced metadata."""

    answer: str = Field(
        ...,
        description="Answer to the question",
        json_schema_extra={
            "example": "Docker containers provide isolation, portability, and consistent environments across different systems."
        },
    )
    model: str = Field(
        ...,
        description="Model used for answering",
        json_schema_extra={"example": "llama2"},
    )
    context_used: bool = Field(
        False,
        description="Whether conversation context was used",
        json_schema_extra={"example": False},
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "To optimize FastAPI performance, consider using async/await, connection pooling, caching, and proper database indexing.",
                "model": "llama2",
                "context_used": False,
            }
        }


class ModelInfo(BaseModel):
    """Comprehensive model information with capabilities."""

    name: str = Field(
        ...,
        description="Model name identifier",
        json_schema_extra={"example": "llama2"},
    )
    size: int | None = Field(
        None,
        description="Model size in bytes",
        json_schema_extra={"example": 3825819519},
    )
    digest: str | None = Field(
        None,
        description="Model digest/hash for verification",
        json_schema_extra={"example": "sha256:1a838c..."},
    )
    details: dict[str, Any] | None = Field(
        None,
        description="Additional model details and capabilities",
        json_schema_extra={
            "example": {
                "format": "gguf",
                "family": "llama",
                "families": ["llama"],
                "parameter_size": "7B",
            }
        },
    )


class HealthCheck(BaseModel):
    """Comprehensive health check response with service status."""

    status: str = Field(
        ...,
        description="Overall health status",
        json_schema_extra={"example": "healthy"},
    )
    localai_connected: bool = Field(
        ...,
        description="LocalAI service connection status",
        json_schema_extra={"example": True},
    )
    database_connected: bool = Field(
        ...,
        description="Database connection status",
        json_schema_extra={"example": True},
    )
    timestamp: str = Field(
        ...,
        description="Health check timestamp",
        json_schema_extra={"example": "2024-01-15T10:30:00Z"},
    )
    version: str = Field(
        ...,
        description="API version",
        json_schema_extra={"example": "1.0.0"},
    )


class LivenessCheck(BaseModel):
    """Liveness probe response for container orchestration."""

    alive: bool = Field(
        ...,
        description="Whether the service is alive and responding",
        json_schema_extra={"example": True},
    )
    timestamp: str = Field(
        ...,
        description="Check timestamp",
        json_schema_extra={"example": "2024-01-15T10:30:00Z"},
    )


class ReadinessCheck(BaseModel):
    """Readiness probe response for container orchestration."""

    ready: bool = Field(
        ...,
        description="Whether the service is ready to handle requests",
        json_schema_extra={"example": True},
    )
    localai_ready: bool = Field(
        ...,
        description="Whether LocalAI backend is ready",
        json_schema_extra={"example": True},
    )
    dependencies_ready: bool = Field(
        ...,
        description="Whether all dependencies are ready",
        json_schema_extra={"example": True},
    )
    timestamp: str = Field(
        ...,
        description="Check timestamp",
        json_schema_extra={"example": "2024-01-15T10:30:00Z"},
    )


class ErrorResponse(BaseModel):
    """Standardized error response format."""

    error: str = Field(
        ...,
        description="Error type identifier",
        json_schema_extra={"example": "ValidationError"},
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        json_schema_extra={"example": "Invalid request parameters"},
    )
    detail: str | None = Field(
        None,
        description="Detailed error information",
        json_schema_extra={"example": "Field 'prompt' is required"},
    )
    timestamp: str = Field(
        ...,
        description="Error timestamp",
        json_schema_extra={"example": "2024-01-15T10:30:00Z"},
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "detail": "Field 'prompt' is required",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class IngestResponse(BaseModel):
    """Response for successful data ingestion."""

    id: str = Field(
        ...,
        description="Unique identifier for the ingested content",
        json_schema_extra={"example": "doc_12345"},
    )
    status: str = Field(
        ...,
        description="Ingestion status",
        json_schema_extra={"example": "success"},
    )
    timestamp: str = Field(
        ...,
        description="Ingestion timestamp",
        json_schema_extra={"example": "2024-01-15T10:30:00Z"},
    )
    content_length: int = Field(
        ...,
        description="Length of ingested content in characters",
        json_schema_extra={"example": 85},
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_12345",
                "status": "success",
                "timestamp": "2024-01-15T10:30:00Z",
                "content_length": 85,
            }
        }


class QueryResult(BaseModel):
    """Individual query result item with enhanced context-aware scoring."""

    id: str = Field(
        ...,
        description="Unique identifier for the content",
        json_schema_extra={"example": "doc_12345"},
    )
    content: str = Field(
        ...,
        description="Relevant content snippet",
        json_schema_extra={
            "example": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+"
        },
    )
    relevance_score: float = Field(
        ...,
        description="Base relevance score between 0.0 and 1.0",
        json_schema_extra={"example": 0.95},
    )
    context_score: float | None = Field(
        None,
        description="Context-aware relevance score (if context provided)",
        json_schema_extra={"example": 0.88},
    )
    final_score: float = Field(
        ...,
        description="Final computed score after re-ranking",
        json_schema_extra={"example": 0.91},
    )
    metadata: dict[str, Any] | None = Field(
        None,
        description="Associated metadata",
        json_schema_extra={"example": {"tags": ["api", "python"]}},
    )


class QueryResponse(BaseModel):
    """Response for query results with context-aware enhancements."""

    query: str = Field(
        ...,
        description="Original query string",
        json_schema_extra={"example": "What web frameworks are mentioned?"},
    )
    context: str | None = Field(
        None,
        description="Context used for enhanced search",
        json_schema_extra={"example": "Previous discussion about Python frameworks"},
    )
    results: list[QueryResult] = Field(
        ...,
        description="List of relevant results sorted by final relevance score",
    )
    total_results: int = Field(
        ...,
        description="Total number of matching documents",
        json_schema_extra={"example": 42},
    )
    query_time_ms: int = Field(
        ...,
        description="Query processing time in milliseconds",
        json_schema_extra={"example": 150},
    )
    reranked: bool = Field(
        default=False,
        description="Whether results were re-ranked using context",
        json_schema_extra={"example": True},
    )
    context_used: bool = Field(
        default=False,
        description="Whether context was applied during search",
        json_schema_extra={"example": True},
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What web frameworks are mentioned?",
                "context": "Previous discussion about Python web development",
                "results": [
                    {
                        "id": "doc_12345",
                        "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
                        "relevance_score": 0.95,
                        "context_score": 0.88,
                        "final_score": 0.91,
                        "metadata": {"tags": ["api", "python"]},
                    }
                ],
                "total_results": 1,
                "query_time_ms": 150,
                "reranked": True,
                "context_used": True,
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response model for all API errors."""
    
    error: str = Field(
        ...,
        description="Error type identifier",
        json_schema_extra={"example": "VALIDATION_ERROR"}
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        json_schema_extra={"example": "Request validation failed"}
    )
    status_code: int = Field(
        ...,
        description="HTTP status code",
        json_schema_extra={"example": 422}
    )
    request_id: Optional[str] = Field(
        None,
        description="Unique request identifier for tracking",
        json_schema_extra={"example": "req_12345"}
    )
    timestamp: float = Field(
        ...,
        description="Error timestamp in Unix epoch format",
        json_schema_extra={"example": 1699123456.789}
    )
    path: Optional[str] = Field(
        None,
        description="Request path where error occurred",
        json_schema_extra={"example": "/v1/query"}
    )
    method: Optional[str] = Field(
        None,
        description="HTTP method used",
        json_schema_extra={"example": "POST"}
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details and context",
        json_schema_extra={
            "example": {
                "validation_errors": [
                    {
                        "field": "query",
                        "message": "field required",
                        "type": "value_error.missing"
                    }
                ],
                "total_errors": 1
            }
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "status_code": 422,
                "request_id": "req_12345",
                "timestamp": 1699123456.789,
                "path": "/v1/query",
                "method": "POST",
                "details": {
                    "validation_errors": [
                        {
                            "field": "query",
                            "message": "field required",
                            "type": "value_error.missing"
                        }
                    ],
                    "total_errors": 1
                }
            }
        }
