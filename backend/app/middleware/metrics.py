"""
Performance and metrics middleware for automated monitoring.
Integrates with Prometheus metrics and debug logging.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import config
from ..logging_utils import get_debug_logger, log_performance


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect performance metrics and integrate with monitoring."""
    
    def __init__(self, app, enable_metrics: bool = True):
        super().__init__(app)
        self.enable_metrics = enable_metrics
        
        # Import metrics functions only if metrics are enabled
        if enable_metrics:
            try:
                from ..routes.metrics import record_request_metrics
                self.record_request_metrics = record_request_metrics
            except ImportError:
                self.record_request_metrics = None
                self.enable_metrics = False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with metrics collection and debug logging."""
        
        # Generate request ID for debug logging
        request_id = str(uuid.uuid4())[:8] if config.debug_logging else ""
        
        # Get logger with request ID binding
        logger = get_debug_logger(__name__, request_id)
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request if debug logging is enabled
        if config.debug_logging:
            logger.debug(
                f"Incoming request: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "client": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown")
                }
            )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics if enabled
            if self.enable_metrics and self.record_request_metrics:
                try:
                    endpoint = request.url.path
                    # Sanitize endpoint for metrics (remove path parameters)
                    if "/v1/" in endpoint:
                        endpoint = endpoint.split("/v1/")[1].split("/")[0] if endpoint.split("/v1/")[1] else "v1"
                        endpoint = f"/v1/{endpoint}"
                    elif endpoint.startswith("/"):
                        endpoint = "/" + endpoint.split("/")[1] if len(endpoint.split("/")) > 1 else endpoint
                    
                    self.record_request_metrics(
                        method=request.method,
                        endpoint=endpoint,
                        status_code=response.status_code,
                        duration=duration
                    )
                except Exception as e:
                    logger.warning(f"Failed to record metrics: {str(e)}")
            
            # Log performance if enabled
            if config.performance_logging:
                log_performance(
                    operation=f"{request.method} {request.url.path}",
                    duration=duration,
                    status_code=response.status_code,
                    request_id=request_id
                )
            
            # Log response if debug logging is enabled
            if config.debug_logging:
                logger.debug(
                    f"Request completed: {response.status_code}",
                    extra={
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "duration_ms": round(duration * 1000, 2)
                    }
                )
            
            return response
            
        except Exception as e:
            # Calculate duration even for errors
            duration = time.time() - start_time
            
            # Record error metrics if enabled
            if self.enable_metrics and self.record_request_metrics:
                try:
                    endpoint = request.url.path
                    self.record_request_metrics(
                        method=request.method,
                        endpoint=endpoint,
                        status_code=500,
                        duration=duration
                    )
                except Exception:
                    pass  # Don't let metrics recording fail the request
            
            # Log error with context
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise


def create_metrics_middleware(enable_metrics: bool = True) -> MetricsMiddleware:
    """Create metrics middleware with optional metrics collection."""
    return lambda app: MetricsMiddleware(app, enable_metrics=enable_metrics)
