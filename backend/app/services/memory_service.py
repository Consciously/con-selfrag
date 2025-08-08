"""
# =============================================================================
# Project: Selfrag
# Module: Memory Service (Phase 3)
# File: services/memory_service.py
# Purpose: Business logic for memory operations with redaction and caching.
# Owner: Core Platform (RAG + Memory)
# Status: Draft (Phase 3) | Created: 2025-08-08
# Notes: Keep Agents out. Coordinator only routes. No external tools.
# =============================================================================
"""
from __future__ import annotations

from typing import Any, Optional

from ..middleware.redaction import scrub
from ..services.cache_service import cache_service
from ..logging_utils import get_logger
from ..database.repositories.memory_repository import MemoryRepository

logger = get_logger(__name__)


class MemoryService:
    """High-level memory operations orchestrating redaction, caching and persistence."""

    def __init__(self, repository: Optional[MemoryRepository] = None) -> None:
        self.repo = repository or MemoryRepository()

    async def log_turn(
        self,
        *,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        tags: Optional[list[str]] = None,
    ) -> str:
        if role not in {"user", "assistant", "system"}:
            raise ValueError("Invalid role")
        redacted = scrub(content)
        tokens = len(redacted.split()) if redacted else 0
        rec_id = await self.repo.insert_episodic(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=redacted,
            tokens=tokens,
            tags=tags,
        )
        cache_key = self._recent_turns_cache_key(user_id, session_id, 10)
        await cache_service.delete(cache_key)
        return rec_id

    async def retrieve_recent_turns(
        self, *, user_id: str, session_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        limit = min(max(limit, 1), 100)
        cache_key = self._recent_turns_cache_key(user_id, session_id, limit)
        cached = await cache_service.get(cache_key)
        if cached is not None:
            return cached
        rows = await self.repo.get_recent_episodic(
            user_id=user_id, session_id=session_id, limit=limit
        )
        await cache_service.set(cache_key, rows, ttl_seconds=30)
        return rows

    async def create_fact(
        self,
        *,
        user_id: str,
        title: str,
        body: str,
        tags: Optional[list[str]] = None,
        source_ref: Optional[str] = None,
    ) -> str:
        redacted_body = scrub(body)
        rec_id = await self.repo.insert_semantic(
            user_id=user_id,
            title=title.strip(),
            body=redacted_body,
            source_ref=source_ref,
            tags=tags,
        )
        return rec_id

    async def get_fact(self, *, user_id: str, memory_id: str) -> Optional[dict[str, Any]]:
        return await self.repo.get_semantic_by_id(user_id=user_id, memory_id=memory_id)

    async def search_facts(
        self, *, user_id: str, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        return await self.repo.search_semantic(user_id=user_id, query_text=query, limit=limit)

    async def update_fact(
        self,
        *,
        user_id: str,
        memory_id: str,
        title: Optional[str] = None,
        body: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> bool:
        red_body = scrub(body) if body is not None else None
        return await self.repo.update_semantic(
            user_id=user_id,
            memory_id=memory_id,
            title=title,
            body=red_body,
            tags=tags,
        )

    async def delete_fact(self, *, user_id: str, memory_id: str) -> bool:
        return await self.repo.delete_semantic(user_id=user_id, memory_id=memory_id)

    @staticmethod
    def _recent_turns_cache_key(user_id: str, session_id: str, limit: int) -> str:
        return f"memory:recent:{user_id}:{session_id}:{limit}"


memory_service = MemoryService()
