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

    # Database placeholders (for future use)
    # Uncomment when database integration is needed
    # postgres_url: str = Field(default="", description="PostgreSQL connection URL")
    # qdrant_host: str = Field(default="localhost", description="Qdrant host")
    # qdrant_port: int = Field(default=6333, description="Qdrant port")

    @property
    def localai_base_url(self) -> str:
        """Get LocalAI base URL."""
        return f"http://{self.localai_host}:{self.localai_port}/v1"


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", "8000")),
        localai_host=os.getenv("LOCALAI_HOST", "localhost"),
        localai_port=int(os.getenv("LOCALAI_PORT", "8080")),
        localai_timeout=float(os.getenv("LOCALAI_TIMEOUT", "30.0")),
        default_model=os.getenv("DEFAULT_MODEL", "llama-3.2-1b-instruct"),
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


# Global config instance
config = load_config()
