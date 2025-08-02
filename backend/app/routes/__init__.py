"""
API routes package.

This package contains all HTTP route handlers organized by domain.
Each route module focuses on request/response handling and delegates
business logic to corresponding services.
"""

from . import debug, health, ingest, llm, query, rag

__all__ = ["debug", "health", "ingest", "llm", "query", "rag"]
