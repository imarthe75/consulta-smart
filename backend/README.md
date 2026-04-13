# 🚀 Backend - ConsultaRPP

Backend FastAPI para ConsultaRPP con integración de caché híbrida que reduce costos de LLM en 60-70%.

## 📋 Tabla de Contenidos

- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecutar](#ejecutar)
- [Caché Híbrida](#caché-híbrida)
- [API Endpoints](#api-endpoints)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Instalación

### 1. Requisitos Previos

```bash
# Python 3.10+
python --version

# Redis (local o Docker)
docker run -d -p 6379:6379 redis:7-alpine

# PostgreSQL (para base de datos)
# Ver docker-compose.yml para detalles
```

### 2. Instalar Dependencias

```bash
cd backend

# Crear virtualenv (recomendado)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Instalar paquetes
pip install -r requirements.txt
```

### 3. Verificar Instalación

```bash
# Que Redis está corriendo
redis-cli ping
# Debe responder: PONG

# Que dependencias están presentes
pip list | grep -E "redis|sentence-transformers|fastapi"
```

---

## ⚙️ Configuración

### Variables de Entorno

Crea archivo `.env` en `/backend`:

```bash
# App
APP_NAME=ConsultaRPP
APP_VERSION=1.0.0
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Base de Datos
DB_HOST=postgres
DB_PORT=5432
DB_USER=consultarpp_user
DB_PASSWORD=your_password
DB_NAME=consultarpp

# Redis / Caché Híbrida
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL_SECONDS=86400  # 24 horas

# LLM
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile

# Auth
JWT_SECRET=your_secret_key
SECRET_KEY=your_app_secret

# CORS
CORS_ORIGINS=http://localhost:3000
```

### Con Docker Compose

```bash
# Ver docker-compose.yml para montaje completo
docker-compose up -d redis postgres

# Verificar servicios
docker-compose ps
```

---

## 🚀 Ejecutar

### Opción 1: Desarrollo (con auto-reload)

```bash
cd backend

# Iniciar servidor con hot reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Logs esperados:
# ✅ Base de datos inicializada
# ✅ Caché Híbrida inicializada (Redis + embeddings)
# SmartLLMRouter inicializado (Groq → Gemini fallback)
```

### Opción 2: Producción

```bash
# Sin reload, con workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Validar que está corriendo

```bash
# Test health endpoint
curl http://localhost:8000/health

# Respuesta esperada:
# {"status": "ok", "service": "backend"}
```

---

## 🏗️ Caché Híbrida

### ¿Qué es?

Sistema de caché que reduce costos de Groq en **60-70%**:

- **30% queries exactas**: Redis → $0 costo
- **50% queries similares**: Embeddings + LLM minimal → ~$0.0001
- **20% queries nuevas**: LLM completo → $0.0005

**Resultado:** $350/mes → $125/mes

### Arquitectura

```
Request Query
    ↓
┌─────────────────────────┐
│  Caché Exacta (Redis)   │  ← 30% queries ($0)
│  MD5 hash normalization │
└────────────┬────────────┘
             ↓
        ¿HIT?
       / \
     YES  NO
     │     │
    $0    │
         ↓
  ┌──────────────────────────┐
  │ Búsqueda Similar          │  ← 50% queries (~$0.0001)
  │ (Embeddings 384-dim)      │
  │ Cosine similarity > 0.75  │
  └─────────┬────────────────┘
            ↓
        ¿HIT?
       / \
     YES  NO
     │     │
   $0    │
        ↓
   ┌──────────────────────────┐
   │ LLM Completo (Groq)       │  ← 20% queries ($0.0005)
   │ Guardar resultado en      │
   │ caché para futuro.        │
   └──────────────────────────┘
           ↓
      Response
```

### Integración

Los endpoints de chat automáticamente:

1. **Verifican caché** antes de llamar a LLM
2. **Devuelven* respuestas cacheadas cuando hay hits
3. **Almacenan** nuevas respuestasautomáticamente
4. **Incluyen metadata** sobre caché en respuesta

### Configuración

En `app/infrastructure/cache_layer.py`:

```python
# Thresholds
EXACT_MATCH_THRESHOLD = 0.85        # Para exactas
SIMILARITY_THRESHOLD = 0.75          # Para similares
REDIS_TTL = 86400                    # 24 horas

# Modelo de embeddings
MODEL = "all-MiniLM-L6-v2"           # 384-dim
DIMENSION = 384
```

### Monitoring

Cada respuesta incluye:

```json
{
  "response": "El costo es $500 MXN",
  "from_cache": "exact_or_similar",
  "cache_info": {
    "similarity_score": 1.0,
    "query_length": 42,
    "response_length": 150
  }
}
```

### Estadísticas

Ver estadísticas en tiempo real:

```bash
# Si endpoint existe (agregar si no)
curl http://localhost:8000/api/v1/chat/cache-stats \
  -H "Authorization: Bearer YOUR_TOKEN"

# Respuesta:
# {
#   "cache_hits": 450,
#   "cache_misses": 550,
#   "hit_rate": 45.0,
#   "estimated_cost_savings": 225.00
# }
```

---

## 🔌 API Endpoints

### Chat

```bash
# Crear sesión
POST /api/v1/chat/sessions
{
  "title": "Mi consulta sobre escritura"
}

# Obtener sesiones del usuario
GET /api/v1/chat/sessions

# Hacer query (con caché)
POST /api/v1/chat/query
{
  "message": "¿Cuál es el costo de una escritura?",
  "session_id": "uuid",
  "conversation_history": []
}

# Healthcheck
GET /api/v1/chat/health
```

### Autenticación

```bash
# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# Respuesta: JWT token en Authorization header
Authorization: Bearer eyJhbGc...
```

---

## 🧪 Tests

### Ejecutar Tests

```bash
cd backend

# Tests unitarios (caché)
pytest tests/test_cache_layer.py -v

# Tests integración
pytest tests/test_integration_cache.py -v

# Todos los tests
pytest tests/ -v

# Con coverage
pytest --cov=app tests/
```

### Tests Especiales

```bash
# Test slowness - Benchmark
pytest tests/test_performance.py -v -s

# Test tagged as "cache"
pytest -m cache

# Run specific test
pytest tests/test_cache_layer.py::TestHybridCacheLayer::test_exact_match_redis_hit -v
```

---

## 📊 Benchmarking

### Verificar Performance

```bash
# Benchmark básico (100 queries)
python scripts/benchmark_cache.py --queries 100

# Benchmark completo (1000 queries)
python scripts/benchmark_cache.py --queries 1000 --output results.json

# Resultados esperados:
# - Latencia: 60% mejora (450ms → 180ms)
# - Tokens: 60% reducción
# - Costo: 60% ahorros
# - Hit rate: 40-60%
```

### Verificar Escalabilidad

```bash
# Load test: 100 usuarios
python scripts/load_test_cache.py --users 100 --duration 60

# Load test: 500 usuarios
python scripts/load_test_cache.py --users 500 --duration 120 --output load_test_500.json

# Criterios:
# ✅ P99 < 1000ms
# ✅ Hit rate > 40%
# ✅ Error rate < 1%
# ✅ Throughput > 10 Q/s
```

---

## 📂 Estructura

```
backend/
├── app/
│   ├── infrastructure/
│   │   ├── cache_layer.py           ⭐ Motor de caché híbrida
│   │   ├── knowledge_base.py        (RAG + pgvector)
│   │   └── ...
│   ├── application/services/
│   │   ├── chat_service.py          (con caché integrada)
│   │   └── ...
│   ├── routes/
│   │   ├── chat.py                  (endpoints con caché)
│   │   ├── auth.py
│   │   └── ...
│   ├── core/
│   │   ├── config.py                (REDIS_HOST, REDIS_PORT, etc)
│   │   ├── database.py
│   │   └── logger.py
│   └── ...
├── tests/
│   ├── test_cache_layer.py          (20+ tests)
│   ├── test_integration_cache.py    (10+ tests)
│   ├── conftest.py                  (fixtures compartidas)
│   └── ...
├── scripts/
│   ├── benchmark_cache.py           (performance analysis)
│   ├── load_test_cache.py           (scalability test)
│   └── ...
├── CACHE_IMPLEMENTATION_GUIDE.md    (guía completa)
├── IMPLEMENTATION_SUMMARY.md        (resumen técnico)
├── main.py                          (entry point con lifespan)
├── requirements.txt
├── pytest.ini
└── README.md                        (este archivo)
```

---

## 🔍 Troubleshooting

### "Redis Connection Error"

```bash
# Verificar Redis está corriendo
redis-cli ping

# Si no responde, iniciar Redis
docker run -d -p 6379:6379 redis:7-alpine
```

### "Failed to load SentenceTransformer"

```bash
# Descargar modelo manualmente
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# O instalar versión específica
pip install sentence-transformers==3.0.1
```

### "Cache hit rate too low"

Posibles causas:
1. Queries no se repiten suficiente
2. TTL muy bajo (aumentar en config)
3. Thresholds de similitud muy altos

Soluciones:
```python
# En cache_layer.py
EXACT_MATCH_THRESHOLD = 0.80    # Bajar de 0.85
SIMILARITY_THRESHOLD = 0.70      # Bajar de 0.75
REDIS_TTL = 172800               # 48 horas
```

### "High latency p99 > 1000ms"

```bash
# Verificar latencia Redis
redis-cli --latency

# Aumentar recursos
# - Redis memory: 512MB → 2GB
# - CPU cores: más workers en uvicorn
# Reiniciar servidor
```

### "Port 8000 already in use"

```bash
# Cambiar puerto
python -m uvicorn main:app --port 8001

# O matar proceso existente
lsof -ti:8000 | xargs kill -9
```

---

## 📖 Documentación Relacionada

- [CACHE_IMPLEMENTATION_GUIDE.md](CACHE_IMPLEMENTATION_GUIDE.md) - Guía paso-a-paso
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Arquitectura técnica
- [../INDICE_IMPLEMENTACION.md](../INDICE_IMPLEMENTACION.md) - Índice y tabla

---

## ✨ Contribuir

Antes de pushear code:

```bash
# 1. Run tests
pytest tests/ -v

# 2. Check coverage
pytest --cov=app tests/

# 3. Format code
black app tests

# 4. Lint
flake8 app tests --max-line-length=100
```

---

## 📞 Soporte

### Logs útiles

```bash
# Ver logs en tiempo real
tail -f nohup.out

# Filtrar por caché
grep -i cache nohup.out

# Filtrar por errores
grep -i error nohup.out | head -20
```

### Contacto

- Docs: Ver [CACHE_IMPLEMENTATION_GUIDE.md](CACHE_IMPLEMENTATION_GUIDE.md)
- Issues: Crear task en ticket system
- Debugging: Ver sección Troubleshooting

---

**Última actualización:** 2026-04-08  
**Version:** 1.0.0  
**Status:** ✅ Producción
