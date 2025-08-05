"""
Comprehensive system status and monitoring endpoint for service health dashboard.
Aggregates all services including database connections, vector DB, Redis, and LocalAI.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..config import config
from ..database.connection import get_database_pools
from ..logging_utils import get_logger
from ..startup_check import service_checker
from .metrics import router as metrics_router

# Import gRPC health check function
try:
    from ..grpc.server import get_grpc_health_status
except ImportError:
    async def get_grpc_health_status():
        return {
            "status": "unavailable",
            "port": None,
            "message": "gRPC server not configured"
        }

router = APIRouter(tags=["System Status"])
logger = get_logger(__name__)

# Include metrics sub-router
router.include_router(metrics_router)


class ServiceStatus(BaseModel):
    """Individual service status model."""
    status: str = Field(..., description="Service status: healthy, unhealthy, degraded, unknown")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    message: Optional[str] = Field(None, description="Status message or error details")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional service details")


class SystemStatus(BaseModel):
    """Complete system status response model."""
    status: str = Field(..., description="Overall system status")
    timestamp: str = Field(..., description="Status check timestamp")
    uptime_seconds: Optional[float] = Field(None, description="Application uptime in seconds")
    version: str = Field(default="2.0.0", description="Application version")
    
    # Service statuses
    database: ServiceStatus = Field(..., description="PostgreSQL database status")
    cache: ServiceStatus = Field(..., description="Redis cache status") 
    vector_db: ServiceStatus = Field(..., description="Qdrant vector database status")
    llm_service: ServiceStatus = Field(..., description="LocalAI LLM service status")
    grpc_service: ServiceStatus = Field(..., description="gRPC service status")
    
    # System metrics
    system_metrics: Optional[Dict[str, Any]] = Field(None, description="System performance metrics")


# Track application start time for uptime calculation
app_start_time = time.time()


async def check_service_with_timing(service_name: str, check_function) -> ServiceStatus:
    """Execute a service check with timing measurements."""
    start_time = time.time()
    
    try:
        result = await check_function()
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return ServiceStatus(
            status=result.get("status", "unknown"),
            response_time_ms=round(response_time, 2),
            message=result.get("message", ""),
            details={
                k: v for k, v in result.items() 
                if k not in ["status", "message"]
            }
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Service check failed for {service_name}", extra={"error": str(e)}, exc_info=True)
        
        return ServiceStatus(
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            message=f"Service check failed: {str(e)}",
            details={"error_type": type(e).__name__}
        )


async def get_system_metrics() -> Dict[str, Any]:
    """Collect system performance metrics."""
    try:
        import psutil
        
        # Get CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get database pool metrics if available
        pools = get_database_pools()
        pool_metrics = {}
        
        if hasattr(pools, 'postgres_pool') and pools.postgres_pool:
            pool_metrics["postgres_pool"] = {
                "size": pools.postgres_pool.get_size(),
                "active_connections": len(pools.postgres_pool._holders) if hasattr(pools.postgres_pool, '_holders') else None
            }
        
        if hasattr(pools, 'redis_pool') and pools.redis_pool:
            pool_metrics["redis_pool"] = {
                "max_connections": pools.redis_pool.max_connections if hasattr(pools.redis_pool, 'max_connections') else None,
                "created_connections": pools.redis_pool.created_connections if hasattr(pools.redis_pool, 'created_connections') else None
            }
        
        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round((disk.used / disk.total) * 100, 1)
            },
            "connection_pools": pool_metrics
        }
    except ImportError:
        # psutil not available
        return {"note": "psutil not installed - system metrics unavailable"}
    except Exception as e:
        logger.warning(f"Failed to collect system metrics: {str(e)}")
        return {"error": f"Metrics collection failed: {str(e)}"}


@router.get(
    "/",
    response_model=SystemStatus,
    summary="Comprehensive system status dashboard",
    description="""
    **Comprehensive system status endpoint aggregating all service health information.**
    
    This endpoint provides a unified view of all system components including:
    - **Database Connections**: PostgreSQL connection health and pool status
    - **Cache Layer**: Redis availability and connection metrics  
    - **Vector Database**: Qdrant status and collection information
    - **LLM Service**: LocalAI responsiveness and model availability
    - **gRPC Service**: gRPC server health (if enabled)
    - **System Metrics**: CPU, memory, disk usage, and connection pool metrics
    
    **Response Format:**
    - Overall system status with individual service breakdowns
    - Response time measurements for each service
    - Detailed error messages for failed services
    - System performance metrics and resource utilization
    - Application uptime and version information
    
    **Status Values:**
    - `healthy`: Service is fully operational
    - `degraded`: Service has limited functionality
    - `unhealthy`: Service is unavailable or failing
    - `unknown`: Service status could not be determined
    
    **Use Cases:**
    - Monitoring dashboard integration
    - Health check automation
    - Performance monitoring
    - Troubleshooting service issues
    - Load balancer health checks
    """
)
async def system_status(request: Request) -> SystemStatus:
    """Get comprehensive system status with all service health information."""
    logger.info("System status dashboard accessed")
    
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat() + "Z"
    uptime = time.time() - app_start_time
    
    try:
        # Run all service checks with timing
        logger.debug("Running comprehensive service checks with timing")
        
        # Check database services
        database_status = await check_service_with_timing("PostgreSQL", service_checker.check_postgres)
        redis_status = await check_service_with_timing("Redis", service_checker.check_redis)
        qdrant_status = await check_service_with_timing("Qdrant", service_checker.check_qdrant)
        localai_status = await check_service_with_timing("LocalAI", service_checker.check_localai)
        grpc_status = await check_service_with_timing("gRPC", get_grpc_health_status)
        
        # Collect system metrics
        system_metrics = await get_system_metrics()
        
        # Determine overall system status
        service_statuses = [
            database_status.status,
            redis_status.status, 
            qdrant_status.status,
            localai_status.status
        ]
        
        if all(status == "healthy" for status in service_statuses):
            overall_status = "healthy"
        elif any(status == "unhealthy" for status in service_statuses):
            overall_status = "degraded"
        else:
            overall_status = "degraded"
        
        # Log status check completion
        total_time = (time.time() - start_time) * 1000
        logger.info(f"System status check completed", extra={
            "overall_status": overall_status,
            "total_check_time_ms": round(total_time, 2),
            "postgres": database_status.status,
            "redis": redis_status.status,
            "qdrant": qdrant_status.status,
            "localai": localai_status.status,
            "grpc": grpc_status.status
        })
        
        return SystemStatus(
            status=overall_status,
            timestamp=timestamp,
            uptime_seconds=round(uptime, 2),
            version="2.0.0",
            database=database_status,
            cache=redis_status,
            vector_db=qdrant_status,
            llm_service=localai_status,
            grpc_service=grpc_status,
            system_metrics=system_metrics
        )
        
    except Exception as e:
        logger.error("System status check failed", extra={"error": str(e)}, exc_info=True)
        
        # Return degraded status with error information
        return SystemStatus(
            status="unhealthy",
            timestamp=timestamp,
            uptime_seconds=round(uptime, 2),
            version="2.0.0",
            database=ServiceStatus(status="unknown", message="Status check failed"),
            cache=ServiceStatus(status="unknown", message="Status check failed"),
            vector_db=ServiceStatus(status="unknown", message="Status check failed"),
            llm_service=ServiceStatus(status="unknown", message="Status check failed"),
            grpc_service=ServiceStatus(status="unknown", message="Status check failed"),
            system_metrics={"error": f"Metrics collection failed: {str(e)}"}
        )


@router.get(
    "/quick",
    summary="Quick system status check",
    description="""
    **Lightweight system status check for high-frequency monitoring.**
    
    Returns a simplified status overview without detailed metrics or timing information.
    Optimized for load balancers and frequent health checks.
    """
)
async def quick_status() -> Dict[str, Any]:
    """Quick system status check without detailed metrics."""
    logger.debug("Quick status check accessed")
    
    try:
        # Run basic service checks without timing
        results = await service_checker.check_all_services()
        
        return {
            "status": results["overall_status"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "services": {
                service: status["status"] 
                for service, status in results["services"].items()
            }
        }
    except Exception as e:
        logger.error("Quick status check failed", extra={"error": str(e)})
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }
