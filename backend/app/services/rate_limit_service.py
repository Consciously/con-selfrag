"""
Redis-based rate limiting service for API protection.

This service provides:
1. Per-IP rate limiting with sliding window
2. Per-user rate limiting for authenticated users  
3. Per-endpoint rate limiting for specific routes
4. Configurable time windows and request limits
5. Redis-backed distributed rate limiting
"""

import time
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import redis.asyncio as redis

from ..database.connection import get_database_pools
from ..logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting rules."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_allowance: int = 0  # Extra requests allowed in short bursts
    window_size: int = 60  # Sliding window size in seconds


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    requests_remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None  # Seconds to wait before retrying
    limit_exceeded_type: Optional[str] = None  # 'minute', 'hour', 'day'


class RateLimitService:
    """Redis-based rate limiting service with sliding window algorithm."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        
        # Default rate limiting configurations
        self.default_config = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_allowance=10
        )
        
        # Endpoint-specific configurations
        self.endpoint_configs: Dict[str, RateLimitConfig] = {
            # Authentication endpoints - more restrictive
            "POST /auth/register": RateLimitConfig(
                requests_per_minute=5,
                requests_per_hour=20,
                requests_per_day=100,
                burst_allowance=2
            ),
            "POST /auth/login": RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=50,
                requests_per_day=200,
                burst_allowance=3
            ),
            
            # Query endpoints - moderate limits
            "POST /query": RateLimitConfig(
                requests_per_minute=30,
                requests_per_hour=500,
                requests_per_day=5000,
                burst_allowance=5
            ),
            
            # Ingestion endpoints - more restrictive (resource intensive)
            "POST /ingest": RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=1000,
                burst_allowance=2
            ),
            
            # Health check endpoints - generous limits
            "GET /health": RateLimitConfig(
                requests_per_minute=120,
                requests_per_hour=2000,
                requests_per_day=20000,
                burst_allowance=20
            ),
        }
        
        # User tier configurations (for authenticated users)
        self.user_tier_configs: Dict[str, RateLimitConfig] = {
            "free": RateLimitConfig(
                requests_per_minute=30,
                requests_per_hour=300,
                requests_per_day=1000,
                burst_allowance=5
            ),
            "premium": RateLimitConfig(
                requests_per_minute=100,
                requests_per_hour=2000,
                requests_per_day=20000,
                burst_allowance=20
            ),
            "admin": RateLimitConfig(
                requests_per_minute=1000,
                requests_per_hour=10000,
                requests_per_day=100000,
                burst_allowance=100
            )
        }
    
    async def initialize(self) -> bool:
        """Initialize Redis connection for rate limiting."""
        try:
            db_pools = get_database_pools()
            if not db_pools or not db_pools.redis_pool:
                logger.error("Redis pool not available for rate limiting")
                return False
                
            self.redis_client = redis.Redis(connection_pool=db_pools.redis_pool)
            
            # Test the connection
            await self.redis_client.ping()
            
            logger.info("Rate limiting service initialized with Redis backend")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize rate limiting service", 
                        extra={"error": str(e)}, exc_info=True)
            return False
    
    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
        user_tier: Optional[str] = None
    ) -> RateLimitResult:
        """
        Check if request is within rate limits using sliding window algorithm.
        
        Args:
            identifier: IP address or user ID for rate limiting
            endpoint: Specific endpoint being accessed (e.g., "POST /query")
            user_tier: User tier for authenticated users ("free", "premium", "admin")
        
        Returns:
            RateLimitResult with allowed status and metadata
        """
        if not self.redis_client:
            # Fail open if Redis is not available
            logger.warning("Rate limiting unavailable - Redis not connected")
            return RateLimitResult(
                allowed=True,
                requests_remaining=999,
                reset_time=datetime.utcnow() + timedelta(minutes=1)
            )
        
        try:
            # Determine configuration to use
            config = self._get_config_for_request(endpoint, user_tier)
            
            # Generate Redis keys for different time windows
            current_time = int(time.time())
            minute_key = f"rate_limit:{identifier}:minute:{current_time // 60}"
            hour_key = f"rate_limit:{identifier}:hour:{current_time // 3600}"
            day_key = f"rate_limit:{identifier}:day:{current_time // 86400}"
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Increment counters for each time window
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)  # Keep for 2 minutes to handle edge cases
            
            pipe.incr(hour_key)
            pipe.expire(hour_key, 7200)  # Keep for 2 hours
            
            pipe.incr(day_key)
            pipe.expire(day_key, 172800)  # Keep for 2 days
            
            # Execute pipeline
            results = await pipe.execute()
            minute_count, hour_count, day_count = results[0], results[2], results[4]
            
            # Check limits in order of severity
            if day_count > config.requests_per_day:
                reset_time = datetime.utcfromtimestamp((current_time // 86400 + 1) * 86400)
                return RateLimitResult(
                    allowed=False,
                    requests_remaining=0,
                    reset_time=reset_time,
                    retry_after=int((reset_time - datetime.utcnow()).total_seconds()),
                    limit_exceeded_type="day"
                )
            
            if hour_count > config.requests_per_hour:
                reset_time = datetime.utcfromtimestamp((current_time // 3600 + 1) * 3600)
                return RateLimitResult(
                    allowed=False,
                    requests_remaining=0,
                    reset_time=reset_time,
                    retry_after=int((reset_time - datetime.utcnow()).total_seconds()),
                    limit_exceeded_type="hour"
                )
            
            # Check minute limit with burst allowance
            effective_minute_limit = config.requests_per_minute + config.burst_allowance
            if minute_count > effective_minute_limit:
                reset_time = datetime.utcfromtimestamp((current_time // 60 + 1) * 60)
                return RateLimitResult(
                    allowed=False,
                    requests_remaining=0,
                    reset_time=reset_time,
                    retry_after=int((reset_time - datetime.utcnow()).total_seconds()),
                    limit_exceeded_type="minute"
                )
            
            # Request allowed - calculate remaining requests
            remaining = min(
                config.requests_per_day - day_count,
                config.requests_per_hour - hour_count,
                effective_minute_limit - minute_count
            )
            
            # Log rate limiting metrics
            await self._log_rate_limit_metrics(
                identifier, endpoint, config, minute_count, hour_count, day_count
            )
            
            return RateLimitResult(
                allowed=True,
                requests_remaining=max(0, remaining),
                reset_time=datetime.utcfromtimestamp((current_time // 60 + 1) * 60)
            )
            
        except Exception as e:
            logger.error("Rate limit check failed", 
                        extra={"identifier": identifier, "endpoint": endpoint, "error": str(e)}, 
                        exc_info=True)
            # Fail open on errors
            return RateLimitResult(
                allowed=True,
                requests_remaining=999,
                reset_time=datetime.utcnow() + timedelta(minutes=1)
            )
    
    async def reset_rate_limit(self, identifier: str) -> bool:
        """Reset rate limits for a specific identifier (admin function)."""
        if not self.redis_client:
            return False
            
        try:
            # Find all keys for this identifier
            pattern = f"rate_limit:{identifier}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info("Rate limit reset", extra={"identifier": identifier, "keys_deleted": len(keys)})
            
            return True
            
        except Exception as e:
            logger.error("Failed to reset rate limit", 
                        extra={"identifier": identifier, "error": str(e)}, exc_info=True)
            return False
    
    async def get_rate_limit_status(self, identifier: str) -> Dict[str, Any]:
        """Get current rate limit status for an identifier."""
        if not self.redis_client:
            return {"status": "unavailable", "reason": "Redis not connected"}
            
        try:
            current_time = int(time.time())
            minute_key = f"rate_limit:{identifier}:minute:{current_time // 60}"
            hour_key = f"rate_limit:{identifier}:hour:{current_time // 3600}"
            day_key = f"rate_limit:{identifier}:day:{current_time // 86400}"
            
            # Get current counts
            pipe = self.redis_client.pipeline()
            pipe.get(minute_key)
            pipe.get(hour_key)
            pipe.get(day_key)
            
            results = await pipe.execute()
            minute_count = int(results[0] or 0)
            hour_count = int(results[1] or 0)
            day_count = int(results[2] or 0)
            
            config = self.default_config
            
            return {
                "identifier": identifier,
                "current_usage": {
                    "minute": minute_count,
                    "hour": hour_count,
                    "day": day_count
                },
                "limits": {
                    "minute": config.requests_per_minute + config.burst_allowance,
                    "hour": config.requests_per_hour,
                    "day": config.requests_per_day
                },
                "remaining": {
                    "minute": max(0, config.requests_per_minute + config.burst_allowance - minute_count),
                    "hour": max(0, config.requests_per_hour - hour_count),
                    "day": max(0, config.requests_per_day - day_count)
                },
                "reset_times": {
                    "minute": datetime.utcfromtimestamp((current_time // 60 + 1) * 60).isoformat(),
                    "hour": datetime.utcfromtimestamp((current_time // 3600 + 1) * 3600).isoformat(),
                    "day": datetime.utcfromtimestamp((current_time // 86400 + 1) * 86400).isoformat()
                }
            }
            
        except Exception as e:
            logger.error("Failed to get rate limit status", 
                        extra={"identifier": identifier, "error": str(e)}, exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def _get_config_for_request(
        self, 
        endpoint: Optional[str] = None, 
        user_tier: Optional[str] = None
    ) -> RateLimitConfig:
        """Determine which rate limit configuration to use for a request."""
        # User tier takes precedence for authenticated users
        if user_tier and user_tier in self.user_tier_configs:
            return self.user_tier_configs[user_tier]
        
        # Endpoint-specific configuration
        if endpoint and endpoint in self.endpoint_configs:
            return self.endpoint_configs[endpoint]
        
        # Default configuration
        return self.default_config
    
    async def _log_rate_limit_metrics(
        self,
        identifier: str,
        endpoint: Optional[str],
        config: RateLimitConfig,
        minute_count: int,
        hour_count: int,
        day_count: int
    ):
        """Log rate limiting metrics for monitoring."""
        try:
            # Only log every 10th request to avoid spam
            if minute_count % 10 == 0:
                logger.info(
                    "Rate limit metrics",
                    extra={
                        "identifier": identifier,
                        "endpoint": endpoint,
                        "usage": {
                            "minute": minute_count,
                            "hour": hour_count,
                            "day": day_count
                        },
                        "limits": {
                            "minute": config.requests_per_minute + config.burst_allowance,
                            "hour": config.requests_per_hour,
                            "day": config.requests_per_day
                        },
                        "utilization": {
                            "minute": round(minute_count / (config.requests_per_minute + config.burst_allowance) * 100, 1),
                            "hour": round(hour_count / config.requests_per_hour * 100, 1),
                            "day": round(day_count / config.requests_per_day * 100, 1)
                        }
                    }
                )
        except Exception as e:
            # Don't let metrics logging break rate limiting
            logger.debug("Rate limit metrics logging failed", extra={"error": str(e)})
    
    async def get_global_statistics(self) -> Dict[str, Any]:
        """Get global rate limiting statistics."""
        if not self.redis_client:
            return {"status": "unavailable"}
            
        try:
            # Get all rate limit keys
            pattern = "rate_limit:*"
            keys = await self.redis_client.keys(pattern)
            
            stats = {
                "total_tracked_identifiers": len(set(key.split(':')[1] for key in keys if len(key.split(':')) >= 3)),
                "total_active_windows": len(keys),
                "configurations": {
                    "default": {
                        "requests_per_minute": self.default_config.requests_per_minute,
                        "requests_per_hour": self.default_config.requests_per_hour,
                        "requests_per_day": self.default_config.requests_per_day
                    },
                    "endpoint_count": len(self.endpoint_configs),
                    "user_tier_count": len(self.user_tier_configs)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get global rate limiting statistics", 
                        extra={"error": str(e)}, exc_info=True)
            return {"status": "error", "error": str(e)}
