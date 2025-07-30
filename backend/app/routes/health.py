"""
Minimal health check routes for container orchestration.

Provides essential liveness and readiness endpoints for Docker and service checks.
"""

from datetime import datetime
from fastapi import APIRouter

from ..models.response_models import LivenessCheck, ReadinessCheck

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
