#!/bin/bash
# postgres_backup.sh - PostgreSQL backup script for CON-SelfRAG

# Configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="selfrag_db"
DB_USER="selfrag_user"
BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="selfrag_db_${DATE}.sql"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "🔄 Starting PostgreSQL backup..."
echo "📅 Date: $(date)"
echo "🗄️  Database: ${DB_NAME}"
echo "📁 Backup file: ${BACKUP_FILE}"

# Full database backup
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
  --host="${DB_HOST}" \
  --port="${DB_PORT}" \
  --username="${DB_USER}" \
  --dbname="${DB_NAME}" \
  --format=custom \
  --compress=9 \
  --verbose \
  --file="${BACKUP_DIR}/${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
    echo "✅ PostgreSQL backup completed successfully!"
    echo "📁 Backup size: ${BACKUP_SIZE}"
    echo "🗂️  Backup location: ${BACKUP_DIR}/${BACKUP_FILE}"
    
    # Log success
    echo "$(date): PostgreSQL backup completed - ${BACKUP_FILE} (${BACKUP_SIZE})" >> /var/log/backup_postgres.log
else
    echo "❌ PostgreSQL backup failed!"
    echo "$(date): PostgreSQL backup FAILED - ${BACKUP_FILE}" >> /var/log/backup_postgres.log
    exit 1
fi

# Cleanup old backups (keep last 30 days)
echo "🧹 Cleaning up old backups..."
DELETED_COUNT=$(find "${BACKUP_DIR}" -name "selfrag_db_*.sql" -mtime +30 -delete -print | wc -l)
echo "🗑️  Deleted ${DELETED_COUNT} backup(s) older than 30 days"

echo "✨ PostgreSQL backup process completed!"
