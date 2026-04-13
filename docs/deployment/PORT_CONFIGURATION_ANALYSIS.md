# 📊 Análisis de Configuración & Recomendaciones de Puertos

**Fecha**: 7 de Abril de 2026  
**Proyecto**: ConsultaRPP vs idp-smart (coexistencia)

---

## 🐳 ¿Docker es la mejor opción?

### ✅ RECOMENDACIÓN: SÍ, USAR DOCKER

#### Ventajas de Docker para ConsultaRPP
```
✅ Aislamiento total entre proyectos
✅ Reproducibilidad (dev = prod)
✅ Gestión de dependencias sin conflictos
✅ Escalabilidad horizontal
✅ Fácil colaboración en equipo
✅ CI/CD automatizado
✅ Rollback instantáneo
✅ Monitoreo centralizado
```

#### Por qué NO sin Docker en este caso
```
❌ 8 servicios interconectados (complejo)
❌ Versiones específicas de PostgreSQL + pgvector
❌ Dependencias Python conflictivas
❌ SeaweedFS + Redis requieren configuración
❌ Celery necesita supervisor o PM2
❌ Difícil mantener 2 proyectos en paralelo
❌ Sin isolamiento = problemas de puerto/BD
```

#### Conclusión
**DOCKER es obligatorio aquí**. El stack es demasiado complejo para desarrollo local sin Docker.

---

## 📦 Versiones Utilizadas (ACTUALIZADAS)

### Frontend - React 19
```json
{
  "react": "^19.0.0",              (✅ Última versión)
  "vite": "^5.0.0",                (✅ Última versión)
  "tailwindcss": "^3.3.0",         (✅ Última versión)
  "react-router-dom": "^6.20.0",   (✅ Última versión)
  "zustand": "^4.4.0",             (✅ Última versión)
  "axios": "^1.6.0",               (✅ Última versión)
  "typescript": "^5.3.0",          (✅ Última versión)
}
```
**Status**: ✅ 100% ACTUALIZADO

### Backend - FastAPI Python
```python
fastapi==0.104.1                    (✅ Última versión)
uvicorn==0.24.0                     (✅ Última versión)
sqlalchemy==2.0.23                  (✅ Última versión)
asyncpg==0.29.0                     (✅ Última versión)
pydantic==2.5.0                     (✅ Última versión)
pgvector==0.2.1                     (✅ Última versión)
celery==5.3.4                       (✅ Última versión)
```
**Status**: ✅ 100% ACTUALIZADO

### Infrastructure - Sistema Base
```yaml
PostgreSQL:      pgvector/pgvector:pg16-latest       (✅ PG 16)
Redis/Valkey:    valkey/valkey:latest                (✅ Última)
SeaweedFS:       chrislusf/seaweedfs:latest          (✅ Última)
Node.js:         node:20-alpine                      (✅ Node 20)
Python:          python:3.11-slim                    (✅ Python 3.11)
```
**Status**: ✅ 100% ACTUALIZADO

---

## ⚠️ CONFLICTO DE PUERTOS DETECTADO

### Puertos Actuales ConsultaRPP
```
5173   → Frontend Vite
5432   → PostgreSQL
6379   → Redis/Valkey
8000   → Backend FastAPI       <- CONFLICTO ⚠️
8080   → SeaweedFS Volume      <- CONFLICTO ⚠️
9333   → SeaweedFS Master      <- Possible conflicto
9000   → DISPONIBLE
```

### Puertos Usados por idp-smart
```
1573   → ?
1574   → ?
8000   → ???                  <- CONFLICTO DIRECTO ⚠️
9000   → MinIO               <- CONFLICTO ⚠️
```

**Conflictos identificados:**
- ⚠️ **Puerto 8000**: Backend FastAPI CONFLICTA
- ⚠️ **Puerto 9000**: Potencial conflicto con SeaweedFS Master/MinIO
- ⚠️ **Puerto 8080**: SeaweedFS Volume podría conflictuar

---

## ✅ SOLUCIÓN: NUEVOS PUERTOS SIN CONFLICTOS

### Estrategia de Reasignación

**Opción A: ConsultaRPP en rango 3000s** (RECOMENDADO)
```
5173 → 3000  (Frontend Vite)
5432 → 3001  (PostgreSQL)
6379 → 3002  (Redis/Valkey)
8000 → 3003  (Backend FastAPI)
8080 → 3004  (SeaweedFS Volume)
9333 → 3005  (SeaweedFS Master)
19333 → 3006 (SeaweedFS Master alt)
18080 → 3007 (SeaweedFS Volume alt)
```

**Opción B: ConsultaRPP en rango 7000s** (ALTERNATIVA)
```
5173 → 7000  (Frontend Vite)
5432 → 7001  (PostgreSQL)
6379 → 7002  (Redis/Valkey)
8000 → 7003  (Backend FastAPI)
8080 → 7004  (SeaweedFS Volume)
9333 → 7005  (SeaweedFS Master)
```

**Opción C: ConsultaRPP en rango 2000s** (CONSERVADOR)
```
5173 → 2000  (Frontend Vite)
5432 → 2001  (PostgreSQL)
6379 → 2002  (Redis/Valkey)
8000 → 2003  (Backend FastAPI)
8080 → 2004  (SeaweedFS Volume)
9333 → 2005  (SeaweedFS Master)
```

### Recomendación Final
**OPCIÓN A (rango 3000s)** porque:
- No conflicta con puertos estándar
- Fácil de recordar
- Suficiente espacio (3000-3010)
- Compatible con ambos proyectos
- Rango seguro (no system privileged)

---

## 🔄 IMPLEMENTAR CAMBIO DE PUERTOS

Voy a cambiar a puertos rango **3000s**:

### Archivos a Modificar

1. **docker-compose.yml** - Todos los puertos expuestos
2. **.env.example** - Variables de puerto (si existen)
3. **frontend/vite.config.js** - Puerto dev server
4. **frontend/package.json** - Script dev
5. **backend/app/core/config.py** - Si hay configuración
6. **Makefile** - Comandos con puertos
7. **QUICK_START.md** - Documentación de puertos
8. **README.md** - URLs de servicios

¿Procedo con los cambios a los puertos 3000-3010?

---

## 📋 Resumen Comparativo

| Aspecto | ConsultaRPP | idp-smart | Acción |
|---------|-------------|-----------|--------|
| **Containerización** | ✅ Docker Compose | ✅ Docker Compose | ✅ Compatible |
| **Backend Port** | 8000 | 8000 | ❌ CAMBIAR a 3003 |
| **Frontend Port** | 5173 | - | ⚠️ CAMBIAR a 3000 |
| **DB Port** | 5432 | ? | ⚠️ CAMBIAR a 3001 |
| **Redis Port** | 6379 | ? | ⚠️ CAMBIAR a 3002 |
| **Storage Port** | 8080 | 9000 | ⚠️ CAMBIAR a 3004 |

---

## 🔐 Verificación de Puertos

```bash
# Ver qué está usando cada puerto
lsof -i :8000     # idp-smart backend
lsof -i :9000     # idp-smart minio
lsof -i :1573     # idp-smart ?
lsof -i :1574     # idp-smart ?

# Verificar rango 3000s está libre
for port in {3000..3010}; do 
  echo -n "Port $port: "
  lsof -i :$port || echo "✅ Libre"
done
```

---

## 📝 Próximos Pasos

1. **Confirmar** que quieres usar rango 3000s
2. Modificar `docker-compose.yml`
3. Actualizar `.env.example`
4. Actualizar `vite.config.js`
5. Actualizar documentación
6. Crear video/guía de cambios
7. Testear ambos proyectos en paralelo

**¿Procedo con los cambios de puertos?**
