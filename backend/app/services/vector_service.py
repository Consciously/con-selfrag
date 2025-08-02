"""
Vector database service for Qdrant integration.

This service handles all vector database operations including
embedding storage, similarity search, and metadata filtering.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, CreateCollection,
    PointStruct, Filter, FieldCondition, MatchValue,
    SearchRequest, ScoredPoint
)

from .document_processor import DocumentChunk
from ..config import config
from ..logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Represents a search result from vector database."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    chunk_id: str
    document_id: str


class VectorService:
    """Service for vector database operations using Qdrant."""
    
    def __init__(self):
        """Initialize Qdrant client and configuration."""
        self.client = None
        self.collection_name = "documents"
        self.vector_size = 384  # Default for sentence-transformers/all-MiniLM-L6-v2
        self._ensure_connection()
    
    def _ensure_connection(self):
        """Ensure Qdrant client is connected."""
        try:
            # Connect to Qdrant (adjust host/port based on your docker-compose setup)
            qdrant_host = getattr(config, 'qdrant_host', 'localhost')
            qdrant_port = getattr(config, 'qdrant_port', 6333)
            
            self.client = QdrantClient(
                host=qdrant_host,
                port=qdrant_port,
                timeout=30.0
            )
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(
                "Connected to Qdrant successfully",
                extra={
                    "host": qdrant_host,
                    "port": qdrant_port,
                    "collections_count": len(collections.collections)
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to connect to Qdrant",
                extra={"error": str(e)},
                exc_info=True
            )
            # Continue without connection for now - can be handled gracefully
            self.client = None
    
    async def ensure_collection_exists(self) -> bool:
        """
        Ensure the documents collection exists in Qdrant.
        
        Returns:
            True if collection exists or was created successfully
        """
        try:
            if not self.client:
                logger.warning("Qdrant client not available")
                return False
            
            # Check if collection exists
            try:
                collection_info = self.client.get_collection(self.collection_name)
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
            self.client.create_collection(
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
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Store document chunks with their embeddings in Qdrant.
        
        Args:
            chunks: List of DocumentChunk objects
            embeddings: List of embedding vectors corresponding to chunks
            
        Returns:
            True if storage was successful
        """
        try:
            if not self.client:
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
            operation_info = self.client.upsert(
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
            if not self.client:
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
            search_results = self.client.search(
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
            if not self.client:
                logger.warning("Qdrant client not available")
                return False
            
            # Delete by filter
            filter_condition = Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            )
            
            operation_info = self.client.delete(
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
            if not self.client:
                return {"error": "Qdrant client not available"}
            
            collection_info = self.client.get_collection(self.collection_name)
            
            stats = {
                "collection_name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
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
    
    def close(self):
        """Close the Qdrant client connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("Closed Qdrant client connection")
            except Exception as e:
                logger.error(
                    "Error closing Qdrant client",
                    extra={"error": str(e)}
                )
