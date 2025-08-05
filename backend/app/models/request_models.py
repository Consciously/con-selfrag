"""
Request models for API endpoints.

This module contains all Pydantic models used for validating incoming requests.
Each model includes comprehensive OpenAPI documentation and examples.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request for text generation with comprehensive options."""

    prompt: str = Field(
        ...,
        description="Input prompt for text generation",
        json_schema_extra={
            "example": "Write a Python function to calculate fibonacci numbers"
        },
    )
    model: str | None = Field(
        default=None,
        description="Model name (uses default if not specified)",
        json_schema_extra={"example": "llama2"},
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature. 0.0 = deterministic, 2.0 = very creative",
        json_schema_extra={"example": 0.7},
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response for real-time text generation",
        json_schema_extra={"example": False},
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
        json_schema_extra={
            "example": "What are the benefits of using Docker containers?"
        },
    )
    model: str | None = Field(
        default=None,
        description="Model name (uses default if not specified)",
        json_schema_extra={"example": "llama2"},
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for response creativity",
        json_schema_extra={"example": 0.7},
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "How do I optimize FastAPI performance?",
                "model": "llama2",
                "temperature": 0.5,
            }
        }


class IngestRequest(BaseModel):
    """Request for ingesting content into the system."""

    content: str = Field(
        ...,
        description="Content to be ingested (text, markdown, etc.)",
        json_schema_extra={
            "example": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+"
        },
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata for the content",
        json_schema_extra={
            "example": {
                "type": "text",
                "language": "en",
                "tags": ["api", "python", "documentation"],
                "author": "user",
            }
        },
    )


class QueryRequest(BaseModel):
    """Request for querying ingested data with context-aware capabilities."""

    query: str = Field(
        ...,
        description="Natural language query to search the ingested content",
        json_schema_extra={
            "example": "What web frameworks are mentioned in the documents?"
        },
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return",
        json_schema_extra={"example": 10},
    )
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Optional filters to apply to the search",
        json_schema_extra={"example": {"source": "user_input", "tags": ["python"]}},
    )
    context: str | None = Field(
        default=None,
        description="Optional conversation or session context to enhance search relevance",
        json_schema_extra={
            "example": "We were discussing Python web development and API frameworks"
        },
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for context-aware search tracking",
        json_schema_extra={"example": "session_12345"},
    )
    enable_reranking: bool = Field(
        default=True,
        description="Enable advanced re-ranking based on context and relevance",
        json_schema_extra={"example": True},
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the best practices for API development?",
                "limit": 10,
                "filters": {"tags": ["api", "python"]},
                "context": "Previous discussion about FastAPI and performance optimization",
                "session_id": "session_12345",
                "enable_reranking": True,
            }
        }