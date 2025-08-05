"""
API Version 1 router configuration.
"""

from fastapi import APIRouter

from ..routes import auth, debug, health, ingest, llm, query, rag, rate_limits

# Create v1 API router
v1_router = APIRouter(prefix="/v1")

# Include all route modules with v1 prefix
v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication v1"])
v1_router.include_router(debug.router, prefix="/debug", tags=["Debug v1"])
v1_router.include_router(health.router, prefix="/health", tags=["Health v1"])
v1_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion v1"])
v1_router.include_router(llm.router, prefix="/llm", tags=["LLM v1"])
v1_router.include_router(query.router, prefix="/query", tags=["Query v1"])
v1_router.include_router(rag.router, prefix="/rag", tags=["RAG Pipeline v1"])
v1_router.include_router(rate_limits.router, tags=["Rate Limiting v1"])

@v1_router.get("/")
async def v1_root():
    """API v1 root endpoint with version information."""
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "description": "Selfrag LLM API Version 1",
        "endpoints": {
            "auth": "/v1/auth",
            "debug": "/v1/debug", 
            "health": "/v1/health",
            "ingest": "/v1/ingest",
            "llm": "/v1/llm",
            "query": "/v1/query",
            "rag": "/v1/rag",
            "rate_limits": "/v1/rate-limits",
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }
