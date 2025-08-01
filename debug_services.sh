#!/bin/bash

# Debug Services Script
# Quick diagnostic tool to check service status and logs

echo "🔍 Service Diagnostic Tool"
echo "=========================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Determine Docker Compose command
DOCKER_COMPOSE_CMD=""
if command -v "docker" &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v "docker-compose" &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    print_error "Docker Compose not found"
    exit 1
fi

print_status "Using $DOCKER_COMPOSE_CMD"
echo ""

# Check container status
print_status "Container Status:"
$DOCKER_COMPOSE_CMD ps
echo ""

# Check port mappings
print_status "Port Mappings:"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "(fastapi|localai|postgres|redis|qdrant)"
echo ""

# Test connectivity
print_status "Testing Connectivity:"

# Test FastAPI on both ports
if curl -f -s http://localhost:8000/health/ > /dev/null 2>&1; then
    print_success "FastAPI responding on port 8000"
elif curl -f -s http://localhost:8080/health/ > /dev/null 2>&1; then
    print_success "FastAPI responding on port 8080"
else
    print_error "FastAPI not responding on either port 8000 or 8080"
fi

# Test LocalAI
if curl -f -s http://localhost:8081/readyz > /dev/null 2>&1; then
    print_success "LocalAI responding on port 8081"
else
    print_warning "LocalAI not responding on port 8081"
fi

# Test other services
if curl -f -s http://localhost:6333/readyz > /dev/null 2>&1; then
    print_success "Qdrant responding on port 6333"
else
    print_warning "Qdrant not responding on port 6333"
fi

echo ""

# Show recent logs
print_status "Recent FastAPI Logs (last 20 lines):"
$DOCKER_COMPOSE_CMD logs --tail=20 fastapi-gateway
echo ""

print_status "Recent LocalAI Logs (last 10 lines):"
$DOCKER_COMPOSE_CMD logs --tail=10 localai
echo ""

# Test a simple API call
print_status "Testing FastAPI Health Endpoint:"
echo "Trying port 8080..."
curl -s http://localhost:8080/health/ | jq . 2>/dev/null || curl -s http://localhost:8080/health/
echo ""

echo "Trying port 8000..."
curl -s http://localhost:8000/health/ | jq . 2>/dev/null || curl -s http://localhost:8000/health/
echo ""

print_status "Diagnostic complete!"
print_status "If FastAPI is not responding, check the logs above for errors."
