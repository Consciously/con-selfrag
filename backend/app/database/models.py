"""
Database models - prepared for SQLAlchemy integration.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class ChatHistory(Base):
    """Chat history table for storing conversations."""

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, index=True)
    user_id = Column(String, index=True)
    message = Column(Text)
    response = Column(Text)
    model = Column(String)
    temperature = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": str(self.session_id) if self.session_id else None,
            "user_id": self.user_id,
            "message": self.message,
            "response": self.response,
            "model": self.model,
            "temperature": self.temperature,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserSession(Base):
    """User session table for tracking user interactions."""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    user_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": str(self.session_id) if self.session_id else None,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "is_active": self.is_active,
        }


class VectorDocument:
    """Document model for Qdrant vector storage."""

    def __init__(
        self,
        id: str | None = None,
        content: str = "",
        metadata: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.content = content
        self.metadata = metadata or {}
        self.embedding = embedding or []

    def to_qdrant_point(self) -> dict[str, Any]:
        """Convert to Qdrant point format."""
        return {
            "id": self.id,
            "vector": self.embedding,
            "payload": {
                "content": self.content,
                "metadata": self.metadata,
            },
        }

    @classmethod
    def from_qdrant_point(cls, point: dict[str, Any]) -> "VectorDocument":
        """Create from Qdrant point."""
        return cls(
            id=point.get("id"),
            content=point.get("payload", {}).get("content", ""),
            metadata=point.get("payload", {}).get("metadata", {}),
            embedding=point.get("vector"),
        )


class SearchResult:
    """Search result with document and relevance score."""

    def __init__(self, document: VectorDocument, score: float, rank: int) -> None:
        self.document = document
        self.score = score
        self.rank = rank

    def to_dict(self) -> dict[str, Any]:
        return {
            "document": {
                "id": self.document.id,
                "content": self.document.content,
                "metadata": self.document.metadata,
            },
            "score": self.score,
            "rank": self.rank,
        }


def create_tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def create_qdrant_collections():
    """Create Qdrant collections."""
    # Placeholder for Qdrant collection creation
    pass


def get_database_schema() -> dict[str, Any]:
    """Get database schema information."""
    return {
        "tables": [
            {
                "name": "chat_history",
                "description": "Stores chat conversation history",
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {"name": "session_id", "type": "UUID", "indexed": True},
                    {"name": "user_id", "type": "String", "indexed": True},
                    {"name": "message", "type": "Text"},
                    {"name": "response", "type": "Text"},
                    {"name": "model", "type": "String"},
                    {"name": "temperature", "type": "Float"},
                    {"name": "created_at", "type": "DateTime"},
                ],
            },
            {
                "name": "user_sessions",
                "description": "Tracks user sessions",
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {
                        "name": "session_id",
                        "type": "UUID",
                        "unique": True,
                        "indexed": True,
                    },
                    {"name": "user_id", "type": "String", "indexed": True},
                    {"name": "created_at", "type": "DateTime"},
                    {"name": "last_activity", "type": "DateTime"},
                    {"name": "is_active", "type": "Boolean"},
                ],
            },
        ],
        "vector_collections": [
            {
                "name": "documents",
                "description": "Vector store for document embeddings",
                "dimension": 1536,  # Example dimension, adjust based on your embedding model
            }
        ],
    }
