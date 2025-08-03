"""
Vector database service for Qdrant operations with optimized connection management.

This service handles all vector database operations using Qdrant,
including document storage, similarity search, and collection management
with connection pooling for improved performance.
"""

import asyncio
from typing import List, Optional, Dict, Any
import uuid

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
    from qdrant_client.http.exceptions import UnexpectedResponse
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from ..database.connection import get_qdrant_client
from ..logging_utils import get_logger
from ..config import config

logger = get_logger(__name__)


class SearchResult:
    """Represents a search result from vector similarity search."""
    
    def __init__(self, id: str, content: str, score: float, metadata: Dict[str, Any], 
                 chunk_id: str = "", document_id: str = ""):
        self.id = id
        self.content = content
        self.score = score
        self.metadata = metadata
        self.chunk_id = chunk_id
        self.document_id = document_id


class VectorService:
    """Service for vector database operations using Qdrant with connection pooling."""
    
    def __init__(self, collection_name: str = "documents", vector_size: int = 384):
        """
        Initialize the vector service.
        
        Args:
            collection_name: Name of the Qdrant collection
            vector_size: Size of the embedding vectors
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        logger.info(
            "Initialized VectorService",
            extra={
                "collection": collection_name,
                "vector_size": vector_size
            }
        )
    
    def _get_client(self) -> QdrantClient:
        """Get Qdrant client from connection pool."""
        try:
            return get_qdrant_client()
        except RuntimeError as e:
            logger.error("Failed to get Qdrant client", extra={"error": str(e)})
            return None
    
    async def get_client(self) -> Optional[QdrantClient]:
        """Get Qdrant client (async wrapper for _get_client)."""
        return self._get_client()
    
    async def ensure_collection_exists(self) -> bool:
        """
        Ensure the documents collection exists in Qdrant.
        
        Returns:
            True if collection exists or was created successfully
        """
        try:
            client = await self.get_client()
            if not client:
                logger.warning("Qdrant client not available")
                return False
            
            # Check if collection exists
            try:
                collection_info = client.get_collection(self.collection_name)
                logger.info(
                    "Collection already exists",
                    extra={
                        "collection": self.collection_name,
                        "vectors_count": collection_info.vectors_count
                    }
                )
                return True
            except Exception:
                # Collection doesn't exist, create it
                pass
            
            # Create collection
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(
                "Created Qdrant collection",
                extra={
                    "collection": self.collection_name,
                    "vector_size": self.vector_size
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to ensure collection exists",
                extra={
                    "collection": self.collection_name,
                    "error": str(e)
                },
                exc_info=True
            )
            return False
    
    async def store_chunks(
        self,
        chunks: List[dict],  # TODO: Use DocumentChunk when model is defined
        embeddings: List[List[float]]
    ) -> bool:
        """
        Store document chunks with their embeddings in Qdrant.
        
        Args:
            chunks: List of document chunk dictionaries  # TODO: Use DocumentChunk objects
            embeddings: List of embedding vectors corresponding to chunks
            
        Returns:
            True if storage was successful
        """
        try:
            client = await self.get_client()
            if not client:
                logger.warning("Qdrant client not available - skipping vector storage")
                return False
            
            if len(chunks) != len(embeddings):
                raise ValueError("Number of chunks must match number of embeddings")
            
            # Ensure collection exists
            if not await self.ensure_collection_exists():
                return False
            
            # Prepare points for insertion
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                point = PointStruct(
                    id=str(uuid.uuid4()),  # Generate unique ID for Qdrant
                    vector=embedding,
                    payload={
                        "chunk_id": chunk.id,
                        "content": chunk.content,
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        "token_count": chunk.token_count,
                        **chunk.metadata  # Include all metadata
                    }
                )
                points.append(point)
            
            # Store in Qdrant
            operation_info = client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(
                "Stored chunks in Qdrant",
                extra={
                    "collection": self.collection_name,
                    "chunks_count": len(chunks),
                    "operation_id": operation_info.operation_id if operation_info else None
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to store chunks in Qdrant",
                extra={
                    "chunks_count": len(chunks),
                    "error": str(e)
                },
                exc_info=True
            )
            return False
    
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Optional metadata filters
            
        Returns:
            List of SearchResult objects
        """
        try:
            client = await self.get_client()
            if not client:
                logger.warning("Qdrant client not available - returning empty results")
                return []
            
            # Build filter conditions
            filter_conditions = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                    # Add more filter types as needed
                
                if conditions:
                    filter_conditions = Filter(must=conditions)
            
            # Perform similarity search
            search_results = client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_conditions
            )
            
            # Convert to SearchResult objects
            results = []
            for result in search_results:
                search_result = SearchResult(
                    id=str(result.id),
                    content=result.payload.get("content", ""),
                    score=result.score,
                    metadata={
                        k: v for k, v in result.payload.items() 
                        if k not in ["content", "chunk_id", "document_id"]
                    },
                    chunk_id=result.payload.get("chunk_id", ""),
                    document_id=result.payload.get("document_id", "")
                )
                results.append(search_result)
            
            logger.info(
                "Vector search completed",
                extra={
                    "results_count": len(results),
                    "limit": limit,
                    "score_threshold": score_threshold,
                    "has_filters": bool(filters)
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Vector search failed",
                extra={
                    "limit": limit,
                    "score_threshold": score_threshold,
                    "error": str(e)
                },
                exc_info=True
            )
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks belonging to a document.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            client = await self.get_client()
            if not client:
                logger.warning("Qdrant client not available")
                return False
            
            # Delete by filter
            filter_condition = Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            )
            
            operation_info = client.delete(
                collection_name=self.collection_name,
                points_selector=filter_condition
            )
            
            logger.info(
                "Deleted document from Qdrant",
                extra={
                    "document_id": document_id,
                    "operation_id": operation_info.operation_id if operation_info else None
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete document from Qdrant",
                extra={
                    "document_id": document_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            client = await self.get_client()
            if not client:
                return {"error": "Qdrant client not available"}
            
            collection_info = client.get_collection(self.collection_name)
            
            stats = {
                "collection_name": self.collection_name,
                "vectors_count": getattr(collection_info, 'points_count', 0),
                "indexed_vectors_count": getattr(collection_info, 'indexed_vectors_count', 0),
                "points_count": getattr(collection_info, 'points_count', 0),
                "status": collection_info.status,
                "vector_size": self.vector_size
            }
            
            logger.info("Retrieved collection stats", extra=stats)
            return stats
            
        except Exception as e:
            logger.error(
                "Failed to get collection stats",
                extra={"error": str(e)},
                exc_info=True
            )
            return {"error": str(e)}
