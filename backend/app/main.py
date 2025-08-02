"""
FastAPI application with clean, extensible architecture and structured logging.
Enhanced with Performance & Caching Layer for optimal throughput and response times.
"""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .routes import debug, health, ingest, llm, query, rag, auth, rate_limits
from .logging_utils import get_logger, log_request
from .startup_check import startup_checks
from .models import ModelInfo
from .middleware.performance import create_performance_middleware
from .middleware.auth import AuthMiddleware
from .middleware.rate_limiting import create_rate_limit_middleware
from .services.auth_service import AuthService
from .services.rate_limit_service import RateLimitService
from .database.connection import get_database_pools

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app with essential configuration
app = FastAPI(
    title="Selfrag LLM API",
    description="""
    **Selfrag LLM API - High-Performance Modular Backend**

    A clean, extensible FastAPI backend for AI-powered applications with integrated LLM capabilities
    and Performance & Caching Layer for optimal throughput and response times.

    ## Performance Features
    - **Connection Pooling**: Optimized database connections for PostgreSQL, Redis, and Qdrant
    - **Multi-Level Caching**: L1 (memory) + L2 (Redis) caching for embeddings and query results
    - **Response Compression**: Automatic gzip compression for bandwidth optimization
    - **Performance Monitoring**: Real-time metrics collection and slow request detection
    - **Async Processing**: Non-blocking operations for maximum throughput

    ## Core Features
    - **Health Monitoring**: Service health and readiness checks
    - **Content Ingestion**: Add content with metadata for processing
    - **Natural Language Search**: Query content using semantic search
    - **LLM Integration**: Text generation, question answering, and model management
    - **Streaming Support**: Real-time text generation with streaming responses
    - **Debug Endpoints**: Direct LocalAI testing and inspection tools

    ## LLM Capabilities
    - **Text Generation**: `/llm/generate` - Generate text using configured models
    - **Streaming Generation**: `/llm/generate/stream` - Real-time text generation
    - **Question Answering**: `/llm/ask` - Conversational Q&A interface
    - **Model Management**: `/llm/models` - List and manage available models
    - **Health Monitoring**: `/llm/health` - LLM service status checks

    ## Debug Endpoints (Development)
    - **Direct Ask**: `/debug/ask` - Test LocalAI question answering directly
    - **Direct Embed**: `/debug/embed` - Test embedding generation directly
    - **Direct Generate**: `/debug/generate` - Test text generation directly
    - **Service Status**: `/debug/status` - Inspect LocalAI configuration and status

    ## Performance Monitoring
    - **Metrics**: `/health/metrics` - Performance statistics and cache analytics
    - **Database Health**: `/health/services` - Connection pool status and health checks

    ## Getting Started
    1. Start the service: `uvicorn app.main:app --reload`
    2. Open Swagger UI: http://localhost:8000/docs
    3. Test endpoints using the interactive documentation

    ## Architecture
    - **Routes**: HTTP endpoint handlers
    - **Services**: Business logic layer with caching
    - **Models**: Pydantic models for validation
    - **Clients**: Pooled connections (LocalAI, Qdrant, PostgreSQL, Redis)
    - **Middleware**: Performance optimization and monitoring
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add performance middleware first (processes requests before CORS)
performance_middleware = create_performance_middleware(
    enable_compression=True,
    compression_threshold=1024,
    enable_metrics=True,
    max_request_time=30.0
)
app.add_middleware(type(performance_middleware))

# Add authentication middleware
auth_service = AuthService(
    secret_key=config.jwt_secret_key,
    algorithm=config.jwt_algorithm,
    token_expire_minutes=config.jwt_expire_minutes
)

# Initialize rate limiting service
rate_limit_service = RateLimitService()

# Configure exempt paths for authentication middleware
exempt_paths = [
    "/docs",
    "/redoc", 
    "/openapi.json",
    "/health",
    "/health/liveness",
    "/health/readiness",
    "/health/services",
    "/auth/login",
    "/auth/register",
    "/models",  # Allow model listing without auth for now
]

# Configure exempt paths for rate limiting (these paths won't be rate limited)
rate_limit_exempt_paths = [
    "/docs",
    "/redoc",
    "/openapi.json", 
    "/health/liveness",  # Health checks should not be rate limited
    "/favicon.ico"
]

# Add rate limiting middleware first (outer layer)
rate_limit_middleware = create_rate_limit_middleware(
    rate_limit_service=rate_limit_service,
    enable_rate_limiting=True,  # Set to False to disable rate limiting entirely
    exempt_paths=rate_limit_exempt_paths,
    trust_forwarded_headers=False  # Set to True if behind reverse proxy
)
app.add_middleware(rate_limit_middleware)

# Add the authentication middleware with proper configuration
app.add_middleware(
    AuthMiddleware,
    auth_service=auth_service,
    exempt_paths=exempt_paths
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Log application startup, initialize database pools, and run service checks."""
    logger.info("🚀 Selfrag API with Performance & Caching Layer starting up...")
    logger.info(f"Server: {config.host}:{config.port}")
    logger.info(f"LocalAI: {config.localai_base_url}")
    logger.info(f"Default model: {config.default_model}")
    logger.info(f"Log level: {config.log_level}")
    logger.info(f"CORS origins: {config.cors_origins}")
    
    # Initialize database connection pools
    logger.info("Initializing database connection pools...")
    try:
        pools = get_database_pools()
        await pools.initialize()
        logger.info("✅ Database connection pools initialized successfully")
    except Exception as e:
        logger.error("❌ Failed to initialize database pools", extra={"error": str(e)}, exc_info=True)
        logger.warning("API starting anyway - some features may be limited")
    
    # Initialize rate limiting service
    logger.info("Initializing rate limiting service...")
    try:
        await rate_limit_service.initialize()
        logger.info("✅ Rate limiting service initialized successfully")
    except Exception as e:
        logger.error("❌ Failed to initialize rate limiting service", extra={"error": str(e)}, exc_info=True)
        logger.warning("Rate limiting will be disabled - requests will not be rate limited")
    
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
    logger.info("🛑 Selfrag API shutting down...")
    
    # Cleanup database connection pools
    try:
        pools = get_database_pools()
        await pools.cleanup()
        logger.info("✅ Database connection pools closed successfully")
    except Exception as e:
        logger.error("❌ Error closing database pools", extra={"error": str(e)}, exc_info=True)
    
    logger.info("Graceful shutdown completed")

# Include modular routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(debug.router, prefix="/debug", tags=["Debug"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(llm.router, prefix="/llm", tags=["LLM"])
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(rag.router, prefix="/rag", tags=["RAG Pipeline"])
app.include_router(rate_limits.router, tags=["Rate Limiting"])


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    logger.info("Root endpoint accessed")
    return {
        "name": "Selfrag API",
        "version": "1.0.0",
        "description": "Modular FastAPI backend for AI applications",
        "endpoints": {
            "debug": "/debug",
            "health": "/health",
            "ingest": "/ingest",
            "llm": "/llm",
            "query": "/query",
            "docs": "/docs",
            "models": "/models",
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
