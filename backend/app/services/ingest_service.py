"""
Content ingestion service for handling business logic.

This service encapsulates the business logic for content ingestion,
including document chunking, embedding generation, and vector storage.
"""

import uuid
from datetime import datetime
from typing import Any, List

from .document_processor import DocumentProcessor
from .embedding_service import EmbeddingService
from .vector_service import VectorService
from ..models.response_models import IngestResponse
from ..config import config
from ..logging_utils import get_logger

logger = get_logger(__name__)


class IngestService:
    """Service for handling content ingestion business logic."""
    
    def __init__(self):
        """Initialize the ingestion service with RAG pipeline components."""
        self.document_processor = DocumentProcessor(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        self.embedding_service = EmbeddingService(
            model_name=config.embedding_model
        )
        self.vector_service = VectorService()

    async def ingest_content(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> IngestResponse:
        """
        Ingest content into the system with full RAG pipeline processing.

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
            document_id = f"doc_{uuid.uuid4().hex[:8]}"

            logger.info(
                "Starting content ingestion",
                extra={
                    "document_id": document_id,
                    "content_length": content_length,
                    "has_metadata": bool(metadata),
                    "metadata_keys": list(metadata.keys()) if metadata else []
                }
            )

            # Step 1: Process document into chunks
            chunks = await self.document_processor.process_document(
                content=content,
                document_id=document_id,
                metadata=metadata
            )

            if not chunks:
                raise RuntimeError("Document processing produced no chunks")

            logger.info(
                "Document chunked successfully",
                extra={
                    "document_id": document_id,
                    "chunk_count": len(chunks),
                    "avg_chunk_size": sum(len(chunk.content) for chunk in chunks) // len(chunks)
                }
            )

            # Step 2: Generate embeddings for all chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.generate_embeddings_batch(
                texts=chunk_texts,
                batch_size=32
            )

            logger.info(
                "Embeddings generated successfully",
                extra={
                    "document_id": document_id,
                    "embedding_count": len(embeddings),
                    "embedding_dimension": len(embeddings[0]) if embeddings else 0
                }
            )

            # Step 3: Store chunks and embeddings in vector database
            storage_success = await self.vector_service.store_chunks(
                chunks=chunks,
                embeddings=embeddings
            )

            if not storage_success:
                logger.warning(
                    "Vector storage failed, but continuing with ingestion",
                    extra={"document_id": document_id}
                )

            # Step 4: Store in relational database (future enhancement)
            # TODO: Store document metadata in PostgreSQL
            # await self.store_document_metadata(document_id, content, metadata)

            logger.info(
                "Content ingested successfully",
                extra={
                    "document_id": document_id,
                    "chunk_count": len(chunks),
                    "vector_storage_success": storage_success
                }
            )

            return IngestResponse(
                id=document_id,
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
        Ingest multiple contents in batch with improved efficiency.

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

            # Process all documents into chunks
            all_chunks = []
            document_ids = []
            
            for i, content in enumerate(contents):
                if not content or not content.strip():
                    logger.warning(f"Skipping empty content at index {i}")
                    continue
                    
                document_id = f"doc_{uuid.uuid4().hex[:8]}"
                document_ids.append(document_id)
                
                metadata = metadatas[i] if metadatas else {}
                chunks = await self.document_processor.process_document(
                    content=content,
                    document_id=document_id,
                    metadata=metadata
                )
                all_chunks.extend(chunks)

            # Generate embeddings for all chunks in batch
            if all_chunks:
                chunk_texts = [chunk.content for chunk in all_chunks]
                embeddings = await self.embedding_service.generate_embeddings_batch(
                    texts=chunk_texts,
                    batch_size=64  # Larger batch for efficiency
                )

                # Store all chunks and embeddings
                await self.vector_service.store_chunks(
                    chunks=all_chunks,
                    embeddings=embeddings
                )

            # Create responses
            results = []
            for i, content in enumerate(contents):
                if content and content.strip():
                    results.append(IngestResponse(
                        id=document_ids[min(i, len(document_ids) - 1)],
                        status="success",
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        content_length=len(content),
                    ))
                else:
                    results.append(IngestResponse(
                        id=f"doc_empty_{i}",
                        status="skipped",
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        content_length=0,
                    ))

            logger.info(
                "Batch ingestion completed",
                extra={
                    "batch_size": len(results),
                    "successful": len([r for r in results if r.status == "success"]),
                    "total_chunks": len(all_chunks)
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
