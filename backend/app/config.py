"""
Simplified configuration management following YAGNI principles.
Flattened structure with only essential configuration options.
"""

import os

from pydantic import BaseModel, Field


class Config(BaseModel):
    """Simplified application configuration."""

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # LocalAI settings
    localai_host: str = Field(default="localhost", description="LocalAI host")
    localai_port: int = Field(default=8080, description="LocalAI port")
    localai_timeout: float = Field(default=30.0, description="LocalAI request timeout")
    default_model: str = Field(
        default="llama-3.2-1b-instruct", description="Default model"
    )

    # CORS settings
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    debug_logging: bool = Field(default=False, description="Enable verbose debug logging")
    performance_logging: bool = Field(default=False, description="Enable performance metric logging")

    # Database settings (now active for RAG pipeline)
    postgres_url: str = Field(default="", description="PostgreSQL connection URL")
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    
    # RAG pipeline settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")
    chunk_size: int = Field(default=1000, description="Document chunk size in characters")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    search_limit: int = Field(default=10, description="Default number of search results")
    search_threshold: float = Field(default=0.5, description="Minimum similarity score for search results")

    # Authentication settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production-please",
        description="JWT secret key for token signing"
    )
    jwt_expire_minutes: int = Field(default=1440, description="JWT token expiration in minutes (24 hours)")
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    
    # Security settings
    password_min_length: int = Field(default=8, description="Minimum password length")
    api_key_expire_days: int = Field(default=365, description="Default API key expiration in days")
    max_login_attempts: int = Field(default=5, description="Maximum login attempts before lockout")
    lockout_duration_minutes: int = Field(default=15, description="Account lockout duration in minutes")

    @property
    def localai_base_url(self) -> str:
        """Get LocalAI base URL."""
        return f"http://{self.localai_host}:{self.localai_port}/v1"

    @property
    def postgres_connection_url(self) -> str:
        """Build PostgreSQL connection URL from environment variables."""
        if self.postgres_url:
            return self.postgres_url
        
        # Build from individual components
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "con_selfrag")
        password = os.getenv("POSTGRES_PASSWORD", "con_selfrag_password")
        database = os.getenv("POSTGRES_DB", "con_selfrag")
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", "8000")),
        localai_host=os.getenv("LOCALAI_HOST", "localhost"),
        localai_port=int(os.getenv("LOCALAI_PORT", "8080")),
        localai_timeout=float(os.getenv("LOCALAI_TIMEOUT", "30.0")),
        default_model=os.getenv("DEFAULT_MODEL", "llama-3.2-1b-instruct"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        debug_logging=os.getenv("DEBUG_LOGGING", "false").lower() == "true",
        performance_logging=os.getenv("PERFORMANCE_LOGGING", "false").lower() == "true",
        # Database settings
        postgres_url=os.getenv("POSTGRES_URL", ""),
        qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
        qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", "6379")),
        # RAG settings
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
        search_limit=int(os.getenv("SEARCH_LIMIT", "10")),
        search_threshold=float(os.getenv("SEARCH_THRESHOLD", "0.5")),
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        # Authentication settings
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-please"),
        jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "1440")),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
        api_key_expire_days=int(os.getenv("API_KEY_EXPIRE_DAYS", "365")),
        max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
        lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
    )


# Global config instance
config = load_config()
