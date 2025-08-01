"""
Health check endpoints for monitoring service status.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
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
