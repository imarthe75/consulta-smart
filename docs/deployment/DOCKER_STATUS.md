# 🚀 ConsultaRPP - Estado Docker Actualizado

**Fecha**: 8 de Abril de 2026  
**Estado**: ✅ **TODOS LOS SERVICIOS CORRIENDO**  
**Acceso**: Flexible - Localhost, IP servidor, o dominio  
**Configuración**: Sin hardcodeo de IPs (dinámico)

## 📊 Estado de Servicios

| Servicio | Puerto | Estado | URL de Acceso |
|----------|--------|--------|---------------|
| Frontend (React) | 3000 | ✅ Up | http://localhost:3000 o http://<IP>:3000 |
| Backend (FastAPI) | 3001 | ✅ Up | http://localhost:3001 o http://<IP>:3001 |
| PostgreSQL | 3002 | ✅ Healthy | localhost:3002 o <IP>:3002 |
| Redis | 3003 | ✅ Healthy | localhost:3003 o <IP>:3003 |
| Celery Worker | interno | ✅ Up | (sin puerto expuesto) |

## 🔐 Acceso a Servicios

### Frontend (React)
```
URL Local: http://localhost:3000
URL Remota: http://<IP_SERVIDOR>:3000  (ejemplo: http://10.4.3.28:3000)
URL Dominio: http://<TU_DOMINIO>:3000
Descripción: Interfaz de usuario de ConsultaRPP
Característica: Se conecta automáticamente al backend detectando el host
```

### Backend API (FastAPI)
```
URL Local: http://localhost:3001
URL Remota: http://<IP_SERVIDOR>:3001  (ejemplo: http://10.4.3.28:3001)
URL Dominio: http://<TU_DOMINIO>:3001

Documentación Swagger: :3001/docs
Documentación ReDoc: :3001/redoc

Característica: El frontend se conecta automáticamente
Acceso: Local o remoto para clientes API
```

### Base de Datos PostgreSQL
```
Host Local: localhost
Host Remoto: <IP_SERVIDOR>  (ejemplo: 10.4.3.28)
Puerto: 3002
Usuario: consultarpp_user
Contraseña: ***DB_PASSWORD_REDACTED***
Base de Datos: consultarpp_db
Nota: pgvector no disponible en postgres:16-alpine (comentado en init-db.sql)
Acceso: Solo desde contenedores o conexiones directas a la red
```

### Redis
```
Host Local: localhost
Host Remoto: <IP_SERVIDOR>  (ejemplo: 10.4.3.28)
Puerto: 3003
Contraseña: redis_secure_2026
Uso: Caché y broker de Celery
Acceso: Solo desde contenedores o conexiones directas a la red
```

## 📋 Cambios Realizados Recientemente

### 1. ✅ Resolución de Conflictos de Puertos
- **Problema**: Puertos 5173 y 8000 estaban ocupados por "idp-smart"
- **Solución**: Remapeado a serie 3000+
  - Frontend: 5173 → 3000
  - Backend: 8000 → 3001
  - PostgreSQL: 5432 → 3002
  - Redis: 6379 → 3003

### 2. ✅ Actualización de Dependencias
- **Problema**: Versiones antiguas de dependencias incompatibles
- **Solución**: Actualizado requirements.txt con versiones compatibles
  - FastAPI: 0.115.12
  - Uvicorn: 0.34.0
  - Celery: 5.5.0
  - Redis: 5.2.1
  - Docling: 2.83.0+ (para procesamiento de documentos)
  - Torch/Transformers para modelos de IA

### 3. ✅ Imágenes Base Corregidas
- **Problema**: Imágenes antiguas y no encontradas
- **Solución**: 
  - PostgreSQL: postgres:16-alpine (lightweight, pgvector omitido)
  - Redis: redis:7-alpine (lightweight)
  - Backend: python:3.12-slim (mejor compatibilidad con dependencias)
  - Frontend: node:20-alpine (Alpine para menor tamaño)

### 4. ✅ Configuración de Base de Datos
- **Problema**: Extension pgvector no disponible en postgres:16-alpine
- **Solución**: Comentada línea de pgvector en init-db.sql
- **Nota**: Si se necesita pgvector, se puede usar pgvector/pgvector:pg16 (imagen oficial)

### 5. ✅ Dockerfile del Frontend
- **Problema**: `package-lock.json` no existía
- **Solución**: Actualizado Dockerfile para usar `npm install` en lugar de `npm ci`

### 6. ✅ Dependencias de Datos
- **Backend** espera a PostgreSQL y Redis (healthcheck)
- **Frontend** espera a Backend
- **Celery Worker** espera a PostgreSQL, Redis y Backend

## 🛠️ Comandos Útiles

### Ver estado de servicios
```bash
docker compose ps
```

### Ver logs de un servicio
```bash
docker compose logs backend    # Backend
docker compose logs frontend   # Frontend
docker compose logs postgres   # PostgreSQL
docker compose logs redis      # Redis
docker compose logs celery-worker  # Celery
```

### Ver logs en tiempo real
```bash
docker compose logs -f backend
```

### Detener servicios
```bash
docker compose down
```

### Detener y eliminar volúmenes
```bash
docker compose down -v
```

### Reiniciar servicios
```bash
docker compose restart
```

### Acceder remotamente desde otro equipo en la red
```bash
# Frontend
curl http://10.4.3.28:3000

# Backend
curl http://10.4.3.28:3001/docs

# Backend Health  
curl http://10.4.3.28:3001/health
```

## 🌐 Acceso desde Cualquier Ubicación

### Desde la misma máquina (Localhost)
```bash
# Desde tu navegador:
http://localhost:3000        # Frontend
http://localhost:3001/docs   # API Documentación

# O desde terminal:
curl http://localhost:3001/docs
```

### Desde otra máquina en la red
```bash
# Obtén la IP del servidor
ip addr show | grep "inet " | grep -v 127

# Desde su navegador:
http://<IP_SERVIDOR>:3000        # Frontend (ejemplo: 10.4.3.28:3000)
http://<IP_SERVIDOR>:3001/docs   # API Docs

# O desde terminal:
curl http://<IP_SERVIDOR>:3001/docs
```

### Desde un dominio (si está configurado)
```bash
# Desde su navegador:
http://mi-dominio.com:3000        # Frontend
http://mi-dominio.com:3001/docs   # API Docs
```

### Configuración de Firewall
Asegúrate que:
- El firewall permita tráfico a puertos 3000-3003
- La red tenga conectividad entre dispositivos
- El servidor sea accesible desde la otra máquina

```bash
# Verificar conectividad desde cliente remoto
ping <IP_SERVIDOR>
curl http://<IP_SERVIDOR>:3000

# En el servidor, si es necesario abrir puertos
sudo ufw allow 3000:3003/tcp
```

### Ventaja de la configuración actual
✅ **Sin hardcodeo de IPs** - El frontend se adapta automáticamente  
✅ **Portable** - Funciona en cualquier servidor sin cambios  
✅ **Flexible** - Localhost, IP remota, o dominio funcionan igual

## 📦 Stack Técnico

```
Frontend:
- React 19
- Vite (bundler)
- TypeScript
- Tailwind CSS

Backend:
- FastAPI 0.115.12
- Python 3.12
- SQLAlchemy ORM
- Async/Await

LLM Integrations:
- Google Gemini (configurado en .env)
- Groq (fallback)
- OpenAI, Anthropic (opcionales)

Document Processing:
- Docling 2.83.0
- PyPDF 4.0.1
- PyMuPDF 1.24.0

Task Queue:
- Celery 5.5.0
- Redis 5.2.1 (broker)

Database:
- PostgreSQL 16
- SQLAlchemy
- Alembic (migrations)

Cache:
- Redis 7
```

## 🔧 Configuración .env

El archivo `.env` debe contener:
```env
GOOGLE_API_KEY=<tu_api_key>
LLM_PROVIDER=gemini
GROQ_API_KEY=<optional>
OPENAI_API_KEY=<optional>
DB_USER=consultarpp_user
DB_PASSWORD=***DB_PASSWORD_REDACTED***
DB_NAME=consultarpp_db
REDIS_PASSWORD=redis_secure_2026
```

## ✅ Checklist de Verificación

- ✅ Frontend accesible en http://localhost:3000 (o http://<IP>:3000)
- ✅ Backend accesible en http://localhost:3001 (o http://<IP>:3001)
- ✅ Swagger UI accesible en http://localhost:3001/docs (o http://<IP>:3001/docs)
- ✅ PostgreSQL conectado a localhost:3002 (o <IP>:3002) y esperando conexiones
- ✅ Redis ejecutando en localhost:3003 (o <IP>:3003) y disponible
- ✅ Celery Worker ejecutando y procesando tareas
- ✅ Todos los puertos mapeados correctamente
- ✅ Variables de entorno configuradas
- ✅ Base de datos inicializada
- ✅ Acceso flexible (sin hardcodeo de IPs) configurado

## 🚩 Notas Importantes

1. **pgvector**: No está disponible en postgres:16-alpine. Si lo necesitas, usa la imagen pgvector/pgvector:pg16
2. **API Key Gemini**: Recuerda nunca hacer commit del .env a Git (ya está en .gitignore)
3. **Rate Limits**: 
   - Gemini: 4/15 RPM, 70.3K/250K TPM
   - Groq: Límites actuales suelen ser más altos
4. **Desarrollo**: Los volúmenes están montados, puedes editar código y los cambios se aplicarán con reload automático
5. **Producción**: Para producción, usa una estrategia de despliegue diferente (no incluyas volúmenes en bind mount)

## 📞 Solución de Problemas

### Si los servicios no inician:
```bash
docker compose down -v
docker compose up -d
```

### Si hay errores de conexión a la base de datos:
```bash
docker compose logs postgres
```

### Si el frontend no carga:
```bash
docker compose logs frontend
docker compose logs -f backend
```

### Para verificar conectividad:
```bash
curl http://localhost:3001/docs
curl http://localhost:3000
nc -zv localhost 3002  # PostgreSQL
nc -zv localhost 3003  # Redis
```

---

**Última actualización**: 8 de Abril de 2026  
**Próximos pasos**: Pruebas funcionales del chat, upload de documentos, y búsqueda con Gemini
