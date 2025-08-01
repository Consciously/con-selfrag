#!/bin/bash

# Quick dependency installation for LocalAI client tests

set -e

echo "🔧 Installing LocalAI client test dependencies..."

# Try different package managers
if command -v uv >/dev/null 2>&1; then
    echo "📦 Using uv..."
    uv pip install --system loguru openai
elif command -v pip3 >/dev/null 2>&1; then
    echo "📦 Using pip3..."
    pip3 install loguru openai
elif command -v pip >/dev/null 2>&1; then
    echo "📦 Using pip..."
    pip install loguru openai
else
    echo "❌ No package installer found (pip/pip3/uv)"
    exit 1
fi

echo "✅ Dependencies installed successfully!"
echo ""
echo "Now you can run the tests:"
echo "  ./test_localai_client.sh"
