#!/bin/bash

# Quick Fix for Milestone 2 Issues with Virtual Environment
# Handles externally managed Python environments (PEP 668)

set -e

echo "⚡ Quick Fix for Milestone 2 Issues (Virtual Environment)"
echo "========================================================"

# Check Docker availability
echo "🐳 Checking Docker services..."
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Use docker compose (newer) or docker-compose (legacy)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Check if services are running, start them if not
echo "🔍 Checking service status..."
if ! docker ps | grep -q postgres || ! docker ps | grep -q redis || ! docker ps | grep -q qdrant; then
    echo "🚀 Starting Docker services..."
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
            echo "Checking PostgreSQL logs:"
            docker logs postgres --tail 10
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
        fi
        sleep 1
    done
else
    echo "✅ Services are already running"
fi

# Install Python dependencies with virtual environment
echo ""
echo "📦 Setting up virtual environment and installing dependencies..."
cd backend

# Check if virtual environment already exists
if [ -d ".venv" ]; then
    echo "✅ Virtual environment already exists"
else
    echo "🔧 Creating virtual environment..."
    if command -v uv >/dev/null 2>&1; then
        echo "Using uv to create virtual environment..."
        uv venv
    elif command -v python3 >/dev/null 2>&1; then
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
if command -v uv >/dev/null 2>&1; then
    echo "Using uv for fast dependency installation..."
    uv pip install -e .
    echo "✅ Python dependencies installed with uv"
elif command -v pip >/dev/null 2>&1; then
    echo "Using pip for dependency installation..."
    pip install -e .
    echo "✅ Python dependencies installed with pip"
else
    echo "❌ No package installer available in virtual environment"
    exit 1
fi

# Test the connectivity now
echo ""
echo "🧪 Testing connectivity with current setup..."

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

python test_milestone2.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed! Milestone 2 is working correctly!"
    echo ""
    echo "📝 Virtual environment info:"
    echo "- Location: $(pwd)/.venv"
    echo "- Python: $(python --version)"
    echo "- To reactivate: source backend/.venv/bin/activate"
    echo ""
    echo "🚀 Next steps:"
    echo "- Keep the virtual environment activated for development"
    echo "- Run FastAPI with: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
    echo "- Test endpoints: curl http://localhost:8000/health/services"
else
    echo ""
    echo "⚠️  Some tests still failing. Check the output above for details."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "- Check service logs: $COMPOSE_CMD logs [postgres|redis|qdrant]"
    echo "- Restart services: $COMPOSE_CMD restart"
    echo "- Check Docker status: docker ps"
fi

cd ..
