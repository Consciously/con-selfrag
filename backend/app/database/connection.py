"""
Database connection utilities with connection pooling for optimal performance.

This module provides connection pool management for PostgreSQL, Redis, and Qdrant
to improve performance by reusing connections and reducing connection overhead.
"""

import asyncio
import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as redis
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from ..logging_utils import get_logger

logger = get_logger(__name__)


class DatabasePools:
    """Manages connection pools for all databases."""
    
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.qdrant_client: Optional[QdrantClient] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all database connection pools."""
        try:
            logger.info("Initializing database connection pools")
            
            # Initialize PostgreSQL pool
            await self._init_postgres_pool()
            
            # Initialize Redis pool  
            await self._init_redis_pool()
            
            # Initialize Qdrant client
            await self._init_qdrant_client()
            
            self._initialized = True
            logger.info("All database pools initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize database pools", extra={"error": str(e)}, exc_info=True)
            await self.cleanup()
            return False
    
    async def _init_postgres_pool(self):
        """Initialize PostgreSQL connection pool."""
        try:
            # Get connection parameters from environment
            postgres_url = os.getenv("POSTGRES_URL")
            if postgres_url:
                self.postgres_pool = await asyncpg.create_pool(
                    postgres_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=30,
                    server_settings={
                        'jit': 'off',  # Disable JIT for faster connection
                        'application_name': 'con_selfrag'
                    }
                )
            else:
                # Build from individual components
                self.postgres_pool = await asyncpg.create_pool(
                    host=os.getenv("POSTGRES_HOST", "localhost"),
                    port=int(os.getenv("POSTGRES_PORT", "5432")),
                    user=os.getenv("POSTGRES_USER", "con_selfrag"),
                    password=os.getenv("POSTGRES_PASSWORD", "con_selfrag_password"),
                    database=os.getenv("POSTGRES_DB", "con_selfrag"),
                    min_size=2,
                    max_size=10,
                    command_timeout=30,
                    server_settings={
                        'jit': 'off',
                        'application_name': 'con_selfrag'
                    }
                )
            
            # Test the pool
            async with self.postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            logger.info("PostgreSQL connection pool initialized", extra={
                "min_size": 2,
                "max_size": 10,
                "host": os.getenv("POSTGRES_HOST", "localhost")
            })
            

        except Exception as e:
            logger.error("Failed to initialize PostgreSQL pool", extra={"error": str(e)}, exc_info=True)
            raise
    

    async def _init_redis_pool(self):
        """Initialize Redis connection pool."""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            
            self.redis_pool = redis.ConnectionPool(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=10,
                socket_timeout=30
            )
            
            # Test the pool
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            await redis_client.ping()
            await redis_client.close()
            
            logger.info("Redis connection pool initialized", extra={
                "host": redis_host,
                "port": redis_port,
                "max_connections": 20
            })
            
        except Exception as e:
            logger.error("Failed to initialize Redis pool", extra={"error": str(e)}, exc_info=True)
            raise
    
    async def _init_qdrant_client(self):
        """Initialize Qdrant client with optimized settings."""
        try:
            qdrant_host = os.getenv("QDRANT_HOST", "localhost")
            qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
            
            self.qdrant_client = QdrantClient(
                host=qdrant_host,
                port=qdrant_port,
                timeout=30.0,
                prefer_grpc=False  # Use HTTP for better compatibility
            )
            
            # Test the connection
            collections = self.qdrant_client.get_collections()
            
            logger.info("Qdrant client initialized", extra={
                "host": qdrant_host,
                "port": qdrant_port,
                "collections_count": len(collections.collections)
            })
            
        except Exception as e:
            logger.error("Failed to initialize Qdrant client", extra={"error": str(e)}, exc_info=True)
            raise
    
    @asynccontextmanager
    async def get_postgres_connection(self):
        """Get a PostgreSQL connection from the pool."""
        if not self.postgres_pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        async with self.postgres_pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                logger.error("PostgreSQL connection error", extra={"error": str(e)})
                raise
    
    @asynccontextmanager  
    async def get_redis_connection(self):
        """Get a Redis connection from the pool."""
        if not self.redis_pool:
            raise RuntimeError("Redis pool not initialized")
        
        redis_client = redis.Redis(connection_pool=self.redis_pool)
        try:
            yield redis_client
        except Exception as e:
            logger.error("Redis connection error", extra={"error": str(e)})
            raise
        finally:
            await redis_client.close()
    
    def get_qdrant_client(self) -> QdrantClient:
        """Get the Qdrant client."""
        if not self.qdrant_client:
            raise RuntimeError("Qdrant client not initialized")
        return self.qdrant_client
    

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all database connections."""
        health_status = {
            "postgres": {"status": "unknown"},
            "redis": {"status": "unknown"},
            "qdrant": {"status": "unknown"}
        }
        
        # Check PostgreSQL
        try:
            if self.postgres_pool:
                async with self.get_postgres_connection() as conn:
                    await conn.fetchval("SELECT 1")
                health_status["postgres"] = {
                    "status": "healthy",
                    "pool_size": self.postgres_pool.get_size(),
                    "active_connections": len(self.postgres_pool._holders)
                }
            else:
                health_status["postgres"]["status"] = "not_initialized"
        except Exception as e:
            health_status["postgres"] = {"status": "unhealthy", "error": str(e)}
        
        # Check Redis
        try:
            if self.redis_pool:
                async with self.get_redis_connection() as redis_client:
                    await redis_client.ping()
                health_status["redis"] = {
                    "status": "healthy",
                    "max_connections": self.redis_pool.max_connections,
                    "created_connections": self.redis_pool.created_connections
                }
            else:
                health_status["redis"]["status"] = "not_initialized"
        except Exception as e:
            health_status["redis"] = {"status": "unhealthy", "error": str(e)}
        
        # Check Qdrant
        try:
            if self.qdrant_client:
                collections = self.qdrant_client.get_collections()
                health_status["qdrant"] = {
                    "status": "healthy",
                    "collections_count": len(collections.collections)
                }
            else:
                health_status["qdrant"]["status"] = "not_initialized"
        except Exception as e:
            health_status["qdrant"] = {"status": "unhealthy", "error": str(e)}
        
        return health_status
    
    async def cleanup(self):
        """Clean up all connection pools."""
        logger.info("Cleaning up database connection pools")
        
        if self.postgres_pool:
            try:
                await self.postgres_pool.close()
                logger.info("PostgreSQL pool closed")
            except Exception as e:
                logger.error("Error closing PostgreSQL pool", extra={"error": str(e)})
        
        if self.redis_pool:
            try:
                await self.redis_pool.disconnect()
                logger.info("Redis pool disconnected")
            except Exception as e:
                logger.error("Error disconnecting Redis pool", extra={"error": str(e)})
        
        if self.qdrant_client:
            try:
                self.qdrant_client.close()
                logger.info("Qdrant client closed")
            except Exception as e:
                logger.error("Error closing Qdrant client", extra={"error": str(e)})
        
        self._initialized = False


# Global database pools instance
db_pools = DatabasePools()


async def check_database_readiness() -> Dict[str, Any]:
    """
    Check if all databases are ready and connection pools are healthy.
    
    Returns:
        Dictionary with readiness status for each database
    """
    if not db_pools._initialized:
        await db_pools.initialize()
    
    return await db_pools.health_check()


# Convenience functions for getting connections
async def get_postgres_connection():
    """Get PostgreSQL connection context manager."""
    return db_pools.get_postgres_connection()


async def get_redis_connection():
    """Get Redis connection context manager."""
    return db_pools.get_redis_connection()


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client."""
    return db_pools.get_qdrant_client()
