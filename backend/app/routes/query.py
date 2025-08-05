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
    summary="Context-aware semantic search with RAG pipeline",
    description="""
    Perform context-aware semantic search using the complete RAG pipeline with vector similarity and intelligent re-ranking.

    **Enhanced RAG Search Features:**
    - **Semantic Search**: Vector similarity using 384-dimensional embeddings
    - **Context-Aware Re-ranking**: Improved relevance using conversation context
    - **Multi-sentence Query Support**: Handles complex, conversational queries
    - **Session Tracking**: Optional session-based context management
    - **Metadata Filtering**: Filter results by source, tags, or custom metadata
    - **Performance Optimized**: Fast Qdrant vector search with advanced caching

    **Context-Aware Search Process:**
    1. Query text embedding generation
    2. Context embedding generation (if provided)
    3. Vector similarity search in Qdrant
    4. Context-aware re-ranking using weighted scoring
    5. Final score calculation and result ordering
    6. Structured result formatting with scoring details

    **Re-ranking Algorithm:**
    - Base relevance score (70% weight): Direct query-document similarity
    - Context relevance score (30% weight): Context-document similarity
    - Final score: Weighted combination for optimal ranking

    **Use Cases:**
    - Conversational knowledge base search
    - Context-aware document retrieval
    - Session-based Q&A systems
    - Advanced semantic content discovery

    **Performance Notes:**
    - Sub-second response times with context processing
    - Context-aware caching for improved performance
    - Configurable re-ranking parameters
    - Comprehensive query and context logging
    """,
    responses={
        200: {
            "description": "Context-aware semantic search executed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "query": "What are the best practices for API development?",
                        "context": "Previous discussion about FastAPI and performance",
                        "results": [
                            {
                                "id": "doc_12345",
                                "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+",
                                "relevance_score": 0.95,
                                "context_score": 0.88,
                                "final_score": 0.91,
                                "metadata": {"tags": ["api", "python"]},
                            }
                        ],
                        "total_results": 1,
                        "query_time_ms": 145,
                        "reranked": True,
                        "context_used": True,
                    }
                }
            },
        },
        422: {"description": "Validation error"},
        500: {"description": "Context-aware search processing failed"},
    },
)
async def query_content(request: QueryRequest):
    """Perform context-aware semantic search using enhanced RAG pipeline."""
    start_time = time.time()

    try:
        logger.info(
            "Processing context-aware semantic search query",
            extra={
                "query": request.query,
                "limit": request.limit,
                "has_filters": bool(request.filters),
                "filter_keys": list(request.filters.keys()) if request.filters else [],
                "has_context": bool(request.context),
                "session_id": request.session_id,
                "enable_reranking": request.enable_reranking
            }
        )

        # Delegate to enhanced RAG query service layer
        result = await query_service.query_content(
            query=request.query, 
            limit=request.limit, 
            filters=request.filters,
            context=request.context,
            session_id=request.session_id,
            enable_reranking=request.enable_reranking
        )

        query_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "Context-aware semantic search completed successfully",
            extra={
                "query_time_ms": query_time_ms,
                "total_results": result.total_results,
                "results_returned": len(result.results),
                "query": request.query,
                "context_used": result.context_used,
                "reranked": result.reranked,
                "session_id": request.session_id
            }
        )

        return result

    except Exception as e:
        query_time_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "Context-aware semantic search processing failed",
            extra={
                "query_time_ms": query_time_ms,
                "query": request.query,
                "error": str(e),
                "has_context": bool(request.context),
                "session_id": request.session_id
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Context-aware semantic search failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ) from e
