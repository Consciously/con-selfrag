#!/bin/bash

# Quick restart script for debug endpoints testing
# This script restarts the FastAPI server and provides easy testing commands

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

echo -e "${BLUE}🔄 Quick Restart - Debug Endpoints${NC}"
echo "=================================="

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

# Check if we're in the right directory
if [ ! -d "$BACKEND_DIR" ]; then
    print_error "Backend directory not found. Please run this script from the project root."
    exit 1
fi

# Stop any existing FastAPI server
print_info "Stopping any existing FastAPI server..."
if [ -f "fastapi.pid" ]; then
    FASTAPI_PID=$(cat fastapi.pid)
    if kill -0 $FASTAPI_PID 2>/dev/null; then
        print_info "Stopping FastAPI server (PID: $FASTAPI_PID)..."
        kill $FASTAPI_PID
        sleep 2
    fi
    rm -f fastapi.pid
fi

# Kill any process using port 8000
print_info "Checking for processes on port 8000..."
if lsof -ti:8000 >/dev/null 2>&1; then
    print_warning "Killing processes on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Go to backend directory
cd $BACKEND_DIR

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    print_info "Activating virtual environment..."
    source venv/bin/activate
else
    print_warning "No virtual environment found. Using system Python."
fi

# Start FastAPI server
print_info "Starting FastAPI server..."
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../fastapi.log 2>&1 &
FASTAPI_PID=$!
echo $FASTAPI_PID > ../fastapi.pid

print_status "FastAPI server started (PID: $FASTAPI_PID)"

# Wait for server to be ready
print_info "Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s --max-time 2 "$API_URL/health" > /dev/null 2>&1; then
        print_status "FastAPI server is ready!"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 30 ]; then
        print_error "Server failed to start within 30 seconds"
        print_info "Check logs: tail -f ../fastapi.log"
        exit 1
    fi
done

echo ""
print_status "🎉 Debug endpoints are ready for testing!"
echo ""

# Show quick test commands
echo -e "${BLUE}🧪 Quick Test Commands:${NC}"
echo "======================="
echo ""
echo "1. Test status endpoint:"
echo "   curl -X GET \"$API_URL/debug/status?verbose=true\""
echo ""
echo "2. Test ask endpoint:"
echo "   curl -X POST \"$API_URL/debug/ask?verbose=true\" \\"
echo "        -H \"Content-Type: application/json\" \\"
echo "        -d '{\"question\": \"What is FastAPI?\", \"temperature\": 0.7}'"
echo ""
echo "3. Test embed endpoint:"
echo "   curl -X POST \"$API_URL/debug/embed?text=Hello%20world&verbose=true\""
echo ""
echo "4. Test generate endpoint:"
echo "   curl -X POST \"$API_URL/debug/generate?verbose=true\" \\"
echo "        -H \"Content-Type: application/json\" \\"
echo "        -d '{\"prompt\": \"Write a Python function:\", \"temperature\": 0.5}'"
echo ""
echo "5. Interactive testing:"
echo "   python3 test_debug_endpoints.py $API_URL interactive"
echo ""
echo "6. Comprehensive test suite:"
echo "   python3 test_debug_endpoints.py $API_URL"
echo ""
echo "7. View Swagger UI:"
echo "   Open: $API_URL/docs"
echo ""

# Test the status endpoint immediately
echo -e "${BLUE}🔍 Testing Status Endpoint:${NC}"
echo "=========================="
if curl -s "$API_URL/debug/status?verbose=true" | python3 -m json.tool 2>/dev/null; then
    print_status "Status endpoint working!"
else
    print_warning "Status endpoint test failed - but server is running"
fi

echo ""
echo -e "${BLUE}📊 Service Information:${NC}"
echo "======================"
echo "FastAPI Server: $API_URL"
echo "Swagger UI: $API_URL/docs"
echo "Server Logs: tail -f ../fastapi.log"
echo "Server PID: $FASTAPI_PID (saved in ../fastapi.pid)"
echo ""

echo -e "${GREEN}✨ Ready for manual verification!${NC}"
echo ""
echo "To stop the server:"
echo "  kill $FASTAPI_PID"
echo "  # or"
echo "  kill \$(cat ../fastapi.pid)"
