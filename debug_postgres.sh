#!/bin/bash

# PostgreSQL Connection Debug Script
# Sets environment variables and runs diagnostic

echo "🔍 PostgreSQL Connection Debug"
echo "=============================="

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=con_selfrag
export POSTGRES_PASSWORD=con_selfrag_password
export POSTGRES_DB=con_selfrag

# Check if PostgreSQL container is running
echo "📋 Checking PostgreSQL container status..."
if docker ps | grep -q postgres; then
    echo "✅ PostgreSQL container is running"
    
    # Show container details
    echo ""
    echo "📊 Container details:"
    docker ps | grep postgres
    
    # Check container logs (last 10 lines)
    echo ""
    echo "📝 Recent PostgreSQL logs:"
    docker logs postgres --tail 10
    
else
    echo "❌ PostgreSQL container is not running"
    echo "Starting PostgreSQL..."
    docker compose up -d postgres
    sleep 5
fi

# Run the diagnostic
echo ""
echo "🧪 Running connection diagnostic..."
python3 debug_postgres.py
