# 📖 ConsultaRPP Production Runbooks

## Quick Navigation

- [⚠️ Incident Response](#incident-response)
- [🚀 Deployment Runbook](#deployment-runbook)
- [🔧 Troubleshooting Guide](#troubleshooting-guide)
- [📋 Operations Manual](#operations-manual)
- [🔄 Backup & Recovery](#backup--recovery)
- [🪵 Logs & Debugging](#logs--debugging)

---

## Incident Response

### Critical Alert Response SLA: 1 Hour

#### Severity Levels

| Severity | Definition | SLA | Action |
|----------|-----------|-----|--------|
| **Critical** | Complete outage / Data loss risk | 1h | Immediate escalation |
| **High** | Partial outage / Performance degradation | 4h | Urgent investigation |
| **Medium** | Feature not working / Intermittent errors | 24h | Schedule fix |
| **Low** | Minor bugs / Cosmetic issues | 1 week | Plan fix |

### Step 1: Verify the Alert

```bash
# SSH into production server
ssh ops@prod-server.com

# Check if it's a real issue
bash scripts/health-check-prod.sh

# View recent logs
tail -f logs/health-checks/health_*.log
```

### Step 2: Identify Root Cause

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs --tail=50 --follow [service-name]

# Check resource usage
docker stats

# Check database
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -d consulta_rpp_prod -c "SELECT version();"
```

### Step 3: Escalation Matrix

**Level 1: On-Call Engineer (30 min response)**
- Verify the alert
- Check logs and metrics
- Attempt basic restart

**Level 2: Engineering Lead (15 min response)**
- Database issues
- Network problems
- Security incidents

**Level 3: Infrastructure Team (10 min response)**
- Server outage
- Disk full
- Network outage

**Level 4: Manager/Director (5 min response)**
- Multiple system failures
- Data loss incident
- Security breach

### Critical Incident: Complete Outage

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down

# 2. Restore from backup
bash scripts/restore-db.sh

# 3. Verify backup integrity
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -d consulta_rpp_prod -c "SELECT COUNT(*) FROM users;"

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Monitor
bash scripts/health-check-prod.sh
watch 'docker-compose -f docker-compose.prod.yml logs --tail=20'
```

---

## Deployment Runbook

### Pre-Deployment Checklist (24 Hours Before)

- [ ] Code review completed
- [ ] All tests passing (440+)
- [ ] Code coverage acceptable (>80%)
- [ ] Security audit passed
- [ ] Performance targets validated
- [ ] Staging deployment successful
- [ ] Team notified (Slack + Email)
- [ ] On-call engineer assigned
- [ ] Runbooks reviewed

### Deployment Steps

#### 1. Prepare Files (T-2 Hours)

```bash
# Create staging environment
cp .env.production.example .env.staging

# Edit with staging values
nano .env.staging

# Test on staging first
bash scripts/deploy-prod.sh staging

# Verify staging deployment
curl https://staging-api.consulta-rpp.com/health
```

#### 2. Create Backup (T-1 Hour)

```bash
# Create full backup
bash scripts/backup-db.sh full

# Verify backup
ls -lh /backups/full_backup_*

# Copy backup to safe location
aws s3 cp /backups/full_backup_* s3://backup-bucket/consulta-rpp/
```

#### 3. Execute Deployment (T+0)

```bash
# Start deployment
bash scripts/deploy-prod.sh production

# Monitor deployment logs
tail -f logs/deploy_production_*.log

# Watch containers
watch 'docker-compose -f docker-compose.prod.yml ps'
```

#### 4. Validation (T+30 Minutes)

```bash
# Run health checks
bash scripts/health-check-prod.sh

# Check API endpoints
curl https://api.consulta-rpp.com/health
curl https://api.consulta-rpp.com/api/v1/auth/status

# Check frontend
curl https://consulta-rpp.com -H "Accept-Language: es"

# Monitor for errors (first 30 min)
docker-compose -f docker-compose.prod.yml logs --follow backend-1 | grep -i error
```

#### 5. Post-Deployment (T+1-24 Hours)

```bash
# Monitor metrics for 24 hours
watch 'curl -s http://localhost:8000/metrics | head -20'

# Check error rates
curl http://localhost/metrics | grep 'http_requests_total{status="500'

# Verify database
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -c "\du+"

# Document any issues
# Issues found: [list here]
# Resolution: [document resolution]
```

### Rollback Procedure

If deployment fails:

```bash
# 1. Stop new deployment
docker-compose -f docker-compose.prod.yml down

# 2. Check available backups
ls -la /backups/

# 3. Restore from backup
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec -T db psql -U consulta_rpp_user < /backups/full_backup_*/database.sql

# 4. Start previous version
docker-compose -f docker-compose.prod.yml up -d --no-build

# 5. Verify
bash scripts/health-check-prod.sh
```

---

## Troubleshooting Guide

### Issue: API Not Responding

```bash
# 1. Check if container is running
docker-compose -f docker-compose.prod.yml ps backend-1

# 2. Check logs
docker-compose -f docker-compose.prod.yml logs backend-1 --tail=50

# 3. Check if port is listening
docker-compose -f docker-compose.prod.yml exec backend-1 curl http://localhost:8000/health

# 4. Check database connection
docker-compose -f docker-compose.prod.yml exec backend-1 curl http://localhost:8000/health/db

# 5. Restart the service
docker-compose -f docker-compose.prod.yml restart backend-1

# 6. If still failing, check docker logs
docker logs consulta-rpp-backend-1-prod
```

### Issue: Database Connection Fails

```bash
# 1. Check if database container is running
docker-compose -f docker-compose.prod.yml ps db

# 2. Check database logs
docker-compose -f docker-compose.prod.yml logs db

# 3. Test connection
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -d consulta_rpp_prod -c "SELECT 1;"

# 4. Check disk space
docker-compose -f docker-compose.prod.yml exec db df -h

# 5. Check connection limit
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -d consulta_rpp_prod -c "SELECT count(*) FROM pg_stat_activity;"

# 6. If too many connections, kill idle ones
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -d consulta_rpp_prod -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle';"
```

### Issue: Redis Connection Fails

```bash
# 1. Check Redis container
docker-compose -f docker-compose.prod.yml ps redis

# 2. Test connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# 3. Check memory usage
docker-compose -f docker-compose.prod.yml exec redis redis-cli info memory

# 4. Check persistence
docker-compose -f docker-compose.prod.yml exec redis redis-cli --rdb

# 5. Flush if needed (WARNING: Clears all cache)
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL

# 6. Restart Redis
docker-compose -f docker-compose.prod.yml restart redis
```

### Issue: High Memory Usage

```bash
# 1. Check memory by container
docker stats

# 2. Find which container is using memory
docker-compose -f docker-compose.prod.yml stats

# 3. For backend, check for memory leaks
docker-compose -f docker-compose.prod.yml logs backend-1 | grep -i memory

# 4. For Redis, check top keys
docker-compose -f docker-compose.prod.yml exec redis redis-cli --bigkeys

# 5. For database, check long-running queries
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -c "SELECT query FROM pg_stat_activity WHERE query_start < NOW() - INTERVAL '5 minutes';"
```

### Issue: Slow API Responses

```bash
# 1. Check API metrics
curl http://localhost:8000/metrics | grep 'http_request_duration_ms'

# 2. Check database query time
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -c "SELECT count(*) FROM pg_stat_statements WHERE mean_time > 1000;"

# 3. Check Redis performance
docker-compose -f docker-compose.prod.yml exec redis redis-cli latency latest

# 4. Check network latency
ping -c 10 db  # Inside backend container

# 5. Enable query logging (temporary)
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -c "SET log_statement = 'all';"

# 6. Analyze slow queries
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -c "SELECT query FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Issue: Disk Space Critical

```bash
# 1. Check disk usage
du -sh /*

# 2. Find large Docker volumes
docker volume ls
docker volume inspect [volume_name]

# 3. Clean up old logs
find logs -name "*.log" -mtime +30 -delete

# 4. Clean up Docker images
docker image prune -a

# 5. Clean up stopped containers
docker container prune

# 6. Backup and rotate old backups
ls -lh /backups/ | tail -10
tar czf /archives/backups_$(date +%Y%m%d).tar.gz /backups/*.sql.gz
```

---

## Operations Manual

### Daily Tasks

**Morning Check (8:00 AM)**
```bash
# Run health checks
bash scripts/health-check-prod.sh

# Review overnight logs
docker-compose -f docker-compose.prod.yml logs --since 8h --until now backend-1 | grep -i error

# Check metrics
curl http://localhost:8000/metrics | head -30
```

**Backup Verification (10:00 AM)**
```bash
# Verify last backup
ls -lh /backups/ | head -5

# Check backup size
du -sh /backups/

# Verify backup integrity
gzip -t /backups/*.sql.gz
```

**Afternoon Check (3:00 PM)**
```bash
# Monitor resource usage
docker stats

# Check for warnings
docker-compose -f docker-compose.prod.yml logs --since 4h | grep -i warn
```

### Weekly Tasks

**Monday Morning**
```bash
# Review logs from weekend
docker-compose -f docker-compose.prod.yml logs --since 72h | grep -i error > weekly_errors.log

# Update documentation
nano docs/RUNBOOKS.md

# Test recovery procedures
bash scripts/backup-db.sh weekly
```

**Weekly Security Review**
```bash
# Check SSL certificate expiry
openssl x509 -in nginx/ssl/consulta-rpp.com.crt -noout -dates

# Review access logs for suspicious activity
grep "\.php\|\.asp\|\.jsp" /var/log/nginx/access.log

# Check failed login attempts
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -c "SELECT COUNT(*) FROM audit_log WHERE event='login_failed' AND created_at > NOW() - INTERVAL '7 days';"
```

---

## Backup & Recovery

### Backup Schedule

- **Daily**: 2:00 AM (SQL dump + gzip)
- **Weekly**: Sunday 1:00 AM (Full backup including Redis)
- **Monthly**: 1st of month (Archive + S3)
- **On-Demand**: Before deployments

### Create Manual Backup

```bash
# Quick daily backup
bash scripts/backup-db.sh daily

# Full backup (database + Redis)
bash scripts/backup-db.sh full

# Verify backup
ls -lh /backups/
gzip -t /backups/*.sql.gz
```

### Restore from Backup

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down

# 2. Restore database
docker-compose -f docker-compose.prod.yml up -d db

# Wait for database to start
sleep 10

# Restore from backup file
docker-compose -f docker-compose.prod.yml exec -T db \
    psql -U consulta_rpp_user -d consulta_rpp_prod < /backups/full_backup_*/database.sql

# 3. Verify
docker-compose -f docker-compose.prod.yml exec db psql -U consulta_rpp_user -d consulta_rpp_prod -c "SELECT COUNT(*) FROM users;"

# 4. Start other services
docker-compose -f docker-compose.prod.yml up -d
```

---

## Logs & Debugging

### Viewing Logs

```bash
# Follow all services
docker-compose -f docker-compose.prod.yml logs --follow

# Follow specific service
docker-compose -f docker-compose.prod.yml logs --follow backend-1

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend-1

# Since specific time
docker-compose -f docker-compose.prod.yml logs --since 2h backend-1
```

### Log Locations

```
Deployment logs:    logs/deploy_*.log
Health check logs:  logs/health-checks/health_*.log
Docker logs:        /var/lib/docker/containers/*/
Nginx logs:         /var/log/nginx/
PostgreSQL logs:    /var/log/postgresql/
```

### Enable Debug Logging

```bash
# In .env.production, change:
LOG_LEVEL=debug

# Restart services
docker-compose -f docker-compose.prod.yml restart backend-1
```

### Common Debug Patterns

```bash
# API errors
docker-compose -f docker-compose.prod.yml logs backend-1 | grep -i "exception\|error\|traceback"

# Database errors
docker-compose -f docker-compose.prod.yml logs db | grep -i "error\|fatal\|panic"

# Network errors
docker-compose -f docker-compose.prod.yml logs | grep -i "connection refused\|timeout"

# Authentication errors
docker-compose -f docker-compose.prod.yml logs | grep -i "authentication\|403\|401"
```

---

## Emergency Contacts

**On-Call Engineer**: [Phone] / [Email]  
**Lead Engineer**: [Phone] / [Email]  
**DevOps Team**: [Slack Channel]  
**Manager**: [Phone] / [Email]  

**Escalation Number**: [Emergency Line]  
**Status Page**: https://status.consulta-rpp.com  

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-04-07 | Initial runbooks created | DevOps Team |

---

**Last Updated**: April 7, 2026  
**Next Review**: April 14, 2026  
**Version**: 1.0
