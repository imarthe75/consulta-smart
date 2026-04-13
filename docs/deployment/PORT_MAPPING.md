# 🔌 Mapeo de Puertos - ConsultaRPP

**Problema:** Puertos 5173 (frontend) y 8000 (backend) ya estaban ocupados por `idp-smart`.

**Solución:** Remapeo a serie 3000 disponible.

---

## 📊 Nuevos Puertos

| Servicio | Puerto Original | Nuevo Puerto | Proposito |
|----------|-----------------|--------------|-----------|
| **Frontend** | 5173 | **3000** | React Vite dev server |
| **Backend API** | 8000 | **3001** | FastAPI uvicorn |
| **PostgreSQL** | 5432 | **3002** | Base de datos |
| **Redis/Valkey** | 6379 | **3003** | Cache & Celery |
| **SeaweedFS Volume** | 8080 | **3004** | Almacenamiento distribuido |
| **SeaweedFS Master** | 9333 | **3005** | Coordinador SeaweedFS |

---

## 🚀 Acceso a Servicios

```bash
# Frontend (React UI)
http://localhost:3000

# Backend API & Documentación
http://localhost:3001/docs         # Swagger UI
http://localhost:3001/redoc        # ReDoc
http://localhost:3001/api/v1/...   # API endpoints

# PostgreSQL (desde cliente SQL)
psql -h localhost -p 3002 -U consultarpp_user -d consultarpp_db

# Redis CLI
redis-cli -p 3003

# SeaweedFS Web UI
http://localhost:3004/
http://localhost:3005/
```

---

## 🔧 Archivos Modificados

1. **docker-compose.yml**
   - Actualizado mapeo de puertos en todos los servicios
   - Corregida variable `VITE_API_URL` a `http://localhost:3001`
   - Corregida network inconsistency (propquery → consultarpp)

2. **scripts/dev-start.sh**
   - URLs actualizadas a nuevos puertos
   - Documentación de acceso mejorada

---

## ▶️ Iniciar Desarrollo

```bash
# Opción 1: Script automático
bash scripts/dev-start.sh

# Opción 2: Manual
cp .env.example .env
docker-compose up -d
docker-compose logs -f
```

---

## ✅ Verificación

```bash
# Verificar que servicios están en los puertos correctos
ss -tulpn | grep -E "3000|3001|3002|3003|3004|3005"

# Probar Frontend
curl http://localhost:3000

# Probar Backend
curl http://localhost:3001/health

# Ver logs
docker-compose logs frontend
docker-compose logs backend
```

---

**Actualizado:** 2025-04-07  
**Status:** ✅ Listo para desarrollo
