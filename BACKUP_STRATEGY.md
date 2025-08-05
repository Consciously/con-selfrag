# 🛡️ CON-SelfRAG Backup Strategy

## Overview

This document outlines the comprehensive backup strategy for the CON-SelfRAG system, covering PostgreSQL database backups and Qdrant vector database backups to ensure data integrity and disaster recovery capabilities.

## 📊 Backup Components

### 1. PostgreSQL Database

- **Tables**: users, api_keys, documents, document_chunks, conversations, messages, memory_logs, etc.
- **Critical Data**: User accounts, authentication, chat history, document metadata
- **Backup Frequency**: Daily automated backups + on-demand backups

### 2. Qdrant Vector Database

- **Collections**: documents (vector embeddings)
- **Critical Data**: 384-dimensional vectors, payload metadata, collection configurations
- **Backup Frequency**: Daily automated backups + on-demand backups

### 3. Application Files

- **Configuration**: Environment files, Docker configurations
- **Logs**: Application logs, error logs (optional retention)
- **Models**: Local AI model files (if cached locally)

## 🚀 Backup Implementation

### PostgreSQL Backup

#### 1. Full Database Backup

```bash
#!/bin/bash
# postgres_backup.sh - Complete PostgreSQL backup script

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

# Full database backup
echo "🔄 Starting PostgreSQL backup..."
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
    echo "✅ PostgreSQL backup completed: ${BACKUP_FILE}"
    echo "📁 Backup size: $(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)"
else
    echo "❌ PostgreSQL backup failed!"
    exit 1
fi

# Cleanup old backups (keep last 30 days)
find "${BACKUP_DIR}" -name "selfrag_db_*.sql" -mtime +30 -delete
echo "🧹 Cleaned up backups older than 30 days"
```

#### 2. Table-Specific Backups

```bash
#!/bin/bash
# postgres_table_backup.sh - Backup specific tables

# Backup critical tables individually
CRITICAL_TABLES=("users" "api_keys" "memory_logs" "documents" "document_chunks")

for table in "${CRITICAL_TABLES[@]}"; do
    echo "🔄 Backing up table: ${table}"
    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
      --host="${DB_HOST}" \
      --port="${DB_PORT}" \
      --username="${DB_USER}" \
      --dbname="${DB_NAME}" \
      --table="${table}" \
      --format=custom \
      --file="${BACKUP_DIR}/${table}_${DATE}.sql"
done
```

### Qdrant Vector Database Backup

#### 1. Collection Snapshot Backup

```bash
#!/bin/bash
# qdrant_backup.sh - Qdrant vector database backup script

# Configuration
QDRANT_URL="http://localhost:6333"
BACKUP_DIR="/backup/qdrant"
DATE=$(date +%Y%m%d_%H%M%S)
COLLECTION_NAME="documents"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "🔄 Starting Qdrant collection backup..."

# Create collection snapshot
curl -X POST "${QDRANT_URL}/collections/${COLLECTION_NAME}/snapshots" \
  -H "Content-Type: application/json"

# Wait for snapshot creation
sleep 5

# List available snapshots
SNAPSHOTS=$(curl -s "${QDRANT_URL}/collections/${COLLECTION_NAME}/snapshots" | python3 -c "
import sys, json
data = json.load(sys.stdin)
snapshots = data.get('result', [])
if snapshots:
    print(snapshots[-1]['name'])
")

if [ -n "$SNAPSHOTS" ]; then
    echo "📥 Downloading snapshot: ${SNAPSHOTS}"

    # Download the snapshot
    curl -X GET "${QDRANT_URL}/collections/${COLLECTION_NAME}/snapshots/${SNAPSHOTS}" \
      --output "${BACKUP_DIR}/${COLLECTION_NAME}_${DATE}.snapshot"

    if [ $? -eq 0 ]; then
        echo "✅ Qdrant backup completed: ${COLLECTION_NAME}_${DATE}.snapshot"
        echo "📁 Backup size: $(du -h "${BACKUP_DIR}/${COLLECTION_NAME}_${DATE}.snapshot" | cut -f1)"
    else
        echo "❌ Qdrant backup download failed!"
        exit 1
    fi
else
    echo "❌ No snapshots found or snapshot creation failed!"
    exit 1
fi

# Cleanup old snapshots (keep last 30 days)
find "${BACKUP_DIR}" -name "${COLLECTION_NAME}_*.snapshot" -mtime +30 -delete
echo "🧹 Cleaned up Qdrant backups older than 30 days"
```

#### 2. Full Qdrant Data Directory Backup

```bash
#!/bin/bash
# qdrant_full_backup.sh - Full Qdrant data directory backup

QDRANT_DATA_DIR="/mnt/workspace/projects/con-selfrag/qdrant_data"
BACKUP_DIR="/backup/qdrant_full"
DATE=$(date +%Y%m%d_%H%M%S)

echo "🔄 Creating full Qdrant data backup..."

# Stop Qdrant service for consistent backup
docker-compose stop qdrant

# Create compressed backup of entire data directory
tar -czf "${BACKUP_DIR}/qdrant_data_${DATE}.tar.gz" -C "$(dirname "$QDRANT_DATA_DIR")" "$(basename "$QDRANT_DATA_DIR")"

# Restart Qdrant service
docker-compose start qdrant

echo "✅ Full Qdrant backup completed: qdrant_data_${DATE}.tar.gz"
```

## 🔄 Automated Backup Schedule

### Daily Backup Cron Jobs

```bash
# Add to crontab: crontab -e

# PostgreSQL backup every day at 2:00 AM
0 2 * * * /path/to/postgres_backup.sh >> /var/log/backup_postgres.log 2>&1

# Qdrant backup every day at 3:00 AM
0 3 * * * /path/to/qdrant_backup.sh >> /var/log/backup_qdrant.log 2>&1

# Weekly full Qdrant backup every Sunday at 4:00 AM
0 4 * * 0 /path/to/qdrant_full_backup.sh >> /var/log/backup_qdrant_full.log 2>&1
```

### Docker-based Backup Service

```yaml
# docker-compose.backup.yml
version: '3.8'

services:
  backup-service:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - ./scripts/backup:/backup/scripts
      - backup-data:/backup/data
      - ./qdrant_data:/qdrant_data:ro
    command: |
      sh -c '
        # Setup cron jobs
        echo "0 2 * * * /backup/scripts/postgres_backup.sh" | crontab -
        echo "0 3 * * * /backup/scripts/qdrant_backup.sh" | crontab -
        # Start cron
        crond -f
      '
    depends_on:
      - postgres
      - qdrant

volumes:
  backup-data:
```

## 📥 Restore Procedures

### PostgreSQL Restore

#### 1. Full Database Restore

```bash
#!/bin/bash
# postgres_restore.sh - Restore PostgreSQL database

BACKUP_FILE="/backup/postgresql/selfrag_db_20240115_020000.sql"
DB_NAME="selfrag_db"

echo "🔄 Restoring PostgreSQL database..."

# Drop existing database (WARNING: This destroys current data!)
PGPASSWORD="${POSTGRES_PASSWORD}" dropdb \
  --host="${DB_HOST}" \
  --port="${DB_PORT}" \
  --username="${DB_USER}" \
  "${DB_NAME}"

# Create new database
PGPASSWORD="${POSTGRES_PASSWORD}" createdb \
  --host="${DB_HOST}" \
  --port="${DB_PORT}" \
  --username="${DB_USER}" \
  "${DB_NAME}"

# Restore from backup
PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
  --host="${DB_HOST}" \
  --port="${DB_PORT}" \
  --username="${DB_USER}" \
  --dbname="${DB_NAME}" \
  --verbose \
  "${BACKUP_FILE}"

echo "✅ PostgreSQL restore completed"
```

#### 2. Selective Table Restore

```bash
# Restore specific table
PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
  --host="${DB_HOST}" \
  --port="${DB_PORT}" \
  --username="${DB_USER}" \
  --dbname="${DB_NAME}" \
  --table="memory_logs" \
  --clean \
  --verbose \
  "${BACKUP_FILE}"
```

### Qdrant Restore

#### 1. Collection Snapshot Restore

```bash
#!/bin/bash
# qdrant_restore.sh - Restore Qdrant collection from snapshot

SNAPSHOT_FILE="/backup/qdrant/documents_20240115_030000.snapshot"
QDRANT_URL="http://localhost:6333"
COLLECTION_NAME="documents"

echo "🔄 Restoring Qdrant collection from snapshot..."

# Delete existing collection (WARNING: This destroys current data!)
curl -X DELETE "${QDRANT_URL}/collections/${COLLECTION_NAME}"

# Upload and restore snapshot
curl -X PUT "${QDRANT_URL}/collections/${COLLECTION_NAME}/snapshots/upload" \
  -H "Content-Type:application/octet-stream" \
  --data-binary "@${SNAPSHOT_FILE}"

echo "✅ Qdrant collection restore completed"
```

#### 2. Full Data Directory Restore

```bash
#!/bin/bash
# qdrant_full_restore.sh - Restore full Qdrant data directory

BACKUP_FILE="/backup/qdrant_full/qdrant_data_20240115_040000.tar.gz"
QDRANT_DATA_DIR="/mnt/workspace/projects/con-selfrag/qdrant_data"

echo "🔄 Restoring full Qdrant data directory..."

# Stop Qdrant service
docker-compose stop qdrant

# Backup current data (safety measure)
mv "${QDRANT_DATA_DIR}" "${QDRANT_DATA_DIR}.backup.$(date +%s)"

# Extract backup
tar -xzf "${BACKUP_FILE}" -C "$(dirname "$QDRANT_DATA_DIR")"

# Restart Qdrant service
docker-compose start qdrant

echo "✅ Full Qdrant restore completed"
```

## 🎯 Backup Validation

### Automated Backup Testing

```bash
#!/bin/bash
# backup_validation.sh - Validate backup integrity

echo "🧪 Validating backup integrity..."

# Test PostgreSQL backup
echo "Testing PostgreSQL backup..."
PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore --list "${BACKUP_FILE}" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL backup is valid"
else
    echo "❌ PostgreSQL backup is corrupted!"
fi

# Test Qdrant snapshot
echo "Testing Qdrant snapshot..."
if [ -f "${SNAPSHOT_FILE}" ]; then
    FILE_SIZE=$(stat -f%z "${SNAPSHOT_FILE}" 2>/dev/null || stat -c%s "${SNAPSHOT_FILE}" 2>/dev/null)
    if [ "$FILE_SIZE" -gt 0 ]; then
        echo "✅ Qdrant snapshot exists and has content (${FILE_SIZE} bytes)"
    else
        echo "❌ Qdrant snapshot is empty!"
    fi
else
    echo "❌ Qdrant snapshot file not found!"
fi
```

## 📊 Monitoring & Alerting

### Backup Success Monitoring

```bash
#!/bin/bash
# backup_monitor.sh - Monitor backup status and send alerts

LAST_POSTGRES_BACKUP=$(find /backup/postgresql -name "selfrag_db_*.sql" -mtime -1 | wc -l)
LAST_QDRANT_BACKUP=$(find /backup/qdrant -name "documents_*.snapshot" -mtime -1 | wc -l)

if [ "$LAST_POSTGRES_BACKUP" -eq 0 ]; then
    echo "❌ ALERT: No PostgreSQL backup found in last 24 hours!"
    # Send alert (email, Slack, etc.)
fi

if [ "$LAST_QDRANT_BACKUP" -eq 0 ]; then
    echo "❌ ALERT: No Qdrant backup found in last 24 hours!"
    # Send alert (email, Slack, etc.)
fi

echo "📊 Backup Status: PostgreSQL: ${LAST_POSTGRES_BACKUP}, Qdrant: ${LAST_QDRANT_BACKUP}"
```

## 🚀 Quick Reference Commands

### Emergency Backup Commands

```bash
# Quick PostgreSQL backup
pg_dump -h localhost -U selfrag_user -d selfrag_db -f emergency_backup_$(date +%s).sql

# Quick Qdrant snapshot
curl -X POST http://localhost:6333/collections/documents/snapshots

# Quick system backup (both)
./scripts/backup/postgres_backup.sh && ./scripts/backup/qdrant_backup.sh
```

### Emergency Restore Commands

```bash
# Quick PostgreSQL restore (⚠️ DESTRUCTIVE)
pg_restore -h localhost -U selfrag_user -d selfrag_db emergency_backup_1705123456.sql

# Quick Qdrant restore (⚠️ DESTRUCTIVE)
curl -X PUT http://localhost:6333/collections/documents/snapshots/upload \
  --data-binary "@documents_20240115_030000.snapshot"
```

## 📋 Backup Checklist

### Daily Checks

- [ ] PostgreSQL backup completed successfully
- [ ] Qdrant snapshot created and downloaded
- [ ] Backup files are not corrupted
- [ ] Old backups cleaned up properly
- [ ] Backup logs reviewed for errors

### Weekly Checks

- [ ] Full Qdrant data directory backup completed
- [ ] Test restore procedure on development environment
- [ ] Verify backup retention policy compliance
- [ ] Check backup storage space availability

### Monthly Checks

- [ ] Full disaster recovery test
- [ ] Review and update backup scripts
- [ ] Audit backup access permissions
- [ ] Document any backup process changes

## 🔒 Security Considerations

### Backup Encryption

```bash
# Encrypt PostgreSQL backups
pg_dump [...] | gpg --cipher-algo AES256 --compress-algo 2 \
  --symmetric --output backup_encrypted.sql.gpg

# Encrypt Qdrant backups
gpg --cipher-algo AES256 --compress-algo 2 --symmetric \
  --output snapshot_encrypted.gpg documents_snapshot.snapshot
```

### Access Control

- Backup files should be readable only by backup service account
- Use separate credentials for backup operations
- Store backup encryption keys securely
- Implement backup integrity verification

## 📚 Additional Resources

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [Qdrant Snapshots Documentation](https://qdrant.tech/documentation/concepts/snapshots/)
- [Docker Backup Best Practices](https://docs.docker.com/storage/bind-mounts/#backup-restore-or-migrate-data-volumes)

---

**⚡ Quick Start**: Run `./scripts/backup/postgres_backup.sh && ./scripts/backup/qdrant_backup.sh` for immediate full system backup.

**📞 Emergency**: In case of data loss, immediately stop all services and contact the system administrator before attempting any restore operations.
