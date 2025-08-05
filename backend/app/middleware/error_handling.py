"""
Global exception handling middleware for enhanced error responses and logging.
"""

import time
import traceback
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, Request, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..logging_utils import get_logger
from ..models.response_models import ErrorResponse

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced error handling middleware that provides structured error responses,
    comprehensive logging, and proper error categorization.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process requests and handle any exceptions with enhanced logging."""
        start_time = time.time()
        request_id = id(request)  # Simple request ID for correlation
        
        try:
            # Process the request
            response = await call_next(request)
            return response
            
        except HTTPException as exc:
            # Handle FastAPI HTTP exceptions with enhanced logging
            duration = time.time() - start_time
            
            logger.warning(
                "HTTP exception occurred",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                    "duration_ms": round(duration * 1000, 2),
                    "user_agent": request.headers.get("user-agent"),
                    "client_ip": self._get_client_ip(request),
                }
            )
            
            # Return structured error response
            error_response = ErrorResponse(
                error="HTTP_EXCEPTION",
                message=str(exc.detail),
                status_code=exc.status_code,
                request_id=str(request_id),
                timestamp=time.time(),
                path=str(request.url.path),
                method=request.method
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.model_dump()
            )
            
        except Exception as exc:
            # Handle unexpected exceptions with full logging
            duration = time.time() - start_time
            error_type = type(exc).__name__
            error_message = str(exc)
            stack_trace = traceback.format_exc()
            
            logger.error(
                "Unhandled exception occurred",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error_type": error_type,
                    "error_message": error_message,
                    "duration_ms": round(duration * 1000, 2),
                    "user_agent": request.headers.get("user-agent"),
                    "client_ip": self._get_client_ip(request),
                    "stack_trace": stack_trace,
                },
                exc_info=True
            )
            
            # Return structured error response for internal errors
            error_response = ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message="An internal server error occurred. Please try again later.",
                status_code=500,
                request_id=str(request_id),
                timestamp=time.time(),
                path=str(request.url.path),
                method=request.method,
                details={
                    "error_type": error_type,
                    "error_id": str(request_id)  # For error tracking
                }
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.model_dump()
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request headers."""
        # Check for forwarded headers first (load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


class ValidationErrorHandler:
    """Custom validation error handler for enhanced error responses."""
    
    @staticmethod
    async def validation_exception_handler(request: Request, exc: Any) -> JSONResponse:
        """Handle Pydantic validation errors with detailed field information."""
        request_id = id(request)
        
        # Extract validation error details
        errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input", "N/A")
            })
        
        logger.warning(
            "Validation error occurred",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "errors": errors,
                "client_ip": ErrorHandlingMiddleware()._get_client_ip(request),
            }
        )
        
        error_response = ErrorResponse(
            error="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=422,
            request_id=str(request_id),
            timestamp=time.time(),
            path=str(request.url.path),
            method=request.method,
            details={
                "validation_errors": errors,
                "total_errors": len(errors)
            }
        )
        
        return JSONResponse(
            status_code=422,
            content=error_response.model_dump()
        )


def create_error_handlers() -> Dict[Union[int, type], Any]:
    """Create enhanced error handlers for the FastAPI application."""
    validation_handler = ValidationErrorHandler()
    
    return {
        422: validation_handler.validation_exception_handler,  # Validation errors
    }


# Custom exception classes for different error types
class ServiceUnavailableError(HTTPException):
    """Raised when a required service is unavailable."""
    
    def __init__(self, service_name: str, detail: Optional[str] = None):
        message = f"Service '{service_name}' is currently unavailable"
        if detail:
            message += f": {detail}"
        super().__init__(status_code=503, detail=message)


class RateLimitExceededError(HTTPException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, limit: int, window: str, detail: Optional[str] = None):
        message = f"Rate limit exceeded: {limit} requests per {window}"
        if detail:
            message += f". {detail}"
        super().__init__(status_code=429, detail=message)


class AuthenticationError(HTTPException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=401, detail=detail)


class AuthorizationError(HTTPException):
    """Raised when authorization fails."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail)


class ValidationError(HTTPException):
    """Raised when request validation fails."""
    
    def __init__(self, field: str, message: str):
        detail = f"Validation error for field '{field}': {message}"
        super().__init__(status_code=422, detail=detail)


class ResourceNotFoundError(HTTPException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        detail = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(status_code=404, detail=detail)


class ConfigurationError(HTTPException):
    """Raised when there's a configuration error."""
    
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"Configuration error: {detail}")


# Error response utilities
def create_error_response(
    error_type: str,
    message: str,
    status_code: int,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """Create a standardized error response."""
    return ErrorResponse(
        error=error_type,
        message=message,
        status_code=status_code,
        request_id=str(id(request)) if request else None,
        timestamp=time.time(),
        path=str(request.url.path) if request else None,
        method=request.method if request else None,
        details=details
    )


def log_error_context(
    logger_instance: Any,
    error: Exception,
    request: Optional[Request] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> None:
    """Log error with comprehensive context information."""
    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if request:
        context.update({
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": ErrorHandlingMiddleware()._get_client_ip(request),
        })
    
    if additional_context:
        context.update(additional_context)
    
    logger_instance.error(
        "Error occurred with context",
        extra=context,
        exc_info=True
    )
