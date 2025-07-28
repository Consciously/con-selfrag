"""
Database package - prepared for PostgreSQL and Qdrant integration.
"""

from .connection import check_database_readiness
from .models import get_database_schema

# Uncomment when database functionality is implemented
# from .connection import postgres_manager, qdrant_manager, initialize_databases, cleanup_databases
# from .models import ChatHistory, UserSession, VectorDocument, SearchResult

__all__ = [
    "check_database_readiness",
    "get_database_schema",
    # Uncomment when implemented
    # "postgres_manager",
    # "qdrant_manager",
    # "initialize_databases",
    # "cleanup_databases",
    # "ChatHistory",
    # "UserSession",
    # "VectorDocument",
    # "SearchResult",
]
