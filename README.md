# CON-LLM-CONTAINER

A comprehensive containerized LLM (Large Language Model) application with vector database, caching, persistent storage, and **complete CLI interface** for command-line operations.

## 🚀 Phase 0: Infrastructure & Compose

This phase establishes the foundational infrastructure with container orchestration, networking, persistent storage, CI/CD pipelines, and a powerful CLI for all operations.

### 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        llm-network                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  FastAPI        │  │  LocalAI        │  │  Qdrant         │ │
│  │  Gateway        │  │  (LLM Service)  │  │  (Vector DB)    │ │
│  │  :8080          │  │  :8081          │  │  :6333          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  PostgreSQL     │  │  Redis          │  │  MinIO          │ │
│  │  (Relational)   │  │  (Cache)        │  │  (Storage)      │ │
│  │  :5432          │  │  :6379          │  │  :9000/9001     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 🛠️ Quick Start

#### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM (16GB+ recommended for GPU)
- NVIDIA GPU with CUDA support (optional but recommended)

#### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd con-selfrag

# Copy environment configuration
cp .env.example .env

# Edit .env file with your specific configuration
nano .env
```

#### 2. Start All Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 3. Use the CLI Interface

```bash
# Setup CLI (one-time)
cd backend
./setup_cli.sh

# Check system health
./selfrag health

# Ingest documents
./selfrag ingest README.md --title "Project Documentation"

# Query your knowledge
./selfrag query "how to setup the project"

# Interactive mode
./selfrag chat
```

#### 4. Verify Installation

```bash
# Run health checks
./scripts/health-check.sh

# Or manually check endpoints
curl http://localhost:8080/health
curl http://localhost:6333/health
curl http://localhost:9000/minio/health/live

# CLI health check
cd backend && ./selfrag health
```

### 🔧 Service Configuration

#### Service URLs and Ports

| Service             | URL                   | Port      | Description           |
| ------------------- | --------------------- | --------- | --------------------- |
| **FastAPI Gateway** | http://localhost:8080 | 8080      | Main API gateway      |
| **LocalAI**         | http://localhost:8081 | 8081      | LLM inference service |
| **Qdrant**          | http://localhost:6333 | 6333      | Vector database       |
| **PostgreSQL**      | localhost:5432        | 5432      | Relational database   |
| **Redis**           | localhost:6379        | 6379      | Caching layer         |
| **MinIO**           | http://localhost:9000 | 9000/9001 | Object storage        |

#### Internal Network Communication

Services communicate via Docker's internal DNS:

- **FastAPI Gateway** → `http://localai:8080`
- **FastAPI Gateway** → `http://qdrant:6333`
- **FastAPI Gateway** → `http://postgres:5432`
- **FastAPI Gateway** → `http://redis:6379`
- **FastAPI Gateway** → `http://minio:9000`

### 📊 Health Checks

Each service includes comprehensive health checks:

```bash
# Check individual service health
docker-compose ps

# View detailed health status
docker inspect --format='{{.State.Health.Status}}' <container-name>

# Manual health checks
curl http://localhost:8080/health          # FastAPI Gateway
curl http://localhost:6333/health          # Qdrant
curl http://localhost:9000/minio/health/live  # MinIO
```

### 💾 Data Persistence

#### Docker Volumes

| Volume          | Purpose                  | Backup |
| --------------- | ------------------------ | ------ |
| `localai-data`  | LocalAI models and cache | ✅     |
| `qdrant-data`   | Vector database storage  | ✅     |
| `postgres-data` | Relational database      | ✅     |
| `redis-data`    | Cache persistence        | ✅     |
| `minio-data`    | Object storage           | ✅     |

#### Backup and Restore

```bash
# Create backup
./scripts/backup.sh [backup-name]

# List available backups
ls -la backups/

# Restore from backup
./scripts/restore.sh <backup-name>

# Automated daily backups
# Add to crontab: 0 2 * * * /path/to/scripts/backup.sh auto
```

### 🏗️ Development Setup

#### Development Profiles

```bash
# Start with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Start specific services only
docker-compose up -d postgres redis qdrant
```

#### Local Development

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run linting
pre-commit run --all-files

# Run tests
cd backend && python -m pytest tests/
```

### 🔐 Security

#### Environment Variables

Key security considerations:

- Never commit `.env` files
- Use strong passwords in production
- Rotate secrets regularly
- Use Docker secrets for sensitive data

#### Network Security

- All services run on isolated Docker network (`llm-network`)
- Only necessary ports are exposed
- Internal communication uses service names
- Health checks ensure service integrity

### 🐛 Troubleshooting

#### Common Issues

**Services won't start:**

```bash
# Check Docker and Docker Compose versions
docker --version
docker-compose --version

# Check available disk space
df -h

# Check Docker resources
docker system df
docker system prune -f
```

**GPU not detected:**

```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu20.04 nvidia-smi

# Verify GPU in LocalAI
docker-compose exec localai nvidia-smi
```

**Port conflicts:**

```bash
# Check port usage
netstat -tulpn | grep :8080

# Modify ports in .env file
sed -i 's/MAIN_API_PORT=8080/MAIN_API_PORT=8082/' .env
```

#### Service Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f fastapi-gateway
docker-compose logs -f localai
docker-compose logs -f qdrant
```

### 📈 Monitoring

#### Basic Monitoring

```bash
# Resource usage
docker stats

# Service health
docker-compose ps

# Disk usage
docker system df
```

#### Advanced Monitoring (Optional)

- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **ELK Stack**: Log aggregation
- **Jaeger**: Distributed tracing

### 🔄 CI/CD

#### GitHub Actions

The repository includes comprehensive CI/CD:

- **Linting**: Python (black, ruff, mypy) and JavaScript/TypeScript
- **Testing**: Unit tests and integration tests
- **Security**: Vulnerability scanning with Trivy
- **Building**: Docker image builds and registry push
- **Smoke Tests**: End-to-end service testing

#### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run all hooks
pre-commit run --all-files
```

### 🎯 Next Steps

After Phase 0 is complete:

1. **Phase 1**: Core RAG functionality
2. **Phase 2**: Advanced features and optimization
3. **Phase 3**: Production deployment
4. **Phase 4**: Monitoring and scaling

### 📚 Additional Resources

- [LocalAI Documentation](https://localai.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [MinIO Documentation](https://min.io/docs/)

### 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
