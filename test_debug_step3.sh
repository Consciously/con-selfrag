#!/bin/bash

# Test Debug Endpoints - Step 3 Verification Script
# This script tests the debug endpoints for manual verification of LocalAI integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="backend"
API_URL="http://localhost:8000"
LOCALAI_URL="http://localhost:8080"

echo -e "${BLUE}🔍 Debug Endpoints Test - Step 3 Verification${NC}"
echo "=================================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to detect Docker Compose command
detect_docker_compose() {
    if command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    else
        return 1
    fi
}

# Function to check if a service is running
check_service() {
    local url=$1
    local service_name=$2
    
    if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
        print_status "$service_name is running at $url"
        return 0
    else
        print_error "$service_name is not accessible at $url"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            print_status "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Check if we're in the right directory
if [ ! -d "$BACKEND_DIR" ]; then
    print_error "Backend directory not found. Please run this script from the project root."
    exit 1
fi

# Step 1: Check Docker services
print_info "Step 1: Checking Docker services..."

# Detect Docker Compose command
DOCKER_COMPOSE_CMD=$(detect_docker_compose)
if [ $? -ne 0 ]; then
    print_warning "Docker Compose not found. Skipping Docker service management."
    print_info "Please ensure LocalAI and other services are running manually:"
    print_info "  - LocalAI: $LOCALAI_URL"
    print_info "  - PostgreSQL: localhost:5432"
    print_info "  - Redis: localhost:6379"
    print_info "  - Qdrant: localhost:6333"
    SKIP_DOCKER=true
else
    print_info "Using Docker Compose command: $DOCKER_COMPOSE_CMD"
    SKIP_DOCKER=false
fi

if [ "$SKIP_DOCKER" = false ]; then
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        print_warning "docker-compose.yml not found. Skipping Docker service management."
        SKIP_DOCKER=true
    fi
fi

if [ "$SKIP_DOCKER" = false ]; then
    if ! $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
        print_warning "Docker services not running. Starting them..."
        $DOCKER_COMPOSE_CMD up -d
        
        # Wait for services to be ready
        wait_for_service "http://localhost:5432" "PostgreSQL" || true
        wait_for_service "http://localhost:6379" "Redis" || true  
        wait_for_service "http://localhost:6333" "Qdrant" || true
        wait_for_service "$LOCALAI_URL/readiness" "LocalAI" || true
    else
        print_status "Docker services are running"
    fi
else
    print_info "Skipping Docker service management - checking if services are available..."
    check_service "$LOCALAI_URL/readiness" "LocalAI" || print_warning "LocalAI not accessible - debug endpoints may fail"
fi

# Step 2: Install Python dependencies
print_info "Step 2: Installing Python dependencies..."
cd $BACKEND_DIR

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
if command -v uv >/dev/null 2>&1; then
    print_info "Using uv for fast dependency installation..."
    uv pip install -e .
    uv pip install httpx  # For testing script
else
    print_info "Using pip for dependency installation..."
    pip install -e .
    pip install httpx  # For testing script
fi

# Step 3: Start the FastAPI server
print_info "Step 3: Starting FastAPI server..."

# Check if server is already running
if check_service "$API_URL/health" "FastAPI"; then
    print_warning "FastAPI server is already running"
else
    print_info "Starting FastAPI server in background..."
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../fastapi.log 2>&1 &
    FASTAPI_PID=$!
    echo $FASTAPI_PID > ../fastapi.pid
    
    # Wait for FastAPI to be ready
    if wait_for_service "$API_URL/health" "FastAPI"; then
        print_status "FastAPI server started successfully (PID: $FASTAPI_PID)"
    else
        print_error "Failed to start FastAPI server"
        print_info "Check the logs: tail -f fastapi.log"
        exit 1
    fi
fi

# Step 4: Run debug endpoint tests
print_info "Step 4: Running debug endpoint tests..."

echo ""
echo -e "${BLUE}🧪 Running Comprehensive Debug Tests${NC}"
echo "======================================"

# Run the comprehensive test suite
if python test_debug_endpoints.py "$API_URL"; then
    print_status "Debug endpoint tests completed successfully!"
else
    print_error "Debug endpoint tests failed"
    print_info "Check the FastAPI logs: tail -f ../fastapi.log"
fi

# Step 5: Interactive testing option
echo ""
echo -e "${BLUE}🎮 Interactive Testing Available${NC}"
echo "================================="
echo "You can now test the debug endpoints interactively:"
echo ""
echo "1. Run interactive mode:"
echo "   python test_debug_endpoints.py $API_URL interactive"
echo ""
echo "2. Test individual endpoints via curl:"
echo "   # Status check"
echo "   curl -X GET \"$API_URL/debug/status?verbose=true\""
echo ""
echo "   # Ask a question"
echo "   curl -X POST \"$API_URL/debug/ask?verbose=true\" \\"
echo "        -H \"Content-Type: application/json\" \\"
echo "        -d '{\"question\": \"What is FastAPI?\", \"temperature\": 0.7}'"
echo ""
echo "   # Generate embeddings"
echo "   curl -X POST \"$API_URL/debug/embed?text=Hello%20world&verbose=true\""
echo ""
echo "   # Generate text"
echo "   curl -X POST \"$API_URL/debug/generate?verbose=true\" \\"
echo "        -H \"Content-Type: application/json\" \\"
echo "        -d '{\"prompt\": \"Write a Python function:\", \"temperature\": 0.5}'"
echo ""
echo "3. View Swagger UI documentation:"
echo "   Open: $API_URL/docs"
echo ""

# Step 6: Service information
echo -e "${BLUE}📊 Service Information${NC}"
echo "======================"
echo "FastAPI Server: $API_URL"
echo "LocalAI Server: $LOCALAI_URL"
echo "Swagger UI: $API_URL/docs"
echo "ReDoc: $API_URL/redoc"
echo ""

# Check service health
print_info "Checking service health..."
if curl -s "$API_URL/health" | grep -q "healthy"; then
    print_status "All services are healthy and ready for testing"
else
    print_warning "Some services may not be fully healthy - check logs"
fi

echo ""
echo -e "${GREEN}🎉 Debug endpoints are ready for manual verification!${NC}"
echo ""
echo "Next steps:"
echo "1. Test the endpoints using the interactive mode or curl commands above"
echo "2. Verify that LocalAI responses are working correctly"
echo "3. Check the terminal logs for detailed debugging information"
echo "4. Use the Swagger UI for easy endpoint testing"
echo ""
echo "To stop the services:"
echo "  kill \$(cat ../fastapi.pid) 2>/dev/null || true  # Stop FastAPI"
if [ "$SKIP_DOCKER" = false ]; then
    echo "  $DOCKER_COMPOSE_CMD down  # Stop Docker services"
fi
echo ""

# Cleanup function
cleanup() {
    print_info "Cleaning up..."
    if [ -f "../fastapi.pid" ]; then
        FASTAPI_PID=$(cat ../fastapi.pid)
        if kill -0 $FASTAPI_PID 2>/dev/null; then
            print_info "Stopping FastAPI server (PID: $FASTAPI_PID)..."
            kill $FASTAPI_PID
        fi
        rm -f ../fastapi.pid
    fi
}

# Set up signal handlers for cleanup
trap cleanup EXIT INT TERM

# Keep script running if in interactive mode
if [ "$1" = "interactive" ]; then
    print_info "Running in interactive mode - press Ctrl+C to exit"
    cd ..
    python $BACKEND_DIR/test_debug_endpoints.py "$API_URL" interactive
fi
