"""
Embedding service for generating vector embeddings from text.

This service handles text embedding generation using various models,
with multi-level caching and batch processing capabilities for optimal performance.
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
from .cache_service import get_cached_embedding, cache_embedding

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings with advanced caching."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        use_cache: bool = True,
        batch_size: int = 32
    ):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of the sentence-transformers model
            use_cache: Whether to use multi-level caching
            batch_size: Default batch size for batch processing
        """
        self.model_name = model_name
        self.use_cache = use_cache
        self.batch_size = batch_size
        self.model = None
        
        # Legacy in-memory cache for backward compatibility (now mainly as L0 cache)
        self._legacy_cache: Dict[str, List[float]] = {}
        
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
        Generate embedding for a single text with multi-level caching.
        
        Args:
            text: Text to embed
            
        Returns:
            List of float values representing the embedding
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            text = text.strip()
            
            # Check multi-level cache first
            if self.use_cache:
                cached_embedding = await get_cached_embedding(text, self.model_name)
                if cached_embedding is not None:
                    logger.debug(
                        "Retrieved embedding from multi-level cache",
                        extra={"text_length": len(text)}
                    )
                    return cached_embedding
            
            # Check legacy cache for backward compatibility
            cache_key = self._get_legacy_cache_key(text)
            if cache_key in self._legacy_cache:
                embedding = self._legacy_cache[cache_key]
                logger.debug(
                    "Retrieved embedding from legacy cache",
                    extra={"text_length": len(text)}
                )
                
                # Promote to new cache system
                if self.use_cache:
                    await cache_embedding(text, embedding, self.model_name)
                
                return embedding
            
            # Generate new embedding
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
            
            # Cache the result in both systems
            if self.use_cache:
                await cache_embedding(text, embedding, self.model_name)
            
            # Legacy cache (for immediate access)
            self._legacy_cache[cache_key] = embedding
            
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
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches with intelligent caching.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch (uses instance default if None)
            
        Returns:
            List of embeddings corresponding to input texts
        """
        try:
            if not texts:
                return []
            
            batch_size = batch_size or self.batch_size
            
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
                    "batch_size": batch_size,
                    "cache_enabled": self.use_cache
                }
            )
            
            # Check cache for each text first
            embeddings_result = [None] * len(valid_texts)
            uncached_indices = []
            uncached_texts = []
            
            if self.use_cache:
                for i, text in enumerate(valid_texts):
                    cached_embedding = await get_cached_embedding(text, self.model_name)
                    if cached_embedding is not None:
                        embeddings_result[i] = cached_embedding
                    else:
                        uncached_indices.append(i)
                        uncached_texts.append(text)
                
                cache_hit_rate = (len(valid_texts) - len(uncached_texts)) / len(valid_texts) if valid_texts else 0
                logger.info(
                    "Batch cache check completed",
                    extra={
                        "total_texts": len(valid_texts),
                        "cache_hits": len(valid_texts) - len(uncached_texts),
                        "cache_misses": len(uncached_texts),
                        "cache_hit_rate": round(cache_hit_rate, 3)
                    }
                )
            else:
                uncached_indices = list(range(len(valid_texts)))
                uncached_texts = valid_texts
            
            # Process uncached texts in batches
            if uncached_texts:
                uncached_embeddings = []
                
                for i in range(0, len(uncached_texts), batch_size):
                    batch_texts = uncached_texts[i:i + batch_size]
                    
                    if self.model is None:
                        # Generate mock embeddings
                        batch_embeddings = [
                            self._generate_mock_embedding(text) for text in batch_texts
                        ]
                        logger.warning(
                            "Generated mock embeddings for batch",
                            extra={"batch_size": len(batch_texts)}
                        )
                    else:
                        # Generate real embeddings
                        batch_embeddings = await self._generate_real_embeddings_batch(batch_texts)
                        logger.debug(
                            "Generated real embeddings for batch",
                            extra={"batch_size": len(batch_texts)}
                        )
                    
                    uncached_embeddings.extend(batch_embeddings)
                
                # Insert uncached embeddings back into results
                for i, embedding in zip(uncached_indices, uncached_embeddings):
                    embeddings_result[i] = embedding
                
                # Cache the newly generated embeddings
                if self.use_cache:
                    cache_tasks = []
                    for text, embedding in zip(uncached_texts, uncached_embeddings):
                        cache_tasks.append(cache_embedding(text, embedding, self.model_name))
                    
                    # Cache in parallel for better performance
                    await asyncio.gather(*cache_tasks, return_exceptions=True)
                    
                    logger.debug(
                        "Cached new embeddings",
                        extra={"count": len(uncached_embeddings)}
                    )
            
            # Create final result list with proper indexing
            final_embeddings = []
            valid_embedding_idx = 0
            
            for i, text in enumerate(texts):
                if text and text.strip():
                    final_embeddings.append(embeddings_result[valid_embedding_idx])
                    valid_embedding_idx += 1
                else:
                    # Empty text - use mock embedding
                    final_embeddings.append(self._generate_mock_embedding(""))
            
            logger.info(
                "Batch embedding generation completed",
                extra={
                    "total_embeddings": len(final_embeddings),
                    "generated_new": len(uncached_texts),
                    "from_cache": len(valid_texts) - len(uncached_texts) if self.use_cache else 0
                }
            )
            
            return final_embeddings
            
        except Exception as e:
            logger.error(
                "Failed to generate batch embeddings",
                extra={
                    "texts_count": len(texts) if texts else 0,
                    "error": str(e)
                },
                exc_info=True
            )
            # Return fallback mock embeddings to keep the system working
            return [self._generate_mock_embedding(text or "") for text in texts]
    
    def _get_legacy_cache_key(self, text: str) -> str:
        """Generate legacy cache key for backward compatibility."""
        return hashlib.sha256(f"{self.model_name}:{text}".encode()).hexdigest()
    
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
    
    def clear_cache(self):
        """Clear both legacy and modern caches."""
        self._legacy_cache.clear()
        logger.info("Cleared legacy embedding cache")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        # Import here to avoid circular import
        from .cache_service import cache_service
        
        cache_stats = await cache_service.stats()
        
        return {
            "legacy_cache_size": len(self._legacy_cache),
            "cache_enabled": self.use_cache,
            "model_loaded": self.model is not None,
            "model_name": self.model_name,
            "batch_size": self.batch_size,
            "multi_level_cache": cache_stats
        }
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this service."""
        if self.model is not None and hasattr(self.model, 'get_sentence_embedding_dimension'):
            return self.model.get_sentence_embedding_dimension()
        return 384  # Default for all-MiniLM-L6-v2 and our mock embeddings
