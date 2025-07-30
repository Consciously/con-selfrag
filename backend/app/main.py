"""
Selfrag API - Minimal FastAPI application shell.

This is a clean, minimal entrypoint that uses the modular route structure.
All business logic is delegated to services via routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import health, ingest, query
from .config import config

# Create FastAPI app with essential configuration
app = FastAPI(
    title="Selfrag API",
    version="0.1.0",
    description="""
    **Selfrag LLM API - Modular Backend Interface**
    
    A clean, extensible FastAPI backend for AI-powered applications.
    
    ## Features
    - **Health Monitoring**: Service health and readiness checks
    - **Content Ingestion**: Add content with metadata for processing
    - **Natural Language Search**: Query content using semantic search
    
    ## Getting Started
    1. Start the service: `uvicorn app.main:app --reload`
    2. Open Swagger UI: http://localhost:8000/docs
    3. Test endpoints using the interactive documentation
    
    ## Architecture
    - **Routes**: HTTP endpoint handlers
    - **Services**: Business logic layer
    - **Models**: Request/response validation
    """,
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

# Include modular routes
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(query.router, prefix="/query", tags=["Query"])


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": "Selfrag API",
        "version": "0.1.0",
        "description": "Modular FastAPI backend for AI applications",
        "endpoints": {
            "health": "/health",
            "ingest": "/ingest",
            "query": "/query",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level=config.log_level.lower(),
    )
