#!/bin/bash

###############################################################################
# Production Deployment Script
# Usage: bash scripts/deploy-prod.sh [staging|production]
###############################################################################

set -e

ENVIRONMENT="${1:-staging}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/backups/consulta_rpp_backup_${TIMESTAMP}.sql.gz"
LOG_FILE="logs/deploy_${ENVIRONMENT}_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Create log directory
mkdir -p logs

log "======================================================================"
log "ConsultaRPP Production Deployment"
log "Environment: $ENVIRONMENT"
log "======================================================================"

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    error "Invalid environment. Use 'staging' or 'production'"
fi

# Check prerequisites
log "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || error "Docker not found"
command -v docker-compose >/dev/null 2>&1 || error "Docker Compose not found"
test -f ".env.${ENVIRONMENT}" || error ".env.${ENVIRONMENT} file not found"
test -f "docker-compose.${ENVIRONMENT}.yml" || error "docker-compose.${ENVIRONMENT}.yml not found"

log "✓ Prerequisites check passed"

# Load environment variables
log "Loading environment variables..."
export $(cat ".env.${ENVIRONMENT}" | grep -v '^#' | xargs)

# Backup database (production only)
if [[ "$ENVIRONMENT" == "production" ]]; then
    log "Creating database backup..."
    mkdir -p /backups
    
    docker-compose -f "docker-compose.${ENVIRONMENT}.yml" exec -T db \
        pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "$BACKUP_FILE" || \
        error "Database backup failed"
    
    log "✓ Backup created: $BACKUP_FILE"
    
    # Verify backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✓ Backup size: $BACKUP_SIZE"
fi

# Build images
log "Building Docker images..."
docker-compose -f "docker-compose.${ENVIRONMENT}.yml" build --no-cache || \
    error "Docker build failed"

log "✓ Docker images built successfully"

# Pull latest images from registry
log "Pulling latest images..."
docker-compose -f "docker-compose.${ENVIRONMENT}.yml" pull || \
    warning "Failed to pull some images from registry"

# Down the service (if running)
log "Stopping current services..."
docker-compose -f "docker-compose.${ENVIRONMENT}.yml" down --remove-orphans || true

# Start services
log "Starting services..."
docker-compose -f "docker-compose.${ENVIRONMENT}.yml" up -d || \
    error "Failed to start services"

log "✓ Services started"

# Wait for services to be healthy
log "Waiting for services to become healthy..."
sleep 10

HEALTHY=false
for i in {1..30}; do
    if docker-compose -f "docker-compose.${ENVIRONMENT}.yml" exec -T backend-1 \
        curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log "✓ Services are healthy"
        HEALTHY=true
        break
    fi
    echo -n "."
    sleep 2
done

if [[ "$HEALTHY" != "true" ]]; then
    error "Services failed to become healthy"
fi

# Run health checks
log "Running health checks..."

# Check API
log "Checking API endpoint..."
API_HEALTH=$(docker-compose -f "docker-compose.${ENVIRONMENT}.yml" exec -T backend-1 \
    curl -s http://localhost:8000/health || echo '{}')

if echo "$API_HEALTH" | grep -q "ok"; then
    log "✓ API is healthy"
else
    warning "API health check may have issues"
fi

# Check database
log "Checking database connectivity..."
if docker-compose -f "docker-compose.${ENVIRONMENT}.yml" exec -T db \
    pg_isready -U "${POSTGRES_USER}" >/dev/null 2>&1; then
    log "✓ Database is accessible"
else
    error "Database connectivity failed"
fi

# Check Redis
log "Checking Redis connectivity..."
if docker-compose -f "docker-compose.${ENVIRONMENT}.yml" exec -T redis \
    redis-cli -a "${REDIS_PASSWORD}" ping >/dev/null 2>&1; then
    log "✓ Redis is healthy"
else
    error "Redis connectivity failed"
fi

# Check SeaweedFS
log "Checking SeaweedFS connectivity..."
if docker-compose -f "docker-compose.${ENVIRONMENT}.yml" exec -T seaweedfs-master \
    curl -s http://localhost:9333/dir/status >/dev/null 2>&1; then
    log "✓ SeaweedFS is healthy"
else
    warning "SeaweedFS may have issues"
fi

# Display summary
log ""
log "======================================================================"
log "Deployment Summary"
log "======================================================================"
log "Environment:     $ENVIRONMENT"
log "Timestamp:       $TIMESTAMP"
log "API Endpoint:    http://localhost:8000/health"
log "Services:        $(docker-compose -f "docker-compose.${ENVIRONMENT}.yml" ps --services)"

if [[ "$ENVIRONMENT" == "production" ]]; then
    log "Backup File:     $BACKUP_FILE"
    log "Backup Size:     $BACKUP_SIZE"
fi

log "Log File:        $LOG_FILE"
log "======================================================================"
log "✓ Deployment completed successfully!"

# Optional: Send notification
if command -v curl >/dev/null 2>&1 && [[ -n "${SLACK_WEBHOOK}" ]]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✓ ConsultaRPP deployment successful on $ENVIRONMENT ($TIMESTAMP)\"}" \
        "${SLACK_WEBHOOK}" 2>/dev/null || true
fi

exit 0
