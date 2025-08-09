"""
# =============================================================================
# Project: Selfrag
# Module: Memory Service (Phase 3)
# File: api/schemas/memory.py
# Purpose: Pydantic request/response schemas for memory endpoints.
# Owner: Core Platform (RAG + Memory)
# Status: Draft (Phase 3) | Created: 2025-08-08
# Notes: Keep Agents out. Coordinator only routes. No external tools.
# =============================================================================
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator

RoleLiteral = Literal["user", "assistant", "system"]


class LogTurnRequest(BaseModel):
    session_id: str = Field(..., description="Chat/session identifier")
    role: RoleLiteral = Field(..., description="Actor role")
    content: str = Field(..., description="Turn content (will be redacted)")
    tags: Optional[list[str]] = Field(None, description="Optional tag labels")


class RetrieveTurnsRequest(BaseModel):
    session_id: str
    limit: Optional[int] = Field(10, ge=1, le=100)


class CreateFactRequest(BaseModel):
    title: str = Field(..., max_length=200)
    body: str
    tags: Optional[list[str]] = None
    source_ref: Optional[str] = None


class SearchFactsRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Full-text substring (ILIKE) match over title/body")
    limit: Optional[int] = Field(20, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def _strip(cls, v: str) -> str:  # noqa: D401
        v2 = v.strip()
        if len(v2) < 2:
            raise ValueError("query must be at least 2 characters")
        return v2


class UpdateFactRequest(BaseModel):
    id: str
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[list[str]] = None


class Turn(BaseModel):
    id: str
    session_id: str
    role: RoleLiteral
    content: str
    created_at: datetime
    tags: Optional[list[str]] = None


class Fact(BaseModel):
    id: str
    title: str
    body: str
    source_ref: Optional[str] = None
    tags: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime


class FactList(BaseModel):
    items: List[Fact]
    total: int


class ErrorResponse(BaseModel):
    detail: str
    code: str


class CreatedIdResponse(BaseModel):
    id: str
