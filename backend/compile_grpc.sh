#!/bin/bash
#
# gRPC Protocol Buffer Compilation Script
# 
# This script compiles the .proto files into Python gRPC code.
# Run this script whenever the .proto files are updated.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔧 Compiling gRPC Protocol Buffers...${NC}"

# Create output directory if it doesn't exist
OUTPUT_DIR="app/grpc/generated"
mkdir -p "$OUTPUT_DIR"

# Create __init__.py for Python package
touch "$OUTPUT_DIR/__init__.py"

# Compile proto files
PROTO_DIR="app/grpc/protos"

if [ ! -d "$PROTO_DIR" ]; then
    echo -e "${RED}❌ Proto directory not found: $PROTO_DIR${NC}"
    exit 1
fi

# Check if proto files exist
PROTO_FILES=$(find "$PROTO_DIR" -name "*.proto" 2>/dev/null || true)

if [ -z "$PROTO_FILES" ]; then
    echo -e "${YELLOW}⚠️ No .proto files found in $PROTO_DIR${NC}"
    echo -e "${YELLOW}Creating placeholder files for Phase 3 development...${NC}"
    
    # Create placeholder generated files
    cat > "$OUTPUT_DIR/selfrag_pb2.py" << 'EOF'
"""
Generated protobuf code for Selfrag gRPC services.
This is a placeholder file for Phase 2 - actual compilation will happen in Phase 3.
"""

# Placeholder classes for type safety
class HealthCheckRequest:
    def __init__(self, service: str = ""):
        self.service = service

class HealthCheckResponse:
    def __init__(self, status: str = "SERVING", message: str = ""):
        self.status = status
        self.message = message

class QueryRequest:
    def __init__(self, query: str = "", limit: int = 10, filters: dict = None, 
                 context: str = "", session_id: str = "", enable_reranking: bool = True):
        self.query = query
        self.limit = limit
        self.filters = filters or {}
        self.context = context
        self.session_id = session_id
        self.enable_reranking = enable_reranking

class QueryResponse:
    def __init__(self, query: str = "", context: str = "", results: list = None,
                 total_results: int = 0, query_time_ms: int = 0, 
                 reranked: bool = False, context_used: bool = False):
        self.query = query
        self.context = context
        self.results = results or []
        self.total_results = total_results
        self.query_time_ms = query_time_ms
        self.reranked = reranked
        self.context_used = context_used

class IngestRequest:
    def __init__(self, content: str = "", metadata: dict = None):
        self.content = content
        self.metadata = metadata or {}

class IngestResponse:
    def __init__(self, id: str = "", status: str = "", message: str = ""):
        self.id = id
        self.status = status
        self.message = message
EOF

    cat > "$OUTPUT_DIR/selfrag_pb2_grpc.py" << 'EOF'
"""
Generated gRPC service code for Selfrag services.
This is a placeholder file for Phase 2 - actual compilation will happen in Phase 3.
"""

# Placeholder service stubs for type safety
class HealthStub:
    def __init__(self, channel):
        self.channel = channel
    
    def Check(self, request, timeout=None):
        # Placeholder implementation
        pass

class QueryStub:
    def __init__(self, channel):
        self.channel = channel
    
    def QueryContent(self, request, timeout=None):
        # Placeholder implementation
        pass

class IngestStub:
    def __init__(self, channel):
        self.channel = channel
    
    def IngestContent(self, request, timeout=None):
        # Placeholder implementation
        pass

# Placeholder servicer base classes
class HealthServicer:
    def Check(self, request, context):
        raise NotImplementedError()

class QueryServicer:
    def QueryContent(self, request, context):
        raise NotImplementedError()

class IngestServicer:
    def IngestContent(self, request, context):
        raise NotImplementedError()

# Placeholder service registration functions
def add_HealthServicer_to_server(servicer, server):
    # Placeholder - actual implementation in Phase 3
    pass

def add_QueryServicer_to_server(servicer, server):
    # Placeholder - actual implementation in Phase 3
    pass

def add_IngestServicer_to_server(servicer, server):
    # Placeholder - actual implementation in Phase 3
    pass
EOF

    echo -e "${GREEN}✅ Placeholder gRPC files created for Phase 2${NC}"
    echo -e "${YELLOW}📝 Note: Run this script again in Phase 3 with actual protobuf compiler${NC}"
    exit 0
fi

# Try to compile proto files (will be used in Phase 3)
echo -e "${YELLOW}📦 Found proto files: $PROTO_FILES${NC}"

# Check if grpcio-tools is available
if ! python -c "import grpc_tools.protoc" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ grpcio-tools not available - creating placeholder files${NC}"
    echo -e "${YELLOW}In Phase 3, install grpcio-tools and run: pip install grpcio-tools${NC}"
    
    # Create placeholder generated files
    
    exit 0
fi

# Actual compilation (for Phase 3)
echo -e "${YELLOW}🔨 Compiling protocol buffers...${NC}"

for PROTO_FILE in $PROTO_FILES; do
    echo -e "  Compiling: $PROTO_FILE"
    python -m grpc_tools.protoc \
        --proto_path="$PROTO_DIR" \
        --python_out="$OUTPUT_DIR" \
        --grpc_python_out="$OUTPUT_DIR" \
        "$PROTO_FILE"
done

echo -e "${GREEN}✅ gRPC compilation completed successfully${NC}"
echo -e "${GREEN}📁 Generated files in: $OUTPUT_DIR${NC}"

# List generated files
echo -e "${YELLOW}📋 Generated files:${NC}"
ls -la "$OUTPUT_DIR"
