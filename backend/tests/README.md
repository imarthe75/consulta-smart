# Backend Tests - Guía de Ejecución

## 📋 Descripción General

Este directorio contiene la suite completa de tests para el backend de ConsultaRPP:
- ✅ Tests unitarios (configuration, database, repositories, services, usecases, routes)
- ✅ Tests de integración (API endpoints, workflows)
- ✅ Tests de message queue (Celery tasks)
- ✅ Tests de performance

**Total: 250+ tests en 8 archivos**

---

## 🚀 Instalación de Dependencias

```bash
# Instalar pytest y extensiones
pip install pytest
pip install pytest-asyncio
pip install pytest-cov
pip install pytest-xdist  # para ejecución paralela
pip install pytest-timeout  # para tests largos

# En requirements.txt ya están incluidos
cd backend
pip install -r requirements.txt
```

---

## ▶️ Ejecución de Tests

### 1️⃣ Ejecutar TODOS los tests
```bash
pytest tests/
```

### 2️⃣ Ejecutar por categoría

#### Tests Unitarios
```bash
pytest tests/ -m unit
# Ejecuta: config, database, repositories, services, usecases, routes
# ~140 tests
```

#### Tests de Integración
```bash
pytest tests/ -m integration
# Ejecuta: API endpoints, workflows
# ~70 tests
```

#### Tests de Performance
```bash
pytest tests/ -m performance
# Ejecuta: response times, throughput, load
# ~40 tests
# ⚠️ Pueden ser lentos
```

### 3️⃣ Ejecutar archivo específico
```bash
# Tests de configuración
pytest tests/test_config.py

# Tests de base de datos
pytest tests/test_database.py

# Tests de repositorios
pytest tests/test_repositories.py

# Tests de servicios
pytest tests/test_services.py

# Tests de use cases
pytest tests/test_usecases.py

# Tests de rutas
pytest tests/test_routes.py

# Tests de integración API
pytest tests/test_api_integration.py

# Tests de Celery/queue
pytest tests/test_message_queue.py

# Tests de performance
pytest tests/test_performance.py
```

### 4️⃣ Ejecución con opciones útiles

#### Ver output detallado
```bash
pytest tests/ -v
# -v: verbose
# -vv: extra verbose
# -vvv: muy detallado
```

#### Mostrar prints/logs
```bash
pytest tests/ -s
# Muestra todos los print() y logs
```

#### Ejecutar en paralelo (más rápido)
```bash
pytest tests/ -n auto
# Requiere: pip install pytest-xdist
```

#### Detener en primer fallo
```bash
pytest tests/ -x
# -x: detiene en primer fallo
# --maxfail=3: detiene después de 3 fallos
```

#### Ejecutar tests específicos
```bash
# Por nombre
pytest tests/ -k "test_upload"

# Por marker
pytest tests/ -m "unit and async"

# Por archivo y clase
pytest tests/test_config.py::TestSettings
pytest tests/test_config.py::TestSettings::test_settings_initialization
```

---

## 📊 Reportes de Cobertura

### Generar reporte de cobertura
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Opciones útiles:
# --cov-report=html      → genera HTML en htmlcov/
# --cov-report=term      → muestra en terminal
# --cov-report=xml       → para CI/CD
# --cov-threshold=80     → requiere 80% cobertura
```

### Ver reporte HTML
```bash
# Genera carpeta htmlcov/
pytest tests/ --cov=app --cov-report=html

# Abre en navegador
open htmlcov/index.html  # macOS
# o
firefox htmlcov/index.html  # Linux
```

---

## 🐛 Debugging Tests

### Ejecutar con debugger
```bash
pytest tests/ --pdb
# Se abre debugger en primer fallo
```

### Ver stack trace completo
```bash
pytest tests/ --tb=long
# Opciones: short, long, native, line
```

### Tests específicos en debug
```bash
pytest tests/test_config.py::TestSettings::test_settings_initialization -vvs --tb=long
```

---

## ⚙️ Configuración de Pytest

Archivo: `pytest.ini` (en raíz del proyecto backend)

```ini
[pytest]
# Markers
markers =
    unit: tests unitarios
    integration: tests de integración
    performance: tests de performance
    async: tests asincronos
    slow: tests lentos
    smoke: verificaciones básicas

# Opciones por defecto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Timeout para tests (en segundos)
timeout = 30

# Salida de logs
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(message)s
```

---

## 🔄 Fixtures Disponibles (conftest.py)

### Fixtures de Base de Datos
```python
@pytest.fixture
async def async_session():
    """Sesión SQLAlchemy en-memoria para tests"""
    
@pytest.fixture
def test_user_data():
    """Datos de usuario de prueba"""
    
@pytest.fixture
def test_document_data():
    """Datos de documento de prueba"""
```

### Fixtures de Mock
```python
@pytest.fixture
def mock_llm_response():
    """Mock de respuesta LLM"""
    
@pytest.fixture  
def mock_embeddings():
    """Mock de embeddings (1536 dimensiones)"""
```

### Usarlas en un test
```python
async def test_ejemplo(async_session, test_user_data, mock_llm_response):
    # Tu test aquí
    pass
```

---

## ✅ Checklist Pre-Commit

Antes de hacer commit, ejecutar:

```bash
# 1. Tests básicos
pytest tests/ -x

# 2. Cobertura mínima
pytest tests/ --cov=app --cov-threshold=80 -q

# 3. Verificar formatos
pytest tests/ -v

# 4. Tests de performance (opcional, lentos)
pytest tests/ -m "performance or slow"
```

---

## 📈 Targets de Cobertura

**Mínimos aceptables:**
- Backend global: >80%
- Core (config, logging): 100%
- Repositories: >90%
- Services: >85%
- Routes: >80%
- Usecases: >95%

**Ver estado actual:**
```bash
pytest tests/ --cov=app --cov-report=term-missing | grep TOTAL
```

---

## 🐳 Tests en Docker

Si usas docker-compose para el backend:

```bash
# Ejecutar tests dentro del contenedor
docker-compose exec backend pytest tests/

# Con cobertura
docker-compose exec backend pytest tests/ --cov=app --cov-report=term

# Con output detallado
docker-compose exec backend pytest tests/ -vvs
```

---

## 📝 Patrones Comunes

### Testing async functions
```python
@pytest.mark.asyncio
async def test_async_operation(async_session):
    result = await some_async_function()
    assert result is not None
```

### Mocking servicios externos
```python
@patch('app.external.llm_service.LLMService.generate')
def test_with_mock(mock_generate):
    mock_generate.return_value = {"response": "test"}
    # tu test aquí
```

### Fixtures parametrizadas
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiply(input, expected):
    assert input * 2 == expected
```

---

## 🔍 Troubleshooting

### "No tests collected"
```bash
# Verificar estructura
pytest tests/ --collect-only

# Verificar nombres
# Archivos deben ser: test_*.py
# Funciones deben ser: test_*
# Clases deben ser: Test*
```

### Tests async no funcionan
```bash
# Instalar pytest-asyncio
pip install pytest-asyncio

# Marcar tests con @pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async():
    pass
```

### Imports fallando
```bash
# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"

# Desde carpeta backend:
cd backend
pytest tests/
```

### Database locked
```bash
# Si SQLite se traba
rm -f test_db.sqlite
pytest tests/

# Para PostrgreSQL, usar transacciones en tests
```

---

## 📚 Referencias

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [Coverage.py](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)

---

## ✨ Próximos Pasos

1. ✅ Backend tests completos (250+ tests)
2. ⏳ Frontend tests (components, stores, services)
3. ⏳ E2E tests con Cypress
4. ⏳ Performance audit completo  
5. ⏳ Security audit (OWASP)

**Estado Overall**: Phase 4B - 100% Backend Complete → Frontend tests en progreso
