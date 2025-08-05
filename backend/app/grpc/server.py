"""
gRPC server implementation for Selfrag API.

This module provides a gRPC interface for high-performance access to the Selfrag API.
It's designed as a skeleton that can be expanded in Phase 3 with full functionality.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from concurrent import futures

import grpc
from grpc import aio

from ..logging_utils import get_logger

# gRPC service imports (will be generated from proto files)
# For now, we'll create stub classes to demonstrate the structure

logger = get_logger(__name__)


class HealthServicer:
    """gRPC Health Check service implementation."""
    
    async def Check(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        """Handle health check requests."""
        try:
            # For now, return a simple healthy status
            # In Phase 3, this would integrate with the actual health service
            logger.info(f"gRPC health check requested for service: {getattr(request, 'service', 'unknown')}")
            
            # Stub response - would use actual protobuf generated classes
            return {
                'status': 'SERVING',
                'message': 'Service is healthy'
            }
            
        except Exception as e:
            logger.error(f"gRPC health check failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Health check failed: {e}")
            return {
                'status': 'NOT_SERVING',
                'message': f'Service error: {e}'
            }


class QueryServicer:
    """gRPC Query service implementation."""
    
    async def QueryContent(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        """Handle content query requests."""
        try:
            # Extract request parameters (would use actual protobuf fields)
            query = getattr(request, 'query', '')
            limit = getattr(request, 'limit', 10)
            context_text = getattr(request, 'context', None)
            
            logger.info(f"gRPC query request: {query[:50]}...")
            
            # Stub implementation - Phase 3 would integrate with actual query service
            # For now, return a mock response
            return {
                'query': query,
                'context': context_text,
                'results': [],
                'total_results': 0,
                'query_time_ms': 50,
                'reranked': False,
                'context_used': bool(context_text)
            }
            
        except Exception as e:
            logger.error(f"gRPC query failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Query failed: {e}")
            return {
                'query': getattr(request, 'query', ''),
                'results': [],
                'total_results': 0,
                'query_time_ms': 0,
                'reranked': False,
                'context_used': False
            }


class IngestServicer:
    """gRPC Ingest service implementation."""
    
    async def IngestContent(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        """Handle content ingestion requests."""
        try:
            # Extract request parameters (would use actual protobuf fields)
            content = getattr(request, 'content', '')
            metadata = getattr(request, 'metadata', {})
            
            logger.info(f"gRPC ingest request: {len(content)} chars")
            
            # Stub implementation - Phase 3 would integrate with actual ingest service
            return {
                'id': 'stub_document_id',
                'status': 'success',
                'message': 'Content ingested successfully (stub)'
            }
            
        except Exception as e:
            logger.error(f"gRPC ingest failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Ingest failed: {e}")
            return {
                'id': '',
                'status': 'error',
                'message': f'Ingest failed: {e}'
            }


class GRPCServer:
    """gRPC server management class."""
    
    def __init__(self, port: int = 50051):
        self.port = port
        self.server: Optional[grpc.aio.Server] = None
        
    async def start(self) -> None:
        """Start the gRPC server."""
        try:
            # Create async gRPC server
            self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
            
            # Add servicers (would use actual protobuf generated code)
            # For now, we create stub servicers to demonstrate structure
            health_servicer = HealthServicer()
            query_servicer = QueryServicer()
            ingest_servicer = IngestServicer()
            
            # In Phase 3, these would be:
            # add_HealthServicer_to_server(health_servicer, self.server)
            # add_QueryServicer_to_server(query_servicer, self.server)
            # add_IngestServicer_to_server(ingest_servicer, self.server)
            
            # Add insecure port
            listen_addr = f'[::]:{self.port}'
            self.server.add_insecure_port(listen_addr)
            
            # Start server
            await self.server.start()
            logger.info(f"🚀 gRPC server started on {listen_addr}")
            
        except Exception as e:
            logger.error(f"Failed to start gRPC server: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the gRPC server."""
        if self.server:
            logger.info("🛑 Stopping gRPC server...")
            await self.server.stop(grace=5.0)
            logger.info("✅ gRPC server stopped")
    
    async def wait_for_termination(self) -> None:
        """Wait for server termination."""
        if self.server:
            await self.server.wait_for_termination()


# Global gRPC server instance
grpc_server: Optional[GRPCServer] = None


async def start_grpc_server(port: int = 50051) -> GRPCServer:
    """Start the gRPC server as a background service."""
    global grpc_server
    
    if grpc_server is None:
        grpc_server = GRPCServer(port)
        await grpc_server.start()
    
    return grpc_server


async def stop_grpc_server() -> None:
    """Stop the gRPC server."""
    global grpc_server
    
    if grpc_server:
        await grpc_server.stop()
        grpc_server = None


async def get_grpc_health_status() -> Dict[str, Any]:
    """Get gRPC server health status."""
    global grpc_server
    
    if grpc_server and grpc_server.server:
        return {
            "status": "healthy",
            "port": grpc_server.port,
            "message": "gRPC server is running"
        }
    else:
        return {
            "status": "unhealthy", 
            "port": None,
            "message": "gRPC server is not running"
        }


# Development main function for testing
async def main():
    """Main function for development testing."""
    logging.basicConfig(level=logging.INFO)
    
    server = GRPCServer()
    
    try:
        await server.start()
        logger.info("gRPC server started successfully - Press Ctrl+C to stop")
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
