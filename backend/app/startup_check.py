"""
Startup checks for all external services.
Validates connectivity to LocalAI, Qdrant, PostgreSQL, and Redis.
"""

import asyncio
import os
import json
from typing import Dict, Any

import asyncpg
import httpx
import redis.asyncio as redis
from app.logging_utils import get_logger
from app.localai_client import localai_client

logger = get_logger(__name__)


class ServiceChecker:
    """Handles connectivity checks for all external services."""
    
    def __init__(self):
        self.postgres_config = {
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER", "con_selfrag"),
            "password": os.getenv("POSTGRES_PASSWORD", "con_selfrag_password"),
            "database": os.getenv("POSTGRES_DB", "con_selfrag")
        }
        
        self.redis_config = {
            "host": os.getenv("REDIS_HOST", "redis"),
            "port": int(os.getenv("REDIS_PORT", "6379"))
        }
        
        self.qdrant_config = {
            "host": os.getenv("QDRANT_HOST", "qdrant"),
            "port": int(os.getenv("QDRANT_PORT", "6333"))
        }
        
        self.localai_config = {
            "host": os.getenv("LOCALAI_HOST", "localai"),
            "port": int(os.getenv("LOCALAI_PORT", "8080"))
        }

    async def check_postgres(self) -> Dict[str, Any]:
        """Check PostgreSQL connectivity and basic schema."""
        try:
            logger.info("Checking PostgreSQL connection...", extra={
                "host": self.postgres_config["host"],
                "port": self.postgres_config["port"],
                "database": self.postgres_config["database"],
                "user": self.postgres_config["user"],
                "password_set": bool(self.postgres_config["password"])
            })
            
            # Try connecting with password first
            conn = None
            try:
                conn = await asyncpg.connect(
                    host=self.postgres_config["host"],
                    port=self.postgres_config["port"],
                    user=self.postgres_config["user"],
                    password=self.postgres_config["password"],
                    database=self.postgres_config["database"]
                )
                logger.info("PostgreSQL connected with password authentication")
            except Exception as password_error:
                logger.warning(f"Password authentication failed: {password_error}")
                logger.info("Trying trust authentication (no password)...")
                
                # Try connecting without password (trust authentication)
                conn = await asyncpg.connect(
                    host=self.postgres_config["host"],
                    port=self.postgres_config["port"],
                    user=self.postgres_config["user"],
                    database=self.postgres_config["database"]
                )
                logger.info("PostgreSQL connected with trust authentication")
            
            # Test basic connectivity
            result = await conn.fetchval("SELECT 1")
            assert result == 1
            
            # Check if our schema exists
            schema_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'con_selfrag')"
            )
            
            # Check if key tables exist
            tables_check = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'con_selfrag' 
                AND table_name IN ('documents', 'document_chunks', 'conversations', 'messages')
            """)
            
            await conn.close()
            
            logger.info("PostgreSQL connection successful", extra={
                "schema_exists": schema_exists,
                "tables_found": len(tables_check)
            })
            
            return {
                "status": "healthy",
                "schema_exists": schema_exists,
                "tables_found": [row["table_name"] for row in tables_check],
                "message": "PostgreSQL connection successful"
            }
            
        except Exception as e:
            logger.error("PostgreSQL connection failed", extra={"error": str(e)}, exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "PostgreSQL connection failed"
            }

    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and basic operations."""
        try:
            logger.info("Checking Redis connection...", extra={
                "host": self.redis_config["host"],
                "port": self.redis_config["port"]
            })
            
            # Connect to Redis
            redis_client = redis.Redis(
                host=self.redis_config["host"],
                port=self.redis_config["port"],
                decode_responses=True
            )
            
            # Test basic connectivity
            await redis_client.ping()
            
            # Test basic operations
            test_key = "startup_check_test"
            await redis_client.set(test_key, "test_value", ex=60)  # Expire in 60 seconds
            value = await redis_client.get(test_key)
            assert value == "test_value"
            
            # Clean up
            await redis_client.delete(test_key)
            
            # Get Redis info
            info = await redis_client.info()
            redis_version = info.get("redis_version", "unknown")
            
            await redis_client.close()
            
            logger.info("Redis connection successful", extra={
                "version": redis_version
            })
            
            return {
                "status": "healthy",
                "version": redis_version,
                "message": "Redis connection successful"
            }
            
        except Exception as e:
            logger.error("Redis connection failed", extra={"error": str(e)}, exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Redis connection failed"
            }

    async def check_qdrant(self) -> Dict[str, Any]:
        """Check Qdrant connectivity and basic operations."""
        try:
            logger.info("Checking Qdrant connection...", extra={
                "host": self.qdrant_config["host"],
                "port": self.qdrant_config["port"]
            })
            
            # Use httpx to check Qdrant health endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.qdrant_config['host']}:{self.qdrant_config['port']}/readyz",
                    timeout=10.0
                )
                response.raise_for_status()
                
                # Get cluster info
                cluster_response = await client.get(
                    f"http://{self.qdrant_config['host']}:{self.qdrant_config['port']}/cluster",
                    timeout=10.0
                )
                cluster_info = cluster_response.json()
                
                # Get collections
                collections_response = await client.get(
                    f"http://{self.qdrant_config['host']}:{self.qdrant_config['port']}/collections",
                    timeout=10.0
                )
                collections_info = collections_response.json()
                collections_count = len(collections_info.get("result", {}).get("collections", []))
            
            logger.info("Qdrant connection successful", extra={
                "collections_count": collections_count
            })
            
            return {
                "status": "healthy",
                "collections_count": collections_count,
                "cluster_info": cluster_info,
                "message": "Qdrant connection successful"
            }
            
        except Exception as e:
            logger.error("Qdrant connection failed", extra={"error": str(e)}, exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Qdrant connection failed"
            }

    async def check_localai(self) -> Dict[str, Any]:
        """Check LocalAI connectivity and basic operations."""
        try:
            logger.info("Checking LocalAI connection...", extra={
                "host": self.localai_config["host"],
                "port": self.localai_config["port"]
            })
            
            # Use the LocalAI client for health check
            is_healthy = await localai_client.health_check()
            
            if not is_healthy:
                return {
                    "status": "unhealthy",
                    "error": "Health check failed",
                    "message": "LocalAI health check failed"
                }
            
            # Try to list models to verify API functionality
            try:
                models = await localai_client.list_models()
                model_names = [model.name for model in models]
                
                logger.info("LocalAI connection successful", extra={
                    "models_count": len(models),
                    "models": model_names
                })
                
                return {
                    "status": "healthy",
                    "models_count": len(models),
                    "available_models": model_names,
                    "message": "LocalAI connection successful"
                }
                
            except Exception as model_error:
                logger.warning("LocalAI model listing failed", extra={"error": str(model_error)})
                return {
                    "status": "healthy",
                    "models_count": 0,
                    "available_models": [],
                    "warning": f"Model listing failed: {str(model_error)}",
                    "message": "LocalAI connection successful (limited functionality)"
                }
            
        except Exception as e:
            logger.error("LocalAI connection failed", extra={"error": str(e)}, exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "LocalAI connection failed"
            }

    async def check_all_services(self) -> Dict[str, Any]:
        """Run all service checks and return comprehensive status."""
        logger.info("Running comprehensive service checks...")
        
        # Run all checks concurrently
        postgres_result, redis_result, qdrant_result, localai_result = await asyncio.gather(
            self.check_postgres(),
            self.check_redis(),
            self.check_qdrant(),
            self.check_localai(),
            return_exceptions=True
        )
        
        # Handle any exceptions from concurrent execution
        if isinstance(postgres_result, Exception):
            postgres_result = {"status": "unhealthy", "error": str(postgres_result), "message": "Check failed"}
        if isinstance(redis_result, Exception):
            redis_result = {"status": "unhealthy", "error": str(redis_result), "message": "Check failed"}
        if isinstance(qdrant_result, Exception):
            qdrant_result = {"status": "unhealthy", "error": str(qdrant_result), "message": "Check failed"}
        if isinstance(localai_result, Exception):
            localai_result = {"status": "unhealthy", "error": str(localai_result), "message": "Check failed"}
        
        # Determine overall health
        all_healthy = all(
            result["status"] == "healthy" 
            for result in [postgres_result, redis_result, qdrant_result, localai_result]
        )
        
        results = {
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "services": {
                "postgres": postgres_result,
                "redis": redis_result,
                "qdrant": qdrant_result,
                "localai": localai_result
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        
        logger.info("Service checks completed", extra={
            "overall_status": results["overall_status"],
            "postgres_status": postgres_result["status"],
            "redis_status": redis_result["status"],
            "qdrant_status": qdrant_result["status"],
            "localai_status": localai_result["status"]
        })
        
        return results

    async def log_dummy_ingest(self) -> Dict[str, Any]:
        """Insert a dummy log entry into PostgreSQL to test write operations."""
        try:
            logger.info("Testing PostgreSQL write operations...")
            
            # Try connecting with password first, fallback to trust authentication
            conn = None
            try:
                conn = await asyncpg.connect(
                    host=self.postgres_config["host"],
                    port=self.postgres_config["port"],
                    user=self.postgres_config["user"],
                    password=self.postgres_config["password"],
                    database=self.postgres_config["database"]
                )
            except Exception:
                # Fallback to trust authentication
                conn = await asyncpg.connect(
                    host=self.postgres_config["host"],
                    port=self.postgres_config["port"],
                    user=self.postgres_config["user"],
                    database=self.postgres_config["database"]
                )
            
            # Insert dummy document
            document_id = await conn.fetchval("""
                INSERT INTO con_selfrag.documents (filename, original_filename, processing_status, metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, "startup_test.md", "startup_test.md", "completed", json.dumps({"test": True, "source": "startup_check"}))
            
            # Insert dummy chunk
            chunk_id = await conn.fetchval("""
                INSERT INTO con_selfrag.document_chunks (document_id, chunk_index, content, token_count)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, document_id, 0, "This is a test document chunk created during startup check.", 12)
            
            await conn.close()
            
            logger.info("PostgreSQL write test successful", extra={
                "document_id": str(document_id),
                "chunk_id": str(chunk_id)
            })
            
            return {
                "status": "success",
                "document_id": str(document_id),
                "chunk_id": str(chunk_id),
                "message": "Dummy data inserted successfully"
            }
            
        except Exception as e:
            logger.error("PostgreSQL write test failed", extra={"error": str(e)}, exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "message": "Failed to insert dummy data"
            }


# Global instance
service_checker = ServiceChecker()


async def startup_checks() -> Dict[str, Any]:
    """Main function to run all startup checks."""
    return await service_checker.check_all_services()


async def test_postgres_write() -> Dict[str, Any]:
    """Test PostgreSQL write operations."""
    return await service_checker.log_dummy_ingest()


if __name__ == "__main__":
    async def main():
        # Run all checks
        results = await startup_checks()
        print(f"Service check results: {results}")
        
        # Test PostgreSQL write if it's healthy
        if results["services"]["postgres"]["status"] == "healthy":
            write_result = await test_postgres_write()
            print(f"PostgreSQL write test: {write_result}")
    
    asyncio.run(main())
