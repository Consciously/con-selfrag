#!/bin/bash

# Setup test environment with virtual environment for LocalAI client tests
# This handles externally managed Python systems (Ubuntu/Debian)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

main() {
    print_status "🔧 Setting up LocalAI client test environment..."
    
    # Check if we're in the right directory
    if [[ ! -f "backend/app/localai_client.py" ]]; then
        print_error "LocalAI client not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Create virtual environment directory
    VENV_DIR="venv_localai_test"
    
    if [[ -d "$VENV_DIR" ]]; then
        print_status "Virtual environment already exists at $VENV_DIR"
    else
        print_status "Creating virtual environment..."
        
        if command_exists uv; then
            print_status "Using uv to create virtual environment..."
            uv venv "$VENV_DIR"
        elif command_exists python3; then
            print_status "Using python3 to create virtual environment..."
            python3 -m venv "$VENV_DIR"
        else
            print_error "Neither uv nor python3 found. Cannot create virtual environment."
            exit 1
        fi
        
        print_success "Virtual environment created at $VENV_DIR"
    fi
    
    # Install dependencies
    print_status "Installing dependencies in virtual environment..."
    
    if command_exists uv && [[ -d "$VENV_DIR" ]]; then
        print_status "Using uv to install packages..."
        # Install from pyproject.toml if available, otherwise install individual packages
        if [[ -f "backend/pyproject.toml" ]]; then
            cd backend
            uv pip install --python "../$VENV_DIR/bin/python" -e .
            cd ..
        else
            # Install essential packages manually
            uv pip install --python "$VENV_DIR/bin/python" \
                fastapi>=0.104.0 \
                openai>=1.0.0 \
                loguru>=0.7.0 \
                pydantic>=2.0.0 \
                uvicorn>=0.24.0 \
                httpx>=0.25.0 \
                asyncpg>=0.29.0 \
                "redis[hiredis]>=5.0.0" \
                qdrant-client>=1.7.0
        fi
    else
        print_status "Using pip to install packages..."
        source "$VENV_DIR/bin/activate"
        
        if [[ -f "backend/pyproject.toml" ]]; then
            cd backend
            pip install -e .
            cd ..
        else
            # Install essential packages manually
            pip install \
                "fastapi>=0.104.0" \
                "openai>=1.0.0" \
                "loguru>=0.7.0" \
                "pydantic>=2.0.0" \
                "uvicorn>=0.24.0" \
                "httpx>=0.25.0" \
                "asyncpg>=0.29.0" \
                "redis[hiredis]>=5.0.0" \
                "qdrant-client>=1.7.0"
        fi
        
        deactivate
    fi
    
    print_success "Dependencies installed successfully!"
    
    # Create a test runner script
    cat > run_localai_tests.sh << 'EOF'
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
EOF
    
    chmod +x run_localai_tests.sh
    
    print_success "Test environment setup complete!"
    echo ""
    print_status "📋 Next steps:"
    echo "  1. Run the tests: ./run_localai_tests.sh"
    echo "  2. Or activate the environment manually:"
    echo "     source $VENV_DIR/bin/activate"
    echo "     cd backend && python test_localai_client.py"
    echo "     deactivate"
    echo ""
    print_status "🧹 To clean up later:"
    echo "  rm -rf $VENV_DIR run_localai_tests.sh"
}

main "$@"
