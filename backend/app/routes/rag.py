"""
RAG Pipeline specific endpoints for vector operations and statistics.

Provides additional RAG-focused endpoints for:
- Collection statistics and health
- Document management
- Vector search operations
- RAG pipeline monitoring
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.vector_service import VectorService
from ..services.embedding_service import EmbeddingService
from ..logging_utils import get_logger

router = APIRouter(tags=["RAG Pipeline"])
vector_service = VectorService()
embedding_service = EmbeddingService()
logger = get_logger(__name__)


# Response Models for RAG endpoints
class CollectionStatsResponse(BaseModel):
    """Response for collection statistics."""
    collection_name: str = Field(..., description="Name of the vector collection")
    points_count: int = Field(..., description="Total number of vectors stored")
    vectors_count: int = Field(..., description="Number of indexed vectors")
    vector_size: int = Field(..., description="Dimension of vectors")
    status: str = Field(..., description="Collection status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "collection_name": "documents",
                "points_count": 42,
                "vectors_count": 42,
                "vector_size": 384,
                "status": "green"
            }
        }


class RAGHealthResponse(BaseModel):
    """Response for RAG pipeline health check."""
    status: str = Field(..., description="Overall RAG pipeline status")
    embedding_service: str = Field(..., description="Embedding service status")
    vector_database: str = Field(..., description="Vector database status")
    checks_passed: int = Field(..., description="Number of successful health checks")
    total_checks: int = Field(..., description="Total number of health checks")
    timestamp: str = Field(..., description="Health check timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "embedding_service": "healthy",
                "vector_database": "healthy",
                "checks_passed": 2,
                "total_checks": 2,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class DocumentDeleteResponse(BaseModel):
    """Response for document deletion."""
    document_id: str = Field(..., description="ID of the deleted document")
    deleted: bool = Field(..., description="Whether deletion was successful")
    timestamp: str = Field(..., description="Deletion timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_12345",
                "deleted": True,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


@router.get(
    "/health",
    response_model=RAGHealthResponse,
    summary="RAG pipeline health check",
    description="""
    Comprehensive health check for the entire RAG pipeline.
    
    **Health Checks:**
    - Embedding service availability and model loading
    - Vector database connectivity and collection status
    - Pipeline component integration
    
    **Use Cases:**
    - System monitoring and alerting
    - Troubleshooting RAG pipeline issues
    - Deployment verification
    """
)
async def rag_health_check():
    """Check the health of the entire RAG pipeline."""
    start_time = time.time()
    checks_passed = 0
    total_checks = 2
    
    try:
        logger.info("Starting RAG pipeline health check")
        
        # Check embedding service
        try:
            test_embedding = await embedding_service.generate_embedding("health check test")
            embedding_status = "healthy" if len(test_embedding) == 384 else "unhealthy"
            if embedding_status == "healthy":
                checks_passed += 1
        except Exception as e:
            logger.warning(f"Embedding service health check failed: {e}")
            embedding_status = "unhealthy"
        
        # Check vector database
        try:
            collection_exists = await vector_service.ensure_collection_exists()
            vector_status = "healthy" if collection_exists else "unhealthy"
            if vector_status == "healthy":
                checks_passed += 1
        except Exception as e:
            logger.warning(f"Vector database health check failed: {e}")
            vector_status = "unhealthy"
        
        # Determine overall status
        overall_status = "healthy" if checks_passed == total_checks else "degraded"
        
        health_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "RAG pipeline health check completed",
            extra={
                "health_check_time_ms": health_time_ms,
                "overall_status": overall_status,
                "checks_passed": checks_passed,
                "total_checks": total_checks
            }
        )
        
        return RAGHealthResponse(
            status=overall_status,
            embedding_service=embedding_status,
            vector_database=vector_status,
            checks_passed=checks_passed,
            total_checks=total_checks,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(
            "RAG pipeline health check failed",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Health check failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        ) from e


@router.get(
    "/collections/stats",
    response_model=CollectionStatsResponse,
    summary="Get vector collection statistics",
    description="""
    Retrieve detailed statistics about the vector collection.
    
    **Statistics Include:**
    - Total number of document chunks stored
    - Vector indexing status
    - Collection health and performance metrics
    
    **Use Cases:**
    - Monitoring data ingestion progress
    - Capacity planning and optimization
    - Performance analysis
    """
)
async def get_collection_stats():
    """Get statistics about the vector collection."""
    try:
        logger.info("Retrieving collection statistics")
        
        stats = await vector_service.get_collection_stats()
        
        if "error" in stats:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Vector database unavailable",
                    "message": stats["error"],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        logger.info(
            "Collection statistics retrieved successfully",
            extra={
                "collection_name": stats["collection_name"],
                "points_count": stats.get("points_count", 0),
                "vectors_count": stats.get("vectors_count", 0)
            }
        )
        
        return CollectionStatsResponse(
            collection_name=stats["collection_name"],
            points_count=stats.get("points_count", 0),
            vectors_count=stats.get("vectors_count", 0),
            vector_size=stats["vector_size"],
            status=stats.get("status", "unknown")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve collection statistics",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Statistics retrieval failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        ) from e


@router.delete(
    "/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete document from RAG pipeline",
    description="""
    Delete all chunks and vectors associated with a specific document.
    
    **Deletion Process:**
    - Removes all document chunks from vector database
    - Cleans up associated metadata
    - Maintains collection integrity
    
    **Use Cases:**
    - Content management and cleanup
    - Data privacy compliance (GDPR, etc.)
    - Updating outdated information
    """
)
async def delete_document(document_id: str):
    """Delete a document and all its chunks from the RAG pipeline."""
    try:
        logger.info(
            "Deleting document from RAG pipeline",
            extra={"document_id": document_id}
        )
        
        success = await vector_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Document not found or deletion failed",
                    "document_id": document_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        logger.info(
            "Document deleted successfully from RAG pipeline",
            extra={"document_id": document_id}
        )
        
        return DocumentDeleteResponse(
            document_id=document_id,
            deleted=True,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Document deletion failed",
            extra={
                "document_id": document_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Document deletion failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        ) from e
