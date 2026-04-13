# Phase 5A - Production Deployment Plan

> **Status**: IN PROGRESS  
> **Date**: April 7, 2026  
> **Objective**: Prepare system for production deployment

---

## 🎯 Phase 5A Objectives

1. ✅ Verify all prerequisites met (Phase 4 complete)
2. ⏳ Create production environment
3. ⏳ Configure production database
4. ⏳ Set up automated backups
5. ⏳ Configure security (SSL, secrets, authentication)
6. ⏳ Configure deployment pipeline
7. ⏳ Document runbooks

---

## ✅ Pre-Deployment Checklist

### Code Quality (All From Phase 4)
- [x] 440+ tests passing
- [x] 85% backend coverage
- [x] 68% frontend coverage
- [x] 0 security vulnerabilities
- [x] All performance targets met
- [x] Documentation complete

### Infrastructure (To Verify)
- [ ] Production server provisioned
- [ ] Database server provisioned
- [ ] Redis server provisioned
- [ ] DNS configured
- [ ] SSL certificates ready
- [ ] CDN configured (if needed)

### Secrets & Security
- [ ] JWT secret generated
- [ ] Database credentials prepared
- [ ] API keys configured
- [ ] Encryption keys ready
- [ ] SSH keys configured

---

## 🏗️ Production Environment Setup

### 1. Infrastructure Architecture

```
Production Setup:
├── Frontend (CDN)
│   ├── Static assets (CloudFront / Cloudflare)
│   └── Web server (Nginx)
├── Backend (Kubernetes / Docker Swarm)
│   ├── API instances (3-5)
│   ├── Load balancer
│   └── Auto-scaling
├── Data Layer
│   ├── PostgreSQL (Primary + Replicas)
│   ├── Redis (Cache + Sessions)
│   └── SeaweedFS (File storage)
├── Monitoring
│   ├── Prometheus
│   ├── Grafana
│   ├── ELK Stack
│   └── Sentry
└── Infrastructure
    ├── VPC / Private network
    ├── Firewalls / Security groups
    └── Load balancing
```

### 2. Server Requirements

**Production Backend Servers**
```
CPU: 4 cores (Min) / 8 cores (Recommended)
RAM: 8GB (Min) / 16GB (Recommended)
Storage: 100GB SSD
Network: 1Gbps
OS: Linux (Ubuntu 22.04 LTS recommended)
```

**Production Database Server**
```
CPU: 8 cores (Minimum)
RAM: 32GB (Minimum)
Storage: 500GB SSD (Recommended RAID 1)
Network: 1Gbps (Minimum)
Backup: Separate backup storage
```

**Storage Server (SeaweedFS)**
```
CPU: 4 cores
RAM: 16GB
Storage: Requirements based on expected document volume
Network: 1Gbps
```

---

## 🗄️ Database Configuration

### 1. Production Database Setup

```bash
# Create production database
sudo -u postgres createdb consulta_rpp_prod

# Create production user with limited privileges
sudo -u postgres psql << EOF
CREATE USER consulta_rpp_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE consulta_rpp_prod TO consulta_rpp_user;
GRANT USAGE ON SCHEMA public TO consulta_rpp_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO consulta_rpp_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO consulta_rpp_user;
EOF

# Run migrations
alembic upgrade head

# Verify setup
psql -U consulta_rpp_user -d consulta_rpp_prod -c "SELECT version();"
```

### 2. Backup Strategy

```bash
# Daily automated backups
0 2 * * * pg_dump -U consulta_rpp_user consulta_rpp_prod | gzip > /backups/consulta_rpp_$(date +\%Y\%m\%d).sql.gz

# Weekly full backups
0 1 * * 0 pg_basebackup -D /backups/full_backup_$(date +\%Y\%m\%d) -Fp -Xs

# Backup retention: 30 days
find /backups -name "*.sql.gz" -mtime +30 -delete
```

### 3. High Availability

```yaml
# PostgreSQL HA Setup (Patroni / Stolon recommended)
postgres-primary:
  replication: true
  standby_servers: 2

postgres-standby-1:
  primary: postgres-primary
  
postgres-standby-2:
  primary: postgres-primary
```

---

## 🔐 Security Configuration

### 1. SSL/TLS Certificates

```bash
# Use Let's Encrypt with Certbot
sudo certbot certonly --standalone \
  -d consulta-rpp.com \
  -d api.consulta-rpp.com \
  -d admin.consulta-rpp.com

# Auto-renewal
0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Environment Secrets

```bash
# Create .env.production file (NEVER commit)
API_URL=https://api.consulta-rpp.com
DATABASE_URL=postgresql://user:pass@db.prod:5432/consulta_rpp_prod
REDIS_URL=redis://redis.prod:6379
JWT_SECRET=<generated-secret-key>
JWT_ALGORITHM=HS256
CORS_ORIGINS=https://consulta-rpp.com
LOG_LEVEL=info
```

### 3. Authentication & Authorization

```
JWT Configuration:
├── Token Expiration: 1 hour
├── Refresh Token: 7 days
├── Algorithm: HS256
├── Secret: Generated (256+ bit)
└── Validation: On every request
```

---

## 📦 Deployment Pipeline

### 1. Staging Deployment

```bash
# 1. Build Docker images
docker-compose -f docker-compose.staging.yml build

# 2. Push to registry
docker push registry.example.com/consulta-rpp:staging-latest

# 3. Deploy to staging
docker-compose -f docker-compose.staging.yml pull
docker-compose -f docker-compose.staging.yml up -d

# 4. Run smoke tests
bash scripts/smoke-tests.sh

# 5. Verify deployment
curl https://staging-api.consulta-rpp.com/health
```

### 2. Production Deployment

```bash
# 1. Backup current production
docker-compose -f docker-compose.prod.yml exec db pg_dump > backup-prod-$(date +%Y%m%d).sql

# 2. Pull new images
docker-compose -f docker-compose.prod.yml pull

# 3. Update services
docker-compose -f docker-compose.prod.yml up -d --no-deps --build

# 4. Verify health
curl https://api.consulta-rpp.com/health

# 5. Monitor metrics
watch 'curl -s https://api.consulta-rpp.com/metrics | head -20'
```

---

## ✅ Health Checks & Validation

### Pre-Deployment Health Checks (To Create)

```bash
# API endpoints
curl https://api.consulta-rpp.com/health
curl https://api.consulta-rpp.com/api/v1/auth/status

# Database connectivity
curl https://api.consulta-rpp.com/health/db

# Cache connectivity
curl https://api.consulta-rpp.com/health/cache

# Frontend
curl https://consulta-rpp.com -H "Accept-Language: es"

# SSL/TLS
openssl s_client -connect api.consulta-rpp.com:443
```

---

## 📊 Performance Targets (Production)

| Metric | Target | SLA |
|--------|--------|-----|
| API Response Time (p95) | < 200ms | 99.9% |
| Page Load Time | < 1.0s | 99.5% |
| Database Query (p95) | < 100ms | 99.9% |
| Error Rate | < 0.1% | 99.9% |
| Availability | > 99.9% | 24/7 |
| Cache Hit Ratio | > 80% | - |

---

## 🔄 Rollback Plan

### If Deployment Fails

```bash
# 1. Stop current deployment
docker-compose -f docker-compose.prod.yml down

# 2. Restore previous version
docker images | grep consulta-rpp
docker-compose -f docker-compose.prod.yml up -d --no-build # Uses previous image

# 3. Restore database if needed
psql -U consulta_rpp_user -d consulta_rpp_prod < backup-prod-$(date +%Y%m%d).sql

# 4. Verify everything works
curl https://api.consulta-rpp.com/health
```

---

## 📋 Deployment Checklist

### 24 Hours Before Deployment
- [ ] Test on staging environment
- [ ] All team members notified
- [ ] Runbooks reviewed
- [ ] Backup verified
- [ ] On-call engineer assigned
- [ ] Communication channel open

### Day of Deployment
- [ ] Final pre-deployment checks
- [ ] Backup taken
- [ ] Start deployment
- [ ] Monitor errors and logs
- [ ] Verify all systems
- [ ] Communicate status

### After Deployment
- [ ] Monitor for 24 hours
- [ ] Alert team of any issues
- [ ] Collect metrics
- [ ] Document lessons learned

---

## 📞 Deployment Support

### Emergency Contacts
- **Engineering Lead**: [Contact info]
- **On-Call Engineer**: [Contact info]
- **DevOps Team**: [Contact info]

### Escalation Path
1. **Level 1**: Automated monitoring alerts
2. **Level 2**: On-call engineer assessment
3. **Level 3**: Engineering lead involvement
4. **Level 4**: Management escalation

---

## 📈 Success Criteria

✅ **Phase 5A Success**:
- [ ] Production environment created
- [ ] Database configured and verified
- [ ] Backups working
- [ ] Security configured
- [ ] Deployment pipeline ready
- [ ] All health checks passing
- [ ] Team trained
- [ ] Runbooks documented

---

**Phase 5A Status**: ⏳ **IN PROGRESS - READY FOR EXECUTION**

Next: Phase 5A - Production Environment Setup

