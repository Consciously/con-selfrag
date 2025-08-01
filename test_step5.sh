#!/bin/bash

# Test script for Step 5 - /models and /health/llm endpoints
# This script manages Docker services and runs comprehensive tests

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
API_URL="http://localhost:8000"
LOCALAI_URL="http://localhost:8081"

echo -e "${BLUE}🚀 Step 5 Endpoint Testing - /models and /health/llm${NC}"
echo "============================================================"
echo

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_success() {
    print_status "$GREEN" "✅ $1"
}

print_error() {
    print_status "$RED" "❌ $1"
}

print_warning() {
    print_status "$YELLOW" "⚠️  $1"
}

print_info() {
    print_status "$BLUE" "ℹ️  $1"
}

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=1

    print_info "Checking $service_name health..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            print_success "$service_name is healthy"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to become healthy after $((max_attempts * 2)) seconds"
    return 1
}

# Function to install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    cd "$BACKEND_DIR"
    
    # Try uv first (faster), fallback to pip
    if command -v uv >/dev/null 2>&1; then
        print_info "Using uv for fast dependency installation..."
        if uv pip install httpx; then
            print_success "Dependencies installed with uv"
        else
            print_warning "uv installation failed, falling back to pip"
            if command -v pip3 >/dev/null 2>&1; then
                pip3 install httpx
            elif command -v pip >/dev/null 2>&1; then
                pip install httpx
            else
                print_error "No fallback package manager available"
                exit 1
            fi
        fi
    elif command -v pip3 >/dev/null 2>&1; then
        print_info "Using pip3 for dependency installation..."
        pip3 install httpx
    elif command -v pip >/dev/null 2>&1; then
        print_info "Using pip for dependency installation..."
        pip install httpx
    else
        print_error "No Python package manager found (uv, pip3, or pip)"
        print_info "Please install httpx manually: pip install httpx"
        exit 1
    fi
    
    # Verify httpx installation
    if python3 -c "import httpx" 2>/dev/null; then
        print_success "httpx is available for Python testing"
    else
        print_warning "httpx installation verification failed"
        print_info "Trying alternative installation methods..."
        
        # Try system package manager as fallback
        if command -v apt-get >/dev/null 2>&1; then
            print_info "Attempting installation via apt..."
            sudo apt-get update && sudo apt-get install -y python3-httpx
        elif command -v yum >/dev/null 2>&1; then
            print_info "Attempting installation via yum..."
            sudo yum install -y python3-httpx
        elif command -v brew >/dev/null 2>&1; then
            print_info "Attempting installation via brew..."
            brew install httpx
        else
            print_error "Unable to install httpx automatically"
            print_info "Please install httpx manually:"
            print_info "  pip3 install httpx"
            print_info "  or: python3 -m pip install httpx"
            exit 1
        fi
    fi
    
    cd "$SCRIPT_DIR"
}

# Function to start Docker services
start_services() {
    print_info "Starting Docker services..."
    
    # Start services with health checks
    docker compose up -d
    
    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    
    # Check LocalAI health
    if ! check_service_health "LocalAI" "$LOCALAI_URL/readyz"; then
        print_error "LocalAI service failed to start"
        print_info "Checking LocalAI logs..."
        docker compose logs localai --tail=20
        return 1
    fi
    
    # Check FastAPI health
    if ! check_service_health "FastAPI" "$API_URL/health/"; then
        print_error "FastAPI service failed to start"
        print_info "Checking FastAPI logs..."
        docker compose logs fastapi-gateway --tail=20
        return 1
    fi
    
    print_success "All services are healthy and ready"
}

# Function to run Step 5 tests
run_step5_tests() {
    print_info "Running Step 5 endpoint tests..."
    
    # Set environment variables for testing
    export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"
    
    # Check if httpx is available for comprehensive tests
    if python3 -c "import httpx" 2>/dev/null; then
        print_info "Using comprehensive test suite with httpx..."
        # Run the comprehensive test script
        if python3 "$SCRIPT_DIR/test_step5_endpoints.py" "$API_URL"; then
            print_success "Step 5 comprehensive tests completed successfully"
            return 0
        else
            print_error "Step 5 comprehensive tests failed"
            return 1
        fi
    else
        print_warning "httpx not available, using quick standard library test..."
        # Run the quick test script using only standard library
        if python3 "$SCRIPT_DIR/quick_test_step5.py" "$API_URL"; then
            print_success "Step 5 quick tests completed successfully"
            return 0
        else
            print_error "Step 5 quick tests failed"
            return 1
        fi
    fi
}

# Function to run quick manual verification
quick_verification() {
    print_info "Running quick manual verification..."
    
    # Check if jq is available for JSON parsing
    local has_jq=false
    if command -v jq >/dev/null 2>&1; then
        has_jq=true
    fi
    
    # Test /models endpoint
    print_info "Testing GET /models..."
    local models_response
    if models_response=$(curl -s "$API_URL/models" 2>/dev/null); then
        if curl -s -f "$API_URL/models" >/dev/null 2>&1; then
            print_success "/models endpoint is working"
            echo "Response received ($(echo "$models_response" | wc -c) bytes)"
            
            if [ "$has_jq" = true ]; then
                echo "Available models:"
                echo "$models_response" | jq -r '.[].name' 2>/dev/null | head -5 | sed 's/^/  - /' || {
                    echo "  Raw response: $models_response"
                }
            else
                echo "  Raw response: $models_response"
                print_info "Install 'jq' for better JSON formatting"
            fi
        else
            print_warning "/models endpoint returned an error"
            echo "  Response: $models_response"
        fi
    else
        print_warning "/models endpoint is not accessible"
    fi
    echo
    
    # Test /health/llm endpoint
    print_info "Testing GET /health/llm..."
    local health_response
    if health_response=$(curl -s "$API_URL/health/llm" 2>/dev/null); then
        local health_status_code
        health_status_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health/llm" 2>/dev/null)
        
        if [ "$health_status_code" = "200" ] || [ "$health_status_code" = "503" ]; then
            print_success "/health/llm endpoint is working (HTTP $health_status_code)"
            
            if [ "$has_jq" = true ]; then
                echo "LLM health status:"
                echo "$health_response" | jq -r '.status, .message' 2>/dev/null | sed 's/^/  /' || {
                    echo "  Raw response: $health_response"
                }
                
                # Show individual check results if available
                echo "Individual checks:"
                echo "$health_response" | jq -r '.checks | to_entries[] | "  \(.key): \(.value.status) - \(.value.message)"' 2>/dev/null || {
                    echo "  (Unable to parse check details)"
                }
            else
                echo "  Raw response: $health_response"
                print_info "Install 'jq' for better JSON formatting"
            fi
        else
            print_warning "/health/llm endpoint returned HTTP $health_status_code"
            echo "  Response: $health_response"
        fi
    else
        print_warning "/health/llm endpoint is not accessible"
    fi
    echo
    
    # Test OpenAPI documentation
    print_info "Checking OpenAPI documentation..."
    local openapi_response
    if openapi_response=$(curl -s "$API_URL/openapi.json" 2>/dev/null); then
        if [ "$has_jq" = true ]; then
            if echo "$openapi_response" | jq -e '.paths."/models"' >/dev/null 2>&1; then
                print_success "/models is documented in OpenAPI"
            else
                print_warning "/models not found in OpenAPI documentation"
            fi
            
            if echo "$openapi_response" | jq -e '.paths."/health/llm"' >/dev/null 2>&1; then
                print_success "/health/llm is documented in OpenAPI"
            else
                print_warning "/health/llm not found in OpenAPI documentation"
            fi
            
            # Show total endpoint count
            local endpoint_count
            endpoint_count=$(echo "$openapi_response" | jq '.paths | keys | length' 2>/dev/null)
            print_info "Total documented endpoints: $endpoint_count"
        else
            # Without jq, do basic string matching
            if echo "$openapi_response" | grep -q '"/models"'; then
                print_success "/models found in OpenAPI documentation"
            else
                print_warning "/models not found in OpenAPI documentation"
            fi
            
            if echo "$openapi_response" | grep -q '"/health/llm"'; then
                print_success "/health/llm found in OpenAPI documentation"
            else
                print_warning "/health/llm not found in OpenAPI documentation"
            fi
            
            print_info "Install 'jq' for detailed OpenAPI analysis"
        fi
    else
        print_warning "Unable to fetch OpenAPI documentation"
    fi
}

# Function to show service logs
show_logs() {
    print_info "Recent service logs:"
    echo
    
    print_info "FastAPI Gateway logs:"
    docker compose logs fastapi-gateway --tail=10
    echo
    
    print_info "LocalAI logs:"
    docker compose logs localai --tail=10
}

# Function to cleanup
cleanup() {
    if [ "$1" = "full" ]; then
        print_info "Stopping and removing all services..."
        docker compose down -v
    else
        print_info "Stopping services..."
        docker compose stop
    fi
}

# Main execution
main() {
    local run_tests=true
    local cleanup_after=false
    local show_logs_after=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-tests)
                run_tests=false
                shift
                ;;
            --cleanup)
                cleanup_after=true
                shift
                ;;
            --logs)
                show_logs_after=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo
                echo "Options:"
                echo "  --no-tests    Skip running tests, just start services"
                echo "  --cleanup     Stop and remove services after testing"
                echo "  --logs        Show service logs after testing"
                echo "  --help, -h    Show this help message"
                echo
                echo "Examples:"
                echo "  $0                    # Run full test suite"
                echo "  $0 --no-tests        # Just start services"
                echo "  $0 --cleanup         # Run tests and cleanup"
                echo "  $0 --logs            # Run tests and show logs"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                print_info "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Check prerequisites
    if ! command -v docker >/dev/null 2>&1; then
        print_error "docker is required but not installed"
        exit 1
    fi
    
    # Check if docker compose is available (V2) or fallback to docker-compose (V1)
    if docker compose version >/dev/null 2>&1; then
        print_info "Using Docker Compose V2 (docker compose)"
    elif command -v docker-compose >/dev/null 2>&1; then
        print_warning "Docker Compose V2 not found, but V1 (docker-compose) is available"
        print_warning "Consider upgrading to Docker Compose V2 for better performance"
        # Note: The script uses 'docker compose' commands, so V1 users need to install V2
        print_error "This script requires Docker Compose V2. Please install it or use 'docker-compose' manually"
        exit 1
    else
        print_error "Docker Compose is required but not installed"
        print_info "Install Docker Compose V2: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    if ! command -v curl >/dev/null 2>&1; then
        print_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        print_warning "jq is not installed - JSON output will be raw"
        print_info "For better output formatting, install jq:"
        if command -v apt-get >/dev/null 2>&1; then
            print_info "  sudo apt-get install jq"
        elif command -v yum >/dev/null 2>&1; then
            print_info "  sudo yum install jq"
        elif command -v brew >/dev/null 2>&1; then
            print_info "  brew install jq"
        else
            print_info "  Visit: https://stedolan.github.io/jq/download/"
        fi
        echo
    fi
    
    # Install dependencies
    install_dependencies
    
    # Start services
    if ! start_services; then
        print_error "Failed to start services"
        show_logs
        exit 1
    fi
    
    # Run tests if requested
    if [ "$run_tests" = true ]; then
        echo
        print_info "Running comprehensive test suite..."
        if run_step5_tests; then
            print_success "All tests completed successfully!"
        else
            print_error "Some tests failed"
            show_logs_after=true
        fi
        
        echo
        print_info "Running quick verification..."
        quick_verification
    else
        print_info "Services are running. Test manually or run with tests enabled."
        print_info "API available at: $API_URL"
        print_info "Swagger UI: $API_URL/docs"
        print_info "LocalAI: $LOCALAI_URL"
    fi
    
    # Show logs if requested or if tests failed
    if [ "$show_logs_after" = true ]; then
        echo
        show_logs
    fi
    
    # Cleanup if requested
    if [ "$cleanup_after" = true ]; then
        echo
        cleanup full
    else
        echo
        print_info "Services are still running. Use 'docker compose down' to stop them."
        print_info "Or run: $0 --cleanup"
    fi
    
    print_success "Step 5 testing completed!"
}

# Handle script interruption
trap 'print_warning "Script interrupted"; cleanup; exit 1' INT TERM

# Run main function
main "$@"
