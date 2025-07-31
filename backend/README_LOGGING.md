# 📝 Logging System Documentation

## Overview

The Selfrag backend now features a comprehensive structured logging system using [Loguru](https://github.com/Delgan/loguru) for enhanced observability and debugging.

## 🚀 Quick Start

### 1. Start the Application

```bash
cd /mnt/workspace/projects/con-selfrag/backend
poetry run uvicorn app.main:app --reload
```

### 2. Watch Logs in Real-Time

**Terminal logs** will show:
```
2025-07-31 17:35:41 | INFO     | app.main:startup_event:62 - 🚀 Selfrag API starting up...
2025-07-31 17:35:41 | INFO     | app.main:startup_event:63 - Environment: development
2025-07-31 17:35:41 | INFO     | app.main:log_requests:79 - Incoming request | method=GET | url=http://localhost:8000/health | client=127.0.0.1
2025-07-31 17:35:41 | INFO     | app.main:log_requests:88 - Request completed | method=GET | url=http://localhost:8000/health | status_code=200 | duration_ms=2.34
```

### 3. Test the Endpoints

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test ingest endpoint
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "FastAPI is a modern web framework", "metadata": {"tags": ["api", "python"]}}'

# Test query endpoint
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "web frameworks", "limit": 5}'
```

## 📁 Log Files

The logging system creates the following files in `backend/logs/`:

- **`app.log`** - All application logs (DEBUG level and above)
- **`error.log`** - Error logs only (ERROR level) in JSON format

## 🔧 Configuration

### Log Levels
- **Console**: INFO level with colors
- **File**: DEBUG level with rotation
- **Error file**: ERROR level with JSON format

### File Rotation
- **App logs**: 10MB rotation, 30-day retention
- **Error logs**: 5MB rotation, 30-day retention

## 🎯 Usage Examples

### Basic Logging

```python
from app.logging_utils import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("User logged in", extra={"user_id": 123})
logger.error("Database connection failed", exc_info=True)
```

### Structured Logging

```python
# With context data
logger.info(
    "Processing request",
    extra={
        "endpoint": "/query",
        "user_id": 123,
        "query_length": len(query),
        "filters": filters
    }
)
```

### Service-Level Logging

```python
# In services
logger.info(
    "Content ingested",
    extra={
        "content_id": content_id,
        "content_length": len(content),
        "processing_time_ms": processing_time
    }
)
```

## 🔍 Log Analysis

### View Logs in Terminal
```bash
# Real-time log viewing
tail -f logs/app.log

# Error logs only
tail -f logs/error.log

# Search for specific patterns
grep "ERROR" logs/app.log
```

### JSON Log Analysis
```bash
# Parse JSON error logs
jq '.' logs/error.log

# Filter specific error types
jq 'select(.level == "ERROR")' logs/error.log
```

## 🧪 Testing

### Run Logging Tests
```bash
# Test the logging system
poetry run python test_logging.py

# Run full test suite
poetry run pytest test_endpoints.py -v
```

### Manual Testing
1. Start the server: `poetry run uvicorn app.main:app --reload`
2. Open browser: http://localhost:8000/docs
3. Try the endpoints and watch the logs

## 🎛️ Environment Variables

You can control logging behavior with environment variables:

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Custom log directory
export LOG_DIR=/custom/logs/path
```

## 🚨 Troubleshooting

### Common Issues

1. **No logs appearing?**
   - Check if logs directory exists: `ls -la logs/`
   - Verify file permissions: `chmod 755 logs/`

2. **Too much log output?**
   - Adjust log level in `logging_utils.py`
   - Use filters when viewing logs

3. **Large log files?**
   - Rotation is automatic (10MB for app.log, 5MB for error.log)
   - Old logs are automatically cleaned up after 30 days

### Log Formats

**Console format:**
```
2025-07-31 17:35:41 | INFO     | app.main:startup_event:62 - Message
```

**File format:**
```
2025-07-31 17:35:41 | INFO     | app.main:startup_event:62 - Message
```

**JSON format (error.log):**
```json
{
  "text": "2025-07-31 17:35:41.123 | ERROR    | app.main:log_requests:95 - Request failed",
  "record": {
    "elapsed": {"repr": "0:00:00.123456", "seconds": 0.123456},
    "exception": null,
    "extra": {},
    "file": {"name": "main.py", "path": "/app/app/main.py"},
    "function": "log_requests",
    "level": {"icon": "❌", "name": "ERROR", "no": 40},
    "line": 95,
    "message": "Request failed",
    "module": "main",
    "name": "app.main",
    "process": {"id": 123, "name": "MainProcess"},
    "thread": {"id": 123456789, "name": "MainThread"},
    "time": {"repr": "2025-07-31 17:35:41.123456+00:00", "timestamp": 1234567890.123456}
  }
}
```

## 📈 Next Steps

1. **Production Monitoring**: Set up log aggregation (ELK stack, Datadog, etc.)
2. **Alerting**: Configure alerts based on error log patterns
3. **Performance**: Add custom metrics and APM integration
4. **Security**: Add request/response sanitization for sensitive data
