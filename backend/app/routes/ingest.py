"""
Content ingestion endpoints for RAG pipeline.

Enhanced to use the complete RAG pipeline:
- Document processing and chunking
- Embedding generation
- Vector storage in Qdrant
"""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models import IngestRequest, IngestResponse
from ..services.ingest_service import IngestService
from ..logging_utils import get_logger

router = APIRouter(tags=["RAG Pipeline"])
ingest_service = IngestService()
logger = get_logger(__name__)


@router.post(
    "/",
    response_model=IngestResponse,
    summary="Ingest content into RAG pipeline",
    description="""
    Ingest content into the complete RAG pipeline with document processing, embedding generation, and vector storage.

    **RAG Pipeline Features:**
    - **Document Processing**: Smart text chunking with semantic boundaries
    - **Embedding Generation**: 384-dimensional vectors using sentence-transformers
    - **Vector Storage**: Qdrant similarity search with metadata
    - **Metadata Support**: Rich metadata for filtering and organization

    **Process Flow:**
    1. Content validation and preprocessing
    2. Document chunking with overlap handling
    3. Embedding generation for each chunk
    4. Vector storage in Qdrant with metadata
    5. Indexing for fast retrieval

    **Use Cases:**
    - Knowledge base population
    - Document ingestion for Q&A
    - Content preparation for semantic search
    - RAG-augmented LLM responses

    **Performance Notes:**
    - Supports batch processing for efficiency
    - Async pipeline for non-blocking operations
    - Comprehensive error handling and logging
    """,
    responses={
        200: {
            "description": "Content ingested successfully into RAG pipeline",
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
        500: {"description": "RAG pipeline ingestion failed"},
    },
)
async def ingest_content(request: IngestRequest):
    """Ingest content into the RAG pipeline with full processing."""
    start_time = time.time()

    try:
        logger.info(
            "Processing RAG pipeline ingestion",
            extra={
                "content_length": len(request.content),
                "source": request.source,
                "has_metadata": bool(request.metadata),
                "metadata_keys": list(request.metadata.keys()) if request.metadata else []
            }
        )

        # Prepare metadata with source information
        ingestion_metadata = {
            "source": request.source,
            "ingestion_timestamp": datetime.utcnow().isoformat() + "Z",
            **(request.metadata or {})
        }

        # Delegate to RAG service layer for complete processing
        result = await ingest_service.ingest_content(
            content=request.content, 
            metadata=ingestion_metadata
        )

        processing_time = int((time.time() - start_time) * 1000)
        logger.info(
            "RAG pipeline ingestion completed successfully",
            extra={
                "processing_time_ms": processing_time,
                "content_id": result.id,
                "content_length": result.content_length,
                "chunks_processed": getattr(result, 'chunks_count', 'unknown'),
                "embeddings_generated": getattr(result, 'embeddings_count', 'unknown')
            }
        )

        return result

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            "RAG pipeline ingestion failed",
            extra={
                "processing_time_ms": processing_time,
                "error": str(e),
                "content_length": len(request.content),
                "source": request.source
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "RAG pipeline ingestion failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ) from e
