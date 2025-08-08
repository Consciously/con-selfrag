"""
# =============================================================================
# Project: Selfrag
# Module: Memory Service (Phase 3)
# File: main.py
# Purpose: Integrate memory routes into application startup.
# Owner: Core Platform (RAG + Memory)
# Status: Draft (Phase 3) | Created: 2025-08-08
# Notes: Keep Agents out. Coordinator only routes. No external tools.
# =============================================================================
FastAPI application with clean, extensible architecture and structured logging.
Enhanced with Performance & Caching Layer for optimal throughput and response times.
Features API versioning, gRPC support, and enhanced error handling.
"""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from .config import config

from .logging_utils import get_logger, log_request, reconfigure_logging
from .startup_check import startup_checks
from .models import ModelInfo
from .middleware.performance import create_performance_middleware
from .middleware.error_handling import (
    ErrorHandlingMiddleware, 
    create_error_handlers,
    ValidationErrorHandler
)
from .middleware.metrics import create_metrics_middleware

from .database.connection import get_database_pools

# Import API versioning
from .api.v1 import v1_router

# Import legacy route modules for backward compatibility
from .routes import auth, debug, health, ingest, llm, query, rag, rate_limits, status
from .routes.memory_routes import router as memory_router

# gRPC server management (optional)
try:
    from .grpc.server import start_grpc_server, stop_grpc_server
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    start_grpc_server = None
    stop_grpc_server = None

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app with essential configuration
app = FastAPI(
    title="Selfrag LLM API",
    description="""
    **Selfrag LLM API - High-Performance Modular Backend with API Versioning**

    A clean, extensible FastAPI backend for AI-powered applications with integrated LLM capabilities,
    Performance & Caching Layer, API versioning, gRPC support, and enhanced error handling.

    ## API Versions
    - **v1**: Current stable API version (`/v1/*`)
    - **Legacy**: Backward compatible endpoints (direct paths)

    ## Performance Features
    - **Connection Pooling**: Optimized database connections for PostgreSQL, Redis, and Qdrant
    - **Multi-Level Caching**: L1 (memory) + L2 (Redis) caching for embeddings and query results
    - **Response Compression**: Automatic gzip compression for bandwidth optimization
    - **Performance Monitoring**: Real-time metrics collection and slow request detection
    - **Async Processing**: Non-blocking operations for maximum throughput

    ## Core Features
    - **Health Monitoring**: Service health and readiness checks (including gRPC)
    - **Content Ingestion**: Add content with metadata for processing
    - **Natural Language Search**: Query content using semantic search
    - **LLM Integration**: Text generation, question answering, and model management
    - **Streaming Support**: Real-time text generation with streaming responses
    - **Debug Endpoints**: Direct LocalAI testing and inspection tools

    ## API Endpoints (v1)
    - **Authentication**: `/v1/auth/*` - User authentication and authorization
    - **Health**: `/v1/health/*` - Service status and health checks
    - **Ingestion**: `/v1/ingest/*` - Content ingestion and management
    - **Query**: `/v1/query/*` - Context-aware semantic search
    - **LLM**: `/v1/llm/*` - Language model operations
    - **RAG**: `/v1/rag/*` - Retrieval-Augmented Generation pipeline
    - **Debug**: `/v1/debug/*` - Development and testing tools

    ## Error Handling
    - **Structured Errors**: Consistent error response format
    - **Request Tracking**: Unique request IDs for error correlation
    - **Context Logging**: Comprehensive error context and stack traces
    - **Graceful Degradation**: Fallback responses for service failures

    ## gRPC Support
    - **High Performance**: Binary protocol for efficient communication
    - **Health Checks**: gRPC health monitoring at `/health/grpc`
    - **Future Ready**: Skeleton for Phase 3 implementation

    ## Getting Started
    1. Start the service: `uvicorn app.main:app --reload`
    2. Open Swagger UI: http://localhost:8000/docs
    3. Test v1 endpoints: http://localhost:8000/v1/
    4. Legacy endpoints: http://localhost:8000/ (backward compatible)

    ## Architecture
    - **Versioned APIs**: Structured API versioning with `/v1` prefix
    - **Routes**: HTTP endpoint handlers with comprehensive documentation
    - **Services**: Business logic layer with caching and performance optimization
    - **Models**: Pydantic models for validation and serialization
    - **Clients**: Pooled connections (LocalAI, Qdrant, PostgreSQL, Redis)
    - **Middleware**: Performance optimization, error handling, and monitoring
    - **gRPC**: High-performance binary protocol support (skeleton)
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add error handling middleware first
app.add_middleware(ErrorHandlingMiddleware)

# Add metrics middleware for monitoring (before performance middleware)
metrics_middleware = create_metrics_middleware(enable_metrics=True)
app.add_middleware(metrics_middleware)

# Add performance middleware (processes requests before CORS)
performance_middleware = create_performance_middleware(
    enable_compression=True,
    compression_threshold=1024,
    enable_metrics=True,
    max_request_time=30.0
)

# Add custom exception handlers
error_handlers = create_error_handlers()
for status_code_or_exception, handler in error_handlers.items():
    app.add_exception_handler(status_code_or_exception, handler)

# Add validation error handler
app.add_exception_handler(RequestValidationError, ValidationErrorHandler.validation_exception_handler)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include memory routes (Phase 3 - Memory Service)
app.include_router(memory_router, prefix="/memory", tags=["memory"])

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and their responses."""
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        "Incoming request",
        extra=log_request(request)
    )
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            extra=log_request(request, response, duration)
        )
        
        return response
        
    except Exception as e:
        # Log any unhandled exceptions
        duration = time.time() - start_time
        logger.error(
            "Request failed",
            extra=log_request(request, duration=duration, error=str(e)),
            exc_info=True
        )
        raise

# Log application startup
@app.on_event("startup")
async def startup_event():
    """Log application startup, initialize database pools, gRPC server, and run service checks."""
    # Reconfigure logging with config settings
    reconfigure_logging(
        log_level=config.log_level,
        debug_logging=config.debug_logging,
        performance_logging=config.performance_logging
    )
    
    logger.info("🚀 Selfrag API v2.0 with Enhanced Features starting up...")
    logger.info(f"Server: {config.host}:{config.port}")
    logger.info(f"LocalAI: {config.localai_base_url}")
    logger.info(f"Default model: {config.default_model}")
    logger.info(f"Log level: {config.log_level}")
    logger.info(f"Debug logging: {config.debug_logging}")
    logger.info(f"Performance logging: {config.performance_logging}")
    logger.info(f"CORS origins: {config.cors_origins}")
    logger.info(f"API versioning: Enabled (v1 + legacy)")
    logger.info(f"gRPC support: {'Enabled' if GRPC_AVAILABLE else 'Disabled (Phase 3)'}")
    
    # Initialize database connection pools
    logger.info("Initializing database connection pools...")
    try:
        pools = get_database_pools()
        await pools.initialize()
        logger.info("✅ Database connection pools initialized successfully")
    except Exception as e:
        logger.error("❌ Failed to initialize database pools", extra={"error": str(e)}, exc_info=True)
        logger.warning("API starting anyway - some features may be limited")
    
    # Start gRPC server if available
    if GRPC_AVAILABLE and start_grpc_server:
        try:
            logger.info("Starting gRPC server...")
            await start_grpc_server(port=50051)
            logger.info("✅ gRPC server started on port 50051")
        except Exception as e:
            logger.error("❌ Failed to start gRPC server", extra={"error": str(e)}, exc_info=True)
            logger.warning("Continuing without gRPC - HTTP API still available")
    
    # Run comprehensive service checks
    logger.info("Running startup service checks...")
    try:
        results = await startup_checks()
        
        if results["overall_status"] == "healthy":
            logger.info("✅ All services healthy - API ready to serve requests", extra={
                "postgres": results["services"]["postgres"]["status"],
                "redis": results["services"]["redis"]["status"],
                "qdrant": results["services"]["qdrant"]["status"],
                "localai": results["services"]["localai"]["status"]
            })
        else:
            logger.warning("⚠️ Some services unhealthy - API may have limited functionality", extra={
                "postgres": results["services"]["postgres"]["status"],
                "redis": results["services"]["redis"]["status"],
                "qdrant": results["services"]["qdrant"]["status"],
                "localai": results["services"]["localai"]["status"]
            })
            
            # Log specific service issues
            for service_name, service_result in results["services"].items():
                if service_result["status"] != "healthy":
                    logger.error(f"Service {service_name} is unhealthy", extra={
                        "service": service_name,
                        "status": service_result["status"],
                        "error": service_result.get("error", "Unknown error")
                    })
                    
    except Exception as e:
        logger.error("❌ Startup service checks failed", extra={"error": str(e)}, exc_info=True)
        logger.warning("API starting anyway - health checks available at /health/services")

# Log application shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown and cleanup resources."""
    logger.info("🛑 Selfrag API v2.0 shutting down...")
    
    # Stop gRPC server if running
    if GRPC_AVAILABLE and stop_grpc_server:
        try:
            logger.info("Stopping gRPC server...")
            await stop_grpc_server()
            logger.info("✅ gRPC server stopped successfully")
        except Exception as e:
            logger.error("❌ Error stopping gRPC server", extra={"error": str(e)}, exc_info=True)
    
    # Cleanup database connection pools
    try:
        pools = get_database_pools()
        logger.info("✅ Database connection pools closed successfully")
    except Exception as e:
        logger.error("❌ Error closing database pools", extra={"error": str(e)}, exc_info=True)
    
    logger.info("Graceful shutdown completed")

# Include versioned API routes
app.include_router(v1_router, tags=["API v1"])

# Include legacy routes for backward compatibility  
app.include_router(auth.router, prefix="/auth", tags=["Authentication (Legacy)"])
app.include_router(debug.router, prefix="/debug", tags=["Debug (Legacy)"])
app.include_router(health.router, prefix="/health", tags=["Health (Legacy)"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion (Legacy)"])
app.include_router(llm.router, prefix="/llm", tags=["LLM (Legacy)"])
app.include_router(query.router, prefix="/query", tags=["Query (Legacy)"])
app.include_router(rag.router, prefix="/rag", tags=["RAG Pipeline (Legacy)"])
app.include_router(rate_limits.router, tags=["Rate Limiting (Legacy)"])
app.include_router(status.router, prefix="/status", tags=["System Status"])


@app.get("/")
async def root():
    """Root endpoint with API version information and available endpoints."""
    logger.info("Root endpoint accessed")
    return {
        "name": "Selfrag LLM API",
        "version": "2.0.0",
        "description": "Modular FastAPI backend for AI applications with API versioning",
        "api_versions": {
            "v1": "/v1/",
            "legacy": "/ (backward compatible)"
        },
        "features": [
            "API Versioning",
            "Enhanced Error Handling", 
            "gRPC Support (skeleton)",
            "Context-Aware RAG",
            "Performance Optimization",
            "Comprehensive Health Checks"
        ],
        "endpoints": {
            "v1_api": "/v1/",
            "legacy": {
                "debug": "/debug",
                "health": "/health", 
                "status": "/status",
                "ingest": "/ingest",
                "llm": "/llm",
                "query": "/query",
                "auth": "/auth"
            },
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc"
            },
            "grpc": {
                "enabled": GRPC_AVAILABLE,
                "port": 50051 if GRPC_AVAILABLE else None,
                "health_check": "/health/grpc"
            }
        },
    }


@app.get(
    "/models",
    response_model=list[ModelInfo],
    summary="List available LLM models",
    description="""
    **List all available LLM models from LocalAI.**
    
    This is a convenience endpoint that provides the same functionality as `/llm/models`
    for easier access and transparency. Returns information about all models available
    in the LocalAI instance.
    
    **Use Cases:**
    - Quick model discovery without navigating to LLM-specific endpoints
    - Integration testing and verification
    - System capability assessment
    - Model availability checking
    
    **Note:** This endpoint delegates to `/llm/models` for consistency.
    """,
    tags=["Models"]
)
async def list_available_models():
    """List all available LLM models - delegates to LLM router for consistency."""
    logger.info("Root models endpoint accessed")
    
    # Import here to avoid circular imports
    from .routes.llm import list_models
    
    # Delegate to the LLM router's models endpoint
    return await list_models()


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
