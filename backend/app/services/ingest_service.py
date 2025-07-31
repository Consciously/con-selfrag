"""
Content ingestion service for handling business logic.

This service encapsulates the business logic for content ingestion,
separating it from HTTP concerns and making it testable in isolation.
"""

import uuid
from datetime import datetime
from typing import Any

from ..models.response_models import IngestResponse
from ..logging_utils import get_logger

logger = get_logger(__name__)


class IngestService:
    """Service for handling content ingestion business logic."""

    async def ingest_content(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> IngestResponse:
        """
        Ingest content into the system.

        Args:
            content: The text content to ingest
            metadata: Optional metadata for the content

        Returns:
            IngestResponse with ingestion details

        Raises:
            ValueError: If content is empty or invalid
            RuntimeError: If ingestion fails
        """
        try:
            # Validate content
            if not content or not content.strip():
                raise ValueError("Content cannot be empty")

            content_length = len(content)

            # Generate unique ID
            content_id = f"doc_{uuid.uuid4().hex[:8]}"

            # TODO: Implement actual ingestion logic
            # - Generate embeddings for semantic search
            # - Store in vector database (Qdrant/Weaviate)
            # - Index metadata for filtering
            # - Validate and sanitize content

            logger.info(
                "Ingesting content",
                extra={
                    "content_id": content_id,
                    "content_length": content_length,
                    "has_metadata": bool(metadata),
                    "metadata_keys": list(metadata.keys()) if metadata else []
                }
            )

            # Placeholder: In production, this would store in database
            # For now, we'll just simulate successful ingestion

            return IngestResponse(
                id=content_id,
                status="success",
                timestamp=datetime.utcnow().isoformat() + "Z",
                content_length=content_length,
            )

        except ValueError as e:
            logger.error(
                "Validation error during ingestion",
                extra={"error": str(e), "content_length": len(content) if content else 0},
                exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                "Ingestion failed",
                extra={"error": str(e), "content_length": len(content) if content else 0},
                exc_info=True
            )
            raise RuntimeError(f"Failed to ingest content: {str(e)}") from e

    async def batch_ingest(
        self, contents: list[str], metadatas: list[dict[str, Any]] | None = None
    ) -> list[IngestResponse]:
        """
        Ingest multiple contents in batch.

        Args:
            contents: List of text contents to ingest
            metadatas: Optional list of metadata for each content

        Returns:
            List of IngestResponse objects

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If batch ingestion fails
        """
        try:
            if not contents:
                raise ValueError("Contents list cannot be empty")

            if metadatas and len(metadatas) != len(contents):
                raise ValueError("Metadatas list must match contents length")

            logger.info(
                "Starting batch ingestion",
                extra={
                    "batch_size": len(contents),
                    "has_metadata": bool(metadatas)
                }
            )

            results = []
            for i, content in enumerate(contents):
                metadata = metadatas[i] if metadatas else None
                result = await self.ingest_content(content, metadata)
                results.append(result)

            logger.info(
                "Batch ingestion completed",
                extra={
                    "batch_size": len(results),
                    "successful": len(results)
                }
            )
            return results

        except Exception as e:
            logger.error(
                "Batch ingestion failed",
                extra={"error": str(e), "batch_size": len(contents) if contents else 0},
                exc_info=True
            )
            raise RuntimeError(f"Failed to batch ingest: {str(e)}") from e
