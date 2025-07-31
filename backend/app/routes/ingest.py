"""
Content ingestion endpoints for adding data to the system.
"""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models.request_models import IngestRequest
from ..models.response_models import IngestResponse
from ..services.ingest_service import IngestService
from ..logging_utils import get_logger

router = APIRouter(tags=["Data Management"])
ingest_service = IngestService()
logger = get_logger(__name__)


@router.post(
    "/",
    response_model=IngestResponse,
    summary="Ingest content into the system",
    description="""
    Ingest content into the system with optional metadata.

    **Features:**
    - Accepts text content with metadata
    - Generates unique content IDs
    - Stores content for future retrieval
    - Supports custom metadata for filtering

    **Use Cases:**
    - Knowledge base population
    - Document ingestion
    - Content preprocessing
    - Training data preparation

    **Note:** This is a placeholder implementation. In production, this would:
    - Generate embeddings for semantic search
    - Store in vector database (Qdrant/Weaviate)
    - Extract and index metadata
    - Support batch ingestion
    """,
    responses={
        200: {
            "description": "Content ingested successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "doc_12345",
                        "status": "success",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "content_length": 85,
                    }
                }
            },
        },
        422: {"description": "Validation error"},
        500: {"description": "Ingestion failed"},
    },
)
async def ingest_content(request: IngestRequest):
    """Ingest content into the system with metadata."""
    start_time = time.time()

    try:
        logger.info(
            "Processing content ingestion",
            extra={
                "content_length": len(request.content),
                "has_metadata": bool(request.metadata),
                "metadata_keys": list(request.metadata.keys()) if request.metadata else []
            }
        )

        # Delegate to service layer
        result = await ingest_service.ingest_content(
            content=request.content, metadata=request.metadata
        )

        processing_time = int((time.time() - start_time) * 1000)
        logger.info(
            "Content ingested successfully",
            extra={
                "processing_time_ms": processing_time,
                "content_id": result.id,
                "content_length": result.content_length
            }
        )

        return result

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            "Content ingestion failed",
            extra={
                "processing_time_ms": processing_time,
                "error": str(e),
                "content_length": len(request.content)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Ingestion failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ) from e
