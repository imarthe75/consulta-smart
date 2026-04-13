# 🚀 QUICK START - PropQuery

Guía completa para poblar en funcionamiento PropQuery en 10 minutos.

---

## Paso 1: Prerequisitos

Verifica que tengas instalado:

```bash
# Python 3.10+
python --version

# Node 18+
node --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Git
git --version
```

Si falta algo, instala desde:
- Python: https://www.python.org/downloads/
- Node: https://nodejs.org/
- Docker: https://www.docker.com/products/docker-desktop

---

## Paso 2: Clonar y Preparar Proyecto

```bash
# Navegar a home
cd ~

# El proyecto ya debería estar en /home/ia/propquery
cd propquery

# Copiar configuración de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env
# O usa tu editor favorito: code .env, vim .env, etc
```

**APIs necesarias en .env:**

```env
# Al menos UNO de estos:
GROQ_API_KEY=gsk_...          # ✅ MÁS FÁCIL (gratis)
GOOGLE_API_KEY=AIza...        # Google Gemini
OPENAI_API_KEY=sk-...         # OpenAI (de pago)
```

---

## Paso 3: Levantar la Infraestructura

```bash
# Desde /home/ia/propquery
docker-compose up -d

# Esperar unos 30 segundos a que se levanten todos los servicios
# Verificar que todo esté bien:
docker-compose ps

# Deberías ver:
# NAME                  STATUS
# propquery-postgres    Up
# propquery-valkey      Up
# propquery-seaweedfs   Up
# propquery-backend     Up
# propquery-frontend    Up
```

En caso de error:
```bash
# Ver logs
docker-compose logs -f backend

# Derribar todo y reintentar
docker-compose down -v
docker-compose up -d
```

---

## Paso 4: Setup del Backend

```bash
# Entrar a la carpeta backend
cd backend

# Crear virtual environment
python -m venv venv

# Activar venv
# En Linux/Mac:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
python scripts/init_db.py

# Ver que está OK:
python -c "import fastapi; print('✅ FastAPI OK')"
```

---

## Paso 5: Setup del Frontend

```bash
# Desde /home/ia/propquery
cd frontend

# Instalar dependencias
npm install

# Verificar
npm list | head -20
```

---

## Paso 6: Crear Base de Datos y Tablas

```bash
# Desde /home/ia/propquery/backend
# (con venv activado)

python scripts/init_db.py

# Output esperado:
# ✅ Tables created successfully
# ✅ pgvector extension installed
```

---

## Paso 7: Cargar Documentos de Ejemplo

```bash
# Desde /home/ia/propquery/scripts

# Crear carpeta de docs si no existe
mkdir -p ../sample_docs

# Copiar o descargar documentos de ejemplo
# (reglamentos, leyes, guías)
cp ~/idp-smart/samples/*.pdf ../sample_docs/ 2>/dev/null || echo "No hay PDFs en idp-smart/samples"

# Cargar documentos en la BD
python load_sample_docs.py

# Debería mostrar:
# ✅ Loaded 0 documents
# ✅ Vector embeddings created
```

---

## Paso 8: Iniciar Servicios

**Terminal 1 - Backend**:
```bash
cd ~/propquery/backend
source venv/bin/activate
python main.py

# Ver:
# ✅ Starting FastAPI server on 0.0.0.0:8000
# 📚 Docs available at http://localhost:8000/docs
```

**Terminal 2 - Frontend**:
```bash
cd ~/propquery/frontend
npm run dev

# Ver:
#   ➜  Local:   http://localhost:3000/
```

**Terminal 3 - Celery Worker** (opcional, para async tasks):
```bash
cd ~/propquery/backend
source venv/bin/activate
celery -A app.workers worker -l info
```

---

## Paso 9: Verificar que Todo Funciona

### Backend API
```bash
# Healthcheck
curl http://localhost:8000/health

# Output:
# {"status":"ok","version":"0.1.0"}
```

### Frontend
Abre en navegador:
```
http://localhost:3000
```

Deberías ver la interfaz de PropQuery.

### Swagger Docs
```
http://localhost:8000/docs
```

Documentación interactiva de la API.

---

## Paso 10: Subir un Documento de Prueba

```bash
# Crear un archivo de prueba
echo "REGLAMENTO DE INSCRIPCIÓN DE PROPIEDADES
Artículo 1: Requisitos básicos
- Cédula de identidad
- Comprobante de pago
- Documentos originales" > ~/propquery/sample_docs/test.txt

# Subir mediante API
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@~/propquery/sample_docs/test.txt" \
  -F "category=reglamentos" \
  -F "title=Test Reglamento"

# Output:
# {
#   "document_id": "doc_xyz123",
#   "status": "processing",
#   "message": "Document uploaded successfully"
# }
```

### O mediante Frontend
1. Abre http://localhost:3000
2. Ve a "Subir Documentos"
3. Selecciona un archivo PDF/TXT
4. Clickea "Subir"

---

## Paso 11: Probar el Chatbot

En http://localhost:3000:

1. Ve a "Chatbot"
2. Escribe una pregunta:
   - "¿Qué requisitos necesito para inscribir una propiedad?"
   - "¿Cuál es el costo del trámite?"
   - etc

El chatbot buscará en los documentos cargados y te dará una respuesta.

---

## Paso 12: Ver Logs y Debug

```bash
# Backend logs
docker-compose logs -f backend

# Frontend
# Abre Developer Tools en el navegador (F12)
# Ve a la pestaña "Console"

# Celery logs
docker-compose logs -f celery-worker

# Base de datos
docker-compose logs -f postgres
```

---

## ✅ Checklist

- [ ] Docker Compose levantado (`docker-compose ps`)
- [ ] Backend corriendo en http://localhost:8000
- [ ] Frontend accesible en http://localhost:3000
- [ ] BD inicializada con tablas
- [ ] Al menos un documento cargado
- [ ] Chat respondiendo preguntas

Si todo está ✅, **¡felicidades! PropQuery está listo para usar!**

---

## 🆘 Troubleshooting

### Error: "Connection refused" en backend

```bash
# Docker no está corriendo
docker-compose up -d

# Puerto 8000 ya en uso
lsof -i :8000
kill -9 <PID>
```

### Error: "GROQ_API_KEY not found"

```bash
# .env no existe o está mal
cp .env.example .env
# Editar .env con tu API key
```

### Error: "Module not found"

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Database connection failed"

```bash
# Esperar a que postgres se levante
docker-compose ps  # Ver si postgres está Up

# Si no, reiniciar
docker-compose down -v
docker-compose up -d
sleep 30
python scripts/init_db.py
```

### Error: "JavaScript bundle failed"

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## Próximos Pasos

Después de completar este quick start:

1. Lee [ARCHITECTURE.md](ARCHITECTURE.md) para entender la arquitectura
2. Explora [API.md](API.md) para la documentación de endpoints
3. Lee [DEV_GUIDE.md](DEV_GUIDE.md) para contribuir
4. Carga tus propios documentos y entrena el modelo
5. Personaliza el frontend con tu marca

---

## Soporte

- 📧 Issues: Crea un issue en GitHub
- 💬 Discussions: Usa GitHub Discussions
- 📚 Docs: Consulta la carpeta `/docs`

---

**¡Bienvenido a PropQuery!** 🎉
