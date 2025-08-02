#!/bin/bash

# Quick fix script for RAG pipeline Docker build issues
# This script helps test and fix dependency installation

echo "🔧 Selfrag RAG Pipeline - Docker Build Fix"
echo "=========================================="

cd "$(dirname "$0")"

echo "📁 Current directory: $(pwd)"

# Option 1: Test local installation first
echo ""
echo "🧪 Option 1: Test Local Installation"
echo "Would you like to test installing dependencies locally first? (y/n)"
read -p "Choice: " choice

if [[ $choice == "y" || $choice == "Y" ]]; then
    echo "📦 Testing local dependency installation..."
    
    # Create a temporary virtual environment
    python -m venv venv_test
    source venv_test/bin/activate
    
    echo "🔄 Upgrading pip and installing build tools..."
    pip install --upgrade pip setuptools wheel
    
    echo "🧮 Installing numpy first..."
    pip install numpy
    
    echo "📚 Installing core dependencies..."
    pip install fastapi uvicorn pydantic loguru openai httpx requests
    
    echo "🔍 Installing database dependencies..."
    pip install asyncpg "redis[hiredis]" qdrant-client
    
    echo "🧠 Installing ML dependencies..."
    pip install sentence-transformers
    
    echo "🛠️ Installing dev dependencies..."
    pip install pytest pytest-asyncio black mypy isort
    
    if [ $? -eq 0 ]; then
        echo "✅ Local installation successful!"
        echo "🐳 Now trying Docker build..."
    else
        echo "❌ Local installation failed. Check the errors above."
        deactivate
        rm -rf venv_test
        exit 1
    fi
    
    deactivate
    rm -rf venv_test
fi

# Option 2: Try lightweight Docker build
echo ""
echo "🐳 Option 2: Try Lightweight Docker Build"
echo "Would you like to try building without ML dependencies first? (y/n)"
read -p "Choice: " choice2

if [[ $choice2 == "y" || $choice2 == "Y" ]]; then
    echo "🔨 Building lightweight Docker image..."
    docker build -f Dockerfile.lite -t selfrag-lite:latest .
    
    if [ $? -eq 0 ]; then
        echo "✅ Lightweight build successful!"
        echo "🚀 You can run it with: docker run -p 8000:8000 selfrag-lite:latest"
        echo "📝 Note: RAG features will use fallback/mock implementations"
    else
        echo "❌ Lightweight build failed"
    fi
fi

# Option 3: Try full Docker build with better error handling
echo ""
echo "🎯 Option 3: Try Full Docker Build"
echo "Would you like to try the full Docker build with RAG features? (y/n)"
read -p "Choice: " choice3

if [[ $choice3 == "y" || $choice3 == "Y" ]]; then
    echo "🔨 Building full Docker image with RAG pipeline..."
    echo "⏰ This may take several minutes to download ML models..."
    
    # Build with more verbose output and progress
    DOCKER_BUILDKIT=1 docker build \
        --progress=plain \
        --target=runtime \
        -t selfrag-full:latest \
        .
    
    if [ $? -eq 0 ]; then
        echo "✅ Full build successful!"
        echo "🚀 You can run it with: docker run -p 8000:8000 selfrag-full:latest"
        echo "📋 To test: curl http://localhost:8000/health/rag"
    else
        echo "❌ Full build failed. See error details above."
        echo ""
        echo "💡 Common fixes:"
        echo "   1. Increase Docker memory allocation (4GB+ recommended)"
        echo "   2. Check internet connection for downloading ML models"
        echo "   3. Try the lightweight version first (Dockerfile.lite)"
        echo "   4. Use local development instead: ./setup_rag.sh"
    fi
fi

echo ""
echo "🎯 Alternative: Local Development"
echo "===============================s="
echo "If Docker builds are problematic, you can develop locally:"
echo "1. Run: ./setup_rag.sh"
echo "2. Start services manually:"
echo "   - Qdrant: docker run -p 6333:6333 qdrant/qdrant"
echo "   - API: uvicorn app.main:app --reload"
echo "3. Test: python demo_rag.py"

echo ""
echo "✨ Build troubleshooting complete!"
