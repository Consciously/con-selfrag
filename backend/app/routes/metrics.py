"""
Prometheus metrics exporter for monitoring system performance and health.
Tracks latency, errors, endpoint hit counts, and custom application metrics.
"""

from typing import Dict, Any
from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from ..config import config
from ..logging_utils import get_logger

router = APIRouter(tags=["Metrics"])
logger = get_logger(__name__)

# Create Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections_total',
    'Number of active connections',
    ['service']
)

SERVICE_HEALTH = Gauge(
    'service_health_status',
    'Service health status (1=healthy, 0=unhealthy)',
    ['service']
)

# Custom application metrics
DOCUMENT_COUNT = Gauge(
    'documents_stored_total',
    'Total number of documents stored in vector database'
)

CACHE_HIT_RATIO = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio percentage'
)

LLM_GENERATION_TIME = Histogram(
    'llm_generation_duration_seconds',
    'LLM text generation duration in seconds',
    ['model']
)

EMBEDDING_GENERATION_TIME = Histogram(
    'embedding_generation_duration_seconds', 
    'Embedding generation duration in seconds',
    ['model']
)


def update_service_health_metrics(service_statuses: Dict[str, str]):
    """Update Prometheus service health metrics."""
    for service, status in service_statuses.items():
        health_value = 1 if status == "healthy" else 0
        SERVICE_HEALTH.labels(service=service).set(health_value)


def update_connection_metrics():
    """Update active connection metrics from database pools."""
    try:
        from ..database.connection import get_database_pools
        
        pools = get_database_pools()
        
        # PostgreSQL connections
        if hasattr(pools, 'postgres_pool') and pools.postgres_pool:
            postgres_connections = len(pools.postgres_pool._holders) if hasattr(pools.postgres_pool, '_holders') else 0
            ACTIVE_CONNECTIONS.labels(service="postgres").set(postgres_connections)
        
        # Redis connections  
        if hasattr(pools, 'redis_pool') and pools.redis_pool:
            redis_connections = pools.redis_pool.created_connections if hasattr(pools.redis_pool, 'created_connections') else 0
            ACTIVE_CONNECTIONS.labels(service="redis").set(redis_connections)
            
    except Exception as e:
        logger.warning(f"Failed to update connection metrics: {str(e)}")


async def update_application_metrics():
    """Update custom application metrics."""
    try:
        # Update document count from Qdrant
        from ..database.connection import get_database_pools
        pools = get_database_pools()
        
        if pools.qdrant_client:
            collections = pools.qdrant_client.get_collections()
            total_docs = 0
            for collection in collections.collections:
                collection_info = pools.qdrant_client.get_collection(collection.name)
                total_docs += collection_info.points_count or 0
            DOCUMENT_COUNT.set(total_docs)
        
        # Update connection metrics
        update_connection_metrics()
        
    except Exception as e:
        logger.warning(f"Failed to update application metrics: {str(e)}")


@router.get(
    "/metrics",
    summary="Prometheus metrics endpoint",
    description="""
    **Export Prometheus metrics for monitoring and alerting.**
    
    This endpoint provides metrics in Prometheus format for monitoring:
    
    **HTTP Metrics:**
    - `http_requests_total`: Total HTTP requests by method, endpoint, and status
    - `http_request_duration_seconds`: Request duration histograms
    
    **Service Health Metrics:**
    - `service_health_status`: Health status of all services (1=healthy, 0=unhealthy)
    - `active_connections_total`: Active database connections by service
    
    **Application Metrics:**
    - `documents_stored_total`: Total documents in vector database
    - `cache_hit_ratio`: Cache effectiveness percentage
    - `llm_generation_duration_seconds`: LLM response time histograms
    - `embedding_generation_duration_seconds`: Embedding generation time histograms
    
    **Usage:**
    Configure Prometheus to scrape this endpoint:
    ```yaml
    scrape_configs:
      - job_name: 'selfrag-api'
        static_configs:
          - targets: ['localhost:8080']
        metrics_path: '/status/metrics'
        scrape_interval: 15s
    ```
    """,
    response_class=Response
)
async def get_metrics():
    """Return Prometheus metrics."""
    logger.debug("Metrics endpoint accessed")
    
    try:
        # Update dynamic metrics before returning
        await update_application_metrics()
        
        # Update service health metrics
        from ..startup_check import service_checker
        results = await service_checker.check_all_services()
        service_statuses = {
            service: status["status"] 
            for service, status in results["services"].items()
        }
        update_service_health_metrics(service_statuses)
        
        # Generate and return metrics
        metrics_data = generate_latest()
        return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
        
    except Exception as e:
        logger.error(f"Failed to generate metrics: {str(e)}", exc_info=True)
        return Response(
            content=f"# Error generating metrics: {str(e)}\n",
            media_type=CONTENT_TYPE_LATEST,
            status_code=500
        )


@router.get(
    "/metrics/health",
    summary="Metrics health check",
    description="Check if metrics collection is working properly"
)
async def metrics_health() -> Dict[str, Any]:
    """Check metrics collection health."""
    try:
        # Test metric collection
        await update_application_metrics()
        
        return {
            "status": "healthy",
            "metrics_available": True,
            "prometheus_format": True,
            "endpoint": "/status/metrics"
        }
    except Exception as e:
        logger.error(f"Metrics health check failed: {str(e)}")
        return {
            "status": "unhealthy", 
            "metrics_available": False,
            "error": str(e)
        }


# Utility functions for instrumenting other parts of the application

def record_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Record HTTP request metrics."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def record_llm_generation_time(model: str, duration: float):
    """Record LLM generation time metric."""
    LLM_GENERATION_TIME.labels(model=model).observe(duration)


def record_embedding_generation_time(model: str, duration: float): 
    """Record embedding generation time metric."""
    EMBEDDING_GENERATION_TIME.labels(model=model).observe(duration)


def set_cache_hit_ratio(ratio: float):
    """Set cache hit ratio metric."""
    CACHE_HIT_RATIO.set(ratio)
