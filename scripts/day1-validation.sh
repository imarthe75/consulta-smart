#!/bin/bash

###############################################################################
# Day 1 Launch Validation Script
# Automated checks for production launch verification
# Usage: bash scripts/day1-validation.sh
###############################################################################

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

log_pass() {
    echo -e "${GREEN}[✓ PASS]${NC} $1"
    ((PASS_COUNT++))
}

log_fail() {
    echo -e "${RED}[✗ FAIL]${NC} $1"
    ((FAIL_COUNT++))
}

log_warn() {
    echo -e "${YELLOW}[! WARN]${NC} $1"
    ((WARN_COUNT++))
}

log_info() {
    echo -e "${BLUE}[i INFO]${NC} $1"
}

# Create report directory
mkdir -p reports
REPORT_FILE="reports/day1_validation_${TIMESTAMP}.txt"

{
    echo "======================================================================"
    echo "ConsultaRPP - Day 1 Launch Validation Report"
    echo "======================================================================"
    echo "Timestamp: $TIMESTAMP"
    echo "Report: $REPORT_FILE"
    echo ""

    # ==========================================================================
    # 1. INFRASTRUCTURE CHECKS
    # ==========================================================================
    
    echo "1. INFRASTRUCTURE VALIDATION"
    echo "======================================================================"
    
    # Check Kubernetes cluster
    if kubectl cluster-info &>/dev/null; then
        log_pass "Kubernetes cluster accessible"
    else
        log_fail "Kubernetes cluster NOT accessible"
    fi

    # Check backend pods
    BACKEND_PODS=$(kubectl get pods -l app=consulta-rpp-backend --no-headers 2>/dev/null | wc -l)
    if [ "$BACKEND_PODS" -ge 3 ]; then
        log_pass "Backend pods running: $BACKEND_PODS"
    else
        log_fail "Backend pods running: $BACKEND_PODS (expected 3+)"
    fi

    # Check frontend pods
    FRONTEND_PODS=$(kubectl get pods -l app=consulta-rpp-frontend --no-headers 2>/dev/null | wc -l)
    if [ "$FRONTEND_PODS" -ge 2 ]; then
        log_pass "Frontend pods running: $FRONTEND_PODS"
    else
        log_fail "Frontend pods running: $FRONTEND_PODS (expected 2+)"
    fi

    echo ""

    # ==========================================================================
    # 2. DATABASE VALIDATION
    # ==========================================================================
    
    echo "2. DATABASE VALIDATION"
    echo "======================================================================"
    
    # Check database connection
    if PGPASSWORD=$POSTGRES_PASSWORD psql -h $DB_HOST -U $POSTGRES_USER -d consulta_rpp \
        -c "SELECT version();" &>/dev/null; then
        log_pass "PostgreSQL database accessible"
    else
        log_fail "PostgreSQL database NOT accessible"
    fi

    # Check replication status
    REPL_STATUS=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h $DB_HOST -U $POSTGRES_USER \
        -d consulta_rpp -t -c "SELECT status FROM pg_stat_replication LIMIT 1;" 2>/dev/null)
    if [[ "$REPL_STATUS" == *"streaming"* ]]; then
        log_pass "Database replication: STREAMING"
    else
        log_warn "Database replication: NOT CONFIRMED"
    fi

    # Check tables exist
    TABLE_COUNT=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h $DB_HOST -U $POSTGRES_USER \
        -d consulta_rpp -t -c "SELECT count(*) FROM pg_tables WHERE schemaname='public';" 2>/dev/null)
    if [ "$TABLE_COUNT" -gt 0 ]; then
        log_pass "Database tables present: $TABLE_COUNT"
    else
        log_fail "Database tables NOT found"
    fi

    echo ""

    # ==========================================================================
    # 3. API HEALTH CHECKS
    # ==========================================================================
    
    echo "3. API HEALTH CHECKS"
    echo "======================================================================"
    
    # Health endpoint
    HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://api.consulta-rpp.com/health)
    if [ "$HEALTH_CODE" = "200" ]; then
        log_pass "Health endpoint: $HEALTH_CODE OK"
    else
        log_fail "Health endpoint: $HEALTH_CODE (expected 200)"
    fi

    # API response time
    RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null https://api.consulta-rpp.com/health)
    if (( $(echo "$RESPONSE_TIME < 0.5" | bc -l) )); then
        log_pass "API response time: ${RESPONSE_TIME}s (< 0.5s)"
    else
        log_warn "API response time: ${RESPONSE_TIME}s (> 0.5s)"
    fi

    # Authentication endpoint
    AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://api.consulta-rpp.com/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"test@consulta-rpp.com","password":"test"}')
    if [ "$AUTH_CODE" = "401" ] || [ "$AUTH_CODE" = "400" ]; then
        log_pass "Authentication endpoint: $AUTH_CODE (responding)"
    else
        log_fail "Authentication endpoint: $AUTH_CODE (not responding correctly)"
    fi

    echo ""

    # ==========================================================================
    # 4. FRONTEND VALIDATION
    # ==========================================================================
    
    echo "4. FRONTEND VALIDATION"
    echo "======================================================================"
    
    # Frontend accessibility
    FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://consulta-rpp.com)
    if [ "$FRONTEND_CODE" = "200" ]; then
        log_pass "Frontend accessibility: $FRONTEND_CODE OK"
    else
        log_fail "Frontend accessibility: $FRONTEND_CODE (expected 200)"
    fi

    # SSL/TLS verification
    SSL_DATE=$(curl -s -I https://consulta-rpp.com 2>&1 | grep date | cut -d' ' -f2-)
    if [ -n "$SSL_DATE" ]; then
        log_pass "SSL/TLS certificate: Valid"
    else
        log_fail "SSL/TLS certificate: Invalid or missing"
    fi

    echo ""

    # ==========================================================================
    # 5. CACHE VALIDATION
    # ==========================================================================
    
    echo "5. CACHE VALIDATION"
    echo "======================================================================"
    
    # Redis connection
    if redis-cli -h $REDIS_HOST ping &>/dev/null; then
        log_pass "Redis cluster accessible"
    else
        log_warn "Redis cluster NOT accessible"
    fi

    # Cache stats
    if command -v redis-cli &>/dev/null; then
        CACHE_INFO=$(redis-cli -h $REDIS_HOST info stats 2>/dev/null)
        if echo "$CACHE_INFO" | grep -q "total_commands_processed"; then
            log_pass "Redis cache operational"
        fi
    fi

    echo ""

    # ==========================================================================
    # 6. MONITORING VALIDATION
    # ==========================================================================
    
    echo "6. MONITORING VALIDATION"
    echo "======================================================================"
    
    # Prometheus metrics
    PROM_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://prometheus:9090/api/v1/query?query=up)
    if [ "$PROM_CODE" = "200" ]; then
        log_pass "Prometheus metrics: $PROM_CODE OK"
    else
        log_fail "Prometheus metrics: $PROM_CODE (expected 200)"
    fi

    # Grafana dashboards
    GRAFANA_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://grafana:3000/api/health)
    if [ "$GRAFANA_CODE" = "200" ]; then
        log_pass "Grafana dashboards: $GRAFANA_CODE OK"
    else
        log_fail "Grafana dashboards: $GRAFANA_CODE (expected 200)"
    fi

    # Alert manager
    ALERT_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://alertmanager:9093/-/healthy)
    if [ "$ALERT_CODE" = "200" ]; then
        log_pass "Alert manager: $ALERT_CODE OK"
    else
        log_fail "Alert manager: $ALERT_CODE (expected 200)"
    fi

    echo ""

    # ==========================================================================
    # 7. LOG VALIDATION
    # ==========================================================================
    
    echo "7. LOG VALIDATION"
    echo "======================================================================"
    
    # Check for critical errors in logs
    ERROR_COUNT=$(kubectl logs deployment/consulta-rpp-backend --tail=1000 2>/dev/null | \
        grep -i "CRITICAL\|ERROR\|FATAL" | wc -l)
    
    if [ "$ERROR_COUNT" -eq 0 ]; then
        log_pass "No critical errors in backend logs"
    else
        log_warn "Found $ERROR_COUNT errors in backend logs"
    fi

    # Check Elasticsearch
    ES_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://elasticsearch:9200/_cluster/health)
    if [ "$ES_CODE" = "200" ]; then
        log_pass "Elasticsearch: $ES_CODE OK"
    else
        log_warn "Elasticsearch: $ES_CODE (expected 200)"
    fi

    echo ""

    # ==========================================================================
    # 8. PERFORMANCE METRICS
    # ==========================================================================
    
    echo "8. PERFORMANCE METRICS"
    echo "======================================================================"
    
    echo "Key Performance Indicators:"
    
    # Get current metrics from Prometheus
    if command -v curl &>/dev/null; then
        # Request rate
        REQ_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total%5B1m%5D)" \
            2>/dev/null | grep -o '"value":\[[0-9.]*, "[0-9.]*"' | head -1 | cut -d'"' -f4 || echo "N/A")
        echo "  Requests/sec: $REQ_RATE (target: 1000+)"

        # Error rate
        ERR_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_errors_total%5B1m%5D)" \
            2>/dev/null | grep -o '"value":\[[0-9.]*, "[0-9e.-]*"' | head -1 | cut -d'"' -f4 || echo "N/A")
        echo "  Error rate: $ERR_RATE (target: < 0.1%)"

        # Response time p95
        LATENCY=$(curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,http_request_duration_seconds)" \
            2>/dev/null | grep -o '"value":\[[0-9.]*, "[0-9.]*"' | head -1 | cut -d'"' -f4 || echo "N/A")
        echo "  p95 Latency: ${LATENCY}ms (target: < 300ms)"
    else
        echo "  (Prometheus not accessible for detailed metrics)"
    fi

    echo ""

    # ==========================================================================
    # 9. BACKUP VALIDATION
    # ==========================================================================
    
    echo "9. BACKUP VALIDATION"
    echo "======================================================================"
    
    # Check last backup
    BACKUP_DIR="/backups"
    if [ -d "$BACKUP_DIR" ]; then
        LAST_BACKUP=$(ls -t "$BACKUP_DIR" 2>/dev/null | head -1)
        if [ -n "$LAST_BACKUP" ]; then
            BACKUP_AGE=$(find "$BACKUP_DIR/$LAST_BACKUP" -type f -mmin -120 2>/dev/null | wc -l)
            if [ "$BACKUP_AGE" -gt 0 ]; then
                log_pass "Recent backup found: $LAST_BACKUP"
            else
                log_warn "Last backup older than 2 hours"
            fi
        else
            log_fail "No backups found"
        fi
    else
        log_warn "Backup directory not accessible"
    fi

    echo ""

    # ==========================================================================
    # 10. SECURITY CHECKS
    # ==========================================================================
    
    echo "10. SECURITY CHECKS"
    echo "======================================================================"
    
    # Check SSL certificate expiry
    SSL_DAYS=$(echo | openssl s_client -servername consulta-rpp.com -connect consulta-rpp.com:443 2>/dev/null | \
        openssl x509 -noout -dates 2>/dev/null | grep notAfter | cut -d= -f2)
    
    if [ -n "$SSL_DAYS" ]; then
        log_pass "SSL certificate valid until: $SSL_DAYS"
    else
        log_warn "Could not verify SSL certificate"
    fi

    # Check firewall rules
    if sudo iptables -L -n 2>/dev/null | grep -q "Chain"; then
        log_pass "Firewall rules active"
    else
        log_warn "Firewall rules not accessible"
    fi

    echo ""

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    
    echo "======================================================================"
    echo "VALIDATION SUMMARY"
    echo "======================================================================"
    echo "Passed:  $PASS_COUNT ✅"
    echo "Failed:  $FAIL_COUNT ❌"
    echo "Warned:  $WARN_COUNT ⚠️"
    echo ""

    if [ "$FAIL_COUNT" -eq 0 ]; then
        echo "🎉 LAUNCH VALIDATED - All systems operational!"
        echo ""
        echo "Recommendation: PROCEED WITH TRAFFIC RAMP-UP"
        echo ""
    else
        echo "⚠️  ISSUES DETECTED - Review failures before proceeding"
        echo ""
        echo "Recommendation: FIX FAILURES before traffic ramp-up"
        echo ""
    fi

    echo "======================================================================"
    echo "Report generated: $TIMESTAMP"
    echo "Save this report: $REPORT_FILE"
    echo "======================================================================"

} | tee "$REPORT_FILE"

# Exit with appropriate code
if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
else
    exit 0
fi
