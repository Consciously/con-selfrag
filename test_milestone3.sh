#!/bin/bash

# Milestone 3 Test Script - LLM Container Integration
# Tests the integration between FastAPI backend and LocalAI container

set -e  # Exit on any error

echo "🚀 Milestone 3 - LLM Container Integration Test"
echo "=============================================="

# Color codes for output
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

# Determine which Docker Compose command to use
DOCKER_COMPOSE_CMD=""
if command -v "docker" &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    print_status "Using modern 'docker compose' command"
elif command -v "docker-compose" &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    print_warning "Using legacy 'docker-compose' command (consider upgrading Docker)"
else
    print_error "Neither 'docker compose' nor 'docker-compose' found. Please install Docker Compose."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Starting services with $DOCKER_COMPOSE_CMD..."

# Start all services
$DOCKER_COMPOSE_CMD up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check service health
print_status "Checking service health..."

# Check FastAPI
if curl -f -s http://localhost:8080/health/ > /dev/null; then
    print_success "FastAPI service is running"
else
    print_warning "FastAPI service may not be ready yet"
fi

# Check LocalAI
if curl -f -s http://localhost:8081/readyz > /dev/null; then
    print_success "LocalAI service is running"
else
    print_warning "LocalAI service may not be ready yet (this is expected on first run)"
fi

# Check PostgreSQL
if $DOCKER_COMPOSE_CMD exec -T postgres pg_isready -U con_selfrag > /dev/null 2>&1; then
    print_success "PostgreSQL service is running"
else
    print_warning "PostgreSQL service may not be ready yet"
fi

# Check Redis
if $DOCKER_COMPOSE_CMD exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis service is running"
else
    print_warning "Redis service may not be ready yet"
fi

# Check Qdrant
if curl -f -s http://localhost:6333/readyz > /dev/null; then
    print_success "Qdrant service is running"
else
    print_warning "Qdrant service may not be ready yet"
fi

print_status "Services status check completed"
echo ""

# Set up Python environment
print_status "Setting up Python environment..."

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "Not in a virtual environment. Creating one..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
else
    print_success "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Install dependencies
print_status "Installing test dependencies..."

# Check if uv is available (faster package installer)
if command -v uv &> /dev/null; then
    print_status "Using uv for fast dependency installation..."
    uv pip install httpx loguru
else
    print_status "Using pip for dependency installation..."
    pip install httpx loguru
fi

# Navigate to backend directory for test execution
cd backend

# Run the comprehensive test suite
print_status "Running Milestone 3 test suite..."
echo ""

python test_milestone3.py

# Capture test exit code
TEST_EXIT_CODE=$?

# Go back to project root
cd ..

# Print final results
echo ""
echo "=============================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "🎉 Milestone 3 tests completed successfully!"
    print_status "✅ LLM Container Integration is working correctly"
else
    print_warning "⚠️ Some Milestone 3 tests failed"
    print_status "This may be expected if LocalAI is still starting up or models are not loaded"
fi

echo ""
print_status "📋 Test Results Summary:"
if [ -f "backend/milestone3_test_results.json" ]; then
    print_status "Detailed results saved to: backend/milestone3_test_results.json"
else
    print_warning "Test results file not found"
fi

echo ""
print_status "🔧 Service Management:"
print_status "• View logs: $DOCKER_COMPOSE_CMD logs -f [service_name]"
print_status "• Stop services: $DOCKER_COMPOSE_CMD down"
print_status "• Restart services: $DOCKER_COMPOSE_CMD restart"
print_status "• Check service status: $DOCKER_COMPOSE_CMD ps"

echo ""
print_status "🌐 Service URLs:"
print_status "• FastAPI: http://localhost:8080"
print_status "• FastAPI Docs: http://localhost:8080/docs"
print_status "• LocalAI: http://localhost:8081"
print_status "• Qdrant: http://localhost:6333"
print_status "• PostgreSQL: localhost:5432"
print_status "• Redis: localhost:6379"

echo ""
print_status "💡 Next Steps:"
print_status "1. Check LocalAI logs if LLM tests failed: $DOCKER_COMPOSE_CMD logs localai"
print_status "2. Verify models are loaded: curl http://localhost:8081/v1/models"
print_status "3. Test individual endpoints manually using the API docs"
print_status "4. Proceed to Milestone 4 - RAG Pipeline Integration"

# Exit with the same code as the tests
exit $TEST_EXIT_CODE
