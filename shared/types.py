"""
Shared types between frontend and backend.
These types ensure consistent API contracts across the application.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# API Request/Response Types
class GenerateRequest(BaseModel):
    """Request for text generation - shared with frontend."""
    prompt: str = Field(..., description="Input prompt")
    model: Optional[str] = Field(None, description="Model name (uses default if not specified)")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    stream: Optional[bool] = Field(False, description="Enable streaming response")


class GenerateResponse(BaseModel):
    """Response for text generation - shared with frontend."""
    response: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used")
    done: bool = Field(True, description="Whether generation is complete")


class AskRequest(BaseModel):
    """Request for conversational question - shared with frontend."""
    question: str = Field(..., description="Question to ask")
    model: Optional[str] = Field(None, description="Model name (uses default if not specified)")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")


class AskResponse(BaseModel):
    """Response for conversational question - shared with frontend."""
    answer: str = Field(..., description="Answer to the question")
    model: str = Field(..., description="Model used")


class ModelInfo(BaseModel):
    """Model information - shared with frontend."""
    name: str = Field(..., description="Model name")
    size: Optional[int] = Field(None, description="Model size in bytes")


class HealthCheck(BaseModel):
    """Health check response - shared with frontend."""
    status: str = Field(..., description="Health status")
    localai_connected: bool = Field(..., description="LocalAI connection status")


class ErrorResponse(BaseModel):
    """Standard error response - shared with frontend."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


# Frontend Integration Types
class APIEndpoint(BaseModel):
    """API endpoint information for frontend integration."""
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="Endpoint path")
    description: str = Field(..., description="Endpoint description")
    request_model: Optional[str] = Field(None, description="Request model type")
    response_model: Optional[str] = Field(None, description="Response model type")


class APIContract(BaseModel):
    """Complete API contract for frontend integration."""
    base_url: str = Field(..., description="API base URL")
    version: str = Field(..., description="API version")
    endpoints: List[APIEndpoint] = Field(..., description="Available endpoints")


# Database Integration Types (for future use)
# Uncomment when database functionality is implemented

# class ChatHistoryItem(BaseModel):
#     """Chat history item for frontend display."""
#     id: int
#     message: str
#     response: str
#     model: str
#     timestamp: str
#     
# class SearchResult(BaseModel):
#     """Vector search result for frontend display."""
#     content: str
#     score: float
#     metadata: Dict[str, Any]


# Utility functions for type conversion
def get_api_contract(base_url: str = "http://localhost:8000") -> APIContract:
    """Get the complete API contract for frontend integration."""
    return APIContract(
        base_url=base_url,
        version="1.0.0",
        endpoints=[
            APIEndpoint(
                method="GET",
                path="/",
                description="Root endpoint with API information",
                response_model="dict"
            ),
            APIEndpoint(
                method="GET",
                path="/health",
                description="Health check endpoint",
                response_model="HealthCheck"
            ),
            APIEndpoint(
                method="POST",
                path="/generate", 
                description="Generate text using Ollama",
                request_model="GenerateRequest",
                response_model="GenerateResponse"
            ),
            APIEndpoint(
                method="POST",
                path="/ask",
                description="Ask conversational questions",
                request_model="AskRequest", 
                response_model="AskResponse"
            ),
            APIEndpoint(
                method="GET",
                path="/models",
                description="List available models",
                response_model="List[ModelInfo]"
            ),
            # Database endpoints (commented for future use)
            # APIEndpoint(
            #     method="GET",
            #     path="/chat/history",
            #     description="Get chat history",
            #     response_model="List[ChatHistoryItem]"
            # ),
            # APIEndpoint(
            #     method="POST", 
            #     path="/documents/search",
            #     description="Search documents with vector similarity",
            #     response_model="List[SearchResult]"
            # ),
        ]
    )


# Export all types for easy importing
__all__ = [
    "GenerateRequest",
    "GenerateResponse", 
    "AskRequest",
    "AskResponse",
    "ModelInfo",
    "HealthCheck",
    "ErrorResponse",
    "APIEndpoint",
    "APIContract",
    "get_api_contract",
    # Database types (uncomment when implemented)
    # "ChatHistoryItem",
    # "SearchResult",
]
