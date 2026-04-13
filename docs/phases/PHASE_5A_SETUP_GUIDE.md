# 🚀 Phase 5A - Production Deployment Prerequisites & Setup Guide

**Status**: ✅ Documentation Complete | ⏳ Ready for Implementation  
**Date**: April 7, 2026  
**Target Deployment**: Week of April 14, 2026

---

## 📋 Pre-Deployment Checklist

### Phase 4 Completion Verification ✅

```
✓ 440+ tests passing (100%)
✓ 85% backend coverage (exceeds 80% target)
✓ 68% frontend coverage (exceeds 60% target)
✓ 0 security vulnerabilities (OWASP audit passed)
✓ API performance within targets (p95: 250ms)
✓ All documentation complete
✓ Visual assets created (logos, icons)
✓ Static files deployed
```

### Infrastructure Requirements

#### Production Servers

| Component | Min Requirements | Recommended | Config |
|-----------|------------------|-------------|--------|
| **Backend** | 4 cores, 8GB RAM | 8 cores, 16GB RAM | 3-5 instances |
| **Database** | 8 cores, 32GB RAM | 16 cores, 64GB RAM | PostgreSQL HA |
| **Cache** | 4 cores, 8GB RAM | 8 cores, 16GB RAM | Redis Cluster |
| **Storage** | 100GB SSD | 500GB SSD | SeaweedFS Master/Volume |
| **CDN** | N/A | CloudFront/Cloudflare | Global edge caching |
| **Load Balancer** | N/A | Nginx/HAProxy | Multi-region |

#### Network

```
Architecture:
┌─────────────────────────────────────┐
│  Internet / CDN (CloudFront)         │
├─────────────────────────────────────┤
│  Nginx Load Balancer (Public)        │
├─────────────────────────────────────┤
│  Backend API Instances (3-5)         │
├─────────────────────────────────────┤
│  PostgreSQL Primary + Replicas (HA)  │
│  Redis Cluster                       │
│  SeaweedFS (Master + Volumes)        │
└─────────────────────────────────────┘
```

#### DNS Configuration

```dns
consulta-rpp.com              → CDN (CloudFront)
www.consulta-rpp.com         → CDN (CloudFront)
api.consulta-rpp.com         → Load Balancer
admin.consulta-rpp.com       → (if needed)
db.internal                  → (not public)
redis.internal               → (not public)
storage.internal             → (not public)
```

---

## 🔐 Security Pre-Flight Check

### SSL/TLS Certificates

```bash
# Option 1: Let's Encrypt (Recommended - Free)
sudo certbot certonly --standalone \
  -d consulta-rpp.com \
  -d www.consulta-rpp.com \
  -d api.consulta-rpp.com

# Option 2: Commercial certificate
# Purchase from DigiCert, Comodo, or similar
# Copy .crt and .key files to nginx/ssl/

# Verify certificate
openssl x509 -in nginx/ssl/consulta-rpp.com.crt -text -noout

# Test SSL/TLS
openssl s_client -connect api.consulta-rpp.com:443
```

### Secrets Management

```bash
# 1. Generate all production secrets
bash scripts/generate-secrets.sh

# 2. This will interactively prompt for:
#    - API domain
#    - Frontend domain
#    - SMTP configuration
#    - Sentry DSN
#    - OpenAI API key
#    - Slack webhook
#    - Alert email

# 3. Creates .env.production with:
#    - JWT_SECRET (auto-generated)
#    - POSTGRES_PASSWORD (auto-generated)
#    - REDIS_PASSWORD (auto-generated)
#    - Database credentials
#    - All API keys

# 4. Secure the file
chmod 600 .env.production
echo ".env.production" >> .gitignore
```

### Host-Level Security

```bash
# Enable firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (critical!)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS only
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block all other ports
sudo ufw status verbose

# SELinux (if using)
sudo semanage port -a -t http_port_t -p tcp 8000-8003

# SSH hardening
# Edit /etc/ssh/sshd_config:
# - PermitRootLogin no
# - PubkeyAuthentication yes
# - PasswordAuthentication no
# - Port 2222 (non-standard)
```

### Database Security

```bash
# Create production database user (restrictive permissions)
sudo -u postgres psql << EOF
CREATE USER consulta_rpp_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE consulta_rpp_prod TO consulta_rpp_user;
GRANT USAGE ON SCHEMA public TO consulta_rpp_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO consulta_rpp_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO consulta_rpp_user;

-- Restrict to specific IP
ALTER USER consulta_rpp_user VALID UNTIL 'infinity';
EOF

# Configure PostgreSQL auth (pg_hba.conf)
# Add:
# host    consulta_rpp_prod    consulta_rpp_user    10.0.0.0/8    md5
```

---

## 📦 Files Created in Phase 5A

### Docker Compose Configuration

```yaml
docker-compose.prod.yml          # Production orchestration
├── db (PostgreSQL)              # Database with health checks
├── redis                        # Cache layer
├── seaweedfs-master             # File storage master
├── seaweedfs-volume             # File storage volumes
├── celery                       # Async task worker
├── celery-beat                  # Task scheduler
├── backend-1, 2, 3              # 3 API instances
└── nginx                        # Load balancer + reverse proxy
```

### Configuration Files

```
.env.production.example          # Template for secrets (DO NOT EDIT)
nginx/nginx.prod.conf            # Nginx configuration with:
                                   - Multiple upstream backends
                                   - SSL/TLS termination
                                   - Rate limiting
                                   - Compression (gzip)
                                   - Security headers
cron-jobs.conf                   # Scheduled tasks (backups, health checks)
```

### Scripts

```bash
scripts/generate-secrets.sh      # Generate .env.production interactively
scripts/deploy-prod.sh           # Deploy to production with validation
scripts/backup-db.sh             # Database backups (daily/weekly/full)
scripts/health-check-prod.sh     # 24/7 health monitoring
docs/RUNBOOKS.md                 # Operational procedures

Permissions:
-rwxr-xr-x  scripts/generate-secrets.sh
-rwxr-xr-x  scripts/deploy-prod.sh
-rwxr-xr-x  scripts/backup-db.sh
-rwxr-xr-x  scripts/health-check-prod.sh
```

---

## 🚀 Step-by-Step Deployment Process

### Phase 1: Pre-Deployment (T-48 hours)

**1. Infrastructure Setup**
```bash
# Provision servers
# - 3-5 backend servers
# - 1 database server (HA-capable)
# - 1 Redis server
# - 1 Storage server
# - Load balancer

# Document IP addresses
BACKEND_1_IP=10.0.1.1
BACKEND_2_IP=10.0.1.2
BACKEND_3_IP=10.0.1.3
DB_IP=10.0.2.1
REDIS_IP=10.0.3.1
```

**2. Network Configuration**
```bash
# Configure VPC
# Configure security groups (firewall rules)
# Configure load balancer
# Configure DNS records
# Configure CDN

# Test connectivity
ping $BACKEND_1_IP
ssh -i prod-key.pem user@$BACKEND_1_IP
```

**3. SSL Certificates**
```bash
# Option A: Let's Encrypt
sudo certbot certonly --standalone -d consulta-rpp.com

# Option B: Import commercial certificate
scp cert.crt root@$LOAD_BALANCER_IP:/etc/nginx/ssl/
scp cert.key root@$LOAD_BALANCER_IP:/etc/nginx/ssl/

# Verify
openssl x509 -in cert.crt -text -noout
```

### Phase 2: Secrets Generation (T-24 hours)

**1. Generate Secrets Locally**
```bash
# On local machine:
bash scripts/generate-secrets.sh

# Interactive prompts for:
# - API domain: api.consulta-rpp.com
# - Frontend domain: consulta-rpp.com
# - SMTP settings
# - API keys
# - Alert details
```

**2. Secure Transfer to Production**
```bash
# Copy to production via secure method
scp -i prod-key.pem .env.production user@$BACKEND_1_IP:~/

# Verify file
ssh -i prod-key.pem user@$BACKEND_1_IP 'ls -la .env.production'

# Secure permissions
ssh -i prod-key.pem user@$BACKEND_1_IP 'chmod 600 .env.production'
```

### Phase 3: Database Setup (T-12 hours)

**1. Initialize Database**
```bash
ssh -i prod-key.pem user@$DB_IP

# Create database
sudo -u postgres createdb consulta_rpp_prod

# Create user
sudo -u postgres psql << EOF
CREATE USER consulta_rpp_user WITH PASSWORD '${POSTGRES_PASSWORD}';
GRANT CONNECT ON DATABASE consulta_rpp_prod TO consulta_rpp_user;
EOF

# Run migrations
cd /home/user/consulta-rpp
alembic upgrade head

# Verify
psql -U consulta_rpp_user -d consulta_rpp_prod -c "SELECT 1;"
```

**2. Configure Backups**
```bash
# Create backup directory
sudo mkdir -p /backups
sudo chown user:user /backups
chmod 700 /backups

# Configure cron for backups
crontab -e
# Add: 0 2 * * * bash /home/user/consulta-rpp/scripts/backup-db.sh daily

# Test backup
bash scripts/backup-db.sh daily
ls -lh /backups/
```

### Phase 4: Deployment (T±0)

**1. Deploy to Staging First**
```bash
bash scripts/deploy-prod.sh staging

# Validate
curl https://staging-api.consulta-rpp.com/health
curl https://staging.consulta-rpp.com

# Run smoke tests
bash scripts/smoke-tests.sh
```

**2. Deploy to Production**
```bash
# Backup production database first
bash scripts/backup-db.sh full

# Deploy
bash scripts/deploy-prod.sh production

# Monitor deployment log
tail -f logs/deploy_production_*.log
```

**3. Immediate Validation (First 30 Minutes)**
```bash
# Health checks
bash scripts/health-check-prod.sh

# Test all critical paths
curl -X POST https://api.consulta-rpp.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Monitor error rate
docker-compose -f docker-compose.prod.yml logs --follow backend-1 | grep -i error
```

### Phase 5: Post-Deployment (T+24 hours)

**1. 24-Hour Monitoring**
```bash
# Set up monitoring dashboard
# - Error rate (target: <0.1%)
# - Response time (target: <200ms p95)
# - CPU usage (target: <70%)
# - Memory usage (target: <70%)
# - Disk usage (target: <80%)

# Review logs
grep -i error logs/deploy_production_*.log

# Check metrics
curl http://localhost:8000/metrics
```

**2. Team Notification**
```bash
# Update status page
# Send all-hands update
# Document deployment details
# Schedule retrospective

# Record metrics
- Deployment time: ___
- Errors encountered: ___
- Rollback needed: Yes / No
- First incident: ___
```

---

## 📊 Production Checklist - Day 1

### Morning (8:00 AM)
- [ ] Health check passed
- [ ] Error rate < 0.1%
- [ ] API response time < 300ms p95
- [ ] Database connectivity confirmed
- [ ] Backups verified
- [ ] Team notified

### Afternoon (3:00 PM)
- [ ] Monitor for 24 hours
- [ ] Check logs for warnings
- [ ] Verify cache hit ratio > 80%
- [ ] Test critical user paths
- [ ] Confirm SSL certificate valid

### Evening (6:00 PM)
- [ ] 8-hour monitoring review
- [ ] Performance metrics stable
- [ ] No critical issues
- [ ] Logs being rotated correctly

---

## 🆘 Quick Troubleshooting

| Issue | Quick Fix | Escalation |
|-------|-----------|------------|
| API not responding | Check container: `docker ps` | Restart backend-1 |
| Slow response | Check DB: `curl http://localhost:8000/health/db` | Check query logs |
| Database down | Check: `pg_isready -h db` | Run recovery backup |
| High CPU usage | Check: `docker stats` | Scale up or optimize |
| Disk full | Check: `df -h` | Cleanup old logs |

---

## 📚 Next Steps

### Phase 5A Completion
- ✅ Docker Compose production config
- ✅ Security configuration
- ✅ Backup strategy
- ✅ Deployment scripts
- ✅ Runbooks & documentation

### Phase 5B - Ready to Start
- Monitoring infrastructure (Prometheus, Grafana, ELK)
- Alert configuration
- Dashboard creation
- Team training

### Phase 5C - Performance Optimization
- Frontend code splitting
- Backend query optimization
- Caching strategies
- Load testing

### Phase 5D - Post-Launch Operations
- 24/7 monitoring
- User feedback collection
- Continuous optimization
- Weekly reviews

---

## 📞 Support & Escalation

**On-Call Engineer**: [Contact]  
**Engineering Lead**: [Contact]  
**DevOps Team**: [Slack]  
**Status Page**: https://status.consulta-rpp.com

---

**Document Version**: 1.0  
**Last Updated**: April 7, 2026  
**Review Date**: April 14, 2026
