#!/bin/bash
# full_backup.sh - Complete system backup for CON-SelfRAG

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/full_backup.log"

echo "🚀 Starting full CON-SelfRAG system backup..."
echo "📅 Date: $(date)"
echo "📍 Script directory: ${SCRIPT_DIR}"

# Create log directory if it doesn't exist
sudo mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$1"
    echo "$(date): $1" >> "$LOG_FILE"
}

log_message "=== Full System Backup Started ==="

# Run PostgreSQL backup
log_message "🗄️  Starting PostgreSQL backup..."
if "${SCRIPT_DIR}/postgres_backup.sh"; then
    log_message "✅ PostgreSQL backup completed successfully"
    POSTGRES_SUCCESS=true
else
    log_message "❌ PostgreSQL backup failed"
    POSTGRES_SUCCESS=false
fi

echo ""

# Run Qdrant backup
log_message "🔍 Starting Qdrant backup..."
if "${SCRIPT_DIR}/qdrant_backup.sh"; then
    log_message "✅ Qdrant backup completed successfully"
    QDRANT_SUCCESS=true
else
    log_message "❌ Qdrant backup failed"
    QDRANT_SUCCESS=false
fi

echo ""

# Summary
log_message "📊 Backup Summary:"
log_message "   PostgreSQL: $([ "$POSTGRES_SUCCESS" = true ] && echo "✅ Success" || echo "❌ Failed")"
log_message "   Qdrant:     $([ "$QDRANT_SUCCESS" = true ] && echo "✅ Success" || echo "❌ Failed")"

if [ "$POSTGRES_SUCCESS" = true ] && [ "$QDRANT_SUCCESS" = true ]; then
    log_message "🎉 Full system backup completed successfully!"
    exit 0
else
    log_message "⚠️  Some backups failed - check individual backup logs"
    exit 1
fi
