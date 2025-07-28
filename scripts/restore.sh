#!/bin/bash

# =============================================================================
# CON-LLM-CONTAINER RESTORE SCRIPT
# =============================================================================
# This script restores data from backups created by backup.sh
# Usage: ./scripts/restore.sh <backup-name>
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo -e "${YELLOW}Warning: .env file not found, using defaults${NC}"
fi

# Default paths
BACKUP_PATH="${BACKUP_PATH:-$PROJECT_ROOT/backups}"

# Check if backup name is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Backup name is required${NC}"
    echo -e "Usage: $0 <backup-name>"
    echo -e "Available backups:"
    ls -la "$BACKUP_PATH" 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_DIR="$BACKUP_PATH/$BACKUP_NAME"

# Validate backup directory
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Backup directory not found: $BACKUP_DIR${NC}"
    exit 1
fi

# Check if manifest exists
if [ ! -f "$BACKUP_DIR/backup_manifest.json" ]; then
    echo -e "${YELLOW}Warning: Backup manifest not found, proceeding with standard restore${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CON-LLM-CONTAINER RESTORE${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Backup: ${GREEN}$BACKUP_NAME${NC}"
echo -e "Restore Path: ${GREEN}$BACKUP_DIR${NC}"
echo -e "Timestamp: $(date)"
echo ""

# Function to confirm dangerous operations
confirm_operation() {
    local operation=$1
    echo -e "${YELLOW}Warning: This will $operation${NC}"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Operation cancelled${NC}"
        exit 0
    fi
}

# Function to stop services
stop_services() {
    echo -e "${BLUE}Stopping Docker services...${NC}"
    cd "$PROJECT_ROOT"
    docker-compose down
    echo -e "${GREEN}✓ Services stopped${NC}"
}

# Function to restore Docker volumes
restore_volume() {
    local volume_name=$1
    local backup_file="$BACKUP_DIR/${volume_name}.tar.gz"
    
    echo -e "${YELLOW}Restoring volume: $volume_name${NC}"
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${YELLOW}Warning: Backup file not found: $backup_file${NC}"
        return 0
    fi
    
    # Create volume if it doesn't exist
    docker volume create "$volume_name" >/dev/null 2>&1 || true
    
    # Restore volume data
    docker run --rm \
        -v "$volume_name":/data \
        -v "$BACKUP_DIR":/backup \
        alpine:latest \
        sh -c "rm -rf /data/* && tar -xzf /backup/${volume_name}.tar.gz -C /data"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Volume $volume_name restored successfully${NC}"
    else
        echo -e "${RED}✗ Failed to restore volume $volume_name${NC}"
        return 1
    fi
}

# Function to restore application data
restore_application_data() {
    local backup_file="$BACKUP_DIR/${1}.tar.gz"
    local target_dir="$2"
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${YELLOW}Warning: Backup file not found: $backup_file${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Restoring application data: $target_dir${NC}"
    
    # Create target directory if it doesn't exist
    mkdir -p "$(dirname "$target_dir")"
    
    # Extract backup
    tar -xzf "$backup_file" -C "$(dirname "$target_dir")"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Application data restored successfully${NC}"
    else
        echo -e "${RED}✗ Failed to restore application data${NC}"
        return 1
    fi
}

# Function to restore PostgreSQL database
restore_postgres() {
    local backup_file="$BACKUP_DIR/postgres_dump.sql"
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${YELLOW}Warning: Database backup not found: $backup_file${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Restoring PostgreSQL database${NC}"
    
    # Start only PostgreSQL service
    cd "$PROJECT_ROOT"
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    echo -e "${BLUE}Waiting for PostgreSQL to be ready...${NC}"
    sleep 10
    
    # Restore database
    docker exec -i postgres psql \
        -U "${POSTGRES_USER:-con_selfrag}" \
        -d "${POSTGRES_DB:-con_selfrag}" \
        < "$backup_file"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PostgreSQL database restored successfully${NC}"
    else
        echo -e "${RED}✗ Failed to restore PostgreSQL database${NC}"
        return 1
    fi
}

# Function to check service health
check_service_health() {
    local service=$1
    local max_attempts=30
    local attempt=0
    
    echo -e "${BLUE}Checking health of $service...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps "$service" | grep -q "Up (healthy)"; then
            echo -e "${GREEN}✓ $service is healthy${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -e "${YELLOW}Waiting for $service to be healthy... ($attempt/$max_attempts)${NC}"
        sleep 10
    done
    
    echo -e "${RED}✗ $service failed to become healthy${NC}"
    return 1
}

# Main restore process
main() {
    echo -e "${BLUE}Starting restore process...${NC}"
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running${NC}"
        exit 1
    fi
    
    # Confirm restore operation
    confirm_operation "overwrite all existing data with backup from $BACKUP_NAME"
    
    # Stop services
    stop_services
    
    # Restore Docker volumes
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}Restoring Docker volumes...${NC}"
    restore_volume "localai-data"
    restore_volume "qdrant-data"
    restore_volume "postgres-data"
    restore_volume "redis-data"
    restore_volume "minio-data"
    
    # Restore application data
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}Restoring application data...${NC}"
    restore_application_data "app_data" "$DATA_PATH"
    restore_application_data "app_logs" "$LOGS_PATH"
    
    # Restore database
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}Restoring database...${NC}"
    restore_postgres
    
    # Start all services
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}Starting all services...${NC}"
    cd "$PROJECT_ROOT"
    docker-compose up -d
    
    # Check service health
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}Checking service health...${NC}"
    
    services=("postgres" "redis" "qdrant" "localai" "fastapi-gateway")
    if docker-compose config --services | grep -q "minio"; then
        services+=("minio")
    fi
    
    for service in "${services[@]}"; do
        check_service_health "$service"
    done
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Restore completed successfully!${NC}"
    echo -e "Restored from: ${GREEN}$BACKUP_NAME${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Run main function
main "$@"
