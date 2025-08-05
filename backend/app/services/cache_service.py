"""
Multi-level caching service for improved performance.

This module implements a sophisticated caching strategy with:
- L1 Cache: In-memory for ultra-fast access
- L2 Cache: Redis for distributed and persistent caching
- Smart cache invalidation and TTL management
"""

import asyncio
import json
import hashlib
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import pickle
import gzip

from ..database.connection import get_redis_connection
from ..logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache layers."""
    l1_max_size: int = 1000  # Maximum items in L1 cache
    l1_ttl_seconds: int = 3600  # 1 hour
    l2_ttl_seconds: int = 86400  # 24 hours
    compression_threshold: int = 1024  # Compress items larger than 1KB
    enable_compression: bool = True


class CacheKey:
    """Utility for generating consistent cache keys."""
    
    @staticmethod
    def embedding(text: str, model: str = "default") -> str:
        """Generate cache key for embeddings."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"emb:{model}:{text_hash}"
    
    @staticmethod
    def query_result(
        query: str, 
        filters: Optional[Dict] = None, 
        limit: int = 10, 
        context_key: Optional[str] = None
    ) -> str:
        """Generate cache key for query results with optional context awareness."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        filters_hash = hashlib.sha256(str(sorted((filters or {}).items())).encode()).hexdigest()[:8]
        context_hash = ""
        if context_key:
            context_hash = f":{hashlib.sha256(context_key.encode()).hexdigest()[:8]}"
        return f"query:{query_hash}:{filters_hash}:{limit}{context_hash}"
    
    @staticmethod
    def document_chunks(document_id: str) -> str:
        """Generate cache key for document chunks."""
        return f"chunks:{document_id}"
    
    @staticmethod
    def collection_stats(collection_name: str) -> str:
        """Generate cache key for collection statistics."""
        return f"stats:{collection_name}"


class L1Cache:
    """In-memory LRU cache for ultra-fast access."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: List[str] = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from L1 cache."""
        if key not in self.cache:
            return None
        
        # Check TTL
        item = self.cache[key]
        if datetime.now() > item["expires_at"]:
            self.delete(key)
            return None
        
        # Update access order (move to end)
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        logger.debug("L1 cache hit", extra={"key": key})
        return item["value"]
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set item in L1 cache."""
        # Ensure we don't exceed max size
        while len(self.cache) >= self.max_size:
            # Remove least recently used item
            if self.access_order:
                lru_key = self.access_order.pop(0)
                del self.cache[lru_key]
        
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self.cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        logger.debug("L1 cache set", extra={"key": key, "ttl": ttl_seconds})
    
    def delete(self, key: str):
        """Delete item from L1 cache."""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)
    
    def clear(self):
        """Clear all items from L1 cache."""
        self.cache.clear()
        self.access_order.clear()
        logger.info("L1 cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get L1 cache statistics."""
        now = datetime.now()
        valid_items = sum(1 for item in self.cache.values() if now <= item["expires_at"])
        
        return {
            "total_items": len(self.cache),
            "valid_items": valid_items,
            "expired_items": len(self.cache) - valid_items,
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size if self.max_size > 0 else 0
        }


class CacheService:
    """Multi-level caching service with L1 (memory) and L2 (Redis) caches."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.l1_cache = L1Cache(max_size=self.config.l1_max_size)
        self._metrics = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "sets": 0,
            "errors": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get item from multi-level cache.
        
        Priority: L1 -> L2 -> None
        """
        try:
            # Try L1 cache first
            value = self.l1_cache.get(key)
            if value is not None:
                self._metrics["l1_hits"] += 1
                return value
            
            self._metrics["l1_misses"] += 1
            
            # Try L2 cache (Redis)
            async with get_redis_connection() as redis_client:
                redis_value = await redis_client.get(key)
                if redis_value is not None:
                    self._metrics["l2_hits"] += 1
                    
                    # Deserialize and decompress if needed
                    value = self._deserialize(redis_value)
                    
                    # Promote to L1 cache
                    self.l1_cache.set(key, value, self.config.l1_ttl_seconds)
                    
                    logger.debug("L2 cache hit, promoted to L1", extra={"key": key})
                    return value
            
            self._metrics["l2_misses"] += 1
            return None
            
        except Exception as e:
            self._metrics["errors"] += 1
            logger.error("Cache get error", extra={"key": key, "error": str(e)}, exc_info=True)
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """
        Set item in multi-level cache.
        
        Stores in both L1 and L2 caches with appropriate TTLs.
        """
        try:
            ttl_seconds = ttl_seconds or self.config.l2_ttl_seconds
            
            # Store in L1 cache
            l1_ttl = min(ttl_seconds, self.config.l1_ttl_seconds)
            self.l1_cache.set(key, value, l1_ttl)
            
            # Store in L2 cache (Redis)
            serialized_value = self._serialize(value)
            
            async with get_redis_connection() as redis_client:
                await redis_client.setex(key, ttl_seconds, serialized_value)
            
            self._metrics["sets"] += 1
            logger.debug("Cache set", extra={"key": key, "ttl": ttl_seconds})
            
        except Exception as e:
            self._metrics["errors"] += 1
            logger.error("Cache set error", extra={"key": key, "error": str(e)}, exc_info=True)
    
    async def delete(self, key: str):
        """Delete item from both cache levels."""
        try:
            # Delete from L1
            self.l1_cache.delete(key)
            
            # Delete from L2
            async with get_redis_connection() as redis_client:
                await redis_client.delete(key)
            
            logger.debug("Cache delete", extra={"key": key})
            
        except Exception as e:
            self._metrics["errors"] += 1
            logger.error("Cache delete error", extra={"key": key, "error": str(e)}, exc_info=True)
    
    async def clear_pattern(self, pattern: str):
        """Clear all cache entries matching a pattern."""
        try:
            # Clear from L1 (simple iteration since it's memory)
            keys_to_delete = [key for key in self.l1_cache.cache.keys() if self._match_pattern(key, pattern)]
            for key in keys_to_delete:
                self.l1_cache.delete(key)
            
            # Clear from L2 (Redis)
            async with get_redis_connection() as redis_client:
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            
            logger.info("Cache pattern cleared", extra={"pattern": pattern, "l1_deleted": len(keys_to_delete)})
            
        except Exception as e:
            self._metrics["errors"] += 1
            logger.error("Cache clear pattern error", extra={"pattern": pattern, "error": str(e)}, exc_info=True)
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcard)."""
        if "*" not in pattern:
            return key == pattern
        
        parts = pattern.split("*")
        if len(parts) == 2:
            prefix, suffix = parts
            return key.startswith(prefix) and key.endswith(suffix)
        
        # More complex patterns could be added here
        return False
    
    def _serialize(self, value: Any) -> str:
        """Serialize and optionally compress value for storage."""
        try:
            # Convert to JSON first
            json_str = json.dumps(value, default=str)
            
            # Compress if large enough and compression is enabled
            if self.config.enable_compression and len(json_str) > self.config.compression_threshold:
                compressed = gzip.compress(json_str.encode())
                # Use pickle to preserve the fact that it's compressed
                return pickle.dumps({"compressed": True, "data": compressed}).decode("latin1")
            else:
                return json_str
                
        except Exception as e:
            logger.error("Serialization error", extra={"error": str(e)}, exc_info=True)
            # Fallback to pickle
            return pickle.dumps(value).decode("latin1")
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize and decompress value from storage."""
        try:
            # Try JSON first (most common case)
            return json.loads(value)
        except json.JSONDecodeError:
            try:
                # Try pickle (might be compressed)
                pickled_data = pickle.loads(value.encode("latin1"))
                if isinstance(pickled_data, dict) and pickled_data.get("compressed"):
                    # Decompress and parse JSON
                    decompressed = gzip.decompress(pickled_data["data"])
                    return json.loads(decompressed.decode())
                else:
                    return pickled_data
            except Exception as e:
                logger.error("Deserialization error", extra={"error": str(e)}, exc_info=True)
                raise
    
    async def stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        l1_stats = self.l1_cache.stats()
        
        # Calculate hit rates
        total_l1 = self._metrics["l1_hits"] + self._metrics["l1_misses"]
        total_l2 = self._metrics["l2_hits"] + self._metrics["l2_misses"]
        total_requests = total_l1
        
        l1_hit_rate = self._metrics["l1_hits"] / total_l1 if total_l1 > 0 else 0
        l2_hit_rate = self._metrics["l2_hits"] / total_l2 if total_l2 > 0 else 0
        overall_hit_rate = (self._metrics["l1_hits"] + self._metrics["l2_hits"]) / total_requests if total_requests > 0 else 0
        
        # Get Redis stats
        redis_stats = {}
        try:
            async with get_redis_connection() as redis_client:
                info = await redis_client.info("memory")
                redis_stats = {
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "max_memory": info.get("maxmemory", 0)
                }
        except Exception as e:
            logger.error("Failed to get Redis stats", extra={"error": str(e)})
        
        return {
            "l1_cache": l1_stats,
            "l2_cache": redis_stats,
            "metrics": self._metrics,
            "hit_rates": {
                "l1_hit_rate": round(l1_hit_rate, 3),
                "l2_hit_rate": round(l2_hit_rate, 3),
                "overall_hit_rate": round(overall_hit_rate, 3)
            },
            "config": {
                "l1_max_size": self.config.l1_max_size,
                "l1_ttl_seconds": self.config.l1_ttl_seconds,
                "l2_ttl_seconds": self.config.l2_ttl_seconds,
                "compression_enabled": self.config.enable_compression
            }
        }


# Global cache service instance
cache_service = CacheService()


# Convenience functions for common caching operations
async def get_cached_embedding(text: str, model: str = "default") -> Optional[List[float]]:
    """Get cached embedding for text."""
    key = CacheKey.embedding(text, model)
    return await cache_service.get(key)


async def cache_embedding(text: str, embedding: List[float], model: str = "default"):
    """Cache embedding for text."""
    key = CacheKey.embedding(text, model)
    await cache_service.set(key, embedding, ttl_seconds=cache_service.config.l2_ttl_seconds)


async def get_cached_query_result(
    query: str, 
    filters: Optional[Dict] = None, 
    limit: int = 10, 
    context_key: Optional[str] = None
) -> Optional[Any]:
    """Get cached query result with optional context awareness."""
    key = CacheKey.query_result(query, filters, limit, context_key)
    return await cache_service.get(key)


async def cache_query_result(
    query: str, 
    result: Any, 
    filters: Optional[Dict] = None, 
    limit: int = 10, 
    ttl_seconds: int = 3600,
    context_key: Optional[str] = None
):
    """Cache query result with optional context awareness."""
    key = CacheKey.query_result(query, filters, limit, context_key)
    await cache_service.set(key, result, ttl_seconds)


async def invalidate_document_cache(document_id: str):
    """Invalidate all cache entries related to a document."""
    patterns = [
        f"chunks:{document_id}",
        f"query:*",  # Invalidate all query results as they might include this document
    ]
    
    for pattern in patterns:
        await cache_service.clear_pattern(pattern)
