"""
Database models - prepared for SQLAlchemy integration.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, Index
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


class User(Base):
    """User authentication table."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # Match existing schema
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)  # Match existing schema
    
    # Fields to be added in migration
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    
    # Add composite index for common queries
    __table_args__ = (
        Index('ix_users_active_username', 'is_active', 'username'),
        Index('ix_users_active_email', 'is_active', 'email'),
    )

    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:
        """Convert to dictionary, optionally excluding sensitive data."""
        result = {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": getattr(self, 'is_admin', False),  # Handle if field doesn't exist yet
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": getattr(self, 'last_login', None) and self.last_login.isoformat(),
        }
        
        if include_sensitive:
            result["password_hash"] = self.password_hash
            
        return result


class ApiKey(Base):
    """API key authentication table."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)  # Foreign key to users.id
    key_id = Column(String(32), unique=True, index=True, nullable=False)  # Public identifier
    key_hash = Column(String(255), nullable=False)  # Hashed secret key
    name = Column(String(100), nullable=False)  # Human-readable name
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Permissions (for future role-based access)
    permissions = Column(Text, nullable=True)  # JSON string of permissions
    
    # Add composite indexes
    __table_args__ = (
        Index('ix_api_keys_active_user', 'is_active', 'user_id'),
        Index('ix_api_keys_active_key_id', 'is_active', 'key_id'),
    )

    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:
        """Convert to dictionary, optionally excluding sensitive data."""
        result = {
            "id": self.id,
            "user_id": str(self.user_id),
            "key_id": self.key_id,
            "name": self.name,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "permissions": self.permissions,
        }
        
        if include_sensitive:
            result["key_hash"] = self.key_hash
            
        return result

    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


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
                "name": "users",
                "description": "User authentication and profile data",
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {"name": "username", "type": "String(50)", "unique": True, "indexed": True},
                    {"name": "email", "type": "String(255)", "unique": True, "indexed": True},
                    {"name": "hashed_password", "type": "String(255)", "nullable": False},
                    {"name": "is_active", "type": "Boolean", "default": True},
                    {"name": "is_admin", "type": "Boolean", "default": False},
                    {"name": "created_at", "type": "DateTime"},
                    {"name": "last_login", "type": "DateTime", "nullable": True},
                ],
                "indexes": [
                    "ix_users_active_username",
                    "ix_users_active_email"
                ]
            },
            {
                "name": "api_keys",
                "description": "API key authentication and management",
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {"name": "user_id", "type": "Integer", "indexed": True},
                    {"name": "key_id", "type": "String(32)", "unique": True, "indexed": True},
                    {"name": "key_hash", "type": "String(255)", "nullable": False},
                    {"name": "name", "type": "String(100)", "nullable": False},
                    {"name": "is_active", "type": "Boolean", "default": True},
                    {"name": "expires_at", "type": "DateTime", "nullable": True},
                    {"name": "last_used", "type": "DateTime", "nullable": True},
                    {"name": "created_at", "type": "DateTime"},
                    {"name": "permissions", "type": "Text", "nullable": True},
                ],
                "indexes": [
                    "ix_api_keys_active_user",
                    "ix_api_keys_active_key_id"
                ]
            },
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
