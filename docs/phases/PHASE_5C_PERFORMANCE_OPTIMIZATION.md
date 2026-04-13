# Phase 5C - Performance Optimization

> **Status**: IN PROGRESS  
> **Date**: April 7, 2026  
> **Objective**: Optimize system performance to exceed targets

---

## 🎯 Current Performance vs. Targets

### Baseline (Phase 4)

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| API Response Time (p95) | 250ms | 200ms | -50ms |
| Page Load Time | 1.5s | 1.0s | -0.5s |
| First Contentful Paint | 0.8s | 0.5s | -0.3s |
| Bundle Size | 1.8MB | 1.5MB | -0.3MB |
| Cache Hit Ratio | N/A | 80%+ | New metric |
| Concurrent Users | 150+ | 300+ | +150 users |

---

## 🚀 Frontend Optimization

### 1. Code Splitting

**Current State:**
- Single bundle: 1.8MB

**Optimization:**
```javascript
// Use React lazy loading
const SearchPage = lazy(() => import('./pages/SearchPage'));
const DocumentsPage = lazy(() => import('./pages/DocumentsPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));

// Result: Reduce main bundle to ~500KB
// Load other chunks on demand
```

**Expected Impact:**
- Main chunk: 500KB (from 1.8MB)
- Search chunk: 200KB
- Documents chunk: 200KB
- Chat chunk: 250KB
- Initial load: -67% (1.5s → 0.5s)

### 2. Image Optimization

**Strategy:**
```
├─ Use WebP format with PNG fallback
├─ Lazy load below-the-fold images
├─ Use srcset for responsive sizes
├─ Compress all images (Imagemin)
└─ Use CDN for image delivery
```

**Commands:**
```bash
# Install imagemin
npm install imagemin imagemin-webp imagemin-pngquant

# Optimize images
npx imagemin assets/logos/* --out-dir=dist/assets/logos --plugin=webp --plugin=pngquant
```

### 3. CSS Optimization

```bash
# Install PurgeCSS
npm install @purgecss/webpack-plugin

# Result: Remove unused CSS
# Expected reduction: 30-40% of CSS size
```

### 4. React Performance

```javascript
// Use useMemo for expensive calculations
const MemoizedComponent = useMemo(() => (
  <ExpensiveComponent data={data} />
), [data]);

// Use useCallback for stable functions
const handleSearch = useCallback((query) => {
  searchDocuments(query);
}, []);

// Use React.memo for component memoization
export default React.memo(SearchResults);
```

### 5. Service Worker Caching

```javascript
// Register service worker for offline support
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(reg => console.log('SW registered'))
    .catch(err => console.log('SW registration failed'));
}

// Cache API responses
self.addEventListener('fetch', event => {
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          if (response) return response;
          return fetch(event.request)
            .then(response => {
              caches.open('api-cache').then(cache => {
                cache.put(event.request, response.clone());
              });
              return response;
            });
        })
    );
  }
});
```

---

## ⚙️ Backend Optimization

### 1. Database Query Optimization

**Current Issues:**
- N+1 queries in document listing
- Missing indexes
- Unoptimized joins

**Fixes:**

```sql
-- Add indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(chat_session_id);
CREATE INDEX idx_vectors_embedding ON vectors USING ivfflat(embedding);

-- Analyze query plans
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM documents WHERE user_id = $1;
```

**Expected Impact:**
- Query time: -50% average
- Database load: -30%
- P99 latency: < 100ms

### 2. Connection Pooling

```python
# backend/app/core/database.py
from sqlalchemy.pool import QueuePool

# Configure connection pool
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Number of connections to keep
    max_overflow=40,        # Maximum overflow connections
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True      # Test connections before using
)
```

**Expected Impact:**
- Connection exhaustion eliminated
- Connection reuse improved
- Query queueing reduced

### 3. Caching Strategy

```python
# Implement Redis caching
from functools import wraps
import redis
import json

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Try cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute and cache
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(ttl=600)
async def get_document_by_id(doc_id):
    return await Document.get(id=doc_id)
```

**Cache Strategy:**
- Search results: 1 hour TTL
- Document metadata: 24 hours TTL
- User preferences: 7 days TTL
- Session data: Session duration

**Expected Impact:**
- API response time: -40% for cached endpoints
- Database load: -50%
- Cache hit ratio: 80%+

### 4. Async Operations

```python
# Use Celery for long-running tasks
from celery import shared_task

@shared_task
def process_document(document_id):
    """Process document asynchronously"""
    doc = Document.get(id=document_id)
    # Long-running processing...
    doc.status = 'processed'
    doc.save()
```

**Expected Impact:**
- API response time: < 100ms (non-blocking)
- User experience: Better responsiveness

### 5. Request Compression

```python
# FastAPI middleware for gzip compression
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1024)
```

**Expected Impact:**
- Response size: -70% for JSON responses
- Network bandwidth: -70%
- Client-side parsing: Slightly slower due to decompression

---

## 🌐 Infrastructure Optimization

### 1. CDN Configuration

```
CDN Setup (AWS CloudFront / Cloudflare):
├─ Edge locations: Global distribution
├─ Static assets: images, CSS, JS, fonts
├─ Cache: 7 days for versioned assets, 1 day for index.html
├─ Compression: gzip + brotli
└─ TLS version: 1.2+
```

**Configuration:**

```yaml
# CloudFront Distribution
Origin:
  Domain: consulta-rpp.com
  Protocol: HTTPS
  TLS: 1.2+

Cache Behaviors:
  - Pattern: /static/* → Cache 7 days
  - Pattern: /*.js, /*.css → Cache 7 days (versioned)
  - Pattern: /api/* → Cache 0 (no-cache)
  - Pattern: /* → Cache 1 day (index.html)

Compression:
  - Enable gzip
  - Enable brotli
  - Min size: 1KB
```

**Expected Impact:**
- Time to First Byte: -70%
- Latency for global users: -50%
- Bandwidth cost: -30%

### 2. Load Balancing

```yaml
# Nginx Load Balancer Configuration
upstream backend {
  server backend1:3003 weight=1;
  server backend2:3003 weight=1;
  server backend3:3003 weight=1;
  
  keepalive 64;
}

server {
  listen 80;
  server_name api.consulta-rpp.com;
  
  # Rate limiting
  limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
  limit_req zone=api_limit burst=20 nodelay;
  
  # Proxy settings
  location / {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
  }
}
```

**Expected Impact:**
- Concurrent users: +100%
- High availability: Automatic failover

### 3. Auto-scaling

```yaml
# Kubernetes HPA Example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Expected Impact:**
- Automatic scaling: Based on CPU/Memory
- No manual intervention: Self-healing
- Cost optimization: Scale down during off-hours

---

## 📊 Expected Performance After Optimization

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| API Response (p95) | 250ms | 150ms | 40% ↓ |
| Page Load | 1.5s | 0.8s | 47% ↓ |
| First Contentful Paint | 0.8s | 0.4s | 50% ↓ |
| Bundle Size | 1.8MB | 0.8MB | 56% ↓ |
| Cache Hit Ratio | N/A | 85% | New |
| Concurrent Users | 150 | 500 | 233% ↑ |

---

## 🔄 Optimization Roadmap

**Week 1: Frontend**
- [ ] Code splitting implementation
- [ ] Image optimization
- [ ] CSS purging
- [ ] Service worker setup

**Week 2: Backend**
- [ ] Database optimization
- [ ] Connection pooling
- [ ] Caching implementation
- [ ] Async task processing

**Week 3: Infrastructure**
- [ ] CDN configuration
- [ ] Load balancing setup
- [ ] Auto-scaling policies
- [ ] Rate limiting

**Week 4: Validation & Tuning**
- [ ] Performance testing
- [ ] Bottleneck identification
- [ ] Fine-tuning
- [ ] Documentation

---

## ✅ Phase 5C Success Criteria

- [ ] All optimizations implemented
- [ ] Performance targets met
- [ ] Load testing passed (500 concurrent users)
- [ ] No regressions in functionality
- [ ] Documentation complete

---

**Phase 5C Status**: ⏳ **READY FOR IMPLEMENTATION**

