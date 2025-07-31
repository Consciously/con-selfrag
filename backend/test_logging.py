#!/usr/bin/env python3
"""
Test script to verify logging setup works correctly.
"""

import asyncio
from app.logging_utils import get_logger
from app.services.ingest_service import IngestService
from app.services.query_service import QueryService

logger = get_logger(__name__)


async def test_logging():
    """Test the logging setup across different components."""
    logger.info("🧪 Starting logging test suite...")
    
    # Test basic logging
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test service logging
    ingest_service = IngestService()
    query_service = QueryService()
    
    # Test ingest service logging
    logger.info("Testing ingest service...")
    try:
        result = await ingest_service.ingest_content(
            content="Test content for logging verification",
            metadata={"test": True, "source": "logging_test"}
        )
        logger.info(f"Ingest test successful: {result.id}")
    except Exception as e:
        logger.error(f"Ingest test failed: {e}")
    
    # Test query service logging
    logger.info("Testing query service...")
    try:
        result = await query_service.query_content(
            query="test framework",
            limit=5,
            filters={"source": "logging_test"}
        )
        logger.info(f"Query test successful: {len(result.results)} results")
    except Exception as e:
        logger.error(f"Query test failed: {e}")
    
    # Test batch ingest logging
    logger.info("Testing batch ingest...")
    try:
        results = await ingest_service.batch_ingest(
            contents=["First test content", "Second test content"],
            metadatas=[{"batch": 1}, {"batch": 2}]
        )
        logger.info(f"Batch ingest test successful: {len(results)} items")
    except Exception as e:
        logger.error(f"Batch ingest test failed: {e}")
    
    logger.info("✅ Logging test suite completed!")


if __name__ == "__main__":
    asyncio.run(test_logging())
