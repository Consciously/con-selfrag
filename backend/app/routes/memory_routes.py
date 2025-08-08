"""
# =============================================================================
# Project: Selfrag
# Module: Memory Service (Phase 3)
# File: routes/memory_routes.py
# Purpose: FastAPI routes exposing memory service endpoints.
# Owner: Core Platform (RAG + Memory)
# Status: Draft (Phase 3) | Created: 2025-08-08
# Notes: Keep Agents out. Coordinator only routes. No external tools.
# =============================================================================
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..api.schemas.memory import (
    LogTurnRequest,
    RetrieveTurnsRequest,
    CreateFactRequest,
    SearchFactsRequest,
    UpdateFactRequest,
    TurnList,
    FactList,
    Fact,
    Turn,
)
from ..middleware.auth import get_current_active_user
from ..services.memory_service import memory_service
from ..logging_utils import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/log",
    response_model=str,
    summary="Log a conversational turn (episodic memory)",
    description="Stores a single conversation turn after redaction."
)
async def log_turn(req: LogTurnRequest, user=Depends(get_current_active_user)):
    try:
        rec_id = await memory_service.log_turn(
            user_id=str(user.id),
            session_id=req.session_id,
            role=req.role,
            content=req.content,
            tags=req.tags,
        )
        return rec_id
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:  # pragma: no cover
        logger.error("Failed to log turn", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to log turn")


@router.post(
    "/retrieve",
    response_model=TurnList,
    summary="Retrieve recent turns",
    description="Returns last N turns for a session (most recent first)",
)
async def retrieve_turns(req: RetrieveTurnsRequest, user=Depends(get_current_active_user)):
    rows = await memory_service.retrieve_recent_turns(
        user_id=str(user.id), session_id=req.session_id, limit=req.limit or 10
    )
    return TurnList(
        turns=[Turn(**r) for r in rows],
        total=len(rows),
    )


@router.post(
    "/facts",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
    summary="Create semantic fact",
    description="Creates a semantic memory entry (fact / note).",
)
async def create_fact(req: CreateFactRequest, user=Depends(get_current_active_user)):
    rec_id = await memory_service.create_fact(
        user_id=str(user.id),
        title=req.title,
        body=req.body,
        tags=req.tags,
        source_ref=req.source_ref,
    )
    return rec_id


@router.get(
    "/facts/{memory_id}",
    response_model=Fact,
    summary="Get fact by ID",
)
async def get_fact(memory_id: str, user=Depends(get_current_active_user)):
    fact = await memory_service.get_fact(user_id=str(user.id), memory_id=memory_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Not found")
    return Fact(**fact)


@router.post(
    "/facts/search",
    response_model=FactList,
    summary="Search semantic facts",
    description="Simple ILIKE-based text search over title and body.",
)
async def search_facts(req: SearchFactsRequest, user=Depends(get_current_active_user)):
    rows = await memory_service.search_facts(
        user_id=str(user.id), query=req.query, limit=req.limit or 20
    )
    return FactList(facts=[Fact(**r) for r in rows], total=len(rows))


@router.patch(
    "/facts/{memory_id}",
    response_model=bool,
    summary="Update fact",
)
async def update_fact(memory_id: str, req: UpdateFactRequest, user=Depends(get_current_active_user)):
    if req.id != memory_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    updated = await memory_service.update_fact(
        user_id=str(user.id),
        memory_id=memory_id,
        title=req.title,
        body=req.body,
        tags=req.tags,
    )
    return updated


@router.delete(
    "/facts/{memory_id}",
    response_model=bool,
    summary="Delete fact",
)
async def delete_fact(memory_id: str, user=Depends(get_current_active_user)):
    deleted = await memory_service.delete_fact(user_id=str(user.id), memory_id=memory_id)
    return deleted
