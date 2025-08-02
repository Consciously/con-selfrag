#!/bin/bash
"""
CLI Demo Script for Selfrag

This script demonstrates the key CLI functionality.
Run this after starting the Selfrag API to see the CLI in action.
"""

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "\n${BLUE}🔹 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if CLI is available
if [ ! -f "selfrag_cli.py" ]; then
    echo -e "${RED}❌ selfrag_cli.py not found. Please run from the backend directory.${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Selfrag CLI Demo${NC}"
echo "This demo showcases the CLI functionality."
echo "Make sure the Selfrag API is running (docker-compose up -d)"
echo ""

# Step 1: Health Check
print_step "Step 1: Health Check"
print_info "Checking if all services are healthy..."
python3 selfrag_cli.py health
echo ""

# Step 2: Create sample content
print_step "Step 2: Create Sample Document"
cat > demo_document.txt << 'EOF'
# Selfrag Knowledge System

Selfrag is a personal knowledge system designed for tech-savvy users who want complete control over their data. The system uses Retrieval-Augmented Generation (RAG) to provide semantic search capabilities over ingested documents.

## Key Features

- Local data storage with no cloud dependencies
- Vector-based semantic search using embeddings
- Support for multiple document formats
- RESTful API and command-line interface
- Docker-based deployment for easy setup

## Architecture

The system consists of several components:
1. FastAPI backend for API operations
2. Qdrant vector database for embeddings storage
3. PostgreSQL for structured data
4. Redis for caching
5. LocalAI for language model operations

## Use Cases

- Personal documentation management
- Research paper organization
- Code snippet and example storage
- Meeting notes and knowledge capture
EOF

print_success "Created demo_document.txt"

# Step 3: Ingest Document
print_step "Step 3: Document Ingestion"
print_info "Ingesting the sample document..."
python3 selfrag_cli.py ingest demo_document.txt \
    --title "Selfrag System Overview" \
    --tags "documentation,overview,system" \
    --type "documentation"
echo ""

# Step 4: Query Examples
print_step "Step 4: Query Examples"

queries=(
    "What is Selfrag?"
    "How does the architecture work?"
    "What are the key features?"
    "Docker deployment"
)

for query in "${queries[@]}"; do
    print_info "Querying: '$query'"
    python3 selfrag_cli.py query "$query" --limit 2
    echo ""
done

# Step 5: Statistics
print_step "Step 5: System Statistics"
print_info "Getting RAG pipeline statistics..."
python3 selfrag_cli.py stats
echo ""

# Step 6: JSON Output Example
print_step "Step 6: JSON Output (for scripting)"
print_info "Getting query results in JSON format..."
python3 selfrag_cli.py query "Selfrag features" --format json --limit 1
echo ""

# Cleanup
print_step "Cleanup"
rm -f demo_document.txt
print_success "Removed demo_document.txt"

echo ""
echo -e "${GREEN}🎉 CLI Demo Complete!${NC}"
echo ""
echo "Try these commands yourself:"
echo "  ./selfrag health"
echo "  ./selfrag query 'your question here'"
echo "  ./selfrag chat  # Interactive mode"
echo ""
echo "For full documentation, see: app/cli/README.md"
