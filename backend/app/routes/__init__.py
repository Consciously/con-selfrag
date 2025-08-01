"""
API routes package.

This package contains all HTTP route handlers organized by domain.
Each route module focuses on request/response handling and delegates
business logic to corresponding services.
"""

from . import health, ingest, llm, query

__all__ = ["health", "ingest", "llm", "query"]
