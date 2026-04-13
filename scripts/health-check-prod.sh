#!/bin/bash

###############################################################################
# Production Health Check Script
# Usage: bash scripts/health-check-prod.sh
# Cron: */5 * * * * /home/user/consulta-rpp/scripts/health-check-prod.sh
###############################################################################

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="logs/health-checks"
LOG_FILE="${LOG_DIR}/health_${TIMESTAMP}.log"
ALERT_EMAIL="${ALERT_EMAIL:-ops-team@consulta-rpp.com}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create log directory
mkdir -p "$LOG_DIR"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ✗ ERROR: $1${NC}" | tee -a "$LOG_FILE"
    ((FAILED++))
}

warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠ WARNING: $1${NC}" | tee -a "$LOG_FILE"
    ((WARNINGS++))
}

success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓ $1${NC}" | tee -a "$LOG_FILE"
    ((PASSED++))
}

# Load environment
[[ -f ".env.production" ]] && export $(cat .env.production | grep -v '^#' | xargs) || true

log "======================================================================"
log "ConsultaRPP Health Check"
log "======================================================================"

# 1. Check Docker containers
log ""
log "Checking Docker containers..."
for container in backend-1 backend-2 backend-3 db redis nginx celery-beat seaweedfs-master seaweedfs-volume; do
    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
        success "Container $container is running"
    else
        error "Container $container is not running"
    fi
done

# 2. Check API health
log ""
log "Checking API endpoints..."
for i in 1 2 3; do
    API_URL="http://localhost:800${i}/health"
    if curl -sf "$API_URL" >/dev/null 2>&1; then
        success "API instance $i (/health) responding"
    else
        error "API instance $i (/health) not responding"
    fi
done

# 3. Check database health
log ""
log "Checking Database..."
if docker-compose -f docker-compose.prod.yml exec -T db \
    pg_isready -U "${POSTGRES_USER}" >/dev/null 2>&1; then
    success "Database is accessible"
    
    # Check connection count
    CONN_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T db \
        psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c \
        "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null || echo "0")
    log "   Active connections: $CONN_COUNT"
    
    if [[ $CONN_COUNT -gt 50 ]]; then
        warning "High connection count: $CONN_COUNT"
    fi
else
    error "Database is not accessible"
fi

# 4. Check Redis health
log ""
log "Checking Redis..."
if docker-compose -f docker-compose.prod.yml exec -T redis \
    redis-cli -a "${REDIS_PASSWORD}" ping 2>/dev/null | grep -q "PONG"; then
    success "Redis is accessible"
    
    # Check memory usage
    REDIS_INFO=$(docker-compose -f docker-compose.prod.yml exec -T redis \
        redis-cli -a "${REDIS_PASSWORD}" info memory 2>/dev/null || echo "")
    
    if echo "$REDIS_INFO" | grep -q "used_memory_human"; then
        MEM_USAGE=$(echo "$REDIS_INFO" | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        log "   Memory usage: $MEM_USAGE"
    fi
else
    error "Redis is not accessible"
fi

# 5. Check SeaweedFS health
log ""
log "Checking SeaweedFS..."
if curl -sf http://localhost:9333/dir/status >/dev/null 2>&1; then
    success "SeaweedFS Master is healthy"
else
    error "SeaweedFS Master is not responding"
fi

if curl -sf http://localhost:8080/status >/dev/null 2>&1; then
    success "SeaweedFS Volume is healthy"
else
    error "SeaweedFS Volume is not responding"
fi

# 6. Check disk space
log ""
log "Checking Disk Space..."
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [[ $DISK_USAGE -lt 80 ]]; then
    success "Disk usage: ${DISK_USAGE}% (acceptable)"
elif [[ $DISK_USAGE -lt 90 ]]; then
    warning "Disk usage: ${DISK_USAGE}% (approaching limit)"
else
    error "Disk usage: ${DISK_USAGE}% (critical)"
fi

# 7. Check system load
log ""
log "Checking System Load..."
LOAD=$(uptime | tail -c 40 | cut -d' ' -f1)
log "System load average: $LOAD (last 1 min)"

# 8. Check SSL certificate
log ""
log "Checking SSL Certificate..."
CERT_DATE=$(docker-compose -f docker-compose.prod.yml exec nginx \
    openssl x509 -in /etc/nginx/ssl/consulta-rpp.com.crt -noout -enddate 2>/dev/null | \
    cut -d= -f2 || echo "Error")

if [[ "$CERT_DATE" != "Error" ]]; then
    log "SSL Certificate expires: $CERT_DATE"
    
    # Check if expiring in next 30 days
    EXPIRY_EPOCH=$(date -d "$CERT_DATE" +%s 2>/dev/null || echo "0")
    NOW_EPOCH=$(date +%s)
    DAYS_UNTIL=$((($EXPIRY_EPOCH - $NOW_EPOCH) / 86400))
    
    if [[ $DAYS_UNTIL -lt 0 ]]; then
        error "SSL Certificate has expired!"
    elif [[ $DAYS_UNTIL -lt 30 ]]; then
        warning "SSL Certificate expires in $DAYS_UNTIL days"
    else
        success "SSL Certificate is valid (expires in $DAYS_UNTIL days)"
    fi
else
    error "Could not verify SSL Certificate"
fi

# 9. Check Nginx
log ""
log "Checking Nginx..."
if curl -sf http://localhost/health >/dev/null 2>&1; then
    success "Nginx is responding"
else
    warning "Nginx may have issues"
fi

# Summary
log ""
log "======================================================================"
log "Health Check Summary"
log "======================================================================"
log "Passed:    ${GREEN}${PASSED}${NC}"
log "Warnings:  ${YELLOW}${WARNINGS}${NC}"
log "Failed:    ${RED}${FAILED}${NC}"
log "Timestamp: $TIMESTAMP"
log "======================================================================"

# Send notification if there are failures
if [[ $FAILED -gt 0 ]]; then
    STATUS="⚠️ HEALTH CHECK FAILED"
    
    # Send Slack notification
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$STATUS - $FAILED issues detected\",\"attachments\":[{\"text\":\"View logs: log_file_${TIMESTAMP}\",\"color\":\"danger\"}]}" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
    
    # Send email notification
    if command -v mail >/dev/null 2>&1; then
        echo "ConsultaRPP Health Check Failed - $FAILED issues" | \
            mail -s "ALERT: ConsultaRPP Health Check Failed" "$ALERT_EMAIL" || true
    fi
fi

if [[ $WARNINGS -gt 0 ]] && [[ $FAILED -eq 0 ]]; then
    log ""
    log "Review warnings above for potential issues"
fi

log "Log file: $LOG_FILE"

exit $FAILED
