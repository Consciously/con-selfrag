"""
FastAPI application with clean, extensible architecture and structured logging.
"""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .routes import debug, health, ingest, llm, query
from .logging_utils import get_logger, log_request
from .startup_check import startup_checks

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app with essential configuration
app = FastAPI(
    title="Selfrag LLM API",
    description="""
    **Selfrag LLM API - Modular Backend Interface**

    A clean, extensible FastAPI backend for AI-powered applications with integrated LLM capabilities.

    ## Features
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

    ## Getting Started
    1. Start the service: `uvicorn app.main:app --reload`
    2. Open Swagger UI: http://localhost:8000/docs
    3. Test endpoints using the interactive documentation

    ## Architecture
    - **Routes**: HTTP endpoint handlers
    - **Services**: Business logic layer
    - **Models**: Pydantic models for validation
    - **Clients**: External service integrations (LocalAI, Qdrant, PostgreSQL, Redis)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    """Log application startup and run service checks."""
    logger.info("🚀 Selfrag API starting up...")
    logger.info(f"Server: {config.host}:{config.port}")
    logger.info(f"LocalAI: {config.localai_base_url}")
    logger.info(f"Default model: {config.default_model}")
    logger.info(f"Log level: {config.log_level}")
    logger.info(f"CORS origins: {config.cors_origins}")
    
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
    """Log application shutdown."""
    logger.info("🛑 Selfrag API shutting down...")
    logger.info("Graceful shutdown completed")

# Include modular routes
app.include_router(debug.router, prefix="/debug", tags=["Debug"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(llm.router, prefix="/llm", tags=["LLM"])
app.include_router(query.router, prefix="/query", tags=["Query"])


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
        },
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
