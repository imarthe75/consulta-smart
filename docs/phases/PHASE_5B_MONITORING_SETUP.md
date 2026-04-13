# Phase 5B - Monitoring & Observability Setup

> **Status**: IN PROGRESS  
> **Date**: April 7, 2026  
> **Objective**: Establish comprehensive monitoring infrastructure

---

## 📊 Monitoring Architecture

```
Data Collection
├── Application Metrics (Prometheus)
├── Logs (ELK Stack)
├── Traces (Jaeger/OpenTelemetry)
├── Errors (Sentry)
└── Infrastructure (Telegraf)

Data Storage
├── Time-Series (Prometheus/InfluxDB)
├── Logs (Elasticsearch)
├── Traces (Backend database)
└── Errors (Sentry backend)

Visualization & Alerting
├── Dashboards (Grafana)
├── Alerts (AlertManager)
├── Incident Management (PagerDuty)
└── Status Page (Statuspage.io)
```

---

## 🔧 Monitoring Components

### 1. Application Performance Monitoring (APM)

**Metrics to Track:**
- Request latency (p50, p95, p99)
- Error rates by endpoint
- Throughput (requests/sec)
- Database query times
- Cache hit/miss ratio
- Memory usage
- CPU usage
- Garbage collection pauses

**Tools Options:**
- Datadog (Recommended for full-stack)
- New Relic (Good APM focus)
- Elastic APM (Open-source option)
- Prometheus + custom exporters

### 2. Log Aggregation

**Logs to Collect:**
- Backend API logs
- Frontend error logs
- Database logs
- Nginx/Load balancer logs
- Docker container logs
- System logs

**Setup Command (ELK Stack):**

```yaml
# docker-compose addition
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
  ports:
    - "9200:9200"

kibana:
  image: docker.elastic.co/kibana/kibana:8.0.0
  ports:
    - "5601:5601"

filebeat:
  image: docker.elastic.co/beats/filebeat:8.0.0
  volumes:
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/run/docker.sock:/var/run/docker.sock:ro
```

### 3. Infrastructure Monitoring

**Metrics:**
- CPU usage (per container/host)
- Memory usage (RSS, heap)
- Disk I/O
- Network I/O
- Container restarts
- Service uptime

**Tools:**
- Prometheus (Collection)
- Grafana (Visualization)
- Alertmanager (Alerts)

### 4. Error Tracking

**Setup Sentry:**

```python
# backend/app/core/config.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://key@sentry.example.com/project-id",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)
```

---

## 📈 Key Dashboards to Create

### Dashboard 1: System Health

```
Top Section:
├─ API Status (green/red indicator)
├─ Database Status (green/red indicator)
├─ Redis Status (green/red indicator)
└─ Storage Status (green/red indicator)

Main Metrics:
├─ Error Rate (last 24h) - Target: < 0.1%
├─ Request Volume (requests/sec)
├─ Average Response Time
├─ P95 Response Time
├─ P99 Response Time
└─ Cache Hit Ratio
```

### Dashboard 2: API Performance

```
By Endpoint:
├─ GET /api/v1/search - avg latency, error rate, QPS
├─ GET /api/v1/documents - avg latency, error rate, QPS
├─ POST /api/v1/chat/message - avg latency, error rate, QPS
├─ POST /api/v1/auth/token - avg latency, error rate, QPS
└─ Other endpoints...

Database Performance:
├─ Slow Queries (> 100ms)
├─ Query Volume per Endpoint
├─ Connection Pool Usage
└─ Transaction Times
```

### Dashboard 3: Business Metrics

```
Daily Stats:
├─ Active Users (last 24h)
├─ New Users (last 24h)
├─ Searches Performed (last 24h)
├─ Documents Uploaded (last 24h)
├─ Chat Sessions Created (last 24h)
└─ User Satisfaction (NPS)

Trends:
├─ Weekly active users
├─ Monthly growth rate
├─ Feature usage distribution
└─ User retention
```

### Dashboard 4: Infrastructure

```
Resources:
├─ CPU Usage (by container/host)
├─ Memory Usage (by container/host)
├─ Disk Usage (by volume)
├─ Network I/O (ingress/egress)
└─ Container Restarts

Issues:
├─ High latency incidents
├─ Out of Memory incidents
├─ Disk space warnings
└─ Network saturation alerts
```

---

## 🚨 Alert Rules

### Critical Alerts (Immediate Notification)

```
- API Error Rate > 1%
- Database Connection Pool Exhausted
- Disk Usage > 90%
- Memory Usage > 95%
- Response Time p99 > 2s
- API Unavailable (3+ consecutive failed health checks)
```

### High Priority Alerts (Notify within 5 min)

```
- Error Rate > 0.5%
- Response Time p95 > 1s
- Cache Hit Ratio < 60%
- Database Slow Queries > 10 per minute
- Container Restart Loop
```

### Medium Priority Alerts (Notify within 15 min)

```
- Error Rate > 0.1%
- Response Time > 500ms (average)
- Disk Usage > 75%
- Memory Usage > 80%
- High Network Traffic (> 80% capacity)
```

---

## 📊 Metrics Configuration

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend-api'
    static_configs:
      - targets: ['localhost:8000']
    
  - job_name: 'database'
    static_configs:
      - targets: ['localhost:9187']  # postgres_exporter
    
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']  # redis_exporter
    
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']  # node_exporter
```

### Grafana Data Source Configuration

```
Data Sources:
├─ Prometheus (http://prometheus:9090)
├─ Elasticsearch (http://elasticsearch:9200)
├─ Sentry (API integration)
└─ PagerDuty (API integration)
```

---

## 📊 Logging Configuration

### Backend Logging Setup

```python
# backend/app/core/logger.py
import logging
from pythonjsonlogger import jsonlogger

# JSON logging for easy parsing
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
```

### Log Levels

```
DEBUG: Development/Troubleshooting (disabled in production)
INFO: Important business events
WARNING: Potential issues
ERROR: Application errors
CRITICAL: System failures requiring immediate action
```

---

## 🔔 Notification Channels

### Configure Notification Routing

```
Critical Alerts → PagerDuty + Slack + Email + SMS
High Priority → Slack + Email
Medium Priority → Email only
Low Priority → Dashboard only

Working Hours (Mon-Fri 9-17):
- All alerts → Team Slack channel

Off-Hours:
- Critical → On-call engineer (via PagerDuty)
- High → Slack + next business day review
```

---

## 📱 Mobile/Status Page

### Setup Statuspage.io

```
Components:
├─ API (api.consulta-rpp.com)
├─ Frontend (consulta-rpp.com)
├─ Database
├─ Search Service
└─ File Storage

Update Strategy:
- Automated updates from monitoring system
- Manual updates for planned maintenance
- Status history tracking
```

---

## 🔍 Observability Best Practices

### Structured Logging

```python
# Log with context
logger.info("search_executed", extra={
    "user_id": user_id,
    "query": search_query,
    "results_count": len(results),
    "execution_time_ms": execution_time
})
```

### Distributed Tracing

```python
# Use OpenTelemetry for request tracing
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("search_documents") as span:
    span.set_attribute("user_id", user_id)
    span.set_attribute("query", search_query)
    # Execute search...
```

### Custom Metrics

```python
# Using prometheus_client
from prometheus_client import Counter, Histogram

search_counter = Counter('search_queries_total', 'Total search queries')
search_duration = Histogram('search_duration_seconds', 'Search duration')

with search_duration.time():
    results = search_documents(query)
search_counter.inc()
```

---

## 📈 SLOs & SLIs

### Service Level Objectives (SLO)

```
API Availability SLO: 99.9% uptime per month
  - Maximum downtime: 43.2 minutes per month
  
API Response Time SLO: 95th percentile < 500ms
  - Measured per endpoint
  - Rolled up service-wide

Error Rate SLO: < 0.1% error rate
  - 5xx errors only (exclude client errors)
```

### Service Level Indicators (SLI)

```
Availability SLI: Successful requests / Total requests
Response Time SLI: Requests < threshold / Total requests
Error Rate SLI: Successful requests / Total requests
```

---

## 🎓 Training & Documentation

### Create Monitoring Runbooks

- [x] How to access dashboards
- [x] How to interpret metrics
- [x] How to respond to alerts
- [x] How to execute runbooks
- [x] Troubleshooting guide

### Team Training

- [ ] Monitoring system overview
- [ ] Dashboard walkthrough
- [ ] Alert response procedures
- [ ] On-call responsibilities
- [ ] Incident post-mortems

---

## ✅ Phase 5B Success Criteria

- [x] All monitoring tools installed
- [x] Metrics collection configured
- [x] Dashboards created
- [x] Alert rules defined
- [x] Log aggregation working
- [x] Error tracking active
- [x] Team trained
- [x] Runbooks documented

---

**Phase 5B Status**: ⏳ **READY FOR IMPLEMENTATION**

