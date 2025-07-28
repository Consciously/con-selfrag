# Template Structure and Extension Points

## Overview

The `con-llm-container-base` is a production-ready, extensible template for building LLM-powered applications with a clean frontend-backend-AI architecture. It follows YAGNI principles and SOLID design patterns while providing clear extension points for customization.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │    │      Ollama     │    │    Database     │
│   (Prepared)    │◄──►│   FastAPI App   │◄──►│   LLM Service   │    │   (Prepared)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Project Structure

```
con-llm-container-base/
├── backend/                    # FastAPI backend service
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── config.py          # Configuration management
│   │   ├── models.py          # Pydantic models (API contracts)
│   │   ├── ollama_client.py   # Ollama integration client
│   │   └── database/          # Database integration (prepared)
│   ├── Dockerfile             # Backend container definition
│   └── pyproject.toml         # Python dependencies and metadata
├── frontend/                   # Frontend preparation directory
│   └── README.md              # Frontend integration guide
├── shared/                     # Shared type definitions
│   ├── types.py               # Python types (backend)
│   └── types.ts               # TypeScript types (frontend)
├── docker-compose.yml          # Main orchestration file
├── backend.yml                # Backend-specific services
├── frontend.yml               # Frontend-specific services
├── .env.example               # Environment configuration template
└── README.md                  # Main documentation
```

## Core Components

### 1. Backend Application (`backend/app/`)

#### `main.py` - FastAPI Application
- **Purpose**: Main application entry point with comprehensive API endpoints
- **Key Features**:
  - CORS middleware for frontend integration
  - Request logging with Loguru
  - Comprehensive health check endpoints (`/health`, `/health/live`, `/health/ready`)
  - Text generation endpoints (`/generate`, `/ask`)
  - Model management endpoint (`/models`)
  - Prometheus metrics endpoint (`/metrics`)
  - Error handling with structured responses
- **Extension Points**:
  - Add new API endpoints
  - Customize middleware stack
  - Integrate authentication/authorization
  - Add rate limiting and caching
  - Implement custom metrics

#### `config.py` - Configuration Management
- **Purpose**: Centralized configuration with environment variable support
- **Key Features**:
  - Pydantic-based configuration validation
  - Environment variable loading with defaults
  - Type-safe configuration access
  - Comprehensive logging configuration
- **Extension Points**:
  - Add new configuration parameters
  - Implement configuration validation rules
  - Add environment-specific configurations
  - Integrate configuration hot-reloading

#### `models.py` - API Contracts
- **Purpose**: Comprehensive Pydantic models for request/response validation
- **Key Features**:
  - Type-safe API contracts with detailed examples
  - Automatic OpenAPI documentation generation
  - Request/response validation with error handling
  - Consistent error response models
  - Health check and metrics models
- **Extension Points**:
  - Add new request/response models
  - Extend existing models with additional fields
  - Add custom validators and transformers
  - Implement model versioning

#### `ollama_client.py` - LLM Integration
- **Purpose**: Abstracted Ollama client for LLM operations
- **Key Features**:
  - Async HTTP client with timeout handling
  - Comprehensive error handling and retries
  - Streaming response support
  - Model management and health checks
  - Performance metrics collection
- **Extension Points**:
  - Add new LLM providers (OpenAI, Anthropic, etc.)
  - Implement model switching and load balancing
  - Add custom generation parameters
  - Implement request caching and optimization

### 2. Shared Types (`shared/`)

#### `types.py` & `types.ts`
- **Purpose**: Consistent type definitions across frontend and backend
- **Key Features**:
  - API contract synchronization
  - Type safety across language boundaries
  - Documentation generation support
  - Version compatibility
- **Extension Points**:
  - Add new shared types for features
  - Extend existing interfaces
  - Implement type validation utilities
  - Add serialization helpers

### 3. Container Orchestration

#### Docker Compose Configuration
- **Main File**: `docker-compose.yml` - Production services
- **Backend Services**: `backend.yml` - Backend-only deployment
- **Frontend Services**: `frontend.yml` - Frontend-only deployment
- **Profiles**: `dev`, `ollama` for different deployment scenarios

## Extension Points

### 1. Frontend Integration

The template is designed to work with any frontend framework:

**Supported Frameworks:**
- React, Vue, Svelte, Angular applications
- Next.js, Nuxt.js, SvelteKit full-stack frameworks
- Static sites with vanilla JavaScript
- Mobile applications via API
- Desktop applications (Electron, Tauri)

**Integration Steps:**
1. Copy shared types from `shared/types.ts`
2. Configure API client with base URL
3. Implement authentication if needed
4. Configure CORS origins in backend

### 2. Database Integration

Prepared structure for database integration:

```python
# backend/app/database/models.py (to be created)
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), index=True)
    user_message = Column(Text)
    ai_response = Column(Text)
    model_used = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelUsage(Base):
    __tablename__ = "model_usage"
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100))
    request_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    last_used = Column(DateTime, default=datetime.utcnow)
```

**Database Options:**
- **PostgreSQL**: For relational data and complex queries
- **Qdrant**: For vector storage and semantic search
- **Redis**: For caching and session management
- **MongoDB**: For document storage and flexible schemas

### 3. Authentication & Authorization

Add authentication layer:

```python
# backend/app/auth.py (to be created)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Usage in endpoints
@app.post("/generate")
async def generate_text(
    request: GenerateRequest,
    user = Depends(verify_token)
):
    # Protected endpoint logic
    pass
```

### 4. Additional LLM Providers

Extend the client interface:

```python
# backend/app/clients/base.py (to be created)
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any

class LLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def stream_generate(self, prompt: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        pass
    
    @abstractmethod
    async def list_models(self) -> Dict[str, Any]:
        pass

# backend/app/clients/openai_client.py (to be created)
import openai
from .base import LLMClient

class OpenAIClient(LLMClient):
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return {
            "response": response.choices[0].message.content,
            "model": model,
            "usage": response.usage.dict() if response.usage else None
        }
```

### 5. Monitoring & Observability

Enhanced monitoring capabilities:

```python
# backend/app/monitoring.py (to be created)
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active WebSocket connections')
OLLAMA_REQUESTS = Counter('ollama_requests_total', 'Total Ollama requests', ['model', 'endpoint'])

def track_metrics(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(method='POST', endpoint=func.__name__, status='success').inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(method='POST', endpoint=func.__name__, status='error').inc()
            raise
        finally:
            REQUEST_DURATION.observe(time.time() - start_time)
    return wrapper
```

## Configuration Management

### Environment Variables

The template uses comprehensive environment variable configuration:

```bash
# Backend Configuration
DEFAULT_MODEL=llama3.2:1b
API_PORT=8000
API_TIMEOUT=300
LOG_LEVEL=INFO

# Ollama Configuration
OLLAMA_HOST=0.0.0.0
OLLAMA_PORT=11434

# Port Mappings
MAIN_API_PORT=8080
MAIN_OLLAMA_PORT=11434
DEV_API_PORT=8081

# Volume Configuration
OLLAMA_MODELS_PATH=./models
LOGS_PATH=./logs
DATA_PATH=./data

# Logging Configuration
LOG_ROTATION=daily
LOG_MAX_SIZE=100MB
LOG_RETENTION_DAYS=30

# Frontend Configuration (Optional)
FRONTEND_PORT=3000
FRONTEND_DEV_PORT=3001
BACKEND_URL=http://backend:8000
NODE_ENV=production

# Database Configuration (when implemented)
POSTGRES_URL=postgresql://user:pass@localhost:5432/db
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379
```

### Adding New Configuration

1. Update `backend/app/config.py`:
```python
class Config(BaseModel):
    # Existing fields...
    
    # New configuration
    new_feature_enabled: bool = Field(default=False, description="Enable new feature")
    new_feature_timeout: float = Field(default=10.0, description="New feature timeout")
    new_feature_api_key: Optional[str] = Field(default=None, description="API key for new feature")
```

2. Update `.env.example`:
```bash
# New Feature Configuration
NEW_FEATURE_ENABLED=false
NEW_FEATURE_TIMEOUT=10.0
NEW_FEATURE_API_KEY=your_api_key_here
```

3. Use in application:
```python
from app.config import get_config

config = get_config()
if config.new_feature_enabled:
    # Use new feature
    pass
```

## Development Workflows

### Adding New API Endpoints

1. **Define Models**: Add request/response models in `models.py`
```python
class NewFeatureRequest(BaseModel):
    input_data: str = Field(..., description="Input for new feature")
    options: Optional[Dict[str, Any]] = Field(default=None)

class NewFeatureResponse(BaseModel):
    result: str = Field(..., description="Feature result")
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

2. **Implement Endpoint**: Add to `main.py`
```python
@app.post("/new-feature", response_model=NewFeatureResponse)
async def new_feature(request: NewFeatureRequest):
    # Implementation
    return NewFeatureResponse(result="processed", metadata={})
```

3. **Update Shared Types**: Sync types in `shared/types.py` and `shared/types.ts`

4. **Test**: Use development environment
```bash
docker compose --profile dev up
```

### Adding New Services

1. Create service-specific configuration
2. Update Docker Compose files
3. Add health checks and monitoring
4. Update environment configuration

### Frontend Integration

1. **Setup API Client**:
```typescript
// frontend/src/api/client.ts
import { GenerateRequest, GenerateResponse } from '../types/shared';

class APIClient {
  constructor(private baseURL: string) {}
  
  async generate(request: GenerateRequest): Promise<GenerateResponse> {
    const response = await fetch(`${this.baseURL}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    return response.json();
  }
}
```

2. **Configure CORS**: Update backend configuration
3. **Test Integration**: Verify API communication

## Best Practices

### Code Organization
- **Separation of Concerns**: Keep business logic separate from framework code
- **Dependency Injection**: Use FastAPI's dependency system for testability
- **Single Responsibility**: Each module should have one clear purpose
- **Error Handling**: Implement comprehensive error handling with structured responses

### Configuration Management
- **Environment Variables**: Use for all configuration
- **Validation**: Validate configuration on startup
- **Documentation**: Document all configuration options
- **Defaults**: Provide sensible defaults for development

### API Design
- **Consistent Naming**: Use clear, consistent endpoint naming
- **HTTP Status Codes**: Implement proper status codes
- **Error Messages**: Provide helpful error messages
- **Versioning**: Plan for API versioning when needed
- **Documentation**: Maintain comprehensive OpenAPI documentation

### Security
- **Authentication**: Implement proper authentication for production
- **Input Validation**: Validate all inputs thoroughly
- **HTTPS**: Use HTTPS in production environments
- **Secrets Management**: Never commit secrets to version control
- **CORS**: Configure CORS appropriately for your frontend

### Performance
- **Async Operations**: Use async/await for I/O operations
- **Connection Pooling**: Implement connection pooling for databases
- **Caching**: Add caching for frequently accessed data
- **Monitoring**: Monitor performance metrics and bottlenecks

## Testing Strategy

### Unit Tests
```python
# tests/test_ollama_client.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.app.ollama_client import OllamaClient

@pytest.mark.asyncio
async def test_generate_text():
    client = OllamaClient()
    
    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {
            "response": "Hello, world!",
            "model": "llama3.2:1b",
            "done": True
        }
        
        response = await client.generate("Hello", "llama3.2:1b")
        
        assert response["response"] == "Hello, world!"
        assert response["model"] == "llama3.2:1b"
        mock_request.assert_called_once()
```

### Integration Tests
```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data

def test_generate_endpoint():
    response = client.post("/generate", json={
        "prompt": "Hello",
        "model": "llama3.2:1b",
        "temperature": 0.7
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "model" in data
```

### Load Testing
```python
# tests/load_test.py
import asyncio
import aiohttp
import time

async def load_test():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = session.post('http://localhost:8080/ask', json={
                "question": f"Test question {i}",
                "temperature": 0.5
            })
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        print(f"Completed 100 requests in {end_time - start_time:.2f} seconds")
        print(f"Average response time: {(end_time - start_time) / 100:.3f} seconds")
```

## Deployment Options

### Development
```bash
# Full development environment
docker compose --profile dev up

# Backend only
docker compose -f backend.yml up

# With debugging
docker compose --profile dev up --build
```

### Production
```bash
# Production deployment
cp .env.example .env
# Configure production values
docker compose up -d

# With scaling
docker compose up -d --scale backend=3
```

### Kubernetes
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-backend
  labels:
    app: llm-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-backend
  template:
    metadata:
      labels:
        app: llm-backend
    spec:
      containers:
      - name: backend
        image: con-llm-container-base:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEFAULT_MODEL
          value: "llama3.2:1b"
        - name: LOG_LEVEL
          value: "INFO"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: llm-backend-service
spec:
  selector:
    app: llm-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Migration Guide

### From Legacy Versions
1. **Update Configuration**: Migrate to new environment variable format
2. **Update Dependencies**: Check `pyproject.toml` for new requirements
3. **Update Docker Commands**: Use `docker compose` instead of `docker-compose`
4. **Test API Compatibility**: Verify existing integrations still work
5. **Update Shared Types**: Sync frontend types with new backend models

### Adding Databases
1. **Choose Database**: PostgreSQL for relational, Qdrant for vectors
2. **Add Configuration**: Update `config.py` with database settings
3. **Create Models**: Add SQLAlchemy or database-specific models
4. **Add Endpoints**: Implement CRUD operations
5. **Update Docker Compose**: Add database services
6. **Add Migrations**: Implement database migration system

### Scaling Considerations
1. **Stateless Design**: Ensure application is stateless
2. **Shared Storage**: Use shared volumes for model storage
3. **Load Balancing**: Add reverse proxy (nginx, traefik)
4. **Database Connections**: Implement connection pooling
5. **Monitoring**: Add comprehensive monitoring and alerting

## Conclusion

This template provides a robust foundation for LLM applications with:

- **Production-Ready**: Comprehensive logging, monitoring, and error handling
- **Extensible**: Clear extension points for customization
- **Type-Safe**: Shared types across frontend and backend
- **Scalable**: Designed for horizontal scaling
- **Developer-Friendly**: Excellent development experience with hot reload and debugging

The template follows modern best practices and provides a solid starting point for building sophisticated LLM-powered applications while maintaining flexibility for future enhancements and customizations.
