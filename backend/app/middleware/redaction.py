"""
# =============================================================================
# Project: Selfrag
# Module: Memory Service (Phase 3)
# File: middleware/redaction.py
# Purpose: Lightweight PII scrubbing utility for memory content.
# Owner: Core Platform (RAG + Memory)
# Status: Draft (Phase 3) | Created: 2025-08-08
# Notes: Keep Agents out. Coordinator only routes. No external tools.
# =============================================================================
"""
from __future__ import annotations

import re
from typing import Pattern

EMAIL_RE: Pattern[str] = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IPV4_RE: Pattern[str] = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
API_KEY_RE: Pattern[str] = re.compile(r"\bsk-[A-Za-z0-9]{10,}\b")
JWT_RE: Pattern[str] = re.compile(r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")


def scrub(text: str | None) -> str:
    """Conservatively mask common PII tokens.

    Patterns:
      - Email addresses
      - IPv4 addresses
      - API keys starting with sk-
      - JWT-like 3-part tokens
    """
    if not text:
        return ""
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = IPV4_RE.sub("[REDACTED_IP]", redacted)
    redacted = API_KEY_RE.sub("sk-REDACTED", redacted)
    redacted = JWT_RE.sub("jwt-REDACTED", redacted)
    return redacted
