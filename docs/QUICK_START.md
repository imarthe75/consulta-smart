# 🚀 ConsultaRPP - Guía de Ejecución Rápida

**Status**: ✅ Phase 2 & 3 Completas - Listo para testing

---

## 📋 Pre-requisitos

- **Docker** & **Docker Compose**
- **Node.js** 18+ (para desarrollo local)
- **Python** 3.10+ (para desarrollo local del backend)
- **API Keys**:
  - Groq API Key (LLM primario)
  - Google Gemini API Key (LLM fallback)

---

## ⚡ Inicio Rápido (Docker Compose)

### 1. Configuración Inicial

```bash
# Entrar al directorio del proyecto
cd consulta-rpp

# Copiar y editar configuración
cp .env.example .env

# Editar .env con tus API keys
nano .env
# Importante: Agregar GROQ_API_KEY y GEMINI_API_KEY
```

### 2. Levantar Todos los Servicios

```bash
# Iniciar Docker Compose (todos los servicios)
docker-compose up -d

# Esperar a que los servicios se inicialicen (30-60 segundos)
sleep 30

# Verificar estado
docker-compose ps
```

### 3. Acceder a la Aplicación

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:3003
- **API Docs (Swagger)**: http://localhost:3003/docs
- **PostgreSQL**: localhost:3001
- **Valkey**: localhost:3002

---

## 🛠️ Desarrollo Local

### Backend FastAPI

```bash
# Verificar backend está corriendo
docker-compose ps | grep backend

# Ver logs del backend
docker-compose logs -f backend

# Ejecutar shell interactivo
make backend-shell

# Tests
make backend-test
```

### Frontend React 19

```bash
# En otra terminal
cd frontend

# Instalar dependencias (primera vez)
npm install

# Iniciar servidor de desarrollo
npm run dev

# Ya está disponible en http://localhost:3000
```

---

## 👤 Credenciales Demo

**User Demo:**
```
Email: demo@example.com
Password: password123
```

O crear nuevo usuario desde la pantalla de registro.

---

## 🔍 Flujo de Uso Completo

### 1. **Autenticación** (LoginPage)
   - Inicia sesión o regístrate
   - JWT token se guarda automáticamente

### 2. **Carga de Documentos** (/documentos)
   - Arrastra documentos PDF, Word o imágenes
   - Selecciona categoría (Reglamentos, Guías, etc)
   - El backend procesa automáticamente con Docling

### 3. **Chat Inteligente** (/)
   - Crea nueva sesión de chat
   - Escribe tu pregunta
   - El backend busca en documentos y genera respuesta con LLM
   - Ver fuentes citadas debajo de respuesta

### 4. **Búsqueda** (/resultados)
   - Busca términos específicos
   - Ver resultados con relevancia
   - Click en resultado para más detalles

---

## 📊 Comandos Útiles

### Docker Compose
```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f postgres

# Entrar a contenedor
docker-compose exec backend bash
docker-compose exec postgres bash

# Detener servicios
docker-compose stop

# Completar limpieza
docker-compose down -v
```

### Makefile
```bash
# Ver todos los comandos disponibles
make help

# Backend
make backend-dev    # Desarrollo local
make backend-test   # Tests
make backend-shell  # Shell Python

# Frontend
make frontend-dev   # Dev server
make frontend-build # Build producción

# Database
make db-shell      # PostgreSQL shell
make db-init       # Inicializar DB

# General
make start         # Iniciar servicios
make stop          # Detener servicios
make clean         # Limpiar todo
make health        # Ver estado
```

---

## 🧪 Verificar Conectividad

### Backend Health Check
```bash
curl http://localhost:3003/health
# Respuesta esperada: {"status": "healthy"}

curl http://localhost:3003/health/detailed
# Ver estado de todas las dependencias
```

### Documentación API
```bash
# Swagger UI
open http://localhost:3003/docs

# ReDoc
open http://localhost:3003/redoc
```

### WebSocket (Chat - Próximo)
```bash
# El frontend se conectará automáticamente
# Los mensajes se envían vía REST por ahora
```

---

## 🐛 Troubleshooting

### Conexión Rechazada
```bash
# Backend no está listo
docker-compose logs backend | tail -20

# Esperar más tiempo
sleep 30
```

### API Keys no válidas
```bash
# Verificar GROQ_API_KEY y GEMINI_API_KEY en .env
grep -E "GROQ|GEMINI" .env

# Asegúrese que sean válidas (sin comillas)
```

### Base de Datos
```bash
# Verificar PostgreSQL está corriendo
docker-compose ps | grep postgres

# Resetear database
docker-compose down postgres
docker-compose up -d postgres
```

### Frontend no carga
```bash
# Verificar Vite está corriendo
docker-compose logs frontend

# Puerto 5173 ocupado
lsof -i :3000
```

---

## 📁 Estructura del Proyecto

```
consulta-rpp/
├── backend/              # FastAPI Python
│   ├── app/
│   ├── main.py
│   └── requirements.txt
├── frontend/             # React 19
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml    # 8 servicios
├── Makefile             # Comandos
└── docs/                # Documentación
```

---

## 🔐 Seguridad en Producción

- ✅ JWT tokens (expiry 24h recomendado)
- ✅ HTTPS required (frontera)
- ✅ CORS configurado
- ✅ Variables secretas en .env
- ✅ Database backups regulares
- ✅ Rate limiting en endpoints

---

## 📈 Escalabilidad

- PostgreSQL + pgvector: 10M+ registros
- Redis/Valkey: Cache distribuido
- SeaweedFS: Almacenamiento escalable
- Celery: Procesamiento async escalable
- Docker: Orquestación con Kubernetes

---

## 📚 Documentación Completa

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Diseño del sistema
- [PHASE_2_REPORT.md](docs/PHASE_2_REPORT.md) - Implementation backend
- [PHASE_3_COMPLETE.md](PHASE_3_COMPLETE.md) - Implementation frontend
- [HEXAGONAL_ARCHITECTURE.md](docs/HEXAGONAL_ARCHITECTURE.md) - Patrón arquitectura
- [LOCALIZATION.md](docs/LOCALIZATION.md) - Internacionalización

---

## 🎯 Próximos Pasos (Phase 4)

- [ ] Tests integración backend-frontend
- [ ] E2E testing (Cypress)
- [ ] Performance profiling
- [ ] Deployment a producción
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring & alerting

---

## 📞 Soporte

Para preguntas o problemas:
1. Revisar logs: `docker-compose logs -f`
2. Consultar documentación en `docs/`
3. Verificar conectividad con `make health`

---

**¡Listo para usar!** 🚀

Cualquier duda, checa la [documentación completa](docs/DOCUMENTATION_INDEX.md).

*ConsultaRPP - Sistema Inteligente de Consultas Legales*
*Abril 2026*
