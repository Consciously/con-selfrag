#!/bin/bash

# Milestone 2 Test Script
# Starts all services and runs connectivity tests

set -e

echo "🚀 Starting Milestone 2 - Service Connectivity Tests"
echo "=================================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command_exists docker; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose is not available"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Start services
echo ""
echo "🐳 Starting Docker services..."
echo "This may take a few minutes on first run..."

# Use docker compose (newer) or docker-compose (legacy)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Start services in background
$COMPOSE_CMD up -d postgres redis qdrant

echo "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL
echo "📊 Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker exec postgres pg_isready -U con_selfrag -d con_selfrag >/dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Wait for Redis
echo "🔴 Waiting for Redis..."
for i in {1..30}; do
    if docker exec redis redis-cli ping >/dev/null 2>&1; then
        echo "✅ Redis is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Redis failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Wait for Qdrant
echo "🔍 Waiting for Qdrant..."
for i in {1..30}; do
    if curl -f http://localhost:6333/readyz >/dev/null 2>&1; then
        echo "✅ Qdrant is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Qdrant failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

echo ""
echo "🎯 All services are ready! Running connectivity tests..."
echo ""

# Run the Python test script
cd backend
if command_exists python3; then
    python3 test_milestone2.py
elif command_exists python; then
    python test_milestone2.py
else
    echo "❌ Python is not installed or not in PATH"
    exit 1
fi

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Milestone 2 tests completed successfully!"
    echo ""
    echo "Next steps:"
    echo "- All services are running and connected"
    echo "- You can now proceed to Milestone 3"
    echo "- To stop services: $COMPOSE_CMD down"
    echo "- To view logs: $COMPOSE_CMD logs [service_name]"
else
    echo ""
    echo "⚠️  Some tests failed. Check the output above for details."
    echo ""
    echo "Troubleshooting:"
    echo "- Check service logs: $COMPOSE_CMD logs [postgres|redis|qdrant]"
    echo "- Restart services: $COMPOSE_CMD restart"
    echo "- Check Docker status: docker ps"
fi
