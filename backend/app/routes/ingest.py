"""
Content ingestion routes for adding data to the system.

This module provides endpoints for ingesting content with metadata
into the system for later retrieval and search.
"""

import time
from datetime import datetime
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..models.request_models import IngestRequest
from ..models.response_models import IngestResponse
from ..services.ingest_service import IngestService

router = APIRouter(prefix="/ingest", tags=["Data Management"])
ingest_service = IngestService()


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
        logger.info(f"Processing content ingestion: {len(request.content)} chars")
        if request.metadata:
            logger.info(f"With metadata: {request.metadata}")
        
        # Delegate to service layer
        result = await ingest_service.ingest_content(
            content=request.content,
            metadata=request.metadata
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Content ingested successfully in {processing_time}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"Content ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "IngestionError",
                "message": "Failed to ingest content",
                "detail": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ) from e
