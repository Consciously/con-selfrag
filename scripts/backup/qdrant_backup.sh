#!/bin/bash
# qdrant_backup.sh - Qdrant vector database backup script for CON-SelfRAG

# Configuration
QDRANT_URL="http://localhost:6333"
BACKUP_DIR="/backup/qdrant"
DATE=$(date +%Y%m%d_%H%M%S)
COLLECTION_NAME="documents"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "🔄 Starting Qdrant collection backup..."
echo "📅 Date: $(date)"
echo "🗂️  Collection: ${COLLECTION_NAME}"
echo "🌐 Qdrant URL: ${QDRANT_URL}"

# Check if Qdrant is accessible
if ! curl -s "${QDRANT_URL}/collections" > /dev/null; then
    echo "❌ Cannot connect to Qdrant at ${QDRANT_URL}"
    echo "$(date): Qdrant backup FAILED - Cannot connect to Qdrant" >> /var/log/backup_qdrant.log
    exit 1
fi

# Create collection snapshot
echo "📸 Creating collection snapshot..."
SNAPSHOT_RESPONSE=$(curl -s -X POST "${QDRANT_URL}/collections/${COLLECTION_NAME}/snapshots" \
  -H "Content-Type: application/json")

# Check if snapshot creation was successful
if echo "$SNAPSHOT_RESPONSE" | grep -q '"status":"ok"'; then
    echo "✅ Snapshot creation initiated successfully"
else
    echo "❌ Failed to create snapshot"
    echo "📄 Response: $SNAPSHOT_RESPONSE"
    exit 1
fi

# Wait for snapshot creation (increase wait time for large collections)
echo "⏳ Waiting for snapshot creation..."
sleep 10

# List available snapshots and get the latest one
echo "📋 Retrieving snapshot list..."
SNAPSHOTS_RESPONSE=$(curl -s "${QDRANT_URL}/collections/${COLLECTION_NAME}/snapshots")
LATEST_SNAPSHOT=$(echo "$SNAPSHOTS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    snapshots = data.get('result', [])
    if snapshots:
        # Sort by creation time and get the latest
        latest = sorted(snapshots, key=lambda x: x.get('creation_time', ''))[-1]
        print(latest['name'])
    else:
        print('')
except Exception as e:
    print('')
" 2>/dev/null)

if [ -n "$LATEST_SNAPSHOT" ]; then
    echo "📥 Downloading snapshot: ${LATEST_SNAPSHOT}"
    
    # Download the snapshot
    curl -X GET "${QDRANT_URL}/collections/${COLLECTION_NAME}/snapshots/${LATEST_SNAPSHOT}" \
      --output "${BACKUP_DIR}/${COLLECTION_NAME}_${DATE}.snapshot" \
      --progress-bar
    
    if [ $? -eq 0 ]; then
        BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${COLLECTION_NAME}_${DATE}.snapshot" | cut -f1)
        echo "✅ Qdrant backup completed successfully!"
        echo "📁 Backup size: ${BACKUP_SIZE}"
        echo "🗂️  Backup location: ${BACKUP_DIR}/${COLLECTION_NAME}_${DATE}.snapshot"
        
        # Log success
        echo "$(date): Qdrant backup completed - ${COLLECTION_NAME}_${DATE}.snapshot (${BACKUP_SIZE})" >> /var/log/backup_qdrant.log
    else
        echo "❌ Qdrant backup download failed!"
        echo "$(date): Qdrant backup FAILED - Download failed for ${LATEST_SNAPSHOT}" >> /var/log/backup_qdrant.log
        exit 1
    fi
    
    # Clean up the snapshot from Qdrant server (optional)
    echo "🧹 Cleaning up server-side snapshot..."
    curl -s -X DELETE "${QDRANT_URL}/collections/${COLLECTION_NAME}/snapshots/${LATEST_SNAPSHOT}" > /dev/null
    
else
    echo "❌ No snapshots found or snapshot creation failed!"
    echo "📄 Snapshots response: $SNAPSHOTS_RESPONSE"
    echo "$(date): Qdrant backup FAILED - No snapshots available" >> /var/log/backup_qdrant.log
    exit 1
fi

# Cleanup old backups (keep last 30 days)
echo "🧹 Cleaning up old backups..."
DELETED_COUNT=$(find "${BACKUP_DIR}" -name "${COLLECTION_NAME}_*.snapshot" -mtime +30 -delete -print | wc -l)
echo "🗑️  Deleted ${DELETED_COUNT} backup(s) older than 30 days"

echo "✨ Qdrant backup process completed!"
