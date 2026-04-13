# 🏛️ ARCHITECTURE - PropQuery

Documento técnico que describe la arquitectura, flujo de datos y decisiones de diseño.

---

## 📐 Arquitectura General

```
┌──────────────────────────────────────────────────────────────────┐
│                        PRESENTACIÓN (Frontend)                    │
│                       React 19 + Tailwind                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Chat View    │    │ Upload View  │    │ Search View  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                   │
└────────────────────────┬─────────────────────────────────────────┘
                         │ REST API / WebSocket
                         │ JSON payloads
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LÓGICA (Backend)                               │
│                    FastAPI / Python                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API Routes (FastAPI)                         │   │
│  │  /api/v1/documents/*                                      │   │
│  │  /api/v1/chat/*                                           │   │
│  │  /api/v1/search/*                                         │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│  ┌────────────────────┴────────────────────────┬──────────────┐ │
│  ▼                                             ▼               ▼ │
│ ┌──────────────┐  ┌──────────────────┐  ┌─────────────────┐   │ │
│ │ Document     │  │ Chat Handler     │  │ Vector Search   │   │ │
│ │ Processor    │  │ (LangGraph)      │  │                 │   │ │
│ │              │  │                  │  │                 │   │ │
│ │ - Parse PDF  │  │ - Context Build  │  │ - pgvector      │   │ │
│ │ - Extract    │  │ - LLM Routing    │  │ - Semantic      │   │ │
│ │   Text       │  │ - Response Gen   │  │   Search        │   │ │
│ └──────────────┘  └──────────────────┘  └─────────────────┘   │ │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           External LLM Services (Groq/Gemini)            │   │
│  │  - Text Embeddings                                        │   │
│  │  - Chat Completion                                        │   │
│  │  - Vision Analysis                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└────────────────────────┬─────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐  ┌──────────┐  ┌──────────────────┐
    │PostgreSQL│  │ Valkey   │  │ SeaweedFS        │
    │+ pgvector│  │ (Redis)  │  │ (S3 Compatible)  │
    │          │  │          │  │                  │
    │- Chat DB │  │- Cache   │  │- Document Store  │
    │- Users   │  │- Sessions│  │- File metadata   │
    │- Docs    │  │-Embeddings│  │                 │
    │- Vectors │  │          │  │                  │
    └─────────┘  └──────────┘  └──────────────────┘
```

---

## 🔄 Flujo de Datos

### 1. Carga de Documentos

```
User Upload (Frontend)
    ↓
    │ POST /api/v1/documents/upload
    │ (file, category, title, description)
    ↓
API Endpoint (Backend)
    ↓
Validate & Store Temporally
    ↓
Queue Celery Task ("process_document")
    ↓
Return Job ID to Frontend
    ↓ (user can check status)
    │ GET /api/v1/documents/{doc_id}/status
    ↓
Celery Worker (Async):
    │
    ├─ 1. Download from Temp Storage
    │
    ├─ 2. Parse with Docling
    │       - Extract text
    │       - Extract images
    │       - Preserve structure
    │
    ├─ 3. Chunk Text
    │       - Split into semantic chunks
    │       - Preserve hierarchy
    │
    ├─ 4. Generate Embeddings (Groq/Gemini)
    │       - Call LLM API
    │       - Get vector representation
    │
    ├─ 5. Store in pgvector
    │       - Insert vectors into DB
    │       - Index for fast search
    │
    ├─ 6. Store File in SeaweedFS
    │       - Upload original file
    │       - Get file ID/reference
    │
    ├─ 7. Update Document Metadata
    │       - Status: "completed"
    │       - Num chunks, tokens, etc
    │
    └─ 8. Notify Frontend (WebSocket)
         - Update UI with completion
```

### 2. Chat / Consulta

```
User Query (Frontend)
    ↓
    │ POST /api/v1/chat
    │ {
    │   "message": "¿Qué requisitos...?",
    │   "session_id": "sess_xyz",
    │   "context": [previous messages]
    │ }
    ↓
API Endpoint (Backend)
    ↓
Extract/Validate Query
    ↓
Load Session from Valkey
    │ (if exists, get conversation history)
    ↓
LangGraph Router:
    │
    ├─ Step 1: Understand Intent
    │           "query" / "extraction" / "calculation"
    │
    ├─ Step 2: Generate Query Embedding (Groq/Gemini)
    │           Convert query to vector
    │
    ├─ Step 3: Vector Search in pgvector
    │           - Find top-K similar chunks
    │           - Get relevance scores
    │           - Score > THRESHOLD?
    │
    ├─ Step 4: Build Context Window
    │           {
    │             "query": "original query",
    │             "context": [top chunks],
    │             "history": [last 5 messages],
    │             "metadata": {document info}
    │           }
    │
    ├─ Step 5: Call LLM (Groq/Gemini/OpenAI)
    │           - Send context + query
    │           - Set Temperature, Max Tokens
    │           - Wait for response
    │
    ├─ Step 6: Post-Process Response
    │           - Extract entities (requirements, dates, costs)
    │           - Format for frontend
    │           - Highlight sources
    │
    ├─ Step 7: Store in Session (Valkey)
    │           - Update conversation history
    │           - Cache response (TTL)
    │
    └─ Step 8: Return to Frontend
         {
           "response": "Para inscribir...",
           "sources": [doc_id_1, doc_id_2],
           "session_id": "sess_xyz",
           "timestamp": "2026-04-07T..."
         }
    ↓
Frontend:
    │ Display response
    │ Highlight sources
    │ Allow follow-up questions
    ↓
User sees formatted answer
```

---

## 🏛️ Componentes Clave

### Backend Architecture

```python
# backend/app/

├── main.py
│   └─ FastAPI app initialization
│      - Route registration
│      - Middleware setup
│      - Error handlers
│
├── core/
│   ├─ config.py          # Configuración global
│   ├─ logger.py          # Logging setup
│   ├─ security.py        # Auth/JWT
│   └─ constants.py       # Constantes
│
├── services/
│   ├─ llm_service.py     # Groq/Gemini integration
│   ├─ docling_service.py # OCR/Parsing
│   ├─ embedding_service.py # Vector generation
│   ├─ seaweedfs_service.py # File storage
│   └─ vector_store.py    # pgvector operations
│
├── routes/
│   ├─ documents.py       # /api/v1/documents/*
│   ├─ chat.py           # /api/v1/chat/*
│   ├─ search.py         # /api/v1/search/*
│   ├─ health.py         # /health
│   └─ admin.py          # /api/v1/admin/*
│
├── workers/
│   ├─ celery_app.py      # Celery config
│   ├─ tasks.py           # Async tasks
│   └─ beat_schedule.py   # Periodic tasks
│
├── models/
│   ├─ user.py
│   ├─ document.py
│   ├─ chat_message.py
│   └─ vector_embedding.py
│
└── schemas/
    ├─ document.py       # Pydantic models
    ├─ chat.py
    ├─ search.py
    └─ ...
```

### Frontend Architecture

```javascript
// frontend/src/

├── App.jsx              # Main component
│
├── components/
│   ├─ Layout.jsx
│   ├─ ChatInterface/
│   │  ├─ ChatView.jsx
│   │  ├─ MessageList.jsx
│   │  ├─ InputBox.jsx
│   │  └─ SourcesTooltip.jsx
│   │
│   ├─ DocumentUpload/
│   │  ├─ UploadZone.jsx
│   │  ├─ FilePreview.jsx
│   │  └─ UploadProgress.jsx
│   │
│   ├─ Search/
│   │  ├─ SearchBar.jsx
│   │  └─ ResultsList.jsx
│   │
│   └─ Common/
│      ├─ Header.jsx
│      ├─ Sidebar.jsx
│      └─ Footer.jsx
│
├── pages/
│   ├─ ChatPage.jsx
│   ├─ UploadPage.jsx
│   ├─ SearchPage.jsx
│   ├─ AdminPage.jsx
│   └─ NotFound.jsx
│
├── services/
│   ├─ api.js           # Axios client
│   ├─ chatService.js   # Chat API calls
│   ├─ documentService.js # Document API calls
│   └─ searchService.js # Search API calls
│
├── hooks/
│   ├─ useChat.js       # Chat logic
│   ├─ useUpload.js     # Upload logic
│   └─ useAuth.js       # Auth logic
│
└── styles/
    ├─ global.css       # Global styles
    ├─ tailwind.config.js
    └─ components.css
```

---

## 🗄️ Base de Datos

### Schema PostgreSQL

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE,
    username VARCHAR UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    title VARCHAR NOT NULL,
    category VARCHAR,
    file_type VARCHAR,    -- pdf, txt, docx, etc
    seaweedfs_file_id VARCHAR,  -- reference in SeaweedFS
    user_id UUID REFERENCES users(id),
    status VARCHAR,       -- processing, completed, failed
    chunk_count INT,
    token_count INT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Document Chunks (for embeddings)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    chunk_number INT,
    text TEXT,
    embedding vector(1536),  -- pgvector dimension
    metadata JSONB,          -- extra info
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat Sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Chat Messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id),
    role VARCHAR,     -- 'user' | 'assistant'
    content TEXT,
    sources JSONB,    -- referenced documents
    tokens_used INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Search History
CREATE TABLE search_history (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    query TEXT,
    results_count INT,
    response_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_messages_session_id ON chat_messages(session_id);
```

---

## 🔄 Flujo de Procesamiento (Detallado)

### Documento: entrada → almacenamiento

```
┌─────────────────┐
│  PDF/Documento  │
└────────┬────────┘
         │
         ▼
    ┌─────────────────────────┐
    │ 1. INGESTA (Frontend)   │
    │ - Validar tamaño        │
    │ - Validar tipo          │
    │ - Enviar upload         │
    └────────┬────────────────┘
             │
             ▼
    ┌─────────────────────────────────┐
    │ 2. API ENDPOINT (Backend)       │
    │ - Recibir archivo               │
    │ - Validar metadatos             │
    │ - Guardar temporalmente         │
    │ - Crear registro en DB          │
    └────────┬────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────┐
    │ 3. QUEUE ASYNC TASK (Celery)   │
    │ - Enviar documento_id           │
    │ - Enqueue en Redis              │
    │ - Return job_id a frontend      │
    └────────┬────────────────────────┘
             │  (User can poll status)
             │
             ▼
    ┌──────────────────────────────────────┐
    │ 4. WORKER PROCESS (Celery Worker)   │
    │                                      │
    │ a) PARSING (Docling)                │
    │    - Detectar layout               │
    │    - Extraer texto                 │
    │    - Preservar estructura          │
    │    - Detectar tablas, imágenes     │
    │                                    │
    │ b) CLEANING                        │
    │    - Normalizar espacios           │
    │    - Corregir encoding             │
    │    - Remover Duplicados            │
    │                                    │
    │ c) CHUNKING                        │
    │    - Split por semántica           │
    │    - Overlap entre chunks          │
    │    - Preservar contexto            │
    │                                    │
    │ d) EMBEDDINGS (Groq/Gemini API)    │
    │    - Call LLM untuk cada chunk     │
    │    - Get vector representation     │
    │    - Rate limiting                │
    │                                    │
    │ e) STORAGE                         │
    │    - Store vectors en pgvector    │
    │    - Store file en SeaweedFS      │
    │    - Update metadata              │
    │                                    │
    │ f) INDEXING                        │
    │    - Create ivfflat index         │
    │    - Optimize para búsqueda       │
    │                                    │
    │ g) NOTIFICATION                    │
    │    - Update status en DB          │
    │    - Notify frontend (WebSocket)  │
    └──────────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────┐
    │  Document Ready for RAG │
    │  - Vectors in DB        │
    │  - File in SeaweedFS    │
    │  - Status: completed    │
    └─────────────────────────┘
```

---

## 🤖 LLM Integration Points

### 1. Embedding Generation
```python
# Convertir texto en vector

client = Groq(api_key=GROQ_API_KEY)
embedding = client.embeddings.create(
    model="nomic-embed-text-1.5",
    input=text_chunk,
    encoding_format="float"
)
# Returns: vector(1536)
```

### 2. Chat Completion
```python
# Generar respuesta

response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context + query}
    ],
    temperature=0.7,
    max_tokens=1024
)
# Returns: response text
```

### 3. Provider Switching
```python
# Groovy fallback hierarchy

if LLM_PROVIDER == "groq":
    client = Groq()
elif LLM_PROVIDER == "gemini":
    client = Anthropic()  # or Google client
elif LLM_PROVIDER == "openai":
    client = OpenAI()
```

---

## 🔐 Seguridad

### Capas de Seguridad

```
┌──────────────────────────────────┐
│ 1. Frontend (CORS)               │
│    - Only allow trusted origins  │
│    - No credentials on URL       │
└──────────────────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 2. API Gateway (Rate Limit)      │
│    - Limit requests/minute       │
│    - IP-based throttling         │
└──────────────────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 3. Authentication (JWT)          │
│    - Validate token              │
│    - Check expiration            │
│    - Verify signature            │
└──────────────────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 4. Authorization                 │
│    - Check user permissions      │
│    - Validate resource owner     │
└──────────────────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 5. Data Encryption (TLS)         │
│    - HTTPS only                  │
│    - Encrypted at rest           │
└──────────────────────────────────┘
             ↓
┌──────────────────────────────────┐
│ 6. API Key Management            │
│    - Keys from environment       │
│    - Rotate regularly            │
│    - Never hardcode              │
└──────────────────────────────────┘
```

---

## 🎯 Decisiones de Diseño

### ¿Por qué Groq?
- ✅ Gratis (beta)
- ✅ Rápido (latencia baja)
- ✅ Modelos open-source (Llama, Mixtral)
- ✅ Bueno para producción local

### ¿Por qué SeaweedFS?
- ✅ S3-compatible (fácil migración)
- ✅ Open source
- ✅ Sin vendor lock-in
- ✅ Escalable y distribuido
- ✅ Mejor que MinIO para documentos históricos

### ¿Por qué pgvector?
- ✅ Integrado en PostgreSQL
- ✅ No requiere DB separado
- ✅ Searchfácil y rápido
- ✅ ACID compliance
- ✅ Backups simplificados

### ¿Por qué LangGraph?
- ✅ Composable workflows
- ✅ Checkpointing automático
- ✅ Debugging facilitado
- ✅ Fácil de extender

---

## 📊 Métricas de Rendimiento

```
Objetivo de SLA:
- Upload: < 500ms
- Embedding generation: < 2s por documento
- Vector search: < 100ms para top-10
- Chat response: < 3s (incluye LLM latency)
- Concurrent users: 100+
- Documentos soportados: 10,000+
- Storage: 1TB+ en SeaweedFS
```

---

**Versión**: 0.1.0  
**Última actualización**: 07 de abril, 2026  
**Mantenedor**: [Tu Nombre]
