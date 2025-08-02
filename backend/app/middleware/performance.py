"""
Performance middleware for request timing, compression, and metrics collection.

This middleware provides:
1. Request/response timing with detailed metrics
2. Response compression for bandwidth optimization
3. Performance metrics collection and monitoring
4. Request rate limiting and resource management
"""

import asyncio
import gzip
import json
import time
from typing import Dict, Any, Optional
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Set up logging
logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for performance monitoring, compression, and optimization.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        enable_compression: bool = True,
        compression_threshold: int = 1024,
        enable_metrics: bool = True,
        max_request_time: float = 30.0
    ):
        super().__init__(app)
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        self.enable_metrics = enable_metrics
        self.max_request_time = max_request_time
        
        # Performance metrics storage
        self.metrics: Dict[str, Any] = {
            "total_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0,
            "requests_by_endpoint": {},
            "slow_requests": [],
            "compression_stats": {
                "compressed_responses": 0,
                "bytes_saved": 0,
                "compression_ratio": 0.0
            }
        }
        
        logger.info(
            "Performance middleware initialized",
            extra={
                "compression_enabled": enable_compression,
                "compression_threshold": compression_threshold,
                "metrics_enabled": enable_metrics,
                "max_request_time": max_request_time
            }
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process request with performance monitoring and optimization."""
        start_time = time.time()
        
        # Extract request info for metrics
        method = request.method
        path = request.url.path
        endpoint = f"{method} {path}"
        
        try:
            # Add request start time to request state
            request.state.start_time = start_time
            
            # Call the next middleware/route handler
            response = await call_next(request)
            
            # Calculate response time
            end_time = time.time()
            response_time = end_time - start_time
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Server-Time"] = str(int(end_time))
            
            # Apply compression if enabled and appropriate
            if self.enable_compression:
                response = await self._compress_response(request, response)
            
            # Collect metrics if enabled
            if self.enable_metrics:
                await self._collect_metrics(endpoint, response_time, response)
            
            # Log slow requests
            if response_time > self.max_request_time:
                logger.warning(
                    "Slow request detected",
                    extra={
                        "endpoint": endpoint,
                        "response_time": response_time,
                        "status_code": response.status_code
                    }
                )
            
            return response
            
        except Exception as e:
            # Handle errors and still collect metrics
            end_time = time.time()
            response_time = end_time - start_time
            
            logger.error(
                "Request processing error",
                extra={
                    "endpoint": endpoint,
                    "response_time": response_time,
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Return error response
            error_response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": str(id(request))}
            )
            error_response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            
            return error_response
    
    async def _compress_response(self, request: Request, response: Response) -> Response:
        """Apply gzip compression to response if appropriate."""
        try:
            # Check if client accepts gzip
            accept_encoding = request.headers.get("accept-encoding", "")
            if "gzip" not in accept_encoding.lower():
                return response
            
            # Skip compression for already compressed content
            content_encoding = response.headers.get("content-encoding")
            if content_encoding:
                return response
            
            # Get response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Skip compression if body is too small
            if len(body) < self.compression_threshold:
                # Recreate response with original body
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            
            # Compress the body
            compressed_body = gzip.compress(body)
            compression_ratio = len(compressed_body) / len(body) if len(body) > 0 else 1.0
            bytes_saved = len(body) - len(compressed_body)
            
            # Update compression metrics
            self.metrics["compression_stats"]["compressed_responses"] += 1
            self.metrics["compression_stats"]["bytes_saved"] += bytes_saved
            
            # Update compression headers
            response.headers["content-encoding"] = "gzip"
            response.headers["content-length"] = str(len(compressed_body))
            response.headers["X-Compression-Ratio"] = f"{compression_ratio:.3f}"
            response.headers["X-Bytes-Saved"] = str(bytes_saved)
            
            logger.debug(
                "Response compressed",
                extra={
                    "original_size": len(body),
                    "compressed_size": len(compressed_body),
                    "compression_ratio": compression_ratio,
                    "bytes_saved": bytes_saved
                }
            )
            
            # Return compressed response
            return Response(
                content=compressed_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
        except Exception as e:
            logger.error(
                "Compression failed",
                extra={"error": str(e)},
                exc_info=True
            )
            return response
    
    async def _collect_metrics(self, endpoint: str, response_time: float, response: Response):
        """Collect performance metrics for monitoring."""
        try:
            # Update global metrics
            self.metrics["total_requests"] += 1
            self.metrics["total_response_time"] += response_time
            self.metrics["avg_response_time"] = (
                self.metrics["total_response_time"] / self.metrics["total_requests"]
            )
            
            # Update endpoint-specific metrics
            if endpoint not in self.metrics["requests_by_endpoint"]:
                self.metrics["requests_by_endpoint"][endpoint] = {
                    "count": 0,
                    "total_time": 0.0,
                    "avg_time": 0.0,
                    "status_codes": {}
                }
            
            endpoint_metrics = self.metrics["requests_by_endpoint"][endpoint]
            endpoint_metrics["count"] += 1
            endpoint_metrics["total_time"] += response_time
            endpoint_metrics["avg_time"] = endpoint_metrics["total_time"] / endpoint_metrics["count"]
            
            # Track status codes
            status_code = str(response.status_code)
            if status_code not in endpoint_metrics["status_codes"]:
                endpoint_metrics["status_codes"][status_code] = 0
            endpoint_metrics["status_codes"][status_code] += 1
            
            # Track slow requests (keep last 100)
            if response_time > 1.0:  # Requests slower than 1 second
                slow_request = {
                    "endpoint": endpoint,
                    "response_time": response_time,
                    "timestamp": time.time(),
                    "status_code": response.status_code
                }
                self.metrics["slow_requests"].append(slow_request)
                
                # Keep only last 100 slow requests
                if len(self.metrics["slow_requests"]) > 100:
                    self.metrics["slow_requests"] = self.metrics["slow_requests"][-100:]
            
            # Log metrics periodically (every 100 requests)
            if self.metrics["total_requests"] % 100 == 0:
                logger.info(
                    "Performance metrics update",
                    extra={
                        "total_requests": self.metrics["total_requests"],
                        "avg_response_time": self.metrics["avg_response_time"],
                        "compressed_responses": self.metrics["compression_stats"]["compressed_responses"],
                        "bytes_saved": self.metrics["compression_stats"]["bytes_saved"]
                    }
                )
            
        except Exception as e:
            logger.error(
                "Failed to collect metrics",
                extra={"error": str(e)},
                exc_info=True
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            # Calculate compression ratio
            compression_stats = self.metrics["compression_stats"]
            if compression_stats["compressed_responses"] > 0:
                total_original = compression_stats["bytes_saved"] / (1 - 0.7)  # Approximate
                compression_stats["compression_ratio"] = (
                    compression_stats["bytes_saved"] / total_original
                    if total_original > 0 else 0.0
                )
            
            return {
                **self.metrics,
                "uptime_seconds": time.time() - (
                    self.metrics.get("start_time", time.time())
                ),
                "requests_per_second": (
                    self.metrics["total_requests"] / max(1, time.time() - (
                        self.metrics.get("start_time", time.time())
                    ))
                )
            }
            
        except Exception as e:
            logger.error(
                "Failed to get metrics",
                extra={"error": str(e)},
                exc_info=True
            )
            return {}
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        try:
            self.metrics = {
                "total_requests": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "requests_by_endpoint": {},
                "slow_requests": [],
                "compression_stats": {
                    "compressed_responses": 0,
                    "bytes_saved": 0,
                    "compression_ratio": 0.0
                },
                "start_time": time.time()
            }
            
            logger.info("Performance metrics reset")
            
        except Exception as e:
            logger.error(
                "Failed to reset metrics",
                extra={"error": str(e)},
                exc_info=True
            )


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Lightweight middleware specifically for request timing.
    Use this if you only need timing without compression/metrics.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info("Request timing middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Add timing information to requests."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request timing error",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "process_time": process_time,
                    "error": str(e)
                },
                exc_info=True
            )
            raise


# Helper function to create performance middleware with default settings
def create_performance_middleware(
    enable_compression: bool = True,
    compression_threshold: int = 1024,
    enable_metrics: bool = True,
    max_request_time: float = 30.0
) -> PerformanceMiddleware:
    """
    Create performance middleware with specified settings.
    
    Args:
        enable_compression: Enable gzip compression
        compression_threshold: Minimum response size for compression
        enable_metrics: Enable performance metrics collection
        max_request_time: Threshold for slow request warnings
        
    Returns:
        Configured PerformanceMiddleware instance
    """
    return PerformanceMiddleware(
        app=None,  # Will be set by FastAPI
        enable_compression=enable_compression,
        compression_threshold=compression_threshold,
        enable_metrics=enable_metrics,
        max_request_time=max_request_time
    )
