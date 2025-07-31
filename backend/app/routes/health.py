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
                "qdrant": results["services"]["qdrant"]["status"]
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
                "qdrant": results["services"]["qdrant"]["status"]
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
                "qdrant": results["services"]["qdrant"]["status"]
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
