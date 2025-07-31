"""
Content query endpoints for searching ingested data.
"""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models.request_models import QueryRequest
from ..models.response_models import QueryResponse
from ..services.query_service import QueryService
from ..logging_utils import get_logger

router = APIRouter(tags=["Data Management"])
query_service = QueryService()
logger = get_logger(__name__)


@router.post(
    "/",
    response_model=QueryResponse,
    summary="Query ingested content",
    description="""
    Query ingested content using natural language search.
    **Features:**
    - Natural language query processing
    - Relevance-based ranking
    - Metadata filtering
    - Pagination support
    **Use Cases:**
    - Knowledge base search
    - Document retrieval
    - Content discovery
    - Q&A over ingested documents
    **Note:** This is a placeholder implementation. In production, this would:
    - Use vector similarity search with embeddings
    - Implement hybrid search (semantic + keyword)
    - Add caching for performance
    - Support faceted search and filtering
    """,
    responses={
        200: {
            "description": "Query executed successfully",
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
        500: {"description": "Query processing failed"},
    },
)
async def query_content(request: QueryRequest):
    """Query ingested content using natural language search."""
    start_time = time.time()

    try:
        logger.info(
            "Processing query",
            extra={
                "query": request.query,
                "limit": request.limit,
                "has_filters": bool(request.filters),
                "filter_keys": list(request.filters.keys()) if request.filters else []
            }
        )

        # Delegate to service layer
        result = await query_service.query_content(
            query=request.query, limit=request.limit, filters=request.filters
        )

        query_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "Query processed successfully",
            extra={
                "query_time_ms": query_time_ms,
                "total_results": result.total_results,
                "query": request.query
            }
        )

        return result

    except Exception as e:
        query_time_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "Query processing failed",
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
                "error": "Query failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ) from e
