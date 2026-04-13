#!/bin/bash

###############################################################################
# Phase 5B - Monitoring Stack Deployment Script
# Usage: bash scripts/deploy-monitoring.sh
###############################################################################

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/deploy_monitoring_${TIMESTAMP}.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
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

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Create log directory
mkdir -p logs

log "======================================================================"
log "ConsultaRPP - Phase 5B Monitoring Stack Deployment"
log "======================================================================"

# Check prerequisites
log "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || error "Docker not found"
command -v docker-compose >/dev/null 2>&1 || error "Docker Compose not found"
test -f ".env.production" || error ".env.production file not found"
test -f "docker-compose.monitoring.yml" || error "docker-compose.monitoring.yml not found"

log "✓ Prerequisites check passed"

# Load environment
export $(cat .env.production | grep -v '^#' | xargs) 2>/dev/null || true

# Create monitoring network (if not exists)
log "Creating monitoring network..."
docker network create consulta-rpp-monitoring 2>/dev/null || log "Network already exists"

# Create Grafana password if not set
if [[ -z "$GRAFANA_PASSWORD" ]]; then
    GRAFANA_PASSWORD=$(openssl rand -base64 16)
    log "GRAFANA_PASSWORD generated: $GRAFANA_PASSWORD (save this!)"
    export GRAFANA_PASSWORD
fi

# Create Elasticsearch password if not set
if [[ -z "$ELASTICSEARCH_PASSWORD" ]]; then
    ELASTICSEARCH_PASSWORD=$(openssl rand -base64 16)
    log "ELASTICSEARCH_PASSWORD generated: $ELASTICSEARCH_PASSWORD (save this!)"
    export ELASTICSEARCH_PASSWORD
fi

# Build and start monitoring stack
log "Building monitoring stack..."
docker-compose -f docker-compose.monitoring.yml build || \
    error "Docker build failed"

log "Starting monitoring services..."
docker-compose -f docker-compose.monitoring.yml up -d || \
    error "Failed to start monitoring services"

log "✓ Monitoring services started"

# Wait for services to be healthy
log "Waiting for services to become healthy (30s)..."
sleep 10

# Check Prometheus
log "Checking Prometheus..."
if curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1; then
    log "✓ Prometheus is healthy"
else
    warning "Prometheus may not be ready yet"
fi

# Check Prometheus targets
log "Checking Prometheus targets..."
TARGET_COUNT=$(curl -s http://localhost:9090/api/v1/targets | grep -o '"up":true' | wc -l)
log "✓ Prometheus has $TARGET_COUNT targets up"

# Check Grafana
log "Checking Grafana..."
if curl -sf http://localhost:3000/api/health >/dev/null 2>&1; then
    log "✓ Grafana is healthy"
else
    warning "Grafana may not be ready yet"
fi

# Check Elasticsearch
log "Checking Elasticsearch..."
if curl -sf http://localhost:9200/_cluster/health >/dev/null 2>&1; then
    log "✓ Elasticsearch is healthy"
else
    warning "Elasticsearch may not be ready yet"
fi

# Check Kibana
log "Checking Kibana..."
if curl -sf http://localhost:5601/api/status >/dev/null 2>&1; then
    log "✓ Kibana is healthy"
else
    warning "Kibana may not be ready yet"
fi

# Summary
log ""
log "======================================================================"
log "Monitoring Stack Deployment Summary"
log "======================================================================"
log ""
log "Services:"
log "  - Prometheus:    http://localhost:9090"
log "  - Grafana:       http://localhost:3000 (admin / ${GRAFANA_PASSWORD})"
log "  - Kibana:        http://localhost:5601"
log "  - Alertmanager:  http://localhost:9093"
log ""
log "Next steps:"
log "  1. Login to Grafana: http://localhost:3000"
log "  2. Change admin password"
log "  3. Import dashboards from ./monitoring/grafana/dashboards/"
log "  4. Create custom dashboards as needed"
log "  5. Configure notification channels (Slack, Email, etc)"
log "  6. Test alert rules"
log ""
log "Documentation:"
log "  - Phase 5B: docs/PHASE_5B_MONITORING_SETUP.md"
log "  - Runbooks: docs/RUNBOOKS.md"
log "  - Sentry:   monitoring/SENTRY_SETUP.md"
log ""
log "Log file: $LOG_FILE"
log "======================================================================"
log "✓ Monitoring stack deployment completed successfully!"

exit 0
