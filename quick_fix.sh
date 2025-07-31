#!/bin/bash

# Quick Fix for Milestone 2 Issues
# Installs Python dependencies and provides PostgreSQL fix guidance

set -e

echo "⚡ Quick Fix for Milestone 2 Issues"
echo "=================================="

# Install Python dependencies first
echo "📦 Installing Python dependencies with uv..."
cd backend

# Check if uv is available, otherwise fall back to pip
if command -v uv >/dev/null 2>&1; then
    echo "Using uv for fast dependency installation..."
    # Install dependencies from pyproject.toml using uv with --system flag
    uv pip install --system -e .
    echo "✅ Python dependencies installed with uv"
elif command -v pip3 >/dev/null 2>&1; then
    echo "uv not found, falling back to pip3..."
    pip3 install -e .
    echo "✅ Python dependencies installed with pip3"
elif command -v pip >/dev/null 2>&1; then
    echo "uv not found, falling back to pip..."
    pip install -e .
    echo "✅ Python dependencies installed with pip"
else
    echo "❌ Neither uv nor pip is installed or not in PATH"
    echo ""
    echo "To install uv (recommended):"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Or install pip3 with your system package manager"
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

python3 test_milestone2.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed! Milestone 2 is working correctly!"
else
    echo ""
    echo "⚠️  PostgreSQL authentication issue detected."
    echo ""
    echo "To fix PostgreSQL authentication, run:"
    echo "1. docker compose down"
    echo "2. docker volume rm con-selfrag_postgres-data"
    echo "3. docker compose up -d postgres redis qdrant"
    echo ""
    echo "Or run the comprehensive fix script:"
    echo "chmod +x fix_milestone2_issues.sh && ./fix_milestone2_issues.sh"
fi

cd ..
