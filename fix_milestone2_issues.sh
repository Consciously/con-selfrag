#!/bin/bash

# Fix Milestone 2 Issues Script
# Resolves PostgreSQL authentication and Python dependency issues

set -e

echo "🔧 Fixing Milestone 2 Issues"
echo "============================="

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

# Use docker compose (newer) or docker-compose (legacy)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "✅ Docker and Docker Compose are available"

# Stop and remove PostgreSQL container and volume
echo ""
echo "🗄️  Resetting PostgreSQL data..."
echo "This will remove all existing PostgreSQL data and recreate with correct credentials"

# Stop services
$COMPOSE_CMD down

# Remove PostgreSQL volume to reset credentials
docker volume rm con-selfrag_postgres-data 2>/dev/null || echo "PostgreSQL volume doesn't exist or already removed"

echo "✅ PostgreSQL data reset"

# Install Python dependencies
echo ""
echo "📦 Setting up virtual environment and installing dependencies..."
cd backend

# Check if virtual environment already exists
if [ -d ".venv" ]; then
    echo "✅ Virtual environment already exists"
else
    echo "🔧 Creating virtual environment..."
    if command_exists uv; then
        echo "Using uv to create virtual environment..."
        uv venv
    elif command_exists python3; then
        echo "Using python3 to create virtual environment..."
        python3 -m venv .venv
    else
        echo "❌ Neither uv nor python3 is available"
        exit 1
    fi
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
if command_exists uv; then
    echo "Using uv for fast dependency installation..."
    uv pip install -e .
    echo "✅ Python dependencies installed with uv"
elif command_exists pip; then
    echo "Using pip for dependency installation..."
    pip install -e .
    echo "✅ Python dependencies installed with pip"
else
    echo "❌ No package installer available in virtual environment"
    exit 1
fi

# Go back to root directory
cd ..

# Start services with fresh PostgreSQL
echo ""
echo "🐳 Starting services with fresh PostgreSQL..."
$COMPOSE_CMD up -d postgres redis qdrant

echo "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL (longer timeout for first initialization)
echo "📊 Waiting for PostgreSQL initialization..."
for i in {1..60}; do
    if docker exec postgres pg_isready -U con_selfrag -d con_selfrag >/dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ PostgreSQL failed to start within 60 seconds"
        echo "Checking PostgreSQL logs:"
        docker logs postgres --tail 20
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
echo "🎯 All services are ready! Testing connectivity..."
echo ""

# Test PostgreSQL connection with correct credentials
echo "🧪 Testing PostgreSQL connection..."
if docker exec postgres psql -U con_selfrag -d con_selfrag -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ PostgreSQL connection successful"
else
    echo "❌ PostgreSQL connection failed"
    echo "Checking PostgreSQL environment:"
    docker exec postgres env | grep POSTGRES
    exit 1
fi

# Run the Python test script
echo ""
echo "🧪 Running comprehensive connectivity tests..."
cd backend

# Set environment variables for host machine testing (use localhost instead of service names)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=con_selfrag
export POSTGRES_PASSWORD=con_selfrag_password
export POSTGRES_DB=con_selfrag
export REDIS_HOST=localhost
export REDIS_PORT=6379
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

python3 test_milestone2.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All issues fixed! Milestone 2 is now working correctly!"
    echo ""
    echo "Services status:"
    echo "- PostgreSQL: ✅ Connected with correct credentials"
    echo "- Redis: ✅ Connected and operational"
    echo "- Qdrant: ✅ Connected and operational"
    echo "- Python dependencies: ✅ Installed"
    echo ""
    echo "You can now proceed with development or run:"
    echo "- curl http://localhost:8080/health/services"
    echo "- curl -X POST http://localhost:8080/health/test-postgres-write"
else
    echo ""
    echo "⚠️  Some tests still failing. Check the output above for details."
fi
