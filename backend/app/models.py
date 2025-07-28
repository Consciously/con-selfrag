"""
Enhanced Pydantic models with comprehensive OpenAPI documentation.
Includes detailed examples and descriptions for better developer experience.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Request Models
class GenerateRequest(BaseModel):
    """Request for text generation with comprehensive options."""

    prompt: str = Field(
        ...,
        description="Input prompt for text generation",
        example="Write a Python function to calculate fibonacci numbers",
    )
    model: str | None = Field(
        None, description="Model name (uses default if not specified)", example="llama2"
    )
    temperature: float | None = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 = deterministic, 2.0 = very creative)",
        example=0.7,
    )
    stream: bool | None = Field(
        False,
        description="Enable streaming response for real-time text generation",
        example=False,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Explain quantum computing in simple terms",
                "model": "llama2",
                "temperature": 0.7,
                "stream": False,
            }
        }


class AskRequest(BaseModel):
    """Request for conversational question with context awareness."""

    question: str = Field(
        ...,
        description="Question to ask the AI assistant",
        example="What are the benefits of using Docker containers?",
    )
    model: str | None = Field(
        None, description="Model name (uses default if not specified)", example="llama2"
    )
    temperature: float | None = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for response creativity",
        example=0.7,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "How do I optimize FastAPI performance?",
                "model": "llama2",
                "temperature": 0.5,
            }
        }


# Response Models
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


# Health Check Models
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


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response with comprehensive details."""

    error: str = Field(
        ..., description="Error type/category", example="ValidationError"
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        example="Invalid temperature value",
    )
    detail: str | None = Field(
        None,
        description="Additional error details for debugging",
        example="Temperature must be between 0.0 and 2.0",
    )
    timestamp: str | None = Field(
        None, description="Error timestamp", example="2024-01-15T10:30:00Z"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ModelNotFound",
                "message": "The specified model is not available",
                "detail": "Model 'gpt-4' not found in available models list",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


# Metrics Models
class MetricsResponse(BaseModel):
    """Prometheus metrics response."""

    metrics: str = Field(
        ...,
        description="Prometheus-formatted metrics data",
        example='# HELP http_requests_total Total HTTP requests\n# TYPE http_requests_total counter\nhttp_requests_total{method="GET",endpoint="/health"} 42',
    )
