#!/bin/bash

# Test script for LocalAI client functionality
# This script sets up the environment and runs comprehensive tests

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if LocalAI is running
check_localai_running() {
    if curl -s "http://localhost:8080/v1/models" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to install Python packages
install_packages() {
    local packages="$1"
    print_status "Installing packages: $packages"
    
    # Try different package managers in order of preference
    if command_exists uv; then
        print_status "Using uv for package installation..."
        if uv pip install --system $packages; then
            print_success "Packages installed successfully with uv"
            return 0
        else
            print_warning "uv installation failed, trying pip3..."
        fi
    fi
    
    if command_exists pip3; then
        print_status "Using pip3 for package installation..."
        if pip3 install $packages; then
            print_success "Packages installed successfully with pip3"
            return 0
        else
            print_warning "pip3 installation failed, trying pip..."
        fi
    fi
    
    if command_exists pip; then
        print_status "Using pip for package installation..."
        if pip install $packages; then
            print_success "Packages installed successfully with pip"
            return 0
        else
            print_error "All package installation methods failed"
            return 1
        fi
    fi
    
    print_error "No package installer found (pip/pip3/uv)"
    return 1
}

# Main execution
main() {
    print_status "🚀 Starting LocalAI Client Test Suite"
    echo "=================================================="
    
    # Check if we're in the right directory
    if [[ ! -f "backend/app/localai_client.py" ]]; then
        print_error "LocalAI client not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Set environment variables for LocalAI connection
    export LOCALAI_HOST=${LOCALAI_HOST:-localhost}
    export LOCALAI_PORT=${LOCALAI_PORT:-8080}
    export LOCALAI_TIMEOUT=${LOCALAI_TIMEOUT:-30.0}
    export DEFAULT_MODEL=${DEFAULT_MODEL:-llama-3.2-1b-instruct}
    
    print_status "Environment Configuration:"
    echo "  LocalAI Host: $LOCALAI_HOST"
    echo "  LocalAI Port: $LOCALAI_PORT"
    echo "  Timeout: $LOCALAI_TIMEOUT seconds"
    echo "  Default Model: $DEFAULT_MODEL"
    echo ""
    
    # Check if LocalAI is running
    print_status "🔍 Checking LocalAI service availability..."
    if check_localai_running; then
        print_success "LocalAI is running and accessible"
    else
        print_warning "LocalAI is not accessible at http://localhost:8080"
        print_status "Attempting to start LocalAI with Docker Compose..."
        
        if command_exists docker-compose; then
            # Try to start LocalAI service
            if docker-compose up -d localai 2>/dev/null; then
                print_status "Waiting for LocalAI to start..."
                sleep 10
                
                # Check again
                if check_localai_running; then
                    print_success "LocalAI started successfully"
                else
                    print_error "LocalAI failed to start or is not responding"
                    print_status "Please ensure LocalAI is properly configured and running"
                    exit 1
                fi
            else
                print_error "Failed to start LocalAI with docker-compose"
                print_status "Please start LocalAI manually and try again"
                exit 1
            fi
        else
            print_error "docker-compose not found and LocalAI is not running"
            print_status "Please start LocalAI manually and try again"
            exit 1
        fi
    fi
    
    # Change to backend directory
    cd backend
    
    # Check Python environment
    print_status "🐍 Checking Python environment..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python not found. Please install Python 3.8+"
        exit 1
    fi
    
    print_status "Using Python: $PYTHON_CMD"
    
    # Check if required packages are installed
    print_status "📦 Checking required packages..."
    
    missing_packages=()
    
    # Check each package individually
    if ! $PYTHON_CMD -c "import loguru" 2>/dev/null; then
        missing_packages+=("loguru")
    fi
    
    if ! $PYTHON_CMD -c "import openai" 2>/dev/null; then
        missing_packages+=("openai")
    fi
    
    if ! $PYTHON_CMD -c "import asyncio" 2>/dev/null; then
        print_error "asyncio not available. Please upgrade to Python 3.7+"
        exit 1
    fi
    
    # Install missing packages if any
    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_warning "Missing packages: ${missing_packages[*]}"
        
        if ! install_packages "${missing_packages[*]}"; then
            print_error "Failed to install required packages"
            print_status "Please install manually:"
            echo "  pip3 install ${missing_packages[*]}"
            exit 1
        fi
        
        # Verify installation
        print_status "Verifying package installation..."
        for package in "${missing_packages[@]}"; do
            if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
                print_error "Package $package still not available after installation"
                exit 1
            fi
        done
        print_success "All packages verified successfully"
    else
        print_success "All required packages are already installed"
    fi
    
    # Run the tests
    print_status "🧪 Running LocalAI client tests..."
    echo ""
    
    if $PYTHON_CMD test_localai_client.py; then
        echo ""
        print_success "🎉 LocalAI client tests completed successfully!"
        
        # Additional verification
        print_status "🔍 Running quick verification..."
        if check_localai_running; then
            print_success "LocalAI service is still running and healthy"
        else
            print_warning "LocalAI service appears to be down after tests"
        fi
        
        exit 0
    else
        echo ""
        print_error "❌ LocalAI client tests failed"
        
        # Provide troubleshooting information
        print_status "🔧 Troubleshooting Information:"
        echo "  1. Ensure LocalAI is running: curl http://localhost:8080/v1/models"
        echo "  2. Check LocalAI logs: docker-compose logs localai"
        echo "  3. Verify model availability in LocalAI"
        echo "  4. Check network connectivity to LocalAI service"
        echo "  5. Try manual package installation: pip3 install loguru openai"
        
        exit 1
    fi
}

# Cleanup function
cleanup() {
    print_status "🧹 Cleaning up..."
    # Add any cleanup tasks here if needed
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"
