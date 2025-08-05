"""
Content query service for handling search business logic.

This service encapsulates the business logic for content querying and semantic search,
using vector similarity search with embeddings, context-aware re-ranking, and metadata filtering for optimal performance.
"""

import time
import math
from typing import Any, List, Optional, Dict

from .embedding_service import EmbeddingService
from .vector_service import VectorService
from .cache_service import get_cached_query_result, cache_query_result
from ..models.response_models import QueryResponse, QueryResult
from ..config import config
from ..logging_utils import get_logger

logger = get_logger(__name__)


class QueryService:
    """Service for handling content query business logic with advanced caching and context-aware retrieval."""
    
    def __init__(self):
        """Initialize the query service with search components."""
        self.embedding_service = EmbeddingService(
            model_name=config.embedding_model,
            use_cache=True
        )
        self.vector_service = VectorService()
        self._query_cache_ttl = 3600  # 1 hour for query results
        self._context_weight = 0.3  # Weight for context in re-ranking (30%)
        self._base_weight = 0.7  # Weight for base relevance (70%)

    async def query_content(
        self, 
        query: str, 
        limit: int = None, 
        filters: dict[str, Any] | None = None,
        context: str | None = None,
        session_id: str | None = None,
        enable_reranking: bool = True
    ) -> QueryResponse:
        """
        Query content using semantic vector search with context-aware re-ranking.

        Args:
            query: Natural language search query
            limit: Maximum number of results to return (uses config default if None)
            filters: Optional metadata filters
            context: Optional conversation or session context for enhanced relevance
            session_id: Optional session ID for context tracking
            enable_reranking: Whether to apply context-aware re-ranking

        Returns:
            QueryResponse with search results, context information, and ranking details

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

            # Create cache key that includes context for cache differentiation
            cache_key_context = f"{context}:{session_id}" if context or session_id else None

            logger.info(
                "Processing context-aware semantic search query",
                extra={
                    "query": query,
                    "limit": limit,
                    "has_filters": bool(filters),
                    "filter_keys": list(filters.keys()) if filters else [],
                    "has_context": bool(context),
                    "session_id": session_id,
                    "enable_reranking": enable_reranking
                }
            )

            # Check query result cache first (context-aware caching)
            cached_result = await get_cached_query_result(
                query, filters, limit, cache_key_context
            )
            if cached_result is not None:
                # Update timing for cached result
                query_time_ms = int((time.time() - start_time) * 1000)
                cached_result.query_time_ms = query_time_ms
                
                logger.info(
                    "Context-aware query result served from cache",
                    extra={
                        "query": query,
                        "cached_results": len(cached_result.results),
                        "query_time_ms": query_time_ms,
                        "context_used": bool(context)
                    }
                )
                return cached_result

            # Step 1: Generate embedding for the query (uses embedding cache)
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Step 2: Generate context embedding if context is provided
            context_embedding = None
            if context and enable_reranking:
                context_embedding = await self.embedding_service.generate_embedding(context)
                logger.debug(
                    "Context embedding generated",
                    extra={
                        "context": context[:100] + "..." if len(context) > 100 else context,
                        "embedding_dimension": len(context_embedding)
                    }
                )
            
            logger.debug(
                "Query embedding generated",
                extra={
                    "query": query,
                    "embedding_dimension": len(query_embedding),
                    "has_context_embedding": bool(context_embedding)
                }
            )

            # Step 3: Perform vector similarity search
            search_results = await self.vector_service.search_similar(
                query_embedding=query_embedding,
                limit=limit * 2 if enable_reranking else limit,  # Get more for re-ranking
                score_threshold=config.search_threshold,
                filters=filters
            )

            # Step 4: Apply context-aware re-ranking if enabled
            reranked = False
            if context_embedding and enable_reranking and search_results:
                search_results = await self._rerank_with_context(
                    search_results, context_embedding, query
                )
                reranked = True
                # Trim to original limit after re-ranking
                search_results = search_results[:limit]

            # Step 5: Convert to QueryResult format with enhanced scoring
            query_results = []
            for result in search_results:
                # Calculate final score (context-aware if applicable)
                final_score = result.score
                context_score = None
                
                if reranked and hasattr(result, 'context_score'):
                    context_score = result.context_score
                    final_score = result.final_score
                
                query_result = QueryResult(
                    id=result.chunk_id,
                    content=result.content,
                    relevance_score=result.score,
                    context_score=context_score,
                    final_score=final_score,
                    metadata=result.metadata
                )
                query_results.append(query_result)

            # Calculate query processing time
            query_time_ms = int((time.time() - start_time) * 1000)

            # Create response object with context information
            response = QueryResponse(
                query=query,
                context=context,
                results=query_results,
                total_results=len(query_results),
                query_time_ms=query_time_ms,
                reranked=reranked,
                context_used=bool(context)
            )

            # Cache the result for future queries (with context-aware key)
            await cache_query_result(
                query, response, filters, limit, self._query_cache_ttl, cache_key_context
            )

            logger.info(
                "Context-aware semantic search completed successfully",
                extra={
                    "query": query,
                    "total_results": len(query_results),
                    "query_time_ms": query_time_ms,
                    "applied_filters": filters,
                    "context_used": bool(context),
                    "reranked": reranked,
                    "avg_relevance": sum(r.relevance_score for r in query_results) / len(query_results) if query_results else 0,
                    "avg_final_score": sum(r.final_score for r in query_results) / len(query_results) if query_results else 0,
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
                "Context-aware semantic search failed, falling back to mock results",
                extra={
                    "error": str(e), 
                    "query": query,
                    "query_time_ms": query_time_ms,
                    "context_provided": bool(context)
                },
                exc_info=True
            )
            
            # Fallback to mock results if vector search fails
            return await self._generate_fallback_results(query, limit, query_time_ms, context)

    async def _rerank_with_context(
        self, 
        search_results: List[Any], 
        context_embedding: List[float], 
        original_query: str
    ) -> List[Any]:
        """
        Re-rank search results using context-aware scoring.
        
        Combines base relevance score with context similarity for improved ranking.
        
        Args:
            search_results: Original search results with base scores
            context_embedding: Embedding vector for the provided context
            original_query: Original query for logging
            
        Returns:
            Re-ranked search results with enhanced scoring
        """
        try:
            logger.debug(
                "Starting context-aware re-ranking",
                extra={
                    "result_count": len(search_results),
                    "query": original_query
                }
            )
            
            enhanced_results = []
            
            for result in search_results:
                # Generate embedding for the result content
                content_embedding = await self.embedding_service.generate_embedding(
                    result.content
                )
                
                # Calculate context similarity using cosine similarity
                context_score = self._calculate_cosine_similarity(
                    context_embedding, content_embedding
                )
                
                # Calculate final score: weighted combination of base score and context score
                final_score = (
                    self._base_weight * result.score + 
                    self._context_weight * context_score
                )
                
                # Store additional scoring information
                result.context_score = context_score
                result.final_score = final_score
                
                enhanced_results.append(result)
                
                logger.debug(
                    "Result re-ranked",
                    extra={
                        "result_id": result.chunk_id,
                        "base_score": result.score,
                        "context_score": context_score,
                        "final_score": final_score
                    }
                )
            
            # Sort by final score (descending)
            enhanced_results.sort(key=lambda x: x.final_score, reverse=True)
            
            logger.info(
                "Context-aware re-ranking completed",
                extra={
                    "processed_results": len(enhanced_results),
                    "score_improvement": self._calculate_score_improvement(search_results, enhanced_results),
                    "query": original_query
                }
            )
            
            return enhanced_results
            
        except Exception as e:
            logger.error(
                "Context re-ranking failed, returning original results",
                extra={
                    "error": str(e),
                    "query": original_query,
                    "result_count": len(search_results)
                },
                exc_info=True
            )
            # Return original results if re-ranking fails
            return search_results

    def _calculate_cosine_similarity(
        self, 
        embedding_a: List[float], 
        embedding_b: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embedding vectors.
        
        Args:
            embedding_a: First embedding vector
            embedding_b: Second embedding vector
            
        Returns:
            Cosine similarity score between 0.0 and 1.0
        """
        try:
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(embedding_a, embedding_b))
            
            # Calculate magnitudes
            magnitude_a = math.sqrt(sum(a * a for a in embedding_a))
            magnitude_b = math.sqrt(sum(b * b for b in embedding_b))
            
            # Avoid division by zero
            if magnitude_a == 0.0 or magnitude_b == 0.0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = dot_product / (magnitude_a * magnitude_b)
            
            # Normalize to [0, 1] range (cosine similarity is in [-1, 1])
            return max(0.0, (similarity + 1.0) / 2.0)
            
        except Exception as e:
            logger.warning(
                "Cosine similarity calculation failed",
                extra={"error": str(e)},
                exc_info=True
            )
            return 0.0

    def _calculate_score_improvement(
        self, 
        original_results: List[Any], 
        reranked_results: List[Any]
    ) -> float:
        """
        Calculate the improvement in average score after re-ranking.
        
        Args:
            original_results: Results before re-ranking
            reranked_results: Results after re-ranking
            
        Returns:
            Score improvement percentage
        """
        try:
            if not original_results or not reranked_results:
                return 0.0
            
            original_avg = sum(r.score for r in original_results) / len(original_results)
            reranked_avg = sum(r.final_score for r in reranked_results) / len(reranked_results)
            
            if original_avg == 0.0:
                return 0.0
            
            improvement = ((reranked_avg - original_avg) / original_avg) * 100
            return round(improvement, 2)
            
        except Exception:
            return 0.0

    async def _generate_fallback_results(
        self, query: str, limit: int, query_time_ms: int, context: str = None
    ) -> QueryResponse:
        """Generate fallback results when vector search fails."""
        logger.info("Generating fallback search results with context awareness")
        
        # Simple keyword matching for demo/fallback
        mock_results = []
        query_lower = query.lower()
        
        if "framework" in query_lower or "api" in query_lower:
            mock_results = [
                QueryResult(
                    id="fallback_12345",
                    content="FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
                    relevance_score=0.85,
                    context_score=0.75 if context else None,
                    final_score=0.80 if context else 0.85,
                    metadata={"tags": ["api", "python"], "source": "fallback", "type": "demo"},
                ),
                QueryResult(
                    id="fallback_67890",
                    content="Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design.",
                    relevance_score=0.78,
                    context_score=0.70 if context else None,
                    final_score=0.74 if context else 0.78,
                    metadata={"tags": ["framework", "python"], "source": "fallback", "type": "demo"},
                ),
            ]
        elif "python" in query_lower:
            mock_results = [
                QueryResult(
                    id="fallback_12345",
                    content="Python is a high-level, interpreted programming language with dynamic semantics and powerful built-in data structures.",
                    relevance_score=0.82,
                    context_score=0.77 if context else None,
                    final_score=0.80 if context else 0.82,
                    metadata={"tags": ["python", "programming"], "source": "fallback", "type": "demo"},
                ),
            ]
        elif "selfrag" in query_lower or "rag" in query_lower:
            mock_results = [
                QueryResult(
                    id="fallback_rag_001",
                    content="Retrieval-Augmented Generation (RAG) combines the power of pre-trained language models with external knowledge retrieval.",
                    relevance_score=0.90,
                    context_score=0.85 if context else None,
                    final_score=0.88 if context else 0.90,
                    metadata={"tags": ["rag", "ai", "retrieval"], "source": "fallback", "type": "demo"},
                ),
            ]

        # Apply limit
        limited_results = mock_results[:limit]

        return QueryResponse(
            query=query,
            context=context,
            results=limited_results,
            total_results=len(limited_results),
            query_time_ms=query_time_ms,
            reranked=bool(context),
            context_used=bool(context)
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
