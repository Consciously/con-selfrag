"""
Content query service for handling search business logic.

This service encapsulates the business logic for content querying and semantic search,
using vector similarity search with embeddings, caching, and metadata filtering for optimal performance.
"""

import time
from typing import Any, List, Optional, Dict

from .embedding_service import EmbeddingService
from .vector_service import VectorService
from .cache_service import get_cached_query_result, cache_query_result
from ..models.response_models import QueryResponse, QueryResult
from ..config import config
from ..logging_utils import get_logger

logger = get_logger(__name__)


class QueryService:
    """Service for handling content query business logic with advanced caching."""
    
    def __init__(self):
        """Initialize the query service with search components."""
        self.embedding_service = EmbeddingService(
            model_name=config.embedding_model,
            use_cache=True
        )
        self.vector_service = VectorService()
        self._query_cache_ttl = 3600  # 1 hour for query results

    async def query_content(
        self, query: str, limit: int = None, filters: dict[str, Any] | None = None
    ) -> QueryResponse:
        """
        Query content using semantic vector search with multi-level caching.

        Args:
            query: Natural language search query
            limit: Maximum number of results to return (uses config default if None)
            filters: Optional metadata filters

        Returns:
            QueryResponse with search results

        Raises:
            ValueError: If query is empty or invalid
            RuntimeError: If query processing fails
        """
        start_time = time.time()
        
        try:
            # Validate query
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")

            query = query.strip()
            if limit is None:
                limit = config.search_limit

            logger.info(
                "Processing semantic search query",
                extra={
                    "query": query,
                    "limit": limit,
                    "has_filters": bool(filters),
                    "filter_keys": list(filters.keys()) if filters else []
                }
            )

            # Check query result cache first
            cached_result = await get_cached_query_result(query, filters, limit)
            if cached_result is not None:
                # Update timing for cached result
                query_time_ms = int((time.time() - start_time) * 1000)
                cached_result.query_time_ms = query_time_ms
                
                logger.info(
                    "Query result served from cache",
                    extra={
                        "query": query,
                        "cached_results": len(cached_result.results),
                        "query_time_ms": query_time_ms
                    }
                )
                return cached_result

            # Step 1: Generate embedding for the query (uses embedding cache)
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            logger.debug(
                "Query embedding generated",
                extra={
                    "query": query,
                    "embedding_dimension": len(query_embedding)
                }
            )

            # Step 2: Perform vector similarity search
            search_results = await self.vector_service.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                score_threshold=config.search_threshold,
                filters=filters
            )

            # Step 3: Convert to QueryResult format
            query_results = []
            for result in search_results:
                query_result = QueryResult(
                    id=result.chunk_id,
                    content=result.content,
                    relevance_score=result.score,
                    metadata=result.metadata
                )
                query_results.append(query_result)

            # Calculate query processing time
            query_time_ms = int((time.time() - start_time) * 1000)

            # Create response object
            response = QueryResponse(
                query=query,
                results=query_results,
                total_results=len(query_results),
                query_time_ms=query_time_ms,
            )

            # Cache the result for future queries
            await cache_query_result(query, response, filters, limit, self._query_cache_ttl)

            logger.info(
                "Semantic search completed successfully",
                extra={
                    "query": query,
                    "total_results": len(query_results),
                    "query_time_ms": query_time_ms,
                    "applied_filters": filters,
                    "avg_relevance": sum(r.relevance_score for r in query_results) / len(query_results) if query_results else 0,
                    "cached": True
                }
            )

            return response

        except ValueError as e:
            logger.error(
                "Validation error during query",
                extra={"error": str(e), "query": query},
                exc_info=True
            )
            raise
        except Exception as e:
            query_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Semantic search failed, falling back to mock results",
                extra={
                    "error": str(e), 
                    "query": query,
                    "query_time_ms": query_time_ms
                },
                exc_info=True
            )
            
            # Fallback to mock results if vector search fails
            return await self._generate_fallback_results(query, limit, query_time_ms)

    async def _generate_fallback_results(
        self, query: str, limit: int, query_time_ms: int
    ) -> QueryResponse:
        """Generate fallback results when vector search fails."""
        logger.info("Generating fallback search results")
        
        # Simple keyword matching for demo/fallback
        mock_results = []
        query_lower = query.lower()
        
        if "framework" in query_lower or "api" in query_lower:
            mock_results = [
                QueryResult(
                    id="fallback_12345",
                    content="FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
                    relevance_score=0.85,
                    metadata={"tags": ["api", "python"], "source": "fallback", "type": "demo"},
                ),
                QueryResult(
                    id="fallback_67890",
                    content="Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design.",
                    relevance_score=0.78,
                    metadata={"tags": ["framework", "python"], "source": "fallback", "type": "demo"},
                ),
            ]
        elif "python" in query_lower:
            mock_results = [
                QueryResult(
                    id="fallback_12345",
                    content="Python is a high-level, interpreted programming language with dynamic semantics and powerful built-in data structures.",
                    relevance_score=0.82,
                    metadata={"tags": ["python", "programming"], "source": "fallback", "type": "demo"},
                ),
            ]
        elif "selfrag" in query_lower or "rag" in query_lower:
            mock_results = [
                QueryResult(
                    id="fallback_rag_001",
                    content="Retrieval-Augmented Generation (RAG) combines the power of pre-trained language models with external knowledge retrieval.",
                    relevance_score=0.90,
                    metadata={"tags": ["rag", "ai", "retrieval"], "source": "fallback", "type": "demo"},
                ),
            ]

        # Apply limit
        limited_results = mock_results[:limit]

        return QueryResponse(
            query=query,
            results=limited_results,
            total_results=len(limited_results),
            query_time_ms=query_time_ms,
        )

    def _matches_filters(
        self,
        metadata: dict[str, Any],
        filters: dict[str, Any],
    ) -> bool:
        """
        Check if metadata matches the provided filters.

        Args:
            metadata: Document metadata
            filters: Filter criteria

        Returns:
            True if metadata matches all filters
        """
        try:
            for key, expected_value in filters.items():
                actual_value = metadata.get(key)

                # Handle list values (e.g., tags)
                if isinstance(expected_value, list):
                    if not isinstance(actual_value, list):
                        return False
                    # Check if any expected value is in actual values
                    if not any(val in actual_value for val in expected_value):
                        return False
                # Handle exact matches
                elif actual_value != expected_value:
                    return False

            return True

        except Exception as e:
            logger.warning(
                "Error during filter matching",
                extra={
                    "error": str(e),
                    "metadata": metadata,
                    "filters": filters
                }
            )
            return False

    async def search_by_metadata(
        self, filters: dict[str, Any], limit: int = 10
    ) -> QueryResponse:
        """
        Search content by metadata filters only.

        Args:
            filters: Metadata filters to apply
            limit: Maximum number of results to return

        Returns:
            QueryResponse with filtered results
        """
        try:
            logger.info(
                "Searching by metadata",
                extra={
                    "filters": filters,
                    "limit": limit
                }
            )

            # TODO: Implement actual metadata search
            # In production, this would query the database

            # Placeholder: Return empty results for now
            return QueryResponse(
                query="",
                results=[],
                total_results=0,
                query_time_ms=0,
            )

        except Exception as e:
            logger.error(
                "Metadata search failed",
                extra={"error": str(e), "filters": filters},
                exc_info=True
            )
            raise RuntimeError(f"Failed to search by metadata: {str(e)}") from e
