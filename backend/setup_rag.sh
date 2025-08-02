#!/bin/bash

# Setup script for RAG pipeline dependencies
# This script installs the required Python packages for the RAG pipeline

echo "🔧 Setting up RAG Pipeline Dependencies"
echo "======================================"

# Check Python availability
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.11+ first."
    exit 1
fi

echo "✅ Using Python: $PYTHON_CMD ($($PYTHON_CMD --version))"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
    PIP_CMD="pip"
else
    echo "⚠️  No virtual environment detected. Using system Python."
    echo "   Consider creating one: $PYTHON_CMD -m venv venv && source venv/bin/activate"
    PIP_CMD="$PYTHON_CMD -m pip"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."

# Core dependencies (should already be there)
echo "🌐 Installing core web dependencies..."
$PIP_CMD install --user fastapi uvicorn pydantic loguru

# RAG pipeline dependencies
echo "🧠 Installing RAG dependencies..."
$PIP_CMD install --user sentence-transformers>=2.2.0
$PIP_CMD install --user qdrant-client>=1.7.0
$PIP_CMD install --user numpy>=1.24.0

# Optional but recommended
echo "🔍 Installing optional dependencies..."
$PIP_CMD install --user httpx requests

echo ""
echo "✅ Dependencies installed successfully!"
echo ""
echo "🚀 Next steps:"
echo "1. Start Qdrant if using Docker: docker run -p 6333:6333 qdrant/qdrant"
echo "2. Test the RAG pipeline: python test_rag_pipeline.py"
echo "3. Start the FastAPI server: uvicorn app.main:app --reload"
echo ""
echo "📚 Available endpoints:"
echo "   - POST /ingest - Ingest documents"
echo "   - POST /query - Search documents"
echo "   - GET /health/rag - Check RAG pipeline health"
echo "   - GET /docs - API documentation"
