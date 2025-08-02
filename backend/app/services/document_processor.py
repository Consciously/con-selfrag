"""
Document processing service for chunking and text preprocessing.

This service handles document chunking, text cleaning, and preparation
for embedding generation and vector storage.
"""

import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    id: str
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    document_id: str
    metadata: Dict[str, Any]
    token_count: Optional[int] = None


class DocumentProcessor:
    """Service for processing documents into chunks suitable for RAG."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000
    ):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
            min_chunk_size: Minimum chunk size to keep
            max_chunk_size: Maximum chunk size before forcing split
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
    async def process_document(
        self,
        content: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Process a document into chunks ready for embedding.
        
        Args:
            content: Raw document content
            document_id: Unique identifier for the document
            metadata: Additional metadata to attach to chunks
            
        Returns:
            List of DocumentChunk objects
            
        Raises:
            ValueError: If content is empty or invalid
        """
        try:
            if not content or not content.strip():
                raise ValueError("Document content cannot be empty")
                
            # Generate document ID if not provided
            if not document_id:
                document_id = f"doc_{uuid.uuid4().hex[:12]}"
                
            # Clean and preprocess content
            cleaned_content = self._clean_text(content)
            
            # Create chunks
            chunks = self._create_chunks(cleaned_content, document_id, metadata or {})
            
            logger.info(
                "Document processed successfully",
                extra={
                    "document_id": document_id,
                    "original_length": len(content),
                    "cleaned_length": len(cleaned_content),
                    "chunk_count": len(chunks),
                    "avg_chunk_size": sum(len(chunk.content) for chunk in chunks) // len(chunks) if chunks else 0
                }
            )
            
            return chunks
            
        except Exception as e:
            logger.error(
                "Document processing failed",
                extra={
                    "document_id": document_id,
                    "content_length": len(content) if content else 0,
                    "error": str(e)
                },
                exc_info=True
            )
            raise RuntimeError(f"Failed to process document: {str(e)}") from e
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters but keep newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('—', '-').replace('–', '-')
        
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def _create_chunks(
        self,
        content: str,
        document_id: str,
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """
        Split content into overlapping chunks.
        
        Args:
            content: Cleaned content to chunk
            document_id: Document identifier
            metadata: Base metadata for all chunks
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        
        # Try to split by paragraphs first for better semantic boundaries
        paragraphs = self._split_by_paragraphs(content)
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max chunk size, finalize current chunk
            if (len(current_chunk) + len(paragraph) > self.chunk_size and 
                len(current_chunk) >= self.min_chunk_size):
                
                # Create chunk from current content
                chunk = self._create_chunk(
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    start_char=current_start,
                    document_id=document_id,
                    metadata=metadata
                )
                if chunk:
                    chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + paragraph
                current_start = current_start + len(current_chunk) - len(overlap_text) - len(paragraph)
                chunk_index += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Handle final chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                start_char=current_start,
                document_id=document_id,
                metadata=metadata
            )
            if chunk:
                chunks.append(chunk)
        
        # If no chunks were created (content too short), create a single chunk
        if not chunks and len(content.strip()) > 0:
            chunk = self._create_chunk(
                content=content.strip(),
                chunk_index=0,
                start_char=0,
                document_id=document_id,
                metadata=metadata
            )
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _split_by_paragraphs(self, content: str) -> List[str]:
        """Split content by paragraphs, preserving semantic boundaries."""
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Clean and filter paragraphs
        cleaned_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para and len(para) >= 10:  # Skip very short paragraphs
                cleaned_paragraphs.append(para)
        
        # If we have very few paragraphs, try splitting by sentences
        if len(cleaned_paragraphs) <= 2:
            return self._split_by_sentences(content)
        
        return cleaned_paragraphs
    
    def _split_by_sentences(self, content: str) -> List[str]:
        """Split content by sentences as fallback."""
        # Simple sentence splitting (can be enhanced with NLTK/spaCy)
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        # Group sentences into paragraph-like chunks
        grouped = []
        current_group = ""
        
        for sentence in sentences:
            if len(current_group) + len(sentence) <= self.chunk_size * 0.7:
                current_group += " " + sentence if current_group else sentence
            else:
                if current_group:
                    grouped.append(current_group.strip())
                current_group = sentence
        
        if current_group:
            grouped.append(current_group.strip())
        
        return grouped
    
    def _get_overlap_text(self, chunk: str) -> str:
        """Extract overlap text from the end of a chunk."""
        if len(chunk) <= self.chunk_overlap:
            return chunk
        
        # Try to find a good breaking point (sentence end)
        overlap_start = len(chunk) - self.chunk_overlap
        
        # Look for sentence boundaries in the overlap region
        overlap_text = chunk[overlap_start:]
        sentence_end = overlap_text.find('. ')
        
        if sentence_end > 0 and sentence_end < self.chunk_overlap * 0.8:
            return overlap_text[sentence_end + 2:]
        
        # Fallback to word boundaries
        words = overlap_text.split()
        if len(words) > 10:
            return ' '.join(words[-10:])
        
        return overlap_text
    
    def _create_chunk(
        self,
        content: str,
        chunk_index: int,
        start_char: int,
        document_id: str,
        metadata: Dict[str, Any]
    ) -> Optional[DocumentChunk]:
        """Create a DocumentChunk object."""
        if not content or len(content) < self.min_chunk_size:
            return None
        
        chunk_id = f"{document_id}_chunk_{chunk_index:04d}"
        
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        token_count = len(content) // 4
        
        # Enhance metadata with chunk-specific information
        chunk_metadata = {
            **metadata,
            "chunk_index": chunk_index,
            "token_count": token_count,
            "char_count": len(content),
            "document_id": document_id,
            "processing_timestamp": str(datetime.now().isoformat())
        }
        
        return DocumentChunk(
            id=chunk_id,
            content=content,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=start_char + len(content),
            document_id=document_id,
            metadata=chunk_metadata,
            token_count=token_count
        )
    
    async def process_multiple_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Process multiple documents in batch.
        
        Args:
            documents: List of documents with 'content', 'id', and 'metadata' keys
            
        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        
        for doc in documents:
            try:
                chunks = await self.process_document(
                    content=doc.get("content", ""),
                    document_id=doc.get("id"),
                    metadata=doc.get("metadata", {})
                )
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(
                    "Failed to process document in batch",
                    extra={
                        "document_id": doc.get("id", "unknown"),
                        "error": str(e)
                    }
                )
                # Continue processing other documents
        
        logger.info(
            "Batch document processing completed",
            extra={
                "total_documents": len(documents),
                "total_chunks": len(all_chunks),
                "avg_chunks_per_doc": len(all_chunks) / len(documents) if documents else 0
            }
        )
        
        return all_chunks
