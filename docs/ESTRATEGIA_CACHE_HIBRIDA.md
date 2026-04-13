# 🔄 ESTRATEGIA DE CACHÉ HÍBRIDA: Groq + Redis + Ollama

## Introducción

Este documento detalla la arquitectura de **caché híbrida** que permite:
- ✅ Reducir 60% del costo Groq ($350 → $125/mes)
- ✅ Mantener escalabilidad ilimitada de usuarios
- ✅ Mejorar latencia con respuestas de caché local
- ✅ Fallback automático sin interrupciones

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                      USUARIO FINAL                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASTAPI + CACHE LAYER (Nuevo)                      │
│                                                                 │
│  1. Recibe pregunta                                             │
│  2. Genera hash de embedding                                    │
│  3. Busca en Redis                                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
        ┌──────────────┐      ┌──────────────┐
        │ REDIS CACHE  │      │ OLLAMA LOCAL │
        │ (24h TTL)    │      │ (fallback)   │
        │ $0/mes       │      │ $0/mes       │
        └──────┬───────┘      └──────┬───────┘
               │ HIT (40%)           │ HIT (40%)
               │                     │
        ┌──────▼─────────────────────▼──────┐
        │  RESPUESTA RÁPIDA (< 200ms)       │
        │  Sin costo adicional               │
        └──────────────────────────────────┘

        ┌────────────────────────────────────┐
        │  Cache MISS (20%)                  │
        │  Consulta nueva/compleja           │
        └──────┬───────────────────────────┘
               ▼
        ┌────────────────────────────────────┐
        │  GROQ CLOUD ($0.0005/consulta)     │
        │  Procesa consulta nueva            │
        │  Retorna en ~0.5s                  │
        └──────┬───────────────────────────┘
               ▼
        ┌────────────────────────────────────┐
        │  Guardar en Redis (24h)            │
        │  Próximas consultas iguales = $0   │
        └────────────────────────────────────┘
```

---

## Flujo Detallado

### 1. PRIMERA CONSULTA (Nuevo usuario)

```
Usuario: "¿Qué es la escritura pública?"

Paso 1: Hash de consulta
  - Normalizar texto
  - Generar embedding (Sentence Transformers)
  - Crear fingerprint único
  - Hash: "escritura_publica_abc123"

Paso 2: Buscar en Redis
  - Redis.get("escritura_publica_abc123")
  - Resultado: NULL (no existe)
  - Seguir a Paso 3

Paso 3: Buscar en Ollama caché
  - Ollama.search(embedding, threshold=0.85)
  - Resultado: NO coincidencia cercana
  - Seguir a Paso 4

Paso 4: Consultar Groq
  - Enviar pregunta a Groq
  - Groq procesa (0.5 segundos)
  - Costo: $0.0005
  - Respuesta: "Escritura pública es el registro..."

Paso 5: Guardar en caché
  - Redis.set(hash, respuesta, expire_in=86400)  # 24 horas
  - Ollama.embed(respuesta)  # Para fallback

Paso 6: Retornar usuario
  - Tiempo total: 0.5 segundos
  - Costo: $0.0005 para Groq
```

### 2. SEGUNDA CONSULTA IDÉNTICA (Otro usuario)

```
Usuario 2: "¿Qué es la escritura pública?"

Paso 1: Hash de consulta
  - Hash: "escritura_publica_abc123" (igual que usuario 1)

Paso 2: Buscar en Redis
  - Redis.get("escritura_publica_abc123")
  - Resultado: ENCONTRADO ✅
  - Respuesta guardada desde usuario 1
  - Saltar directo a Retornar

Paso 6: Retornar usuario
  - Tiempo total: < 50ms
  - Costo: $0 (caché hit)
  - RED DE AHORRO: $0.0005 por consulta
```

### 3. CONSULTA SIMILAR (Variación)

```
Usuario 3: "¿Cómo registro una escritura pública?"

Paso 1: Hash de consulta
  - Hash: "como_registro_escritura_publica_def456"
  - Hash DIFERENTE a primero

Paso 2: Buscar en Redis
  - Redis.get("como_registro_escritura_publica_def456")
  - Resultado: NULL (no existe exacto)

Paso 3: Buscar en Ollama caché
  - Ollama.search(embedding, threshold=0.75)
  - Encontrar embedding similar: "escritura_publica_abc123"
  - Similitud: 0.87 > 0.75 ✅
  - Respuesta similar existe

Paso 4: Opción A - Usar Ollama directamente
  - Si similitud > 0.85: usar respuesta de Ollama
  - Tiempo: < 100ms
  - Costo: $0 ✅

  OPCIÓN B - Refinar con Groq
  - Si similitud 0.75-0.85: contexto promedio
  - Enviar a Groq con contexto de Ollama
  - Groq refina la respuesta (cheaper prompt)
  - Costo: $0.0002 (50% menos)
```

---

## Parámetros de Configuración

### Redis Configuration
```yaml
# Cache Settings
REDIS_HOST: localhost
REDIS_PORT: 6379
CACHE_TTL: 86400  # 24 horas

# Strategies
CACHE_STRATEGY: "hybrid"  # Redis + Ollama
CACHE_HIT_THRESHOLD: 0.85  # Similitud mínima
FALLBACK_TO_GROQ: true  # Si no encuentra en caché
```

### Ollama Configuration
```yaml
# Embedding Model
OLLAMA_MODEL: "nomic-embed-text"  # 768-dim embeddings
OLLAMA_SIMILARITY_MODEL: "llama2"  # Para respuestas similares

# Performance
EMBEDDING_BATCH_SIZE: 32
SIMILARITY_THRESHOLD: 0.75  # Respuestas "cercanas"
STRICT_THRESHOLD: 0.85     # Respuestas exactas
```

### Groq Configuration
```yaml
# Plan Optimization
GROQ_MODEL: "mixtral-8x7b-32768"
GROQ_TIER: "optimized"  # Nuevo tier (vs complete)
GROQ_MAX_TOKENS: 1024
GROQ_TEMPERATURE: 0.3

# Cost Control
GROQ_CACHE_BEFORE_CALL: true  # Siempre revisar caché primero
GROQ_ENABLE_PROMPT_CACHING: true  # Groq caches también
GROQ_BUDGET_ALERT: 120  # USD/mes
```

---

## Estimación de Ahorros

### Patrón de Consultas Típico (1,000 consultas/día)

```
Categoría de Consultas:

30% - EXACTAMENTE IGUALES (Redis hit):
  • Preguntas: "¿Qué es la escritura pública?" (repetidas)
  • Usuarios: Múltiples buscando misma cosa
  • Costo: $0 (Redis + Ollama, sin Groq)
  • Ejemplo: 300 consultas → $0 costo
  • Latencia: < 50ms

50% - SIMILARES/VARIACIONES (Ollama + refinación Groq):
  • Preguntas: "¿Cómo registro?" vs "¿Dónde registro?"
  • Usuarios: Variaciones sobre tema común
  • Costo: $0.0001 (pequeño refinamiento Groq)
  • Ejemplo: 500 consultas → $0.05 costo
  • Latencia: 100-300ms

20% - COMPLETAMENTE NUEVAS (Groq completo):
  • Preguntas: Consultas complejas/específicas
  • Usuarios: Casos edge, consultas raras
  • Costo: $0.0005 (Groq normal)
  • Ejemplo: 200 consultas → $0.10 costo
  • Latencia: 500ms
```

### Cálculo Mensual

```
Consultas/día:        1,000
Consultas/mes:        30,000
Consultas/año:        360,000

ACTUAL (Groq $350/mes):
  • Trataba ~120,000 consultas/mes
  • Costo por consulta: $350/120,000 = $0.003
  • Total: $0.003 × 30,000 = $90

CON CACHÉ HÍBRIDA:
  • Redis hit (30%):        $0.00 × 9,000 = $0
  • Ollama+Groq (50%):      $0.0001 × 15,000 = $1.50
  • Groq completo (20%):    $0.0005 × 6,000 = $3.00
  • Total mes: $4.50

AHORRO:
  • Antes: $90/mes
  • Después: $4.50/mes
  • Reducción: 95% ✅
  
  Dato: Groq plan optimizado ronda $125/mes
  Nuestro caché la deja en ~$25/mes
```

---

## Implementación: Código FastAPI

### Cache Layer Architecture

```python
from fastapi import FastAPI
from redis import Redis
import ollama
from groq import Groq
import hashlib
from sentence_transformers import SentenceTransformer

app = FastAPI()

# Initialize clients
redis_client = Redis(host='localhost', port=6379, decode_responses=True)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

class CacheStrategy:
    REDIS_TTL = 86400  # 24 hours
    SIMILARITY_THRESHOLD = 0.85
    
    @staticmethod
    def generate_cache_key(query: str) -> str:
        """Generate deterministic cache key from query"""
        normalized = query.lower().strip()
        return f"rpp_cache_{hashlib.md5(normalized.encode()).hexdigest()}"
    
    @staticmethod
    def get_embedding(text: str) -> list:
        """Get embedding for similarity search"""
        return sentence_model.encode(text).tolist()

class HybridCache:
    def __init__(self, redis_conn, ollama_client, groq_client):
        self.redis = redis_conn
        self.ollama = ollama_client
        self.groq = groq_client
        self.strategy = CacheStrategy()
    
    def get_answer(self, query: str) -> tuple[str, str]:
        """
        Get answer with hybrid cache strategy
        Returns: (answer, source: 'redis'|'ollama'|'groq'|'groq_refined')
        """
        
        cache_key = self.strategy.generate_cache_key(query)
        
        # Step 1: Check Redis
        redis_answer = self.redis.get(cache_key)
        if redis_answer:
            print(f"✅ Redis HIT: {cache_key}")
            return redis_answer, "redis"
        
        # Step 2: Check Ollama similarity
        query_embedding = self.strategy.get_embedding(query)
        ollama_answer = self._search_ollama(query_embedding)
        
        if ollama_answer and ollama_answer['score'] > self.strategy.SIMILARITY_THRESHOLD:
            print(f"✅ Ollama HIT (similarity: {ollama_answer['score']:.2f})")
            # Cache it for future exact matches
            self.redis.setex(cache_key, self.strategy.REDIS_TTL, ollama_answer['text'])
            return ollama_answer['text'], "ollama"
        
        # Step 3: Groq fallback
        if ollama_answer and ollama_answer['score'] > 0.75:
            # Found similar answer, but refine it
            groq_answer = self._refine_with_groq(query, ollama_answer['text'])
            print(f"🔄 Ollama + Groq refinement")
        else:
            # No cache found, ask Groq
            groq_answer = self._ask_groq(query)
            print(f"❌ Cache MISS, Groq asked")
        
        # Step 4: Cache the answer
        self.redis.setex(cache_key, self.strategy.REDIS_TTL, groq_answer)
        self.ollama.embed(groq_answer, cache_key)  # Add to Ollama
        
        return groq_answer, "groq"
    
    def _search_ollama(self, embedding: list) -> dict:
        """Search similar answers in Ollama"""
        try:
            results = self.ollama.search(embedding, threshold=0.75)
            if results:
                return {
                    'text': results[0].get('text'),
                    'score': results[0].get('score', 0)
                }
        except Exception as e:
            print(f"Ollama search error: {e}")
        return None
    
    def _ask_groq(self, query: str) -> str:
        """Ask Groq for answer"""
        response = self.groq.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{
                "role": "user",
                "content": f"Consulta RPP: {query}"
            }],
            temperature=0.3,
            max_tokens=1024
        )
        return response.choices[0].message.content
    
    def _refine_with_groq(self, query: str, ollama_context: str) -> str:
        """Refine Ollama answer with Groq"""
        response = self.groq.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{
                "role": "user",
                "content": f"""
                Consulta: {query}
                Contexto disponible: {ollama_context}
                
                Si el contexto es relevante, refina la respuesta.
                Si no es relevante, responde directamente.
                """
            }],
            temperature=0.3,
            max_tokens=512  # Smaller because partial
        )
        return response.choices[0].message.content

# Initialize hybrid cache
hybrid_cache = HybridCache(redis_client, ollama, groq_client)

@app.post("/api/consult")
async def consult(query: str):
    """Main endpoint with hybrid cache"""
    answer, source = hybrid_cache.get_answer(query)
    return {
        "query": query,
        "answer": answer,
        "source": source,  # For debugging/stats
        "cached": source != "groq"
    }

@app.get("/api/cache-stats")
async def cache_stats():
    """Cache performance statistics"""
    return {
        "redis_keys": redis_client.dbsize(),
        "cache_ttl": CacheStrategy.REDIS_TTL,
        "ollama_vectors": len(ollama.list()),  # Approximate
    }
```

---

## Monitoreo de Caché

### Métricas Clave

```yaml
# Dashboard Prometheus
metrics:
  - cache_hits_total: Contador de Redis hits
  - cache_misses_total: Contador de misses
  - cache_hit_ratio: (hits / total) = debería ser 40-60%
  - groq_calls_total: Llamadas a Groq (debería ↓60%)
  - ollama_refinements: Refinamientos Groq (debería ~50%)
  - response_time_p95: Latencia p95 (Redis ~50ms, Groq ~500ms)
  - groq_cost_daily: Costo diario (debería ~$1-2/día = $25-60/mes)
```

### Alertas Configuradas

```yaml
alerts:
  - name: "Cache Hit Ratio Low"
    condition: "cache_hit_ratio < 0.30"  # Should be 40%+
    action: "Review RAG chunking/design"
  
  - name: "Groq Cost Spike"
    condition: "groq_cost_daily > $5"
    action: "Investigate queries, review cache config"
  
  - name: "Ollama Unavailable"
    condition: "ollama_response_time > 2000ms"
    action: "Auto-fallback to Groq only"
  
  - name: "Redis Full"
    condition: "redis_memory_usage > 90%"
    action: "Rotate old entries (cleanup)"
```

---

## Timeline de Implementación

### Día 1-2: Setup
- Instalar Redis
- Instalar Ollama local
- Configurar embeddings

### Día 3-4: Integration
- Agregar cache layer a FastAPI
- Implementar Groq refinement
- Configurar TTLs y thresholds

### Día 5-6: Testing
- Load test 100 usuarios simultáneos
- Validar cache hit ratio
- Medir ahorros reales

### Día 7: Deployment
- Deploy a producción
- Validar funcionalidad
- Monitoreo activo

---

## Comparativa: Con vs Sin Caché

| Métrica | Sin Caché (Actual) | Con Caché Híbrida |
|---------|-------------------|-------------------|
| Costo/mes | $350 | $125 |
| Costo/consulta | $0.003 | $0.0005 |
| Latencia p95 | 500ms | 150ms |
| Usuarios soportados | Ilimitado | Ilimitado |
| Hit ratio | N/A | 40-60% |
| Escalabilidad | via Groq API | Sin limite |
| Dependencia | Groq cloud | Local + Groq fallback |

---

## Conclusión

La estrategia de **caché híbrida** permite:

✅ **Ahorrar 60-70% en costos Groq** (caché resuelve mayoría)  
✅ **Mantener escalabilidad ilimitada** (Groq siempre disponible)  
✅ **Mejorar performance** (caché más rápido)  
✅ **Reducir dependencia** (Ollama como fallback)  
✅ **Presupuesto realista** ($125/mes vs $350)  

**Presupuesto estimado mensual: $125/mes (con variaciones según uso)**

---

**Documento preparado para: Equipo Técnico**  
**Fecha: 8 de Abril, 2026**  
**Estado: Impementación Lista**
