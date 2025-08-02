"""
Health check endpoints for monitoring service status and performance metrics.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request
from ..services.embedding_service import EmbeddingService
from ..services.vector_service import VectorService
from ..database.connection import get_database_pools
from ..logging_utils import get_logger
from ..startup_check import service_checker

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)


@router.get("/liveness")
async def liveness():
    """Simple liveness probe for container orchestration."""
    logger.debug("Liveness probe accessed")
    return {"status": "alive"}


@router.get("/readiness")
async def readiness():
    """Comprehensive readiness probe with dependency checks."""
    logger.debug("Readiness probe accessed")
    
    try:
        # Run all service checks
        results = await service_checker.check_all_services()
        
        if results["overall_status"] == "healthy":
            logger.debug("All services healthy", extra={
                "postgres": results["services"]["postgres"]["status"],
                "redis": results["services"]["redis"]["status"],
                "qdrant": results["services"]["qdrant"]["status"],
                "localai": results["services"]["localai"]["status"]
            })
            return {
                "status": "ready",
                "services": results["services"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            logger.warning("Some services unhealthy", extra={
                "postgres": results["services"]["postgres"]["status"],
                "redis": results["services"]["redis"]["status"],
                "qdrant": results["services"]["qdrant"]["status"],
                "localai": results["services"]["localai"]["status"]
            })
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "services": results["services"],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
    except Exception as e:
        logger.error("Readiness check failed", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.get("/")
async def health():
    """Basic health check endpoint with service status."""
    logger.debug("Health check accessed")
    
    try:
        # Quick service checks (non-blocking)
        results = await service_checker.check_all_services()
        
        return {
            "status": "healthy",
            "overall_status": results["overall_status"],
            "services": {
                "postgres": results["services"]["postgres"]["status"],
                "redis": results["services"]["redis"]["status"],
                "qdrant": results["services"]["qdrant"]["status"],
                "localai": results["services"]["localai"]["status"]
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)}, exc_info=True)
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.get("/services")
async def services_detailed():
    """Detailed service status with comprehensive information."""
    logger.debug("Detailed services check accessed")
    
    try:
        results = await service_checker.check_all_services()
        return {
            "overall_status": results["overall_status"],
            "services": results["services"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error("Detailed services check failed", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.post("/test-postgres-write")
async def test_postgres_write():
    """Test PostgreSQL write operations by inserting dummy data."""
    logger.debug("PostgreSQL write test accessed")
    
    try:
        result = await service_checker.log_dummy_ingest()
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": "PostgreSQL write test successful",
                "data": result,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "failed",
                    "message": "PostgreSQL write test failed",
                    "error": result.get("error"),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
    except Exception as e:
        logger.error("PostgreSQL write test failed", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.get(
    "/llm",
    responses={
        200: {"description": "LLM service is healthy and operational"},
        503: {"description": "LLM service is unhealthy or unavailable"},
    },
    summary="Check LLM service health",
    description="""
    **Comprehensive LLM service health check with operational verification.**
    
    This endpoint performs a thorough health check of the LocalAI service by:
    1. Testing basic connectivity to LocalAI
    2. Verifying model availability with `list_models()`
    3. Testing embedding functionality with `embed('test')`
    
    **Health Check Process:**
    - **Connection Test**: Verifies LocalAI service is reachable
    - **Model Availability**: Lists available models to ensure service is functional
    - **Embedding Test**: Performs a lightweight embedding operation to verify inference capabilities
    
    **Use Cases:**
    - Verify LLM service operational status before processing workloads
    - Integration testing and service monitoring
    - Troubleshooting LLM connectivity issues
    - Production readiness verification
    
    **Response Codes:**
    - 200: LLM service is fully operational with all capabilities verified
    - 503: LLM service is unavailable or has limited functionality
    """,
)
async def llm_health_check():
    """Comprehensive LLM health check with model listing and embedding tests."""
    logger.info("LLM health check requested")
    
    # Import here to avoid circular imports
    from ..localai_client import localai_client
    
    health_status = {
        "status": "healthy",
        "service": "LocalAI",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "connectivity": {"status": "unknown", "message": ""},
            "models": {"status": "unknown", "message": "", "count": 0},
            "embedding": {"status": "unknown", "message": ""}
        }
    }
    
    try:
        # Test 1: Basic connectivity check
        logger.debug("Testing LocalAI connectivity")
        is_healthy = await localai_client.health_check()
        
        if is_healthy:
            health_status["checks"]["connectivity"]["status"] = "healthy"
            health_status["checks"]["connectivity"]["message"] = "LocalAI service is reachable"
            logger.debug("LocalAI connectivity check passed")
        else:
            health_status["checks"]["connectivity"]["status"] = "unhealthy"
            health_status["checks"]["connectivity"]["message"] = "LocalAI service is not responding"
            logger.warning("LocalAI connectivity check failed")
        
        # Test 2: Model listing check
        logger.debug("Testing model availability")
        try:
            models = await localai_client.list_models()
            model_count = len(models)
            
            if model_count > 0:
                health_status["checks"]["models"]["status"] = "healthy"
                health_status["checks"]["models"]["message"] = f"Found {model_count} available models"
                health_status["checks"]["models"]["count"] = model_count
                health_status["checks"]["models"]["models"] = [model.name for model in models[:5]]  # Show first 5 models
                logger.debug(f"Model listing check passed: {model_count} models available")
            else:
                health_status["checks"]["models"]["status"] = "warning"
                health_status["checks"]["models"]["message"] = "No models available"
                health_status["checks"]["models"]["count"] = 0
                logger.warning("Model listing check: no models found")
                
        except Exception as e:
            health_status["checks"]["models"]["status"] = "unhealthy"
            health_status["checks"]["models"]["message"] = f"Model listing failed: {str(e)}"
            logger.error(f"Model listing check failed: {str(e)}")
        
        # Test 3: Embedding functionality check
        logger.debug("Testing embedding functionality")
        try:
            # Use a simple test string for embedding
            test_text = "test"
            embedding_result = await localai_client.embed(test_text)
            
            # The embed method returns List[float] directly, not an object with .embedding attribute
            if embedding_result and isinstance(embedding_result, list) and len(embedding_result) > 0:
                embedding_dims = len(embedding_result)
                health_status["checks"]["embedding"]["status"] = "healthy"
                health_status["checks"]["embedding"]["message"] = f"Embedding generation successful ({embedding_dims} dimensions)"
                health_status["checks"]["embedding"]["dimensions"] = embedding_dims
                logger.debug(f"Embedding check passed: {embedding_dims} dimensions")
            else:
                health_status["checks"]["embedding"]["status"] = "unhealthy"
                health_status["checks"]["embedding"]["message"] = "Embedding generation returned empty result"
                logger.warning("Embedding check failed: empty result")
                
        except Exception as e:
            health_status["checks"]["embedding"]["status"] = "unhealthy"
            health_status["checks"]["embedding"]["message"] = f"Embedding test failed: {str(e)}"
            logger.error(f"Embedding check failed: {str(e)}")
        
        # Determine overall health status
        check_statuses = [check["status"] for check in health_status["checks"].values()]
        
        if all(status == "healthy" for status in check_statuses):
            health_status["status"] = "healthy"
            health_status["message"] = "All LLM service checks passed"
            logger.info("LLM health check: all checks passed")
            return health_status
        elif any(status == "unhealthy" for status in check_statuses):
            health_status["status"] = "unhealthy"
            health_status["message"] = "One or more LLM service checks failed"
            logger.warning("LLM health check: some checks failed")
            raise HTTPException(
                status_code=503,
                detail=health_status
            )
        else:
            health_status["status"] = "degraded"
            health_status["message"] = "LLM service has limited functionality"
            logger.warning("LLM health check: degraded functionality")
            return health_status
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "LLM health check error",
            extra={"error": str(e)},
            exc_info=True
        )
        health_status["status"] = "error"
        health_status["message"] = f"Health check failed: {str(e)}"
        raise HTTPException(
            status_code=503,
            detail=health_status
        ) from e


@router.get(
    "/metrics",
    summary="Performance Metrics",
    description="""
    **Get comprehensive performance metrics and cache analytics.**
    
    Returns real-time performance data including:
    - Request timing and throughput statistics
    - Cache hit rates and effectiveness
    - Database connection pool health
    - Response compression statistics
    - Slow request monitoring
    
    **Use Cases:**
    - Performance monitoring and optimization
    - Cache effectiveness analysis
    - System health assessment
    - Capacity planning and scaling decisions
    """
)
async def get_performance_metrics(request: Request) -> Dict[str, Any]:
    """Get comprehensive performance metrics and system statistics."""
    try:
        logger.debug("Performance metrics requested")
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "performance": {},
            "cache": {},
            "database_pools": {},
            "system": {}
        }
        
        # Get performance middleware metrics if available
        try:
            # Check if performance middleware is available
            app = request.app
            for middleware in app.user_middleware:
                if hasattr(middleware[0], 'get_metrics'):
                    performance_metrics = middleware[0].get_metrics()
                    metrics["performance"] = performance_metrics
                    break
            else:
                metrics["performance"] = {"error": "Performance middleware not found"}
        except Exception as e:
            logger.warning(f"Failed to get performance metrics: {str(e)}")
            metrics["performance"] = {"error": str(e)}
        
        # Get database connection pool metrics
        try:
            pools = get_database_pools()
            pool_stats = await pools.get_pool_stats()
            metrics["database_pools"] = pool_stats
        except Exception as e:
            logger.warning(f"Failed to get database pool metrics: {str(e)}")
            metrics["database_pools"] = {"error": str(e)}
        
        # Get cache service metrics if available
        try:
            from ..services.cache_service import CacheService
            cache_service = CacheService()
            cache_stats = await cache_service.get_cache_analytics()
            metrics["cache"] = cache_stats
        except Exception as e:
            logger.warning(f"Failed to get cache metrics: {str(e)}")
            metrics["cache"] = {"error": str(e)}
        
        # Get basic system information
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            metrics["system"] = {
                "cpu_percent": psutil.cpu_percent(),
                "memory": {
                    "rss": memory_info.rss,
                    "vms": memory_info.vms,
                    "percent": process.memory_percent()
                },
                "process_id": os.getpid(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
            }
        except ImportError:
            # psutil not available
            metrics["system"] = {"error": "psutil not available - install for system metrics"}
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {str(e)}")
            metrics["system"] = {"error": str(e)}
        
        logger.info("Performance metrics collected successfully")
        return metrics
        
    except Exception as e:
        logger.error(
            "Failed to collect performance metrics",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to collect performance metrics", "details": str(e)}
        ) from e


@router.get(
    "/cache/analytics",
    summary="Cache Analytics",
    description="""
    **Get detailed cache performance analytics.**
    
    Returns comprehensive cache statistics including:
    - L1 (memory) and L2 (Redis) cache hit rates
    - Cache size and memory usage
    - Most frequently accessed items
    - Cache invalidation patterns
    - Performance impact metrics
    """
)
async def get_cache_analytics() -> Dict[str, Any]:
    """Get detailed cache performance analytics."""
    try:
        logger.debug("Cache analytics requested")
        
        from ..services.cache_service import CacheService
        cache_service = CacheService()
        
        analytics = await cache_service.get_cache_analytics()
        analytics["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        logger.info("Cache analytics collected successfully")
        return analytics
        
    except Exception as e:
        logger.error(
            "Failed to get cache analytics",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to get cache analytics", "details": str(e)}
        ) from e


@router.post(
    "/cache/clear",
    summary="Clear Cache",
    description="""
    **Clear all cached data for performance testing or troubleshooting.**
    
    This endpoint clears both L1 (memory) and L2 (Redis) caches.
    Use with caution as this will cause temporary performance degradation
    while caches rebuild.
    """
)
async def clear_cache() -> Dict[str, Any]:
    """Clear all cached data."""
    try:
        logger.info("Cache clear requested")
        
        from ..services.cache_service import CacheService
        cache_service = CacheService()
        
        # Clear both L1 and L2 caches
        l1_cleared = await cache_service.clear_l1_cache()
        l2_cleared = await cache_service.clear_l2_cache()
        
        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "l1_cache_cleared": l1_cleared,
            "l2_cache_cleared": l2_cleared,
            "status": "success" if (l1_cleared and l2_cleared) else "partial"
        }
        
        logger.info("Cache cleared successfully", extra=result)
        return result
        
    except Exception as e:
        logger.error(
            "Failed to clear cache",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to clear cache", "details": str(e)}
        ) from e