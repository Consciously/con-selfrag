"""
Health check endpoints for monitoring service status.
"""

from datetime import datetime

from fastapi import APIRouter
from ..logging_utils import get_logger

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)


@router.get("/liveness")
async def liveness():
    """Simple liveness probe for container orchestration."""
    logger.debug("Liveness probe accessed")
    return {"status": "alive"}


@router.get("/readiness")
async def readiness():
    """Simple readiness probe - add DB/Redis checks later."""
    logger.debug("Readiness probe accessed")
    # TODO: Add actual dependency checks (DB, Redis, LocalAI)
    return {"status": "ready"}


@router.get("/")
async def health():
    """Basic health check endpoint."""
    logger.debug("Health check accessed")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
