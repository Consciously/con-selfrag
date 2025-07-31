"""
Health check endpoints for monitoring service status.
"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/liveness")
async def liveness():
    """Simple liveness probe for container orchestration."""
    return {"status": "alive"}


@router.get("/readiness")
async def readiness():
    """Simple readiness probe - add DB/Redis checks later."""
    # TODO: Add actual dependency checks (DB, Redis, LocalAI)
    return {"status": "ready"}


@router.get("/")
async def health():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
