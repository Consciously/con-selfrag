"""
Content query endpoints for RAG pipeline semantic search.

Enhanced to use the complete RAG pipeline:
- Semantic vector search
- Relevance ranking
- Metadata filtering
"""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models import QueryRequest, QueryResponse
from ..services.query_service import QueryService
from ..logging_utils import get_logger

router = APIRouter(tags=["RAG Pipeline"])
query_service = QueryService()
logger = get_logger(__name__)


@router.post(
    "/",
    response_model=QueryResponse,
    summary="Semantic search with RAG pipeline",
    description="""
    Perform semantic search using the complete RAG pipeline with vector similarity and relevance ranking.

    **RAG Search Features:**
    - **Semantic Search**: Vector similarity using 384-dimensional embeddings
    - **Relevance Ranking**: Results sorted by cosine similarity scores
    - **Metadata Filtering**: Filter results by source, tags, or custom metadata
    - **Performance Optimized**: Fast Qdrant vector search with configurable limits

    **Search Process:**
    1. Query text embedding generation
    2. Vector similarity search in Qdrant
    3. Relevance score calculation
    4. Metadata filtering and ranking
    5. Structured result formatting

    **Use Cases:**
    - Knowledge base search
    - Document retrieval for Q&A
    - Context preparation for LLM responses
    - Semantic content discovery

    **Performance Notes:**
    - Sub-second response times for most queries
    - Configurable similarity thresholds
    - Efficient metadata indexing
    - Comprehensive query logging
    """,
    responses={
        200: {
            "description": "Semantic search executed successfully",
            "content": {
                "application/json": {
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
            },
        },
        422: {"description": "Validation error"},
        500: {"description": "Semantic search processing failed"},
    },
)
async def query_content(request: QueryRequest):
    """Perform semantic search using RAG pipeline."""
    start_time = time.time()

    try:
        logger.info(
            "Processing semantic search query",
            extra={
                "query": request.query,
                "limit": request.limit,
                "has_filters": bool(request.filters),
                "filter_keys": list(request.filters.keys()) if request.filters else []
            }
        )

        # Delegate to RAG query service layer
        result = await query_service.query_content(
            query=request.query, limit=request.limit, filters=request.filters
        )

        query_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "Semantic search completed successfully",
            extra={
                "query_time_ms": query_time_ms,
                "total_results": result.total_results,
                "results_returned": len(result.results),
                "query": request.query
            }
        )

        return result

    except Exception as e:
        query_time_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "Semantic search processing failed",
            extra={
                "query_time_ms": query_time_ms,
                "query": request.query,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Semantic search failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ) from e
