"""
Data models package.

This package contains all Pydantic models for request/response validation.
Models are organized by type (requests vs responses) and provide
comprehensive OpenAPI documentation with examples.
"""

# Import all request models
from .request_models import *

# Import all response models
from .response_models import *
# Memory models (Phase 3)
try:  # pragma: no cover - optional import if SQLAlchemy available
    from .memory_models import EpisodicMemory, SemanticMemory  # type: ignore
except Exception:  # noqa: BLE001
    EpisodicMemory = None  # type: ignore
    SemanticMemory = None  # type: ignore

# Explicit exports for better IDE support
__all__ = [
    # Request models
    "GenerateRequest",
    "AskRequest", 
    "IngestRequest",
    "QueryRequest",
    # Response models
    "AskResponse",
    "GenerateResponse", 
    "ModelInfo",
    "HealthCheck",
    "LivenessCheck",
    "ReadinessCheck",
    "ErrorResponse",
    "IngestResponse",
    "QueryResult",
    "QueryResponse",
    # Memory models
    "EpisodicMemory",
    "SemanticMemory",
]
