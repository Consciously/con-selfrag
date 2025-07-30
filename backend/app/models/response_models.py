"""
Response models for API endpoints.

This module contains all Pydantic models used for API responses.
Each model includes comprehensive OpenAPI documentation and examples.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GenerateResponse(BaseModel):
    """Response for text generation with metadata."""

    response: str = Field(
        ...,
        description="Generated text content",
        example="Here's a Python function to calculate fibonacci numbers:\n\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    )
    model: str = Field(..., description="Model used for generation", example="llama2")
    done: bool = Field(True, description="Whether generation is complete", example=True)
    total_duration: int | None = Field(
        None, description="Total generation time in nanoseconds", example=1234567890
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
        example="Docker containers provide isolation, portability, and consistent environments across different systems.",
    )
    model: str = Field(..., description="Model used for answering", example="llama2")
    context_used: bool | None = Field(
        False, description="Whether conversation context was used", example=False
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

    name: str = Field(..., description="Model name identifier", example="llama2")
    size: int | None = Field(
        None, description="Model size in bytes", example=3825819519
    )
    digest: str | None = Field(
        None,
        description="Model digest/hash for verification",
        example="sha256:1a838c...",
    )
    details: dict[str, Any] | None = Field(
        None, description="Additional model details and capabilities"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "llama2",
                "size": 3825819519,
                "digest": "sha256:1a838c2d3e4f5a6b7c8d9e0f",
                "details": {
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "7B",
                },
            }
        }


class HealthCheck(BaseModel):
    """Comprehensive health check response with service status."""

    status: str = Field(..., description="Overall health status", example="healthy")
    localai_connected: bool = Field(
        ..., description="LocalAI service connection status", example=True
    )
    timestamp: str | None = Field(
        None, description="Health check timestamp", example="2024-01-15T10:30:00Z"
    )
    version: str | None = Field(None, description="API version", example="1.0.0")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "localai_connected": True,
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
            }
        }


class LivenessCheck(BaseModel):
    """Liveness probe response for container orchestration."""

    alive: bool = Field(
        ..., description="Whether the service is alive and responding", example=True
    )
    timestamp: str = Field(
        ..., description="Check timestamp", example="2024-01-15T10:30:00Z"
    )


class ReadinessCheck(BaseModel):
    """Readiness probe response for container orchestration."""

    ready: bool = Field(
        ..., description="Whether the service is ready to handle requests", example=True
    )
    localai_ready: bool = Field(
        ..., description="Whether LocalAI backend is ready", example=True
    )
    dependencies_ready: bool = Field(
        ..., description="Whether all dependencies are ready", example=True
    )
    timestamp: str = Field(
        ..., description="Check timestamp", example="2024-01-15T10:30:00Z"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ready": True,
                "localai_ready": True,
                "dependencies_ready": True,
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response format."""

    error: str = Field(..., description="Error type identifier", example="ValidationError")
    message: str = Field(..., description="Human-readable error message", example="Invalid request parameters")
    detail: str | None = Field(None, description="Detailed error information", example="Field 'prompt' is required")
    timestamp: str = Field(..., description="Error timestamp", example="2024-01-15T10:30:00Z")

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
        ..., description="Unique identifier for the ingested content", example="doc_12345"
    )
    status: str = Field(
        ..., description="Ingestion status", example="success"
    )
    timestamp: str = Field(
        ..., description="Ingestion timestamp", example="2024-01-15T10:30:00Z"
    )
    content_length: int = Field(
        ..., description="Length of ingested content in characters", example=85
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
    """Individual query result item."""

    id: str = Field(
        ..., description="Unique identifier for the content", example="doc_12345"
    )
    content: str = Field(
        ...,
        description="Relevant content snippet",
        example="FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
    )
    relevance_score: float = Field(
        ..., description="Relevance score between 0.0 and 1.0", example=0.95
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Associated metadata", example={"tags": ["api", "python"]}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_12345",
                "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
                "relevance_score": 0.95,
                "metadata": {"tags": ["api", "python"], "source": "user_input"},
            }
        }


class QueryResponse(BaseModel):
    """Response for query results."""

    query: str = Field(
        ..., description="Original query string", example="What web frameworks are mentioned?"
    )
    results: list[QueryResult] = Field(
        ..., description="List of relevant results sorted by relevance"
    )
    total_results: int = Field(
        ..., description="Total number of results found", example=3
    )
    query_time_ms: int = Field(
        ..., description="Query processing time in milliseconds", example=150
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What web frameworks are mentioned?",
                "results": [
                    {
                        "id": "doc_12345",
                        "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
                        "relevance_score": 0.95,
                        "metadata": {"tags": ["api", "python"]},
                    }
                ],
                "total_results": 1,
                "query_time_ms": 45,
            }
        }
