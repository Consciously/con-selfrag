"""
# =============================================================================
# Project: Selfrag
# Module: Memory Service (Phase 3)
# File: database/repositories/memory_repository.py
# Purpose: Repository layer for CRUD operations on episodic and semantic memory.
# Owner: Core Platform (RAG + Memory)
# Status: Draft (Phase 3) | Created: 2025-08-08
# Notes: Keep Agents out. Coordinator only routes. No external tools.
# =============================================================================
"""
from __future__ import annotations

import uuid
from typing import Any, Optional, Sequence

from ...database.connection import get_database_pools
from ...logging_utils import get_logger

logger = get_logger(__name__)

MAX_PAGE_SIZE = 100


class MemoryRepository:
    """Data access layer using asyncpg for memory tables."""

    def __init__(self) -> None:
        self._pools = get_database_pools()

    async def insert_episodic(
        self,
        *,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        tokens: Optional[int] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> str:
        rec_id = str(uuid.uuid4())
        query = """
            INSERT INTO episodic_memories (id, user_id, session_id, role, content, tokens, tags)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
        """
        async with self._pools.get_postgres_connection() as conn:
            await conn.execute(
                query,
                rec_id,
                user_id,
                session_id,
                role,
                content,
                tokens,
                list(tags) if tags else None,
            )
        return rec_id

    async def get_recent_episodic(
        self, *, user_id: str, session_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        limit = min(max(limit, 1), MAX_PAGE_SIZE)
        query = """
            SELECT id, session_id, role, content, tokens, tags, created_at, updated_at
            FROM episodic_memories
            WHERE user_id=$1 AND session_id=$2
            ORDER BY created_at DESC
            LIMIT $3
        """
        async with self._pools.get_postgres_connection() as conn:
            rows = await conn.fetch(query, user_id, session_id, limit)
        return [dict(r) for r in rows]

    async def insert_semantic(
        self,
        *,
        user_id: str,
        title: str,
        body: str,
        source_ref: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> str:
        rec_id = str(uuid.uuid4())
        query = """
            INSERT INTO semantic_memories (id, user_id, title, body, source_ref, tags)
            VALUES ($1,$2,$3,$4,$5,$6)
        """
        async with self._pools.get_postgres_connection() as conn:
            await conn.execute(
                query,
                rec_id,
                user_id,
                title,
                body,
                source_ref,
                list(tags) if tags else None,
            )
        return rec_id

    async def get_semantic_by_id(self, *, user_id: str, memory_id: str) -> Optional[dict[str, Any]]:
        query = """
            SELECT id, title, body, source_ref, tags, created_at, updated_at
            FROM semantic_memories
            WHERE user_id=$1 AND id=$2
        """
        async with self._pools.get_postgres_connection() as conn:
            row = await conn.fetchrow(query, user_id, memory_id)
        return dict(row) if row else None

    async def search_semantic(
        self, *, user_id: str, query_text: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        limit = min(max(limit, 1), MAX_PAGE_SIZE)
        pattern = f"%{query_text}%"
        query = """
            SELECT id, title, body, source_ref, tags, created_at, updated_at
            FROM semantic_memories
            WHERE user_id=$1 AND (title ILIKE $2 OR body ILIKE $2)
            ORDER BY created_at DESC
            LIMIT $3
        """
        async with self._pools.get_postgres_connection() as conn:
            rows = await conn.fetch(query, user_id, pattern, limit)
        return [dict(r) for r in rows]

    async def update_semantic(
        self,
        *,
        user_id: str,
        memory_id: str,
        title: Optional[str] = None,
        body: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> bool:
        fields = []
        values: list[Any] = []
        if title is not None:
            fields.append("title=$1")
            values.append(title)
        if body is not None:
            fields.append("body=$%d" % (len(values) + 1))
            values.append(body)
        if tags is not None:
            fields.append("tags=$%d" % (len(values) + 1))
            values.append(list(tags))
        if not fields:
            return False
        fields.append("updated_at=NOW()")
        set_clause = ", ".join(fields)
        values.append(user_id)
        values.append(memory_id)
        query = f"UPDATE semantic_memories SET {set_clause} WHERE user_id=${len(values)-1} AND id=${len(values)}"
        async with self._pools.get_postgres_connection() as conn:
            result = await conn.execute(query, *values)
        return result.upper().startswith("UPDATE")

    async def delete_semantic(self, *, user_id: str, memory_id: str) -> bool:
        query = "DELETE FROM semantic_memories WHERE user_id=$1 AND id=$2"
        async with self._pools.get_postgres_connection() as conn:
            result = await conn.execute(query, user_id, memory_id)
        return result.upper().startswith("DELETE")
