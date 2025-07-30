"""
Request models for API endpoints.

This module contains all Pydantic models used for validating incoming requests.
Each model includes comprehensive OpenAPI documentation and examples.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


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


class IngestRequest(BaseModel):
    """Request for ingesting content into the system."""

    content: str = Field(
        ...,
        description="Content to be ingested (text, markdown, etc.)",
        example="FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
    )
    metadata: Dict[str, Any] | None = Field(
        None,
        description="Optional metadata for the content",
        example={
            "type": "text",
            "language": "en",
            "tags": ["api", "python", "documentation"],
            "author": "user",
        },
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
                "metadata": {
                    "type": "text",
                    "language": "en",
                    "tags": ["api", "python", "documentation"],
                    "author": "user",
                },
            }
        }


class QueryRequest(BaseModel):
    """Request for querying ingested data."""

    query: str = Field(
        ...,
        description="Natural language query to search the ingested content",
        example="What web frameworks are mentioned in the documents?",
    )
    limit: int | None = Field(
        10,
        ge=1,
        le=100,
        description="Maximum number of results to return",
        example=10,
    )
    filters: dict[str, Any] | None = Field(
        None,
        description="Optional filters to apply to the search",
        example={"source": "user_input", "tags": ["python"]},
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What web frameworks are mentioned in the documents?",
                "limit": 5,
                "filters": {"source": "user_input", "tags": ["python"]},
            }
        }
