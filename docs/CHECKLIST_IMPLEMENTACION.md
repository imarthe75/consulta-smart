# 🚀 CHECKLIST DE IMPLEMENTACIÓN: OLLAMA MIGRATION

**Proyecto**: ConsultaRPP Addon (Migración: Groq → Ollama)  
**Timeline**: 3 semanas  
**Responsable**: DevOps Lead  
**Status**: [ ] No iniciado [ ] En progreso [ ] Completado  

---

## SEMANA 1: PRUEBA CONCEPTO (POC)

### Día 1: Instalación
- [ ] Asignar servidor para pruebas (o usar compartido)
- [ ] Verificar requisitos mínimos:
  - [ ] CPU 4+ cores disponibles
  - [ ] RAM 8+ GB disponibles
  - [ ] Disk 100+ GB disponibles
  - [ ] Red con acceso a localhost
- [ ] Documentar especificaciones del servidor

### Día 1-2: Ollama Installation
```bash
# Linux
- [ ] curl https://ollama.ai/install.sh | sh
- [ ] Verificar: ollama --version
- [ ] Iniciar: ollama serve (background)
- [ ] Esperar 2 min
- [ ] Test: curl http://localhost:11434
```

```bash
# Docker
- [ ] Crear Dockerfile.ollama
- [ ] Build: docker build -t ollama-test -f Dockerfile.ollama .
- [ ] Run: docker run -d -p 11434:11434 ollama-test
- [ ] Esperar 3 min
- [ ] Test: curl http://localhost:11434
```

### Día 2: Descargar Modelo
```bash
- [ ] Opción A: ollama pull llama2          (4GB, 10 min)
- [ ] O Opción B: ollama pull mistral       (3.5GB, 8 min)
- [ ] O Opción C: ollama pull phi           (1.6GB, 5 min)
- [ ] Esperar descarga completa
- [ ] Verificar: ollama list
- [ ] Modelo debe aparecer: NAME    ID    SIZE
```

### Día 2-3: Test Manual
```bash
- [ ] CLI Test:
      ollama run llama2
      >>> ¿Cuáles son las oficinas en Quintana Roo?
      (Enter y esperar respuesta ~30 seg)
      
- [ ] HTTP API Test:
      curl -X POST http://localhost:11434/api/generate \
        -d '{"model":"llama2","prompt":"Hola","stream":false}'
      (Debería retornar JSON con response)
      
- [ ] Python Test:
      python3 scripts/test_ollama_direct.py
      (Debería mostrar: "✅ Ollama conectado")
```

### Día 3: Integración con FastAPI
- [ ] Crear clase OllamaProvider en `llm_service.py`
  - [ ] Heredar de LLMProvider
  - [ ] Implementar `async def chat()`
  - [ ] Implementar `async def embed()`
  - [ ] Manejo de errores y timeouts
  - [ ] Logging estructurado

- [ ] Actualizar SmartLLMRouter:
  - [ ] Cambiar provider_list a ["ollama"]
  - [ ] Remover Groq e inicialización
  - [ ] Remover Gemini e inicialización
  - [ ] Verificar priority_order

- [ ] Actualizar .env:
  - [ ] LLM_PROVIDER=ollama
  - [ ] OLLAMA_BASE_URL=http://localhost:11434
  - [ ] OLLAMA_MODEL=llama2
  - [ ] Remover GROQ_API_KEY, GOOGLE_API_KEY

### Día 3-4: Comparativa Groq vs Ollama
- [ ] Ejecutar script benchmark:
  ```bash
  scripts/compare-ollama-vs-groq.sh
  ```
- [ ] Registrar resultados:
  - [ ] Latencia Ollama: ____ ms
  - [ ] Latencia Groq: ____ ms
  - [ ] Calidad respuesta Ollama: 1-10: ____
  - [ ] Calidad respuesta Groq: 1-10: ____

- [ ] Documentar diferencias en `POC_REPORT.md`

### Día 4: Entregables Semana 1
- [ ] README_IMPLEMENTACION_POC.md (¿qué funcionó?)
- [ ] LIMITACIONES_IDENTIFICADAS.md (¿qué no?)
- [ ] RECOMENDACIONES.md (próximos pasos)
- [ ] Demo para stakeholders (si es posible)

### Status Semana 1
- [ ] Ollama instalado y funcionando ✅
- [ ] Modelo descargado y testeable ✅
- [ ] Integrado con FastAPI ✅
- [ ] Comparativa documentada ✅
- [ ] Reportes listos para aprobación ✅

---

## SEMANA 2: STAGING & TESTING

### Día 5: Ambiente Staging
- [ ] Provisionar servidor de staging:
  - [ ] OS: Ubuntu 22.04 LTS
  - [ ] CPU: 4+ cores
  - [ ] RAM: 16GB
  - [ ] Disk: 500GB SSD
  - [ ] Network: Conectado a red interna

- [ ] Instalar Docker & Docker Compose
  - [ ] Verificar: docker --version
  - [ ] Verificar: docker-compose --version
  - [ ] Test: docker run hello-world

### Día 5-6: Deploy Staging
```bash
- [ ] Copiar docker-compose.yml actualizado
  (con servicio Ollama)
- [ ] Verificar variables de entorno
- [ ] docker-compose build
- [ ] docker-compose up -d
- [ ] Esperar 5 minutos
- [ ] docker-compose ps (verificar todos ✅)
- [ ] docker logs consultarpp-ollama (sin errores)
```

### Día 6: Testing Básico
```bash
- [ ] Health check:
      curl http://localhost:11434 → HTTP 200
      
- [ ] API test:
      curl -X POST http://localhost:3001/api/v1/auth/login \
        -d 'username=demo@example.com&password=password123'
      (Debería retornar JWT token)
      
- [ ] Chat query test:
      curl -X POST http://localhost:3001/api/v1/chat/query \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"message":"¿Hola?","session_id":"test"}'
      (Debería retornar respuesta JSON)
```

### Día 6-7: Load Testing
- [ ] Instalar herramienta load testing:
  ```bash
  npm install -g autocannon
  # o
  brew install hey
  ```

- [ ] Test de 10 usuarios concurrentes:
  ```bash
  autocannon -c 10 -d 60 http://localhost:3001/api/v1/chat/query
  # Registrar:
  # - Throughput: ____ req/sec
  # - Latency p50: ____ ms
  # - Latency p95: ____ ms
  # - Latency p99: ____ ms
  # - Errors: ____
  ```

- [ ] Test de 50 usuarios concurrentes (si hardware permite):
  ```bash
  autocannon -c 50 -d 120 http://localhost:3001/api/v1/chat/query
  # Registrar mismos datos
  ```

- [ ] Captura de métricas:
  - [ ] CPU util: ____%
  - [ ] RAM util: ____GB / 16GB
  - [ ] Disk util: ____%
  - [ ] Reqs/seg: ____
  - [ ] Errores: ____

### Día 7: Performance Tuning
- [ ] Si latencia > 5s:
  - [ ] Revisar logs del Ollama
  - [ ] Aumentar RAM alocado a Ollama
  - [ ] Cambiar a modelo más ligero (Phi)
  - [ ] Habilitar caché Redis

- [ ] Si CPU > 90%:
  - [ ] Reducir max concurrent requests
  - [ ] Habilitar quantization (4-bit)
  - [ ] O agregar segundo servidor Ollama

- [ ] Documentar cambios en `PERFORMANCE_TUNING.md`

### Día 7: Capacitación Inicial
- [ ] Preparar guía de operación para oncall
- [ ] Entrenar a 2-3 operadores en:
  - [ ] Cómo revisar logs
  - [ ] Cómo monitorear recursos
  - [ ] Cómo reiniciar servicios
  - [ ] Cómo detectar problemas
  - [ ] Cómo activar fallback (si es necesario)

### Entregables Semana 2
- [ ] Sistema en staging funcionando 24/7
- [ ] Load testing completado
- [ ] Performance report
- [ ] Operación guide
- [ ] Capacity planning document

### Status Semana 2
- [ ] Staging operativo ✅
- [ ] Load tests passed (>10 usuarios) ✅
- [ ] Performance dentro de parámetros ✅
- [ ] Equipo capacitado ✅
- [ ] Listo para producción ✅

---

## SEMANA 3: PRODUCCIÓN & ROLLOUT

### Día 8: Pre-migración (Preparativos)
- [ ] Backup de base de datos:
  ```bash
  docker exec consultarpp-postgres pg_dump -U consultarpp_user \
    consultarpp > backup-pre-ollama.sql
  ```

- [ ] Snapshot de máquina (si es posible)
- [ ] Comunicado a usuarios:
  - [ ] "Mantenimiento de sistemas 2-3 horas"
  - [ ] "Posible latencia aumentada 1-2 segundos"
  - [ ] "Se espera mejoría en privacidad y costo"

- [ ] Plan B (rollback) documentado:
  - [ ] Si falla, volver a Groq en 1 hora
  - [ ] Sin pérdida de datos
  - [ ] Usuarios no afectados

### Día 8: Copia de Producción a Staging
- [ ] Actualizar docker-compose a versión production-ready
- [ ] Verificar todas las variables .env
- [ ] Habilitar logging extendido
- [ ] Configurar alertas
- [ ] Health checks en "critical"

### Día 9: Migración en Vivo (Morning 6am)
```bash
# Pre-migración checks
- [ ] Verificar backup realizado: ls -la backup-pre-ollama.sql
- [ ] Verificar Groq actualmente funcionando
- [ ] Tener consola abierta: docker logs -f consultarpp-backend

# Migración
- [ ] docker-compose stop backend
- [ ] docker-compose build backend
- [ ] docker-compose up -d  # Con Ollama incluido
- [ ] Esperar 30 segundos
- [ ] docker-compose ps (todos en GREEN)

# Validación
- [ ] curl http://localhost:3001/api/v1/health
- [ ] curl auth/login y obtener token
- [ ] Hacer 3 queries de chat
- [ ] Revisar logs: "No errors"
- [ ] Monitorear recursos
```

### Día 9: Monitoreo Post-Migración
- [ ] Primera 2 horas: monitoreo cada 5 min
- [ ] Siguiente 6 horas: monitoreo cada 15 min
- [ ] Siguiente 24 horas: monitoreo cada hora

- [ ] Métricas a monitorear:
  - [ ] API response time p95 < 5s
  - [ ] Error rate < 1%
  - [ ] CPU utilization < 80%
  - [ ] RAM utilization < 85%
  - [ ] Disk utilization < 70%
  - [ ] User complaints: NONE

### Día 9-10: Validación de Usuarios
- [ ] Invitar 5-10 usuarios test
- [ ] Hacer queries reales
- [ ] Recolectar feedback:
  - [ ] "¿Respuestas correctas?" YES/NO
  - [ ] "¿Latencia aceptable?" YES/NO
  - [ ] "¿Confianza en datos?" YES/NO
  - [ ] "¿Problemas técnicos?" None/Minor/Critical

- [ ] Registrar en `USER_FEEDBACK_DAY1.md`

### Día 10: Go-live Completo
- [ ] Si todo OK (no hay "Critical"):
  - [ ] Anunciar a todos los usuarios
  - [ ] Habilitar queries normales
  - [ ] Monitoreo continuo

- [ ] Si hay problemas ("Critical"):
  - [ ] Activar rollback a Groq
  - [ ] Documentar issue
  - [ ] Investigar root cause
  - [ ] Iterar y volver a intentar

### Día 10: Documentación Final
- [ ] Post-mortem document (si issues)
- [ ] Lessons learned
- [ ] Process improvements
- [ ] SLA finalmente establecido:
  - [ ] Disponibilidad: ____%
  - [ ] Latencia p95: ____ ms
  - [ ] Métrica de calidad: ____
  - [ ] Respuesta a problemas: 30 min

### Entregables Semana 3
- [ ] Sistema en producción
- [ ] Cero downtime (esperado)
- [ ] Usuarios satisfechos
- [ ] Monitoreo operativo
- [ ] Documentación actual

### Status Semana 3
- [ ] Ollama en producción ✅
- [ ] Migracion exitosa (zero downtime) ✅
- [ ] Usuarios activos ✅
- [ ] Monitoreo 24/7 activo ✅
- [ ] Costo: $0/mes ✅

---

## SEMANA 4+: OPTIMIZACIÓN CONTINUA

- [ ] Semana 4: Fine-tuning prompts basado en user feedback
- [ ] Semana 5: Implementar caché Redis para queries frecuentes
- [ ] Semana 6: Análisis de queries: top 10 preguntas
- [ ] Semana 7: Posible actualización a GPT-3.5 quality tuning
- [ ] Mensual: Review de costos actuales vs proyectado

---

## RIESGOS MITIGATION MATRIX

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-----------|--------|------------|
| Ollama lento | Media | Media | Test load antes de prod |
| Out of Memory | Baja | Alto | Monitoreo de RAM, reducir conexiones |
| Modelo impreciso | Media | Bajo | Usar Mistral si es mejor |
| Usuarios insatisfechos | Baja | Medio | Plan de comunicación + FAQ |
| Hardware falla | Muy baja | Alto | Backup en Groq fallback |

---

## COMUNICACIÓN STAKEHOLDERS

### Pre-migración (Día 3)
- [ ] Email a dirección: "POC exitoso, listo para staging"
- [ ] Adjuntar: PROPUESTA_EJECUTIVA.md, resultados POC

### Pre-producción (Día 8)
- [ ] Email a IT team: "Migración programada Día 9, 6am"
- [ ] Adjuntar: runbooks, rollback procedures

### Post-migración (Día 10)
- [ ] Email a usuarios: "Mudanza completada, sigue siendo gratis, mejor privacidad"
- [ ] Adjuntar: FAQ, cómo reportar problemas

### Mensual
- [ ] Report: Uptime, # queries, satisfaction score
- [ ] Proyección: Costos ahorrados ese mes

---

## DOCUMENTOS GENERADOS (Checklist)

Al final, deberías tener en `/consulta-rpp/docs/`:

- [ ] PROPUESTA_EJECUTIVA.md (dado)
- [ ] ANALISIS_FINANCIERO_ADDON_GRATUITO.md (dado)
- [ ] GUIA_TECNICA_MIGRACION_OLLAMA.md (dado)
- [ ] POC_REPORT.md (⬅ generar)
- [ ] PERFORMANCE_TUNING.md (⬅ generar)
- [ ] OPERACION_GUIDE.md (⬅ generar)
- [ ] USER_FEEDBACK_DAY1.md (⬅ generar)
- [ ] POSTMORTEM_MIGRACION.md (⬅ si problemas)
- [ ] SLA_FINAL.md (⬅ generar)

---

## SIGN-OFF

**Proyecto**: ConsultaRPP Addon Ollama  
**Preparado por**:  _________________________ Fecha: _________  
**Revisado por**:  _________________________ Fecha: _________  
**Aprobado por**:  _________________________ Fecha: _________  

**Status Final**: [ ] No iniciado [ ] En progreso [ ] COMPLETADO ✅

---

**Documento**: CHECKLIST_IMPLEMENTACION.md  
**Versión**: 1.0  
**Última actualización**: Abril 2026  
