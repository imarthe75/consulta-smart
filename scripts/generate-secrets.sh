#!/bin/bash

###############################################################################
# Generate Production Secrets Script
# Usage: bash scripts/generate-secrets.sh
# WARNING: Run this BEFORE first deployment to production
###############################################################################

set -e

OUTPUT_FILE=".env.production"
BACKUP_FILE=".env.production.backup"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[✓]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo "======================================================================="
echo "ConsultaRPP Production Secrets Generator"
echo "======================================================================="
echo ""

# Check if .env.production already exists
if [[ -f "$OUTPUT_FILE" ]]; then
    warning "$OUTPUT_FILE already exists"
    read -p "Backup and overwrite? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$OUTPUT_FILE" "$BACKUP_FILE"
        log "Backup created: $BACKUP_FILE"
    else
        echo "Aborted."
        exit 0
    fi
fi

echo ""
echo "Generating secrets..."
echo ""

# Generate strong secrets
JWT_SECRET=$(openssl rand -base64 128 | head -c 43)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

log "JWT_SECRET generated (43 chars)"
log "POSTGRES_PASSWORD generated (32 chars)"
log "REDIS_PASSWORD generated (32 chars)"

echo ""
echo "======================================================================="
echo "Configuration Prompts"
echo "======================================================================="
echo ""

# Interactive configuration
read -p "Enter API domain (e.g., api.consulta-rpp.com): " API_DOMAIN
API_DOMAIN=${API_DOMAIN:-api.consulta-rpp.com}

read -p "Enter Frontend domain (e.g., consulta-rpp.com): " FRONTEND_DOMAIN
FRONTEND_DOMAIN=${FRONTEND_DOMAIN:-consulta-rpp.com}

read -p "Enter SMTP host (e.g., smtp.gmail.com): " SMTP_HOST
SMTP_HOST=${SMTP_HOST:-smtp.gmail.com}

read -p "Enter SMTP username (email): " SMTP_USERNAME

read -sp "Enter SMTP password: " SMTP_PASSWORD
echo ""

read -p "Enter Sentry DSN (leave blank to skip): " SENTRY_DSN

read -p "Enter OpenAI API key (leave blank to skip): " OPENAI_API_KEY

read -p "Enter Slack webhook URL (leave blank to skip): " SLACK_WEBHOOK

read -p "Enter alert email (ops-team@consulta-rpp.com): " ALERT_EMAIL
ALERT_EMAIL=${ALERT_EMAIL:-ops-team@consulta-rpp.com}

echo ""
echo "======================================================================="
echo "Generating .env.production file..."
echo "======================================================================="
echo ""

# Create .env.production file
cat > "$OUTPUT_FILE" << EOF
# Production Environment Variables
# Generated: $(date)
# WARNING: Never commit this file to version control

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=info
DEBUG=false

# API Configuration
API_URL=https://${API_DOMAIN}
API_PORT=8000
WORKERS=4

# Frontend Configuration
FRONTEND_URL=https://${FRONTEND_DOMAIN}
FRONTEND_PORT=3000

# Database Configuration (PostgreSQL)
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=consulta_rpp_prod
POSTGRES_USER=consulta_rpp_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Database Connection Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=3600

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=${REDIS_PASSWORD}

# JWT Configuration
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1
JWT_REFRESH_EXPIRATION_DAYS=7

# CORS Configuration
CORS_ORIGINS=https://${FRONTEND_DOMAIN},https://www.${FRONTEND_DOMAIN}
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# SeaweedFS Configuration
SEAWEEDFS_MASTER_URL=http://seaweedfs-master:9333
SEAWEEDFS_VOLUME_URL=http://seaweedfs-volume:8080
MAX_UPLOAD_SIZE=100000000  # 100MB

# Celery Configuration
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_TASK_TIME_LIMIT=3600
CELERY_CONCURRENCY=4

# Security
ALLOWED_HOSTS=${API_DOMAIN},${FRONTEND_DOMAIN}
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
CSRF_TRUSTED_ORIGINS=https://${FRONTEND_DOMAIN},https://www.${FRONTEND_DOMAIN}

# Monitoring & Logging
SENTRY_DSN=${SENTRY_DSN}
LOG_FORMAT=json
ENABLE_METRICS=true

# Email Configuration
SMTP_HOST=${SMTP_HOST}
SMTP_PORT=587
SMTP_USERNAME=${SMTP_USERNAME}
SMTP_PASSWORD=${SMTP_PASSWORD}
SMTP_FROM_EMAIL=noreply@${FRONTEND_DOMAIN}

# Third-party Services
OPENAI_API_KEY=${OPENAI_API_KEY}

# Performance Settings
CACHE_TTL_SEARCH=3600  # 1 hour
CACHE_TTL_DOCUMENTS=86400  # 24 hours
CACHE_TTL_USER_PREFS=604800  # 7 days
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600

# Backup Configuration
BACKUP_SCHEDULE=daily
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=/backups

# Alarms & Alerts
ALERT_EMAIL=${ALERT_EMAIL}
ALERT_SLACK_WEBHOOK=${SLACK_WEBHOOK}
ERROR_NOTIFICATION_THRESHOLD=5
EOF

log ".env.production created successfully"

# Set file permissions
chmod 600 "$OUTPUT_FILE"
log "File permissions set to 600 (secure)"

# Display summary
echo ""
echo "======================================================================="
echo "Secrets Generated Summary"
echo "======================================================================="
echo ""

echo "File: $OUTPUT_FILE"
echo "Permissions: 600 (owner read/write only)"
echo ""
echo "Configuration:"
echo "  API Domain:          ${API_DOMAIN}"
echo "  Frontend Domain:     ${FRONTEND_DOMAIN}"
echo "  SMTP Host:           ${SMTP_HOST}"
echo "  Alert Email:         ${ALERT_EMAIL}"
echo ""
echo "Secrets (shown once):"
echo "  JWT_SECRET:          ${JWT_SECRET:0:20}... (${#JWT_SECRET} chars)"
echo "  POSTGRES_PASSWORD:   ${POSTGRES_PASSWORD:0:10}... (${#POSTGRES_PASSWORD} chars)"
echo "  REDIS_PASSWORD:      ${REDIS_PASSWORD:0:10}... (${#REDIS_PASSWORD} chars)"
echo ""

# Security warnings
echo ""
warning "⚠️  IMPORTANT SECURITY WARNINGS:"
echo "  1. NEVER commit .env.production to Git"
echo "  2. Add to .gitignore: echo '.env.production' >> .gitignore"
echo "  3. Backup this file in a secure location"
echo "  4. Restrict file permissions: chmod 600 .env.production"
echo "  5. Only copy to production servers (not via email)"
echo "  6. Regenerate secrets if compromised"
echo ""

# Verification
echo "======================================================================="
log "Secrets generation completed successfully"
echo "======================================================================="
echo ""
echo "Next steps:"
echo "  1. Review generated file: nano .env.production"
echo "  2. Copy to production server via secure method (ssh, scp)"
echo "  3. Run deployment: bash scripts/deploy-prod.sh production"
echo ""

exit 0
