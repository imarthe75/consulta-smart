# 🔧 GUÍA TÉCNICA: MIGRACIÓN GROQ → OLLAMA (100% GRATIS)

**Versión**: 1.0  
**Audience**: Arquitectos de TI, DevOps  
**Complejidad**: Media  
**Tiempo de implementación**: 1 dia completo  

---

## 📐 ARQUITECTURA PROPUESTA

### Diagrama Actual (Groq Cloud)
```
┌─────────────────────────────────────┐
│        Frontend (React)              │
│     http://localhost:3000           │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│     API FastAPI (localhost:3001)    │
│   POST /api/v1/chat/query           │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│     Chat Service (FastAPI app)      │
│   - RAG Pipeline                    │
│   - KB Search                       │
└──────────────────┬──────────────────┘
                   │ (llamada API HTTP)
    ┌──────────────▼──────────────────┐
    │   GROQ CLOUD API                │
    │   api.groq.com:443              │
    │   (Costo: $100-350/mes)         │
    └─────────────────────────────────┘
```

### Diagrama Propuesto (Ollama Local)
```
┌─────────────────────────────────────┐
│        Frontend (React)              │
│     http://localhost:3000           │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│     API FastAPI (localhost:3001)    │
│   POST /api/v1/chat/query           │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│     Chat Service (FastAPI app)      │
│   - RAG Pipeline                    │
│   - KB Search                       │
└──────────────────┬──────────────────┘
                   │ (llamada HTTP local)
    ┌──────────────▼──────────────────┐
    │   OLLAMA LOCAL                  │
    │   localhost:11434               │
    │   (Costo: $0/mes - solo electr) │
    └──────────────────────────────────┘
            ↓ (modelo en memoria)
    ┌──────────────────────────────────┐
    │  Llama 2 7B (4GB modelo)         │
    │  O Mistral 7B o Phi 2.7B        │
    └──────────────────────────────────┘
```

---

## 💻 COMPARATIVA DE MODELOS

### Opción 1: Llama 2 7B Chat (RECOMENDADO)
```
Proveedor:          Meta (Facebook)
Licencia:           MIT + Community
Tamaño:             4 GB (descargado)
RAM requerida:      8 GB (durante ejecución)
VRAM requerida:     GPU opcional
Velocidad (CPU):    20-30 tokens/seg
Velocidad (GPU):    200+ tokens/seg
Calidad:            8/10 (excelente para chat)
Soporte español:    Bueno (fine-tuned)
Ejecución:          ollama pull llama2
API:                Compatible OpenAI ✅

PROS:
  ✅ Bien entrenado para tareas específicas
  ✅ Excelente para instrucciones
  ✅ Comunidad muy activa
  ✅ Fácil deployment

CONTRAS:
  ❌ Puede ser impreciso en números
  ❌ Un poco lento en CPU pura
```

---

### Opción 2: Mistral 7B Chat
```
Proveedor:          Mistral AI
Licencia:           Apache 2.0
Tamaño:             3.5 GB
RAM requerida:      8 GB
VRAM requerida:     GPU opcional (mejor)
Velocidad (CPU):    25-35 tokens/seg
Velocidad (GPU):    300+ tokens/seg
Calidad:            8.5/10 (muy bueno)
Soporte español:    Excelente ✅
Ejecución:          ollama pull mistral
API:                Compatible OpenAI ✅

PROS:
  ✅ Mejor para español que Llama
  ✅ Más rápido que Llama 2
  ✅ Mejor precisión en números
  ✅ Menor consumo de recursos

CONTRAS:
  ❌ Comunidad más pequeña
  ❌ Menos ejemplos en web
```

---

### Opción 3: Phi 2.7B (Si hardware es muy limitado)
```
Proveedor:          Microsoft
Licencia:           MIT
Tamaño:             1.6 GB
RAM requerida:      4 GB
VRAM requerida:     GPU opcional
Velocidad (CPU):    50+ tokens/seg
Velocidad (GPU):    500+ tokens/seg
Calidad:            7.5/10 (bueno para su tamaño)
Soporte español:    Regular
Ejecución:          ollama pull phi
API:                Compatible OpenAI ✅

PROS:
  ✅ Muy rápido hasta en CPU vieja
  ✅ Usa muy poca RAM
  ✅ Mejor para hardware limitado

CONTRAS:
  ❌ Menos preciso que Llama/Mistral
  ❌ Español no tan bueno
```

---

## 🛠️ INSTALACIÓN PASO A PASO

### PASO 1: Instalar Ollama (15 minutos)

#### En Linux (Ubuntu/Debian)
```bash
# Descargar e instalar
curl https://ollama.ai/install.sh | sh

# Verificar instalación
ollama --version

# Iniciar servicio
ollama serve

# En otra terminal, verificar que escucha en puerto 11434
curl http://localhost:11434
```

#### En macOS
```bash
# Con Homebrew
brew install ollama

# O descargar directamente de https://ollama.ai/download

# Iniciar
ollama serve
```

#### En Docker (RECOMENDADO para producción)
```bash
# Crear Dockerfile
cat > Dockerfile.ollama <<EOF
FROM ollama/ollama:latest

# Pre-descargar modelo (opcional, para imagen más pequeña al init)
RUN ollama pull llama2
EOF

# Build
docker build -f Dockerfile.ollama -t ollama-llama2 .

# Run
docker run -d \
  --name ollama \
  -p 11434:11434 \
  --gpus all \  # Si tiene GPU (opcional)
  -v ollama_data:/root/.ollama \
  ollama-llama2

# Verificar
curl http://localhost:11434
```

---

### PASO 2: Descargar Modelo (10-20 minutos)

```bash
# Opción A: Llama 2 7B (RECOMENDADO)
ollama pull llama2

# Opción B: Mistral 7B
ollama pull mistral

# Opción C: Phi 2.7B (si RAM limitada)
ollama pull phi

# Verificar que está disponible
ollama list
# Debería mostrar:
# NAME                    ID              SIZE      MODIFIED
# llama2:latest           44..........    4.0 GB    2 minutes ago
```

---

### PASO 3: Test Manual (5 minutos)

```bash
# Test 1: Via CLI
ollama run llama2

# Ingresa prompt:
# >>> ¿Cuáles son los requisitos para registrar una propiedad?
# Sale respuesta del modelo

# Test 2: Via API HTTP
curl http://localhost:11434/api/generate \
  -d '{
    "model": "llama2",
    "prompt": "¿Cuánto cuesta registrar una propiedad en Quintana Roo?",
    "stream": false
  }' | python3 -m json.tool

# Debería retornar:
# {
#   "model": "llama2",
#   "created_at": "...",
#   "response": "El costo de registrar una propiedad...",
#   "done": true,
#   "total_duration": 2500000000,
#   "load_duration": 100000000,
#   "prompt_eval_count": 15,
#   "eval_count": 128,
#   "eval_duration": 2300000000
# }

# Test 3: Via Python
python3 << 'PYEOF'
import requests
import json

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama2",
        "prompt": "Hola",
        "stream": False
    },
    timeout=60
)
result = response.json()
print(result["response"])
PYEOF
```

---

## 🔌 INTEGRACIÓN CON FASTAPI

### CAMBIO 1: Actualizar `llm_service.py`

**Archivo**: `/backend/app/infrastructure/external/llm_service.py`

```python
# ANTES (Groq Cloud)
class GroqProvider(LLMProvider):
    def __init__(self):
        from groq import Groq
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
    
    async def chat(self, messages, ...):
        response = self.client.chat.completions.create(...)
        return response.choices[0].message.content

# DESPUÉS (Ollama Local)
class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        import requests
        self.base_url = base_url
        self.model = "llama2"  # o mistral, phi, etc
        self.client = requests.Session()
        # Verificar que Ollama está disponible
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            logger.info(f"✅ Ollama conectado: {response.json()}")
        except Exception as e:
            logger.error(f"❌ Ollama no disponible en {self.base_url}: {e}")
    
    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """Chat con Ollama local (API compatible con OpenAI)"""
        try:
            # Convertir formato OpenAI a prompt format para Ollama
            system_prompt = kwargs.get('system', '')
            
            # Construir conversación
            prompt = ""
            if system_prompt:
                prompt += f"<s>[INST] {system_prompt}\n\n"
            
            for msg in messages:
                if msg['role'] == 'user':
                    prompt += f"{msg['content']} [/INST] "
                else:
                    prompt += f"{msg['content']} </s><s>[INST] "
            
            # Llamar a Ollama (síncrono NO ASYNC en esta versión)
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": settings.TOP_P,
                },
                timeout=60
            )
            
            result = response.json()
            return result.get("response", "Sin respuesta del modelo")
            
        except Exception as e:
            logger.error(f"Error en Ollama: {e}")
            raise
```

---

### CAMBIO 2: Actualizar `smart_llm_router.py`

```python
# ANTES
from app.infrastructure.external.llm_service import GroqProvider, GeminiProvider

class SmartLLMRouter:
    def __init__(self):
        self.providers = {
            "groq": GroqProvider(),   # Cloud
            "gemini": GeminiProvider(), # Cloud
        }
        self.priority_order = ["groq"]

# DESPUÉS
from app.infrastructure.external.llm_service import OllamaProvider
from app.infrastructure.external.local_embedding_service import LocalEmbeddingService

class SmartLLMRouter:
    def __init__(self):
        # Solo Ollama local - sin dependencias cloud
        self.providers = {
            "ollama": OllamaProvider(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            ),
        }
        self.priority_order = ["ollama"]
        logger.info("✅ SmartLLMRouter: Usando Ollama local (100% gratis)")
```

---

### CAMBIO 3: Actualizar `.env`

```bash
# ANTES
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_*****
GROQ_MODEL=llama-3.3-70b-versatile
GOOGLE_API_KEY=AIza*****

# DESPUÉS
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
# (Sin API keys necesarias)
```

---

## 📦 DEPLOYMENT CON DOCKER COMPOSE

### Opción 1: Compartido con idp-smart

```yaml
# docker-compose.yml - Agregar servicio Ollama

services:
  ollama:
    image: ollama/ollama:latest
    container_name: consulta-rpp-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    # Descargar modelo al iniciar (20 min la primera vez)
    command: bash -c "ollama pull llama2 && ollama serve"
    deploy:
      resources:
        limits:
          memory: 8G       # Limite RAM
        reservations:
          memory: 6G       # Garantizar
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - consultarpp-network

  backend:
    # ...resto de config...
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      ollama:
        condition: service_healthy

volumes:
  ollama-data:

networks:
  consultarpp-network:
```

---

### Opción 2: Dedicado (servidor separado)

```yaml
# docker-compose.ollama.yml - En servidor dedicado

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama-server
    ports:
      - "0.0.0.0:11434:11434"  # Exponer al network interno
    volumes:
      - /mnt/storage/ollama:/root/.ollama  # Storage local
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
      - OLLAMA_NUM_PARALLEL=4  # Soportar múltiples requests
    entrypoint: bash -c "ollama pull llama2 && ollama serve"
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 12G
    restart: always
    # En FastAPI, conectar a: http://172.20.0.2:11434 (IP del servidor)
```

---

## ⚡ OPTIMIZACIONES DE PERFORMANCE

### Optimización 1: Quantización de Modelo

Reducir tamaño del modelo a 4-bit sin perder mucha calidad:

```bash
# Crear versión cuantizada (4-bit)
ollama create llama2-4bit -f - <<EOF
FROM llama2
PARAMETER quantize q4
EOF

# Usar en fastapi:
OLLAMA_MODEL=llama2-4bit

# Beneficios:
# - 50% menos RAM (8GB → 4GB)
# - Velocidad similar
# - Calidad: 95% de original
```

---

### Optimización 2: Caché de Respuestas

```python
# En chat_service.py
import hashlib
from app.infrastructure.knowledge_base import REDIS

class ChatService:
    async def process_query(self, query, ...):
        # Generar hash de query normalizada
        cache_key = f"chat:{hashlib.md5(query.lower().encode()).hexdigest()}"
        
        # Buscar en caché Redis
        cached = await REDIS.get(cache_key)
        if cached:
            logger.info(f"✅ Respuesta servida desde caché")
            return json.loads(cached)
        
        # Si no está, generar y cachear
        result = await self._generate_response(query)
        await REDIS.setex(cache_key, 86400, json.dumps(result))  # 24 horas
        return result
```

---

### Optimización 3: Batch Processing

```python
# Procesar múltiples queries en paralelo
async def process_queries_batch(queries: List[str]):
    """Procesar queries concurrentes"""
    tasks = [
        process_query(q) 
        for q in queries
    ]
    return await asyncio.gather(*tasks)

# Ollama puede manejar:
# - 4-6 requests simultáneos en CPU 4-core
# - 20-50+ con GPU
```

---

## 🚦 MONITOREO Y OBSERVABILIDAD

### Métricas a Monitorear

```yaml
# prometheus.yml - Agregar endpoint
scrape_configs:
  - job_name: "ollama"
    metrics_path: "/api/metrics"  # Si Ollama expone métricas
    static_configs:
      - targets: ["localhost:11434"]

# Métricas custom en FastAPI
@app.get("/metrics")
async def metrics():
    return {
        "ollama_status": "ok" if ollama_available else "down",
        "model_loaded": "llama2",
        "avg_latency_ms": 2500,
        "requests_total": 12345,
        "requests_error": 5,
        "memory_used_mb": 4000,
    }
```

---

### Alertas Recomendadas

```yaml
# alertmanager.yml
groups:
  - name: ollama
    rules:
      - alert: OllamaDown
        expr: up{job="ollama"} == 0
        for: 1m
        annotations:
          summary: "Ollama service is down"
      
      - alert: HighLatency
        expr: ollama_latency_ms > 10000
        for: 5m
        annotations:
          summary: "Ollama latency > 10 seconds"
      
      - alert: HighErrorRate
        expr: rate(ollama_errors[5m]) > 0.05
        for: 2m
        annotations:
          summary: "Ollama error rate > 5%"
```

---

## 📊 BENCHMARKS ESPERADOS

### Hardware: Intel Xeon 4-core, 16GB RAM

```
┌────────────────────────────────────────────┐
│  MODELO: Llama 2 7B (CPU only)             │
├────────────────────────────────────────────┤
│ Tiempo respuesta (p50):      2.1 segundos  │
│ Tiempo respuesta (p95):      4.3 segundos  │
│ Tiempo respuesta (p99):      6.2 segundos  │
│ Tokens/segundo:              25 tok/seg    │
│ Usuarios simultáneos:        15 (máx)      │
│ Queries/minuto:              12            │
│ RAM usado:                   ~6 GB         │
│ CPU usado:                   95-100%       │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│  MODELO: Mistral 7B (CPU only)             │
├────────────────────────────────────────────┤
│ Tiempo respuesta (p50):      1.8 segundos  │
│ Tiempo respuesta (p95):      3.5 segundos  │
│ Tiempo respuesta (p99):      5.1 segundos  │
│ Tokens/segundo:              30 tok/seg    │
│ Usuarios simultáneos:        20 (máx) ✅   │
│ Queries/minuto:              15            │
│ RAM usado:                   ~5 GB         │
│ CPU usado:                   90-100%       │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│  CON GPU NVIDIA A100 40GB                  │
├────────────────────────────────────────────┤
│ Tiempo respuesta (p50):      0.3 segundos  │
│ Tiempo respuesta (p95):      0.8 segundos  │
│ Tokens/segundo:              500+ tok/seg  │
│ Usuarios simultáneos:        100+          │
│ Queries/minuto:              300+          │
│ VRAM usado:                  ~8 GB         │
└────────────────────────────────────────────┘
```

---

## ✅ CHECKLIST DE MIGRACIÓN

### Pre-migración
- [ ] Backup de base de datos RPP
- [ ] Snapshot de servidor actual
- [ ] Comunicado a usuarios (SLA puede cambiar)
- [ ] Plantel de soporte informado

### Instalación
- [ ] Ollama instalado en servidor
- [ ] Modelo descargado y verificado
- [ ] API responde en puerto 11434
- [ ] Caché Redis limpio

### Integración código
- [ ] OllamaProvider implementado
- [ ] SmartLLMRouter actualizado
- [ ] .env actualizado
- [ ] Tests unitarios pasando
- [ ] Tests E2E pasando

### Validación
- [ ] 100 queries de prueba (comparar con Groq)
- [ ] Latencia dentro de parámetros
- [ ] Hallucinations verificados
- [ ] Spanish language quality OK
- [ ] Load testing (50 usuarios simultáneos)

### Deployment
- [ ] Docker image construida
- [ ] docker-compose.yml validado
- [ ] Healthchecks funcionando
- [ ] Logs configurados
- [ ] Alertas activas

### Post-deployment
- [ ] Monitoreo 24/7
- [ ] Usuarios informados de cambios
- [ ] Documentación actualizada
- [ ] SLA definido y comunicado
- [ ] Plan B (rollback) preparado

---

## 🆘 TROUBLESHOOTING

### Problema 1: "Connection refused" en ollama:11434

```bash
# Verificar si Ollama está corriendo
ps aux | grep ollama

# Si no:
ollama serve

# O en Docker:
docker start consulta-rpp-ollama

# Si sigue fallando:
docker logs consulta-rpp-ollama
```

---

### Problema 2: Latencia muy alta (> 10s)

```bash
# Causa común: Modelo siendo descargado
docker exec consulta-rpp-ollama ollama list

# Si modelo no está:
docker exec consulta-rpp-ollama ollama pull llama2

# Verificar recursos:
docker stats consulta-rpp-ollama

# Si CPU al 100%:
- Reducir conexiones simultáneas
- Cambiar a modelo más pequeño (phi)
- Agregar GPU si es posible
```

---

### Problema 3: Out of Memory (OOM)

```bash
# Aumentar límite de swap
sudo sysctl -w vm.swappiness=50

# O cambiar a modelo más pequeño
ollama pull phi  # 1.6GB vs 4GB

# Verificar cuánta RAM usa:
docker stats --no-stream consulta-rpp-ollama
```

---

## 📈 PLAN DE ESCALABILIDAD SIN COSTO

### Si usuarios crecen a 100

```
Opción 1: Agregar GPU
  - NVIDIA T4 (~$200 usado)
  - Speedup 10x
  - Soporta 100+ usuarios

Opción 2: Agregar servidores Ollama
  - Load balancer (Nginx gratis)
  - 3x servidores con Ollama
  - Distribución automática
  - Failover automático
```

---

## 🎓 CONCLUSIÓN

**Migración de Groq a Ollama es:**
- ✅ Técnicamente viable (1-2 días)
- ✅ Financieramente atractiva ($0 → $350 anual)
- ✅ Operacionalmente simple (Docker `)
- ✅ Escalable sin costo (agregar hardware local)
- ✅ Independencia del estado (soberanía TI)

**Próximos pasos:**
1. Aprobación de arquitectura
2. Asignación de servidor
3. Implementación (1 semana)
4. Migración en vivo (1 día)
5. Monitoreo post-deploy (14 días)

---

**Documento: GUÍA_TECH_OLLAMA.md**  
**Versión**: 1.0  
**Fecha**: Abril 2026  
