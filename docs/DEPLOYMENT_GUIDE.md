# SelfRAG Deployment Guide

## Quick Deployment

### Local Development

```bash
# 1. Clone and setup
git clone <repository-url>
cd con-selfrag
cp .env.example .env

# 2. Start services
docker-compose up -d

# 3. Verify deployment
./scripts/health-check.sh
cd backend && python selfrag_cli.py health
```

### Production Deployment

#### 1. Environment Configuration

Create production `.env`:

```bash
# Production API settings
FASTAPI_DEBUG=false
FASTAPI_HOST=0.0.0.0
LOG_LEVEL=INFO

# Secure database credentials
POSTGRES_PASSWORD=secure_production_password
REDIS_PASSWORD=secure_redis_password

# Performance tuning
DATABASE_POOL_SIZE=20
CACHE_TTL_SECONDS=7200
MAX_CHUNK_SIZE=1500
```

#### 2. Resource Limits

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'
services:
  fastapi-gateway:
    environment:
      - FASTAPI_DEBUG=false
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  localai:
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G
          cpus: '2.0'

  qdrant:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

#### 3. Deploy Production Stack

```bash
# Deploy with production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify deployment
./scripts/health-check.sh
```

## Scaling and Performance

### Horizontal Scaling

For high-traffic deployments:

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  fastapi-gateway:
    deploy:
      replicas: 3

  # Load balancer
  nginx:
    image: nginx:alpine
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - fastapi-gateway
```

### Performance Tuning

#### Database Optimization

```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
```

#### Cache Configuration

```python
# Optimize cache settings in backend/app/services/cache_service.py
CACHE_L1_MAX_SIZE = 2000  # Increase L1 cache size
CACHE_L1_TTL_SECONDS = 7200  # Longer TTL for production
CACHE_COMPRESSION_THRESHOLD = 512  # Lower compression threshold
```

## Monitoring and Maintenance

### Health Monitoring

Create monitoring script (`monitor.sh`):

```bash
#!/bin/bash
# monitor.sh - Production health monitoring

HEALTH_URL="http://localhost:8080/health/readiness"
ALERT_EMAIL="admin@yourcompany.com"

while true; do
    if ! curl -sf "$HEALTH_URL" > /dev/null; then
        echo "$(date): Health check failed" | tee -a /var/log/selfrag-monitor.log
        # Send alert (configure mail system)
        echo "SelfRAG health check failed at $(date)" | mail -s "SelfRAG Alert" "$ALERT_EMAIL"
        sleep 300  # Wait 5 minutes before next check
    else
        echo "$(date): System healthy"
        sleep 60   # Check every minute when healthy
    fi
done
```

### Log Management

```bash
# Configure log rotation
cat > /etc/logrotate.d/selfrag << EOF
/var/log/selfrag/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
# backup-daily.sh

BACKUP_DIR="/backup/selfrag"
DATE=$(date +%Y%m%d)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup databases
docker exec postgres pg_dump -U con_selfrag con_selfrag > "$BACKUP_DIR/$DATE/postgres.sql"

# Backup Qdrant data
docker exec qdrant tar czf - /qdrant/storage > "$BACKUP_DIR/$DATE/qdrant.tar.gz"

# Backup configuration
cp .env "$BACKUP_DIR/$DATE/"
cp docker-compose.yml "$BACKUP_DIR/$DATE/"

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR/$DATE"
```

## Security Hardening

### Network Security

```yaml
# Secure network configuration
networks:
  llm-network:
    driver: bridge
    internal: true # Isolate from external networks
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Authentication

Enable JWT authentication:

```bash
# Generate secure keys
JWT_SECRET_KEY=$(openssl rand -base64 32)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Add to .env
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> .env
echo "JWT_ALGORITHM=HS256" >> .env
echo "JWT_EXPIRE_MINUTES=30" >> .env
```

### SSL/TLS Setup

```nginx
# nginx SSL configuration
server {
    listen 443 ssl http2;
    server_name yourdomai.com;

    ssl_certificate /etc/ssl/certs/selfrag.crt;
    ssl_certificate_key /etc/ssl/private/selfrag.key;

    location / {
        proxy_pass http://fastapi-gateway:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting Deployment

### Common Issues

#### Service Startup Failures

```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs -f <service-name>

# Restart specific service
docker-compose restart <service-name>
```

#### Memory Issues

```bash
# Check memory usage
docker stats

# Increase limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

#### Performance Issues

```bash
# Check cache performance
curl http://localhost:8080/health/cache/analytics

# Monitor database connections
curl http://localhost:8080/health/metrics | jq '.database'

# Clear cache if needed
curl -X POST http://localhost:8080/health/cache/clear
```

### Recovery Procedures

#### Full System Recovery

```bash
# 1. Stop all services
docker-compose down

# 2. Clean up volumes (if needed)
docker-compose down -v

# 3. Restore from backup
./scripts/restore.sh <backup-date>

# 4. Restart services
docker-compose up -d

# 5. Verify health
./scripts/health-check.sh
```

#### Database Recovery

```bash
# Restore PostgreSQL from backup
docker exec -i postgres psql -U con_selfrag -d con_selfrag < backup/postgres.sql

# Restore Qdrant data
docker exec qdrant tar xzf - -C / < backup/qdrant.tar.gz
docker-compose restart qdrant
```

## Maintenance Tasks

### Weekly Tasks

```bash
# Update dependencies
docker-compose pull

# Clean unused Docker resources
docker system prune -f

# Check disk usage
df -h
docker system df
```

### Monthly Tasks

```bash
# Full backup verification
./scripts/backup.sh verify

# Performance optimization
./scripts/optimize-database.sh

# Security updates
docker-compose down
docker-compose pull
docker-compose up -d
```

### Performance Monitoring

Monitor these key metrics:

- **Response Time**: < 100ms for 95% of requests
- **Cache Hit Rate**: > 85%
- **Memory Usage**: < 80% of allocated
- **CPU Usage**: < 70% average
- **Error Rate**: < 0.1%

```bash
# Monitor in real-time
watch -n 5 'curl -s http://localhost:8080/health/metrics | jq ".application"'
```

This deployment guide ensures a robust, scalable, and maintainable SelfRAG installation for production use.
