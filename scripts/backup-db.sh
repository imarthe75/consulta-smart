#!/bin/bash

###############################################################################
# Production Database Backup Script
# Usage: bash scripts/backup-db.sh [daily|weekly|full]
# Cron: 0 2 * * * /home/user/consulta-rpp/scripts/backup-db.sh daily
###############################################################################

set -e

BACKUP_TYPE="${1:-daily}"
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "======================================================================"
log "ConsultaRPP Database Backup"
log "Type: $BACKUP_TYPE"
log "======================================================================"

# Load environment
if [[ -f ".env.production" ]]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Perform backup based on type
case "$BACKUP_TYPE" in
    daily)
        BACKUP_FILE="${BACKUP_DIR}/daily_backup_${TIMESTAMP}.sql.gz"
        log "Creating daily backup..."
        docker-compose -f docker-compose.prod.yml exec -T db \
            pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "$BACKUP_FILE"
        ;;
    weekly)
        BACKUP_FILE="${BACKUP_DIR}/weekly_backup_$(date +%Y%m%d_%A).sql.gz"
        log "Creating weekly backup..."
        docker-compose -f docker-compose.prod.yml exec -T db \
            pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "$BACKUP_FILE"
        ;;
    full)
        BACKUP_DIR_FULL="${BACKUP_DIR}/full_backup_${TIMESTAMP}"
        mkdir -p "$BACKUP_DIR_FULL"
        BACKUP_FILE="$BACKUP_DIR_FULL"
        log "Creating full backup..."
        
        # Database dump
        log "Exporting database..."
        docker-compose -f docker-compose.prod.yml exec -T db \
            pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | \
            gzip > "$BACKUP_DIR_FULL/database.sql.gz"
        
        # Redis dump
        log "Exporting Redis data..."
        docker-compose -f docker-compose.prod.yml exec -T redis \
            redis-cli -a "${REDIS_PASSWORD}" BGSAVE
        sleep 5
        
        # SeaweedFS data can be backed up via master server
        log "SeaweedFS backup configured separately"
        
        BACKUP_FILE="$BACKUP_DIR_FULL"
        ;;
    *)
        error "Invalid backup type: $BACKUP_TYPE. Use 'daily', 'weekly', or 'full'"
        ;;
esac

# Verify backup
log "Verifying backup..."
if [[ -d "$BACKUP_FILE" ]]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
else
    if [[ ! -f "$BACKUP_FILE" ]]; then
        error "Backup file not created"
    fi
    BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
fi

log "✓ Backup size: $BACKUP_SIZE"

# Test backup integrity (for SQL files only)
if [[ "$BACKUP_FILE" == *.sql.gz ]]; then
    log "Testing backup integrity..."
    if gzip -t "$BACKUP_FILE" 2>/dev/null; then
        log "✓ Backup integrity verified"
    else
        error "Backup file is corrupted"
    fi
fi

# Clean old backups
log "Cleaning old backups (retention: $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -maxdepth 1 -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -maxdepth 1 -name "daily_backup_*" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true

OLD_COUNT=$(find "$BACKUP_DIR" -maxdepth 1 -name "*.sql.gz" | wc -l)
log "✓ Old backups cleaned (remaining: $OLD_COUNT backups)"

# Summary
log ""
log "======================================================================"
log "Backup Summary"
log "======================================================================"
log "Backup Type:    $BACKUP_TYPE"
log "Backup File:    $BACKUP_FILE"
log "Backup Size:    $BACKUP_SIZE"
log "Timestamp:      $TIMESTAMP"
log "Log File:       $LOG_FILE"
log "======================================================================"
log "✓ Backup completed successfully!"

# Send notification if webhook configured
if [[ -n "${SLACK_WEBHOOK}" ]]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✓ Database backup completed ($BACKUP_TYPE) - Size: $BACKUP_SIZE\"}" \
        "${SLACK_WEBHOOK}" 2>/dev/null || true
fi

exit 0
