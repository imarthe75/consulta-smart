# 🏗️ HEXAGONAL ARCHITECTURE - PropQuery

Documento que explica la arquitectura refactorizada con Hexagonal Architecture y los patrones de Everything Claude Code.

---

## 📐 Overview

**PropQuery** utiliza **Hexagonal Architecture** (también conocida como Ports & Adapters) reorganizada en 3 capas principales:

```
┌─────────────────────────────────────────────────────────┐
│           Presentation Layer (API Routes)              │
│    ↓ HTTP Requests  ↑ REST Responses                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │    Application Layer (Use Cases / Services)      │  │
│  │  ├─ DTOs (Data Transfer Objects)                 │  │
│  │  ├─ Use Cases (Business Logic)                   │  │
│  │  └─ Orquestación                                 │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↕                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │      Domain Layer (Entities & Rules)             │  │
│  │  ├─ Entities (User, Document, ChatSession)       │  │
│  │  ├─ Value Objects                                │  │
│  │  ├─ Domain Exceptions                            │  │
│  │  └─ Repository Interfaces (Abstracciones)        │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↕                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │   Infrastructure Layer (Implementations)         │  │
│  │  ├─ Repositories (PostgreSQL, SeaweedFS)        │  │
│  │  ├─ External Services (Groq, Gemini)            │  │
│  │  ├─ Vector Store (pgvector)                      │  │
│  │  └─ File Storage (SeaweedFS)                     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│          External Systems (Out of Process)             │
│  Database  │  Vector DB  │  Cloud APIs  │  File Store  │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 Estructura de Carpetas

```
backend/app/
│
├── domain/                    # ⭐ DOMINIO (Lógica Pura)
│   ├── entities/              # Entidades del negocio
│   │   ├── entity.py          # Base class
│   │   ├── user.py            # Usurios
│   │   ├── document.py        # Documentos
│   │   └── chat_session.py    # Sesiónes de chat
│   │
│   ├── interfaces/            # Abstracciones
│   │   └── repositories.py    # Repository pattern
│   │
│   └── exceptions/            # Excepciones de negocio
│       └── domain_exceptions.py
│
├── application/               # 🔄 LÓGICA DE APLICACIÓN
│   ├── dtos/                  # Data Transfer Objects
│   │   └── common_dtos.py
│   │
│   ├── usecases/              # Use Cases (Orquestación)
│   │   └── base.py
│   │
│   └── services/              # Servicios de aplicación
│       (a implementar)
│
├── infrastructure/            # 🔧 IMPLEMENTACIONES
│   ├── repositories/          # Implementaciones concretas
│   │   (PostgreSQL, etc)
│   │
│   └── external/              # Servicios externos
│       (Groq, Docling, etc)
│
├── core/
│   ├── config.py              # Configuración global
│   ├── response.py            # Envelope de respuestas API
│   └── logger.py              # Logging
│
├── routes/                    # 🌐 API ENDPOINTS
│   ├── documents.py
│   ├── chat.py
│   └── search.py
│
├── workers/                   # 📦 CELERY WORKERS
│   ├── tasks.py
│   └── celery_app.py
│
└── main.py                    # FastAPI app entry
```

---

## 🎯 Principios Clave

### 1. **Separation of Concerns**

```python
# ✅ BUENO: Cada capa tiene responsabilidad clara

# Domain Layer - Solo reglas de negocio
class Document(Entity):
    def mark_processing_started(self):
        self.status = DocumentStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()

# Application Layer - Orquestación
class ProcessDocumentUseCase(UseCase):
    async def execute(self, document_id: str):
        doc = await self.repo.find_by_id(document_id)
        doc.mark_processing_started()
        # ... más lógica

# Infrastructure Layer - Detalles técnicos
class PostgresDocumentRepository(DocumentRepository):
    async def update(self, entity: Document) -> Document:
        # SQL, ORM, detalles técnicos
        pass

# ❌ MALO: Todo mezclado
@app.post("/documents")
async def upload_document(file):
    # SQL aquí
    # LLM aquí
    # File storage aquí
    # Validación aquí
    return result
```

### 2. **Dependency Injection**

Usar constructor injection para desacoplamiento:

```python
# ✅ GOOD: Inyectar dependencias

class ProcessDocumentUseCase:
    def __init__(
        self,
        doc_repo: DocumentRepository,    # Interface, no concreción
        vector_store: VectorStore,
        file_storage: FileStorage,
        embedding_service: EmbeddingService
    ):
        self.doc_repo = doc_repo
        self.vector_store = vector_store
        self.file_storage = file_storage
        self.embedding_service = embedding_service  # Fácil de mockear


# ❌ BAD: Importar directamente
class ProcessDocumentUseCase:
    def __init__(self):
        self.doc_repo = PostgresDocumentRepository()  # Acoplado
        self.vector_store = PgVectorStore()           # Acoplado
```

### 3. **Repository Pattern**

Abstracción sobre acceso a datos:

```python
# Domain Layer: Interface
class DocumentRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Document]:
        pass
    
    @abstractmethod
    async def create(self, entity: Document) -> Document:
        pass


# Infrastructure Layer: Implementación
class PostgresDocumentRepository(DocumentRepository):
    async def find_by_id(self, id: str) -> Optional[Document]:
        # Detalles de PostgreSQL, ORM, etc.
        result = await self.session.query(DocumentModel).filter(...).first()
        return Document.from_orm(result)
```

**Beneficios**:
- ✅ Fácil de testear (mockear repositorios)
- ✅ Cambiar base de datos sin tocar lógica
- ✅ Múltiples implementaciones (DB, cache, archivo)

### 4. **API Response Envelope**

Respuestas consistentes:

```python
# ✅ STANDAR
{
  "status": "success",
  "data": { /* actual data */ },
  "error": null,
  "meta": {
    "timestamp": "2026-04-07T10:00:00",
    "version": "0.1.0",
    "request_id": "req_123abc"
  }
}

# ❌ INCONSISTENTE
{
  "document": {},
  "success": true
}

# ❌ DIFERENTE POR ENDPOINT
{
  "results": [],
  "status_code": 200
}
```

---

## 🏆 Ventajas de Hexagonal Architecture

| Aspecto | Beneficio |
|---------|-----------|
| **Testability** | Mock fácil de repositorios e interfaces |
| **Flexibility** | Cambiar implementación sin afectar lógica |
| **Scalability** | Fácil agregar nuevas features |
| **Maintainability** | Código organizado y predecible |
| **Reusability** | Use cases reutilizables |

---

## 🔄 Flujo de una Request

```
1. HTTP Request
   ↓
2. API Route Handler (routes/documents.py)
   └─ Parsea request, valida auth
   ↓
3. Use Case Execution (application/usecases/*)
   └─ Orquesta la lógica de negocio
   ├─ Carga entidades del repo
   ├─ Aplica reglas de dominio
   ├─ Coordina servicios externos
   └─ Actualiza repositorios
   ↓
4. Domain Logic (domain/entities/*)
   └─ Valida reglas de negocio
   ├─ Can delete? Status check
   ├─ Mark as updated
   └─ Raise exceptions si hay problemas
   ↓
5. Repository Access (infrastructure/repositories)
   └─ Accede a datos
   ├─ SQL queries
   ├─ Transactions
   └─ Error handling
   ↓
6. Response Envelope (core/response.py)
   └─ Formatea respuesta standard
   ↓
7. HTTP Response
```

---

## 🧠 Testing Benefits

```python
# Testear use case SIN base de datos

@pytest.mark.asyncio
async def test_process_document():
    # Mock repositories
    doc_repo = AsyncMock(spec=DocumentRepository)
    vector_store = AsyncMock(spec=VectorStore)
    file_storage = AsyncMock(spec=FileStorage)
    
    # Setup mocks
    doc = Document(title="Test", ...)
    doc_repo.find_by_id.return_value = doc
    
    # Create use case
    usecase = ProcessDocumentUseCase(
        doc_repo=doc_repo,
        vector_store=vector_store,
        file_storage=file_storage,
        ...
    )
    
    # Execute
    await usecase.execute(document_id="doc_123")
    
    # Verify
    doc_repo.find_by_id.assert_called_once_with("doc_123")
    doc_repo.update.assert_called_once()
    vector_store.add.assert_called()
    
    # ✅ Test pasó sin BD!
```

---

## 🛠️ Implementation Notes

### DTOs vs Entidades

```python
# Domain Entity - Reglas de negocio
class Document(Entity):
    def mark_processing_completed(self, chunks: int, tokens: int):
        if self.status != DocumentStatus.PROCESSING:
            raise InvalidOperation("Can't mark as complete")
        self.chunk_count = chunks
        self.token_count = tokens
        self.mark_as_updated()


# Application DTO - Transfer entre capas
class DocumentResponseDTO(BaseModel):
    id: str
    title: str
    status: str
    chunk_count: int
    token_count: int
    
    @staticmethod
    def from_entity(doc: Document) -> 'DocumentResponseDTO':
        return DocumentResponseDTO(
            id=doc.id,
            title=doc.title,
            status=doc.status.value,
            chunk_count=doc.chunk_count,
            token_count=doc.token_count
        )
```

### Use Case Template

```python
class SampleUseCase(UseCase):
    def __init__(self, repo: Repository, service: Service):
        self.repo = repo
        self.service = service
    
    async def execute(self, input_id: str, **kwargs):
        # 1. Validate input
        if not input_id:
            raise InvalidEntity("Input", "ID required")
        
        # 2. Load entities
        entity = await self.repo.find_by_id(input_id)
        if not entity:
            raise EntityNotFound("Entity", input_id)
        
        # 3. Apply business logic
        entity.do_something()
        
        # 4. Call external services if needed
        result = await self.service.process(entity)
        
        # 5. Update and persist
        updated = await self.repo.update(entity)
        
        # 6. Return DTO
        return SampleResponseDTO.from_entity(updated)
```

---

## 🎓 Comparativa: Antes vs Después

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Estructura** | Flat (services + routes) | Hexagonal (domain → app → infra) |
| **Testing** | Difícil (acoplado a DB) | Fácil (mock interfaces) |
| **DB Changes** | Impacta todo | Solo importa en infrastructure |
| **Reusability** | Limitada (hardcoded) | Alta (injección de dependencias) |
| **Mantenibilidad** | Difícil (todo mezclado) | Fácil (responsabilidades claras) |
| **Escalabilidad** | Baja (monolítico) | Alta (componentes independientes) |

---

## 📚 Referencias Externas

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture - Robert Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Dependency Injection - Python](https://docs.python.org/3/library/typing.html)

---

## 🚀 Próximos Pasos

1. ✅ Estructura base creada (Opción A completada)
2. ⏳ Implementar repositorios concretos (PostgreSQL)
3. ⏳ Implementar servicios externos (Groq, Docling, etc)
4. ⏳ Crear API routes que usen use cases
5. ⏳ Integrar Celery para async tasks
6. ⏳ Escribir tests completos
7. ⏳ Deployment con Docker

---

**Versión**: 0.1.0  
**Última actualización**: 07 de Abril, 2026  
**Mantenedor**: [Tu Nombre/Equipo]  
**Status**: 🟡 En Implementación
