"""
# =============================================================================
# Project: Selfrag
# Module: Memory Service (Phase 3)
# File: models/memory_models.py
# Purpose: SQLAlchemy ORM models for EpisodicMemory and SemanticMemory tables.
# Owner: Core Platform (RAG + Memory)
# Status: Draft (Phase 3) | Created: 2025-08-08
# Notes: Keep Agents out. Coordinator only routes. No external tools.
# =============================================================================
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

from ..database.models import Base  # Reuse existing declarative base


class EpisodicMemory(Base):
    """Chat/session turn storage (episodic memory)."""

    __tablename__ = "episodic_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    # Stored as plain string to avoid enum migration complexity (phase 3 scope)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    embedding = Column(JSONB, nullable=True)  # Placeholder until pgvector enabled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_ep_mem_user_created", "user_id", "created_at"),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "tokens": self.tokens,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SemanticMemory(Base):
    """Fact / note storage (semantic memory)."""

    __tablename__ = "semantic_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    body = Column(Text, nullable=False)
    source_ref = Column(String, nullable=True, index=True)
    tags = Column(ARRAY(String), nullable=True)
    embedding = Column(JSONB, nullable=True)  # Placeholder until pgvector enabled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_se_mem_user_created", "user_id", "created_at"),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "title": self.title,
            "body": self.body,
            "source_ref": self.source_ref,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
