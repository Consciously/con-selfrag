"""
Rate limiting middleware for API protection using Redis-based sliding window algorithm.

This middleware provides:
1. Per-IP rate limiting for anonymous requests
2. Per-user rate limiting for authenticated requests  
3. Per-endpoint rate limiting for specific routes
4. Configurable rate limits and time windows
5. Graceful handling of Redis connection failures
"""

import time
from typing import Optional, Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..services.rate_limit_service import RateLimitService, RateLimitResult
from ..logging_utils import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing rate limits on API requests."""
    
    def __init__(
        self,
        app: ASGIApp,
        rate_limit_service: RateLimitService,
        enable_rate_limiting: bool = True,
        exempt_paths: Optional[list] = None,
        trust_forwarded_headers: bool = False
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: ASGI application
            rate_limit_service: Rate limiting service instance
            enable_rate_limiting: Whether to enforce rate limits
            exempt_paths: List of paths to exempt from rate limiting
            trust_forwarded_headers: Whether to trust X-Forwarded-For headers for IP detection
        """
        super().__init__(app)
        self.rate_limit_service = rate_limit_service
        self.enable_rate_limiting = enable_rate_limiting
        self.trust_forwarded_headers = trust_forwarded_headers
        
        # Default exempt paths (can be overridden)
        self.exempt_paths = exempt_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health/liveness",  # Health checks should not be rate limited
            "/favicon.ico"
        ]
        
        logger.info(
            "Rate limiting middleware initialized",
            extra={
                "enabled": enable_rate_limiting,
                "exempt_paths": self.exempt_paths,
                "trust_forwarded_headers": trust_forwarded_headers
            }
        )
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to incoming requests."""
        # Skip if rate limiting is disabled
        if not self.enable_rate_limiting:
            return await call_next(request)
        
        # Skip exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        try:
            # Get client identifier (IP or user ID)
            identifier = self._get_client_identifier(request)
            
            # Get endpoint string for endpoint-specific limits
            endpoint = f"{request.method} {request.url.path}"
            
            # Get user tier if authenticated
            user_tier = self._get_user_tier(request)
            
            # Check rate limits
            rate_limit_result = await self.rate_limit_service.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint,
                user_tier=user_tier
            )
            
            # Handle rate limit exceeded
            if not rate_limit_result.allowed:
                return self._create_rate_limit_response(rate_limit_result, identifier)
            
            # Add rate limit headers to request state for response headers
            request.state.rate_limit_result = rate_limit_result
            
            # Continue with request processing
            response = await call_next(request)
            
            # Add rate limiting headers to response
            self._add_rate_limit_headers(response, rate_limit_result)
            
            return response
            
        except Exception as e:
            # Log error but don't block request on rate limiting failures
            logger.error(
                "Rate limiting middleware error",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Continue with request if rate limiting fails
            return await call_next(request)
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client (IP or user ID)."""
        # Try to get authenticated user ID first
        if hasattr(request.state, 'user') and request.state.user:
            user_id = getattr(request.state.user, 'id', None)
            if user_id:
                return f"user:{user_id}"
        
        # Fall back to IP address
        return f"ip:{self._get_client_ip(request)}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers if trusted
        if self.trust_forwarded_headers:
            # Check X-Forwarded-For header (may contain multiple IPs)
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                # Take the first IP (original client)
                return forwarded_for.split(",")[0].strip()
            
            # Check X-Real-IP header
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip.strip()
        
        # Fall back to direct client IP
        client_host = request.client.host if request.client else "unknown"
        return client_host
    
    def _get_user_tier(self, request: Request) -> Optional[str]:
        """Get user tier for authenticated users."""
        if hasattr(request.state, 'user') and request.state.user:
            user = request.state.user
            
            # Check if user is admin
            if getattr(user, 'is_admin', False):
                return "admin"
            
            # Check for user tier attribute (could be added to User model)
            tier = getattr(user, 'tier', None)
            if tier:
                return tier
            
            # Default to free tier for authenticated users
            return "free"
        
        return None
    
    def _create_rate_limit_response(
        self, 
        rate_limit_result: RateLimitResult, 
        identifier: str
    ) -> JSONResponse:
        """Create rate limit exceeded response."""
        # Log rate limit violation
        logger.warning(
            "Rate limit exceeded",
            extra={
                "identifier": identifier,
                "limit_type": rate_limit_result.limit_exceeded_type,
                "retry_after": rate_limit_result.retry_after,
                "reset_time": rate_limit_result.reset_time.isoformat()
            }
        )
        
        # Create error response
        error_detail = {
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit exceeded for {rate_limit_result.limit_exceeded_type} window.",
            "limit_exceeded_type": rate_limit_result.limit_exceeded_type,
            "retry_after": rate_limit_result.retry_after,
            "reset_time": rate_limit_result.reset_time.isoformat(),
            "requests_remaining": 0
        }
        
        response = JSONResponse(
            status_code=429,
            content=error_detail
        )
        
        # Add standard rate limit headers
        self._add_rate_limit_headers(response, rate_limit_result)
        
        # Add Retry-After header for client guidance
        if rate_limit_result.retry_after:
            response.headers["Retry-After"] = str(rate_limit_result.retry_after)
        
        return response
    
    def _add_rate_limit_headers(self, response, rate_limit_result: RateLimitResult):
        """Add rate limiting headers to response."""
        try:
            # Standard rate limiting headers
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_result.requests_remaining)
            response.headers["X-RateLimit-Reset"] = str(int(rate_limit_result.reset_time.timestamp()))
            response.headers["X-RateLimit-Reset-ISO"] = rate_limit_result.reset_time.isoformat()
            
            # Custom headers for additional info
            if rate_limit_result.limit_exceeded_type:
                response.headers["X-RateLimit-Limit-Type"] = rate_limit_result.limit_exceeded_type
            
        except Exception as e:
            # Don't let header addition break the response
            logger.debug("Failed to add rate limit headers", extra={"error": str(e)})


def create_rate_limit_middleware(
    rate_limit_service: RateLimitService,
    enable_rate_limiting: bool = True,
    exempt_paths: Optional[list] = None,
    trust_forwarded_headers: bool = False
) -> RateLimitMiddleware:
    """
    Create rate limiting middleware with default settings.
    
    Args:
        rate_limit_service: Initialized rate limiting service
        enable_rate_limiting: Whether to enforce rate limits
        exempt_paths: Additional paths to exempt from rate limiting
        trust_forwarded_headers: Whether to trust X-Forwarded-For headers
    
    Returns:
        Configured RateLimitMiddleware instance
    """
    default_exempt_paths = [
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/health/liveness",
        "/favicon.ico"
    ]
    
    if exempt_paths:
        default_exempt_paths.extend(exempt_paths)
    
    def middleware_factory(app: ASGIApp) -> RateLimitMiddleware:
        return RateLimitMiddleware(
            app=app,
            rate_limit_service=rate_limit_service,
            enable_rate_limiting=enable_rate_limiting,
            exempt_paths=default_exempt_paths,
            trust_forwarded_headers=trust_forwarded_headers
        )
    
    return middleware_factory
