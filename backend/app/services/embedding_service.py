"""
Embedding service for generating vector embeddings from text.

This service handles text embedding generation using various models,
with caching and batch processing capabilities.
"""

import asyncio
from typing import List, Optional, Dict, Any
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from ..logging_utils import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_embeddings: bool = True
    ):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of the sentence-transformers model
            cache_embeddings: Whether to cache embeddings in memory
        """
        self.model_name = model_name
        self.cache_embeddings = cache_embeddings
        self.model = None
        self._embedding_cache: Dict[str, List[float]] = {}
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        try:
            if not EMBEDDINGS_AVAILABLE:
                logger.warning(
                    "Sentence transformers not available - embeddings will use mock data",
                    extra={"model_name": self.model_name}
                )
                return
            
            logger.info(
                "Loading embedding model",
                extra={"model_name": self.model_name}
            )
            
            self.model = SentenceTransformer(self.model_name)
            
            # Get model info
            max_seq_length = getattr(self.model, 'max_seq_length', 512)
            embedding_dimension = self.model.get_sentence_embedding_dimension()
            
            logger.info(
                "Embedding model loaded successfully",
                extra={
                    "model_name": self.model_name,
                    "max_sequence_length": max_seq_length,
                    "embedding_dimension": embedding_dimension
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to load embedding model",
                extra={
                    "model_name": self.model_name,
                    "error": str(e)
                },
                exc_info=True
            )
            self.model = None
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of float values representing the embedding
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            text = text.strip()
            
            # Check cache first
            if self.cache_embeddings:
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    logger.debug(
                        "Retrieved embedding from cache",
                        extra={"text_length": len(text)}
                    )
                    return self._embedding_cache[cache_key]
            
            # Generate embedding
            if self.model is None:
                # Fallback to mock embedding for development/testing
                embedding = self._generate_mock_embedding(text)
                logger.warning(
                    "Generated mock embedding (model not available)",
                    extra={"text_length": len(text), "embedding_dim": len(embedding)}
                )
            else:
                # Use actual model
                embedding = await self._generate_real_embedding(text)
                logger.debug(
                    "Generated real embedding",
                    extra={"text_length": len(text), "embedding_dim": len(embedding)}
                )
            
            # Cache the result
            if self.cache_embeddings:
                cache_key = self._get_cache_key(text)
                self._embedding_cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(
                "Failed to generate embedding",
                extra={
                    "text_length": len(text) if text else 0,
                    "error": str(e)
                },
                exc_info=True
            )
            # Return a fallback mock embedding to keep the system working
            return self._generate_mock_embedding(text)
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embeddings corresponding to input texts
        """
        try:
            if not texts:
                return []
            
            # Filter empty texts and keep track of indices
            valid_texts = []
            valid_indices = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text.strip())
                    valid_indices.append(i)
            
            if not valid_texts:
                logger.warning("No valid texts provided for embedding")
                return [self._generate_mock_embedding("") for _ in texts]
            
            logger.info(
                "Starting batch embedding generation",
                extra={
                    "total_texts": len(texts),
                    "valid_texts": len(valid_texts),
                    "batch_size": batch_size
                }
            )
            
            # Process in batches
            all_embeddings = []
            for i in range(0, len(valid_texts), batch_size):
                batch_texts = valid_texts[i:i + batch_size]
                
                if self.model is None:
                    # Generate mock embeddings
                    batch_embeddings = [
                        self._generate_mock_embedding(text) for text in batch_texts
                    ]
                else:
                    # Generate real embeddings
                    batch_embeddings = await self._generate_real_embeddings_batch(batch_texts)
                
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(
                    "Processed embedding batch",
                    extra={
                        "batch_index": i // batch_size + 1,
                        "batch_size": len(batch_texts),
                        "total_batches": (len(valid_texts) + batch_size - 1) // batch_size
                    }
                )
            
            # Create final result list with correct positioning
            result_embeddings = []
            valid_embedding_index = 0
            
            for i, text in enumerate(texts):
                if i in valid_indices:
                    result_embeddings.append(all_embeddings[valid_embedding_index])
                    valid_embedding_index += 1
                else:
                    # Empty text - provide mock embedding
                    result_embeddings.append(self._generate_mock_embedding(""))
            
            logger.info(
                "Batch embedding generation completed",
                extra={
                    "total_embeddings": len(result_embeddings),
                    "valid_embeddings": len(all_embeddings)
                }
            )
            
            return result_embeddings
            
        except Exception as e:
            logger.error(
                "Batch embedding generation failed",
                extra={
                    "texts_count": len(texts),
                    "error": str(e)
                },
                exc_info=True
            )
            # Return mock embeddings as fallback
            return [self._generate_mock_embedding(text) for text in texts]
    
    async def _generate_real_embedding(self, text: str) -> List[float]:
        """Generate embedding using the actual model."""
        # Run in thread pool to avoid blocking async loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, 
            self.model.encode, 
            text
        )
        return embedding.tolist()
    
    async def _generate_real_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch using the actual model."""
        # Run in thread pool to avoid blocking async loop
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            self.model.encode,
            texts
        )
        return embeddings.tolist()
    
    def _generate_mock_embedding(self, text: str, dimension: int = 384) -> List[float]:
        """
        Generate a deterministic mock embedding for development/testing.
        
        Args:
            text: Input text
            dimension: Embedding dimension
            
        Returns:
            Mock embedding vector
        """
        # Create deterministic but varied mock embedding based on text hash
        if not text:
            text = "empty"
        
        # Use hash to create consistent mock embeddings
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Generate mock embedding with some variation
        import random
        random.seed(int(text_hash[:8], 16))  # Use first 8 chars of hash as seed
        
        # Generate normalized random vector
        mock_embedding = [random.uniform(-1, 1) for _ in range(dimension)]
        
        # Normalize the vector
        magnitude = sum(x * x for x in mock_embedding) ** 0.5
        if magnitude > 0:
            mock_embedding = [x / magnitude for x in mock_embedding]
        
        return mock_embedding
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.sha256(f"{self.model_name}:{text}".encode()).hexdigest()
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Cleared embedding cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._embedding_cache),
            "cache_enabled": self.cache_embeddings,
            "model_loaded": self.model is not None,
            "model_name": self.model_name
        }
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this service."""
        if self.model is not None and hasattr(self.model, 'get_sentence_embedding_dimension'):
            return self.model.get_sentence_embedding_dimension()
        return 384  # Default for all-MiniLM-L6-v2 and our mock embeddings
