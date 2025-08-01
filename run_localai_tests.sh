#!/bin/bash

# Activate virtual environment and run LocalAI client tests

set -e

VENV_DIR="venv_localai_test"

if [[ ! -d "$VENV_DIR" ]]; then
    echo "❌ Virtual environment not found. Run ./setup_test_env.sh first"
    exit 1
fi

echo "🚀 Running LocalAI client tests in virtual environment..."

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set environment variables
export LOCALAI_HOST=${LOCALAI_HOST:-localhost}
export LOCALAI_PORT=${LOCALAI_PORT:-8080}
export LOCALAI_TIMEOUT=${LOCALAI_TIMEOUT:-30.0}
export DEFAULT_MODEL=${DEFAULT_MODEL:-llama-3.2-1b-instruct}

# Run tests
cd backend
python test_localai_client.py

# Deactivate virtual environment
deactivate

echo "✅ Tests completed!"
