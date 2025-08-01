#!/bin/bash

# Diagnostic script for LocalAI service
# This script checks if LocalAI is running and what endpoints/models are available

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

# Function to test HTTP endpoint
test_endpoint() {
    local url="$1"
    local description="$2"
    
    print_status "Testing: $description"
    echo "  URL: $url"
    
    if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
        print_success "✅ $description - Accessible"
        
        # Show response if it's JSON
        response=$(curl -s --max-time 5 "$url" 2>/dev/null || echo "")
        if echo "$response" | jq . >/dev/null 2>&1; then
            echo "  Response: $(echo "$response" | jq -c . | head -c 200)..."
        else
            echo "  Response: $(echo "$response" | head -c 200)..."
        fi
    else
        print_error "❌ $description - Not accessible"
        
        # Try with verbose output to see what's wrong
        print_status "Detailed error information:"
        curl -v --max-time 5 "$url" 2>&1 | head -10 | sed 's/^/    /'
    fi
    echo ""
}

main() {
    print_status "🔍 LocalAI Service Diagnostic"
    echo "=============================================="
    
    # Check if curl is available
    if ! command_exists curl; then
        print_error "curl is not installed. Please install curl to run diagnostics."
        exit 1
    fi
    
    # Check if jq is available (optional, for pretty JSON)
    if ! command_exists jq; then
        print_warning "jq is not installed. JSON responses will not be formatted."
    fi
    
    # Set LocalAI connection details
    LOCALAI_HOST=${LOCALAI_HOST:-localhost}
    LOCALAI_PORT=${LOCALAI_PORT:-8080}
    BASE_URL="http://${LOCALAI_HOST}:${LOCALAI_PORT}"
    
    print_status "Configuration:"
    echo "  Host: $LOCALAI_HOST"
    echo "  Port: $LOCALAI_PORT"
    echo "  Base URL: $BASE_URL"
    echo ""
    
    # Test basic connectivity
    print_status "🌐 Testing Basic Connectivity"
    echo "=============================================="
    
    # Test root endpoint
    test_endpoint "$BASE_URL" "Root endpoint"
    
    # Test health endpoint (if available)
    test_endpoint "$BASE_URL/health" "Health endpoint"
    test_endpoint "$BASE_URL/readiness" "Readiness endpoint"
    
    # Test OpenAI API endpoints
    print_status "🤖 Testing OpenAI API Endpoints"
    echo "=============================================="
    
    # Test models endpoint
    test_endpoint "$BASE_URL/v1/models" "Models endpoint"
    
    # Test completions endpoint (with a simple request)
    print_status "Testing: Completions endpoint"
    echo "  URL: $BASE_URL/v1/completions"
    
    # Create a test request
    test_request='{
        "model": "test",
        "prompt": "Hello",
        "max_tokens": 5,
        "temperature": 0.1
    }'
    
    response=$(curl -s --max-time 10 -X POST \
        -H "Content-Type: application/json" \
        -d "$test_request" \
        "$BASE_URL/v1/completions" 2>/dev/null || echo "ERROR")
    
    if [[ "$response" != "ERROR" ]]; then
        print_success "✅ Completions endpoint - Accessible"
        echo "  Response: $(echo "$response" | head -c 200)..."
    else
        print_error "❌ Completions endpoint - Not accessible"
    fi
    echo ""
    
    # Test chat completions endpoint
    print_status "Testing: Chat completions endpoint"
    echo "  URL: $BASE_URL/v1/chat/completions"
    
    chat_request='{
        "model": "test",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5,
        "temperature": 0.1
    }'
    
    response=$(curl -s --max-time 10 -X POST \
        -H "Content-Type: application/json" \
        -d "$chat_request" \
        "$BASE_URL/v1/chat/completions" 2>/dev/null || echo "ERROR")
    
    if [[ "$response" != "ERROR" ]]; then
        print_success "✅ Chat completions endpoint - Accessible"
        echo "  Response: $(echo "$response" | head -c 200)..."
    else
        print_error "❌ Chat completions endpoint - Not accessible"
    fi
    echo ""
    
    # Test embeddings endpoint
    test_endpoint "$BASE_URL/v1/embeddings" "Embeddings endpoint (GET)"
    
    # Check Docker containers if docker is available
    if command_exists docker; then
        print_status "🐳 Docker Container Status"
        echo "=============================================="
        
        # Check if LocalAI container is running
        localai_containers=$(docker ps --filter "name=localai" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "")
        
        if [[ -n "$localai_containers" ]]; then
            print_success "LocalAI containers found:"
            echo "$localai_containers"
        else
            print_warning "No running LocalAI containers found"
            
            # Check if there are stopped containers
            stopped_containers=$(docker ps -a --filter "name=localai" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "")
            if [[ -n "$stopped_containers" ]]; then
                print_warning "Stopped LocalAI containers:"
                echo "$stopped_containers"
            fi
        fi
        echo ""
        
        # Check docker-compose services if available
        if command_exists docker-compose && [[ -f "docker-compose.yml" ]]; then
            print_status "Docker Compose Services:"
            docker-compose ps 2>/dev/null || print_warning "Could not get docker-compose status"
            echo ""
        fi
    fi
    
    # Check if LocalAI process is running
    print_status "🔍 Process Status"
    echo "=============================================="
    
    localai_processes=$(ps aux | grep -i localai | grep -v grep || echo "")
    if [[ -n "$localai_processes" ]]; then
        print_success "LocalAI processes found:"
        echo "$localai_processes"
    else
        print_warning "No LocalAI processes found"
    fi
    echo ""
    
    # Network connectivity test
    print_status "🌐 Network Connectivity"
    echo "=============================================="
    
    if nc -z "$LOCALAI_HOST" "$LOCALAI_PORT" 2>/dev/null; then
        print_success "✅ Port $LOCALAI_PORT is open on $LOCALAI_HOST"
    else
        print_error "❌ Port $LOCALAI_PORT is not accessible on $LOCALAI_HOST"
        
        if command_exists netstat; then
            print_status "Checking what's listening on port $LOCALAI_PORT:"
            netstat -tlnp 2>/dev/null | grep ":$LOCALAI_PORT " || print_warning "Nothing listening on port $LOCALAI_PORT"
        fi
    fi
    echo ""
    
    # Summary and recommendations
    print_status "📋 Summary and Recommendations"
    echo "=============================================="
    
    # Test if basic LocalAI endpoint works
    if curl -s --max-time 5 "$BASE_URL/v1/models" >/dev/null 2>&1; then
        print_success "✅ LocalAI appears to be running and accessible"
        print_status "Next steps:"
        echo "  1. Check if models are loaded: curl $BASE_URL/v1/models"
        echo "  2. Try running the LocalAI client tests again"
    else
        print_error "❌ LocalAI is not accessible"
        print_status "Troubleshooting steps:"
        echo "  1. Start LocalAI: docker-compose up -d localai"
        echo "  2. Check LocalAI logs: docker-compose logs localai"
        echo "  3. Verify LocalAI configuration in docker-compose.yml"
        echo "  4. Ensure models are properly loaded in LocalAI"
    fi
}

main "$@"
