#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# Default ports (can be overridden by .env)
MAIN_API_PORT=8080
LOCALAI_PORT=8081
QDRANT_PORT=6333
POSTGRES_PORT=5432
REDIS_PORT=6379
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001

# Load environment variables if .env exists
if [[ -f "$ENV_FILE" ]]; then
    source "$ENV_FILE"
fi

# Use environment variables if set, otherwise defaults
MAIN_API_PORT=${MAIN_API_PORT:-8080}
LOCALAI_PORT=${LOCALAI_PORT:-8081}
QDRANT_PORT=${QDRANT_PORT:-6333}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
REDIS_PORT=${REDIS_PORT:-6379}
MINIO_API_PORT=${MINIO_API_PORT:-9000}
MINIO_CONSOLE_PORT=${MINIO_CONSOLE_PORT:-9001}

# Service health check functions
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    if command -v curl &> /dev/null; then
        if curl -s -f -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
            echo -e "${GREEN}✓ HEALTHY${NC}"
            return 0
        else
            echo -e "${RED}✗ UNHEALTHY${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ curl not available, skipping${NC}"
        return 1
    fi
}

check_container_health() {
    local service_name=$1
    local container_name=$2
    
    echo -n "Checking $service_name container health... "
    
    if ! docker compose ps -q "$container_name" &> /dev/null; then
        echo -e "${RED}✗ NOT RUNNING${NC}"
        return 1
    fi
    
    local health_status
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")
    
    case "$health_status" in
        "healthy")
            echo -e "${GREEN}✓ HEALTHY${NC}"
            return 0
            ;;
        "starting")
            echo -e "${YELLOW}⚠ STARTING${NC}"
            return 1
            ;;
        "unhealthy")
            echo -e "${RED}✗ UNHEALTHY${NC}"
            return 1
            ;;
        *)
            echo -e "${RED}✗ NO HEALTH CHECK${NC}"
            return 1
            ;;
    esac
}

check_port() {
    local service_name=$1
    local port=$2
    
    echo -n "Checking $service_name port $port... "
    
    if nc -z localhost "$port" 2>/dev/null || timeout 2 bash -c "</dev/tcp/localhost/$port" 2>/dev/null; then
        echo -e "${GREEN}✓ OPEN${NC}"
        return 0
    else
        echo -e "${RED}✗ CLOSED${NC}"
        return 1
    fi
}

check_database_connection() {
    echo -n "Checking PostgreSQL connection... "
    
    if docker compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        echo -e "${GREEN}✓ CONNECTED${NC}"
        return 0
    else
        echo -e "${RED}✗ CONNECTION FAILED${NC}"
        return 1
    fi
}

check_redis_connection() {
    echo -n "Checking Redis connection... "
    
    if docker compose exec -T redis redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ CONNECTED${NC}"
        return 0
    else
        echo -e "${RED}✗ CONNECTION FAILED${NC}"
        return 1
    fi
}

# Main health check function
main() {
    echo "🚀 CON-LLM Health Check"
    echo "======================"
    echo
    
    # Check if docker-compose is running
    if ! docker compose ps &> /dev/null; then
        echo -e "${RED}❌ Docker Compose services are not running${NC}"
        echo "Run: docker-compose up -d"
        exit 1
    fi
    
    local failed_checks=0
    
    # Check container health statuses
    echo "📦 Container Health Statuses:"
    echo "-----------------------------"
    check_container_health "FastAPI Gateway" "fastapi-gateway" || ((failed_checks++))
    check_container_health "LocalAI" "localai" || ((failed_checks++))
    check_container_health "Qdrant" "qdrant" || ((failed_checks++))
    check_container_health "PostgreSQL" "postgres" || ((failed_checks++))
    check_container_health "Redis" "redis" || ((failed_checks++))
    check_container_health "MinIO" "minio" || ((failed_checks++))
    echo
    
    # Check service endpoints
    echo "🔗 Service Endpoints:"
    echo "--------------------"
    check_service "FastAPI Gateway" "http://localhost:$MAIN_API_PORT/health" || ((failed_checks++))
    check_service "LocalAI" "http://localhost:$LOCALAI_PORT/health" || ((failed_checks++))
    check_service "Qdrant" "http://localhost:$QDRANT_PORT/readyz" || ((failed_checks++))
    check_service "MinIO API" "http://localhost:$MINIO_API_PORT/minio/health/live" || ((failed_checks++))
    echo
    
    # Check database connections
    echo "🗄️ Database Connections:"
    echo "-----------------------"
    check_database_connection || ((failed_checks++))
    check_redis_connection || ((failed_checks++))
    echo
    
    # Check port availability
    echo "🔌 Port Availability:"
    echo "--------------------"
    check_port "FastAPI Gateway" "$MAIN_API_PORT" || ((failed_checks++))
    check_port "LocalAI" "$LOCALAI_PORT" || ((failed_checks++))
    check_port "Qdrant" "$QDRANT_PORT" || ((failed_checks++))
    check_port "PostgreSQL" "$POSTGRES_PORT" || ((failed_checks++))
    check_port "Redis" "$REDIS_PORT" || ((failed_checks++))
    check_port "MinIO API" "$MINIO_API_PORT" || ((failed_checks++))
    check_port "MinIO Console" "$MINIO_CONSOLE_PORT" || ((failed_checks++))
    echo
    
    # Summary
    echo "📊 Health Check Summary:"
    echo "======================="
    if [[ $failed_checks -eq 0 ]]; then
        echo -e "${GREEN}✅ All services are healthy!${NC}"
        echo
        echo "🎉 Your CON-LLM infrastructure is ready!"
        echo "   FastAPI Gateway: http://localhost:$MAIN_API_PORT"
        echo "   LocalAI: http://localhost:$LOCALAI_PORT"
        echo "   Qdrant: http://localhost:$QDRANT_PORT"
        echo "   MinIO Console: http://localhost:$MINIO_CONSOLE_PORT"
        exit 0
    else
        echo -e "${RED}❌ $failed_checks service(s) have issues${NC}"
        echo
        echo "🔧 Troubleshooting:"
        echo "   1. Check service logs: docker-compose logs [service-name]"
        echo "   2. Restart services: docker-compose restart"
        echo "   3. View detailed logs: docker-compose logs -f"
        echo "   4. Check resource usage: docker stats"
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Missing dependencies: ${missing_deps[*]}${NC}"
        exit 1
    fi
}

# Run dependency check
check_dependencies

# Change to project root
cd "$PROJECT_ROOT"

# Run main health check
main "$@"
