"""
Rate limiting management endpoints for monitoring and administration.

These endpoints provide:
1. Rate limit status checking for administrators
2. Rate limit reset functionality  
3. Global rate limiting statistics
4. Rate limiting configuration information
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..services.rate_limit_service import RateLimitService
from ..middleware.auth import require_admin  # For admin-only endpoints
from ..logging_utils import get_logger

router = APIRouter(prefix="/admin/rate-limits", tags=["Rate Limiting"])
logger = get_logger(__name__)

# Global rate limiting service instance
rate_limit_service = RateLimitService()


# Response Models
class RateLimitStatusResponse(BaseModel):
    """Response for rate limit status checks."""
    identifier: str
    current_usage: Dict[str, int] = Field(description="Current request counts per time window")
    limits: Dict[str, int] = Field(description="Maximum requests allowed per time window")
    remaining: Dict[str, int] = Field(description="Remaining requests per time window")
    reset_times: Dict[str, str] = Field(description="ISO timestamps when limits reset")


class RateLimitResetResponse(BaseModel):
    """Response for rate limit reset operations."""
    success: bool
    identifier: str
    message: str


class GlobalRateLimitStatsResponse(BaseModel):
    """Response for global rate limiting statistics."""
    total_tracked_identifiers: int
    total_active_windows: int
    configurations: Dict[str, Any]
    timestamp: str


class RateLimitConfigResponse(BaseModel):
    """Response for rate limiting configuration."""
    default_config: Dict[str, Any]
    endpoint_configs: Dict[str, Dict[str, Any]]
    user_tier_configs: Dict[str, Dict[str, Any]]


# Request Models
class RateLimitResetRequest(BaseModel):
    """Request to reset rate limits for an identifier."""
    identifier: str = Field(description="IP address or user ID to reset (e.g., 'ip:192.168.1.1' or 'user:123')")
    reason: Optional[str] = Field(None, description="Reason for reset (for audit logging)")


@router.get(
    "/status/{identifier}",
    response_model=RateLimitStatusResponse,
    summary="Get rate limit status for identifier",
    description="""
    Get current rate limiting status for a specific IP address or user ID.
    
    **Admin Access Required**
    
    **Examples:**
    - `/admin/rate-limits/status/ip:192.168.1.1` - Check IP rate limits
    - `/admin/rate-limits/status/user:12345` - Check user rate limits
    
    **Use Cases:**
    - Debugging rate limit issues
    - Monitoring user/IP usage patterns
    - Investigating suspected abuse
    """
)
async def get_rate_limit_status(
    identifier: str,
    admin_user=Depends(require_admin)
) -> RateLimitStatusResponse:
    """Get rate limit status for a specific identifier."""
    try:
        await _ensure_rate_limit_service()
        
        status = await rate_limit_service.get_rate_limit_status(identifier)
        
        if "error" in status:
            raise HTTPException(status_code=500, detail=f"Failed to get rate limit status: {status['error']}")
        
        if status.get("status") == "unavailable":
            raise HTTPException(status_code=503, detail="Rate limiting service unavailable")
        
        logger.info(
            "Rate limit status requested",
            extra={
                "admin_user": admin_user.username,
                "identifier": identifier,
                "status": status
            }
        )
        
        return RateLimitStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get rate limit status",
            extra={"identifier": identifier, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/reset",
    response_model=RateLimitResetResponse,
    summary="Reset rate limits for identifier",
    description="""
    Reset all rate limits for a specific IP address or user ID.
    
    **Admin Access Required**
    
    **Use Cases:**
    - Resolving false positive rate limit triggers
    - Emergency access restoration
    - Testing rate limiting functionality
    
    **Warning:** Use with caution as this removes protection for the identifier.
    """
)
async def reset_rate_limits(
    request: RateLimitResetRequest,
    admin_user=Depends(require_admin)
) -> RateLimitResetResponse:
    """Reset rate limits for a specific identifier."""
    try:
        await _ensure_rate_limit_service()
        
        success = await rate_limit_service.reset_rate_limit(request.identifier)
        
        if success:
            message = f"Rate limits reset successfully for {request.identifier}"
            logger.warning(
                "Rate limits reset by admin",
                extra={
                    "admin_user": admin_user.username,
                    "identifier": request.identifier,
                    "reason": request.reason
                }
            )
        else:
            message = f"Failed to reset rate limits for {request.identifier}"
            logger.error(
                "Rate limit reset failed",
                extra={
                    "admin_user": admin_user.username,
                    "identifier": request.identifier
                }
            )
        
        return RateLimitResetResponse(
            success=success,
            identifier=request.identifier,
            message=message
        )
        
    except Exception as e:
        logger.error(
            "Rate limit reset error",
            extra={
                "identifier": request.identifier,
                "admin_user": admin_user.username,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to reset rate limits: {str(e)}")


@router.get(
    "/statistics",
    response_model=GlobalRateLimitStatsResponse,
    summary="Get global rate limiting statistics", 
    description="""
    Get comprehensive statistics about the rate limiting system.
    
    **Admin Access Required**
    
    **Returns:**
    - Total number of tracked identifiers
    - Active rate limiting windows
    - Configuration summary
    - Current timestamp
    
    **Use Cases:**
    - System monitoring and health checks
    - Capacity planning
    - Performance analysis
    """
)
async def get_global_statistics(
    admin_user=Depends(require_admin)
) -> GlobalRateLimitStatsResponse:
    """Get global rate limiting statistics."""
    try:
        await _ensure_rate_limit_service()
        
        stats = await rate_limit_service.get_global_statistics()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=f"Failed to get statistics: {stats['error']}")
        
        if stats.get("status") == "unavailable":
            raise HTTPException(status_code=503, detail="Rate limiting service unavailable")
        
        logger.info(
            "Global rate limit statistics requested",
            extra={"admin_user": admin_user.username, "stats": stats}
        )
        
        return GlobalRateLimitStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get global rate limit statistics",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/configuration",
    response_model=RateLimitConfigResponse,
    summary="Get rate limiting configuration",
    description="""
    Get current rate limiting configuration including default limits,
    endpoint-specific limits, and user tier configurations.
    
    **Admin Access Required**
    
    **Use Cases:**
    - Understanding current rate limit settings
    - Configuration auditing
    - Troubleshooting rate limit behavior
    """
)
async def get_configuration(
    admin_user=Depends(require_admin)
) -> RateLimitConfigResponse:
    """Get current rate limiting configuration."""
    try:
        await _ensure_rate_limit_service()
        
        # Convert configuration to dictionary format
        default_config = {
            "requests_per_minute": rate_limit_service.default_config.requests_per_minute,
            "requests_per_hour": rate_limit_service.default_config.requests_per_hour,
            "requests_per_day": rate_limit_service.default_config.requests_per_day,
            "burst_allowance": rate_limit_service.default_config.burst_allowance
        }
        
        endpoint_configs = {}
        for endpoint, config in rate_limit_service.endpoint_configs.items():
            endpoint_configs[endpoint] = {
                "requests_per_minute": config.requests_per_minute,
                "requests_per_hour": config.requests_per_hour,
                "requests_per_day": config.requests_per_day,
                "burst_allowance": config.burst_allowance
            }
        
        user_tier_configs = {}
        for tier, config in rate_limit_service.user_tier_configs.items():
            user_tier_configs[tier] = {
                "requests_per_minute": config.requests_per_minute,
                "requests_per_hour": config.requests_per_hour,
                "requests_per_day": config.requests_per_day,
                "burst_allowance": config.burst_allowance
            }
        
        logger.info(
            "Rate limit configuration requested",
            extra={"admin_user": admin_user.username}
        )
        
        return RateLimitConfigResponse(
            default_config=default_config,
            endpoint_configs=endpoint_configs,
            user_tier_configs=user_tier_configs
        )
        
    except Exception as e:
        logger.error(
            "Failed to get rate limit configuration",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Health check endpoint for rate limiting service
@router.get(
    "/health",
    summary="Rate limiting service health check",
    description="""
    Check if the rate limiting service is healthy and connected to Redis.
    
    **Admin Access Required**
    
    **Returns:**
    - Service status
    - Redis connection status
    - Service initialization status
    """
)
async def health_check(
    admin_user=Depends(require_admin)
) -> Dict[str, Any]:
    """Check rate limiting service health."""
    try:
        status = {
            "service": "rate_limiting",
            "status": "unknown",
            "redis_connected": False,
            "initialized": False,
            "timestamp": None
        }
        
        if rate_limit_service.redis_client:
            try:
                await rate_limit_service.redis_client.ping()
                status["redis_connected"] = True
                status["initialized"] = True
                status["status"] = "healthy"
            except Exception as e:
                status["status"] = "unhealthy"
                status["error"] = f"Redis connection failed: {str(e)}"
        else:
            status["status"] = "unhealthy"
            status["error"] = "Redis client not initialized"
        
        from datetime import datetime
        status["timestamp"] = datetime.utcnow().isoformat()
        
        logger.info(
            "Rate limiting health check",
            extra={"admin_user": admin_user.username, "status": status}
        )
        
        return status
        
    except Exception as e:
        logger.error(
            "Rate limiting health check failed",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            "service": "rate_limiting",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def _ensure_rate_limit_service():
    """Ensure rate limiting service is initialized."""
    if not rate_limit_service.redis_client:
        success = await rate_limit_service.initialize()
        if not success:
            raise HTTPException(
                status_code=503, 
                detail="Rate limiting service unavailable - Redis connection failed"
            )
