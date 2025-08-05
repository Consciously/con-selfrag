# Monitoring & Developer Diagnostics Configuration

This document describes the monitoring and diagnostics features added in the final 15% completion phase.

## 🎯 Completed Features

### 1. Service Health Dashboard

**Enhanced `/status` endpoint** - Comprehensive system status aggregating all services:

- **Endpoint**: `GET /status/`
- **Quick Check**: `GET /status/quick`
- **Features**:
  - Database connections (PostgreSQL, Redis, Qdrant)
  - Vector DB status and collection counts
  - LocalAI responsiveness and model availability
  - gRPC service health (if enabled)
  - Response time measurements for each service
  - System metrics (CPU, memory, disk usage)
  - Connection pool statistics
  - Application uptime tracking

**Usage Examples:**

```bash
# Full system status with metrics
curl http://localhost:8080/status/

# Quick status for load balancers
curl http://localhost:8080/status/quick

# Legacy health endpoints still available
curl http://localhost:8080/health/
curl http://localhost:8080/health/services
```

### 2. Prometheus Metrics Exporter

**Added prometheus-fastapi-instrumentator** for comprehensive metrics:

- **Endpoint**: `GET /status/metrics`
- **Health Check**: `GET /status/metrics/health`

**Available Metrics:**

- `http_requests_total` - HTTP request counts by method/endpoint/status
- `http_request_duration_seconds` - Request duration histograms
- `service_health_status` - Service health (1=healthy, 0=unhealthy)
- `active_connections_total` - Database connection pool metrics
- `documents_stored_total` - Vector database document counts
- `cache_hit_ratio` - Cache effectiveness percentage
- `llm_generation_duration_seconds` - LLM response time histograms
- `embedding_generation_duration_seconds` - Embedding generation time

**Prometheus Configuration:**

```yaml
scrape_configs:
  - job_name: 'selfrag-api'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/status/metrics'
    scrape_interval: 15s
```

### 3. Developer Logging Toggle

**Environment-based debug configuration:**

```bash
# .env file settings
DEBUG_LOGGING=true          # Enable verbose debug logging
PERFORMANCE_LOGGING=true    # Enable performance metrics logging
LOG_LEVEL=DEBUG            # Base logging level
```

**Features:**

- **Request Tracking**: Each request gets a unique ID for correlation
- **Performance Logs**: Separate log file for timing and metrics
- **Enhanced Console**: More detailed console output in debug mode
- **CLI Debug Mode**: `./selfrag --debug command` for verbose CLI output

**Log File Organization:**

- `logs/app.log` - Main application logs
- `logs/error.log` - Error-only logs with stack traces
- `logs/performance.log` - Performance metrics (when enabled)

### 4. Refactored Docker Healthchecks

**Improved healthcheck configuration:**

- **FastAPI Gateway**: Uses new `/status/quick` endpoint
- **LocalAI**: Extended timeout for model loading
- **Qdrant**: Optimized check frequency
- **PostgreSQL**: Added connection timeout
- **Redis**: Added latency monitoring

**Key Improvements:**

- More reliable health detection
- Reduced false positives during startup
- Better timeout handling
- Optimized check frequencies

## 🛠️ Installation & Setup

### 1. Install New Dependencies

```bash
cd backend
pip install psutil prometheus-fastapi-instrumentator
```

Or with uv:

```bash
uv add psutil prometheus-fastapi-instrumentator
```

### 2. Environment Configuration

Copy the updated `.env.example` to `.env` and configure:

```bash
# Enable debugging features
DEBUG_LOGGING=true
PERFORMANCE_LOGGING=true
LOG_LEVEL=DEBUG
```

### 3. Docker Deployment

The updated `docker-compose.yml` includes improved healthchecks:

```bash
# Start with new health monitoring
docker-compose up -d

# Check service health
docker-compose ps
curl http://localhost:8080/status/
```

## 📊 Monitoring Integration

### Prometheus + Grafana

1. **Configure Prometheus** to scrape `/status/metrics`
2. **Import Grafana dashboards** for FastAPI metrics
3. **Set up alerts** based on service health metrics

### Load Balancer Integration

Use `/status/quick` for high-frequency health checks:

```nginx
# Nginx upstream health check
upstream selfrag_backend {
    server localhost:8080;
    health_check uri=/status/quick;
}
```

### Development Workflow

**Debug Mode:**

```bash
# Enable debug logging
export DEBUG_LOGGING=true
export PERFORMANCE_LOGGING=true

# Run with debug CLI
./selfrag --debug health
./selfrag --debug --verbose query "test question"
```

**Performance Monitoring:**

```bash
# Check metrics endpoint
curl http://localhost:8080/status/metrics | grep -E "(http_request|service_health)"

# Monitor performance logs
tail -f logs/performance.log
```

## 🎉 Benefits Achieved

### ✅ Production Readiness

- Comprehensive health monitoring across all services
- Prometheus metrics for observability
- Enhanced error detection and debugging

### ✅ Developer Experience

- Toggle-based debug logging
- Detailed performance insights
- Enhanced CLI with verbose modes

### ✅ Operational Excellence

- Improved Docker healthchecks
- Load balancer-ready endpoints
- Standardized monitoring approach

### ✅ System Insights

- Real-time performance metrics
- Connection pool monitoring
- Service dependency tracking

## 📈 System Status: 100% Complete

**Phase 2 Monitoring & Diagnostics - COMPLETE!**

From 85% → 100% completion achieved with:

- ✅ Service Health Dashboard (`/status/`)
- ✅ Prometheus Metrics Exporter (`/status/metrics`)
- ✅ Developer Logging Toggle (environment-based)
- ✅ Refactored Docker Healthchecks

**The con-selfrag project now has enterprise-grade monitoring and diagnostics capabilities ready for production deployment!** 🚀
