#!/bin/bash

# Start FastAPI Server with Environment Variables
# Ensures all database services are properly configured

echo "🚀 Starting FastAPI Server"
echo "=========================="

# Navigate to backend directory
cd backend

# Set environment variables for database connections
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=con_selfrag
export POSTGRES_PASSWORD=con_selfrag_password
export POSTGRES_DB=con_selfrag
export REDIS_HOST=localhost
export REDIS_PORT=6379
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🔌 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import app.main" 2>/dev/null; then
    echo "❌ Dependencies not installed. Installing now..."
    if command -v uv >/dev/null 2>&1; then
        uv pip install -e .
    else
        pip install -e .
    fi
fi

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📊 Health endpoints:"
echo "  - http://localhost:8000/health/"
echo "  - http://localhost:8000/health/services"
echo "  - http://localhost:8000/health/readiness"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
