#!/bin/bash

# =============================================================================
# CON-LLM-CONTAINER BACKUP SCRIPT
# =============================================================================
# This script creates backups of all persistent data volumes
# Usage: ./scripts/backup.sh [backup-name]
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
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${1:-backup_$TIMESTAMP}"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo -e "${YELLOW}Warning: .env file not found, using defaults${NC}"
fi

# Default paths
BACKUP_PATH="${BACKUP_PATH:-$BACKUP_DIR}"
DATA_PATH="${DATA_PATH:-./data}"
LOGS_PATH="${LOGS_PATH:-./logs}"

# Create backup directory
mkdir -p "$BACKUP_PATH/$BACKUP_NAME"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CON-LLM-CONTAINER BACKUP${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Backup Name: ${GREEN}$BACKUP_NAME${NC}"
echo -e "Backup Path: ${GREEN}$BACKUP_PATH/$BACKUP_NAME${NC}"
echo -e "Timestamp: $(date)"
echo ""

# Function to backup Docker volumes
backup_volume() {
    local volume_name=$1
    local backup_file="$BACKUP_PATH/$BACKUP_NAME/${volume_name}.tar.gz"
    
    echo -e "${YELLOW}Backing up volume: $volume_name${NC}"
    
    if docker volume ls | grep -q "$volume_name"; then
        docker run --rm \
            -v "$volume_name":/data \
            -v "$BACKUP_PATH/$BACKUP_NAME":/backup \
            alpine:latest \
            tar -czf "/backup/${volume_name}.tar.gz" -C /data .
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Volume $volume_name backed up successfully${NC}"
            ls -lh "$backup_file"
        else
            echo -e "${RED}✗ Failed to backup volume $volume_name${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}Warning: Volume $volume_name not found, skipping${NC}"
    fi
}

# Function to backup application dataackup_application_data() {
    local source_dir=$1
    local backup_name=$2
    local backup_file="$BACKUP_PATH/$BACKUP_NAME/${backup_name}.tar.gz"
    
    if [ -d "$source_dir" ]; then
        echo -e "${YELLOW}Backing up application data: $source_dir${NC}"
        tar -czf "$backup_file" -C "$(dirname "$source_dir")" "$(basename "$source_dir")"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Application data backed up successfully${NC}"
            ls -lh "$backup_file"
        else
            echo -e "${RED}✗ Failed to backup application data${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}Warning: Directory $source_dir not found, skipping${NC}"
    fi
}

# Function to backup PostgreSQL database
backup_postgres() {
    local backup_file="$BACKUP_PATH/$BACKUP_NAME/postgres_dump.sql"
    
    echo -e "${YELLOW}Backing up PostgreSQL database${NC}"
    
    if docker ps | grep -q "postgres"; then
        docker exec postgres pg_dump \
            -U "${POSTGRES_USER:-con_selfrag}" \
            -d "${POSTGRES_DB:-con_selfrag}" \
            --no-password \
            --clean \
            --if-exists \
            > "$backup_file"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ PostgreSQL database backed up successfully${NC}"
            ls -lh "$backup_file"
        else
            echo -e "${RED}✗ Failed to backup PostgreSQL database${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}Warning: PostgreSQL container not running, skipping database backup${NC}"
    fi
}

# Create backup manifest
create_manifest() {
    local manifest_file="$BACKUP_PATH/$BACKUP_NAME/backup_manifest.json"
    
    cat > "$manifest_file" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "docker_version": "$(docker --version)",
    "docker_compose_version": "$(docker-compose --version 2>/dev/null || echo 'Not installed')",
    "volumes": [
        "localai-data",
        "qdrant-data",
        "postgres-data",
        "redis-data",
        "minio-data"
    ],
    "application_data": [
        "${DATA_PATH:-./data}",
        "${LOGS_PATH:-./logs}"
    ],
    "database": "postgres_dump.sql"
}
EOF
    
    echo -e "${GREEN}✓ Backup manifest created${NC}"
}

# Main backup process
main() {
    echo -e "${BLUE}Starting backup process...${NC}"
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running${NC}"
        exit 1
    fi
    
    # Backup Docker volumes
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}Backing up Docker volumes...${NC}"
    backup_volume "localai-data"
    backup_volume "qdrant-data"
    backup_volume "postgres-data"
    backup_volume "redis-data"
    backup_volume "minio-data"
    
    # Backup application data
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}Backing up application data...${NC}"
    backup_application_data "$DATA_PATH" "app_data"
    backup_application_data "$LOGS_PATH" "app_logs"
    
    # Backup database
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}Backing up database...${NC}"
    backup_postgres
    
    # Create manifest
    create_manifest
    
    # Calculate total backup size
    local total_size=$(du -sh "$BACKUP_PATH/$BACKUP_NAME" | cut -f1)
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Backup completed successfully!${NC}"
    echo -e "Backup location: ${GREEN}$BACKUP_PATH/$BACKUP_NAME${NC}"
    echo -e "Total size: ${GREEN}$total_size${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Clean old backups (keep last 7 days by default)
    if [ -d "$BACKUP_PATH" ]; then
        find "$BACKUP_PATH" -maxdepth 1 -type d -name "backup_*" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
        echo -e "${YELLOW}Old backups cleaned up (older than 7 days)${NC}"
    fi
}

# Run main function
main "$@"
