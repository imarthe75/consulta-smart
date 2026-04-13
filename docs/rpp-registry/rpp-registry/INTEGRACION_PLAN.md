# Integración de Documentación RPP - ConsultaRPP

> **Descripción**: Cómo integrar la documentación de Registro Público (Puebla y Quintana Roo) en la aplicación  
> **Última actualización**: Abril 2026

## 📦 Estructura de Datos RPP

```
docs/rpp-registry/
├── INDEX.md                        ← Índice maestro
├── quintana-roo/
│   ├── LEGISLACION.md             ← Leyes y códigos
│   ├── PROCEDIMIENTOS.md          ← Procesos paso a paso
│   └── COSTOS_ARANCELES.md        ← Tarifas
└── puebla/
    ├── LEGISLACION.md              ← Leyes y códigos
    ├── PROCEDIMIENTOS.md           ← Procesos paso a paso
    └── COSTOS_ARANCELES.md         ← Tarifas
```

## 🔌 Integración en Backend

### 1. Crear servicio de busqueda RPP

```python
# backend/app/infrastructure/external/rpp_knowledge_service.py

from pathlib import Path
from typing import List, Dict, Optional
import json

class RPPKnowledgeService:
    """Servicio para acceder a documentación RPP"""
    
    def __init__(self):
        self.docs_path = Path("/home/ia/consulta-rpp/docs/rpp-registry")
        self.cache = {}
    
    def search_by_state(self, state: str, query: str) -> List[Dict]:
        """Buscar en documentación por estado"""
        # state: "quintana_roo" | "puebla"
        # Cargar índices y buscar
        pass
    
    def get_legislation(self, state: str) -> str:
        """Obtener legislación del estado"""
        path = self.docs_path / state / "LEGISLACION.md"
        return path.read_text()
    
    def get_procedures(self, state: str, procedure_type: str) -> str:
        """Obtener procedimientos específicos"""
        # procedure_type: "registration" | "usufruct" | "annotation"
        pass
    
    def get_costs(self, state: str) -> Dict:
        """Obtener aranceles y costos"""
        pass
    
    def search_keywords(self, keywords: List[str], state: Optional[str] = None) -> List[Dict]:
        """Búsqueda por palabras clave"""
        pass
```

### 2. Crear endpoints para consulta RPP

```python
# backend/app/routes/rpp.py

from fastapi import APIRouter, Query
from app.infrastructure.external.rpp_knowledge_service import RPPKnowledgeService

router = APIRouter(prefix="/api/v1/rpp", tags=["RPP"])
service = RPPKnowledgeService()

@router.get("/search")
async def search_rpp(
    query: str = Query(..., min_length=3),
    state: str = Query(None, regex="^(quintana_roo|puebla)$"),
    category: str = Query(None, regex="^(legislation|procedures|costs)$")
):
    """Buscar en documentación RPP"""
    results = service.search_by_state(state or "all", query)
    if category:
        results = [r for r in results if r.get("category") == category]
    return {"results": results, "total": len(results)}

@router.get("/states/{state}/legislation")
async def get_legislation(state: str):
    """Obtener legislación de estado específico"""
    return service.get_legislation(state)

@router.get("/states/{state}/procedures")
async def get_procedures(state: str, procedure: str = Query(None)):
    """Obtener procedimientos"""
    return service.get_procedures(state, procedure)

@router.get("/states/{state}/costs")
async def get_costs(state: str):
    """Obtener aranceles y costos"""
    return service.get_costs(state)

@router.get("/compare")
async def compare_states(
    criteria: str = Query("costs", regex="^(costs|procedures|time)$")
):
    """Comparar información entre estados"""
    qroo_data = service.get_data("quintana_roo", criteria)
    puebla_data = service.get_data("puebla", criteria)
    return {"quintana_roo": qroo_data, "puebla": puebla_data}
```

### 3. Memoria Vector para RPP

```python
# Agregar al conftest del backend

@pytest.fixture
async def rpp_vector_store(test_session):
    """Cargar documentación RPP en vector store"""
    from app.infrastructure.external.rpp_knowledge_service import RPPKnowledgeService
    
    service = RPPKnowledgeService()
    
    # Cargar documentos RPP
    rpp_docs = {
        "qroo_legislation": service.get_legislation("quintana_roo"),
        "qroo_procedures": service.get_procedures("quintana_roo", "all"),
        "qroo_costs": service.get_costs("quintana_roo"),
        "puebla_legislation": service.get_legislation("puebla"),
        "puebla_procedures": service.get_procedures("puebla", "all"),
        "puebla_costs": service.get_costs("puebla"),
    }
    
    # Embeddings y almacenamiento
    return rpp_docs
```

## 🎨 Integración en Frontend

### 1. Crear componente RPP Search

```jsx
// frontend/src/components/RPPSearch.jsx

export function RPPSearch() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState("quintana_roo");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/rpp/search?query=${query}&state=${state}`
      );
      const data = await response.json();
      setResults(data.results);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rpp-search">
      <h2>Consultar Registro Público</h2>
      
      <select value={state} onChange={(e) => setState(e.target.value)}>
        <option value="quintana_roo">Quintana Roo</option>
        <option value="puebla">Puebla</option>
      </select>
      
      <input
        type="text"
        placeholder="Buscar documentación..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      
      <button onClick={handleSearch} disabled={loading}>
        {loading ? "Buscando..." : "Buscar"}
      </button>
      
      <div className="results">
        {results.map((result) => (
          <ResultCard key={result.id} result={result} />
        ))}
      </div>
    </div>
  );
}
```

### 2. Crear página de Información RPP

```jsx
// frontend/src/pages/RPPInfo.jsx

export function RPPInfo() {
  return (
    <div className="rpp-info-page">
      <h1>Registro Público de la Propiedad</h1>
      
      <StateComparison />
      
      <RPPGuides />
      
      <FAQSection />
      
      <ContactsSection />
    </div>
  );
}
```

### 3. Componentes de tabla comparativa

```jsx
// frontend/src/components/StateComparison.jsx

export function StateComparison() {
  const [criteria, setCriteria] = useState("costs");
  const [comparison, setComparison] = useState(null);

  useEffect(() => {
    fetch(`/api/v1/rpp/compare?criteria=${criteria}`)
      .then(r => r.json())
      .then(setComparison);
  }, [criteria]);

  return (
    <div className="comparison">
      <div className="controls">
        <label>Comparar por:</label>
        <select value={criteria} onChange={(e) => setCriteria(e.target.value)}>
          <option value="costs">Costos</option>
          <option value="procedures">Procedimientos</option>
          <option value="time">Tiempo</option>
        </select>
      </div>
      
      <table>
        <thead>
          <tr>
            <th>Quintana Roo</th>
            <th>Puebla</th>
          </tr>
        </thead>
        <tbody>
          {/* Datos de comparación */}
        </tbody>
      </table>
    </div>
  );
}
```

## 🔗 Rutas de API Propuestas

### Búsqueda General
```
GET /api/v1/rpp/search?query=usufructo&state=quintana_roo&category=procedures
```

### Por Estado
```
GET /api/v1/rpp/states/quintana_roo/legislation
GET /api/v1/rpp/states/quintana_roo/procedures
GET /api/v1/rpp/states/quintana_roo/costs
```

### Comparativas
```
GET /api/v1/rpp/compare?criteria=costs
GET /api/v1/rpp/compare?criteria=procedures
```

### Información Específica
```
GET /api/v1/rpp/procedures/registration?state=quintana_roo
GET /api/v1/rpp/procedures/usufruct?state=puebla
GET /api/v1/rpp/procedures/annotation?state=quintana_roo
```

## 💾 Almacenamiento en BD

### Tabla: RPP_Documents
```sql
CREATE TABLE rpp_documents (
  id UUID PRIMARY KEY,
  state VARCHAR(20) -- 'quintana_roo' | 'puebla'
  category VARCHAR(50) -- 'legislation' | 'procedures' | 'costs'
  title VARCHAR(255),
  content TEXT,
  source_file VARCHAR(255),
  last_updated TIMESTAMP,
  search_index TSVECTOR
);

CREATE INDEX idx_rpp_state ON rpp_documents(state);
CREATE INDEX idx_rpp_category ON rpp_documents(category);
CREATE INDEX idx_rpp_search ON rpp_documents USING GIN(search_index);
```

### Tabla: RPP_Procedures
```sql
CREATE TABLE rpp_procedures (
  id UUID PRIMARY KEY,
  state VARCHAR(20),
  procedure_type VARCHAR(50), -- 'registration' | 'usufruct' | 'annotation'
  title VARCHAR(255),
  steps JSONB,
  requirements JSONB,
  timeline VARCHAR(50),
  cost_range VARCHAR(100),
  created_at TIMESTAMP
);
```

## 🤖 Integración con Chat

### Usar RPP docs en contexto de Chat

```python
# backend/app/application/usecases/chat_usecases.py

async def send_message_with_rpp_context(
    session_id: UUID,
    message: str,
    state: Optional[str] = None
):
    """Enviar mensaje con contexto RPP"""
    
    # 1. Buscar documentos RPP relevantes
    rpp_context = rpp_service.search_by_state(state or "all", message)
    
    # 2. Generar embedding de mensaje
    message_embedding = embed_service.embed(message)
    
    # 3. Buscar documentos del usuario
    user_docs = await document_repo.search(
        user_id=session.user_id,
        embedding=message_embedding
    )
    
    # 4. Combinar contexto (RPP + user docs)
    combined_context = rpp_context + user_docs
    
    # 5. Llamar LLM con contexto completo
    response = await llm_service.generate_response(
        message=message,
        context=combined_context,
        conversation_history=session.messages
    )
    
    return response
```

## 📊 Búsqueda Semántica RPP

### Embeddings para RPP documents

```python
# Cargar RPP docs al desplegar la aplicación

async def initialize_rpp_embeddings():
    """Generar embeddings para documentación RPP"""
    
    for state in ["quintana_roo", "puebla"]:
        for category in ["legislation", "procedures", "costs"]:
            doc = load_rpp_doc(state, category)
            chunks = chunk_document(doc)
            
            for chunk in chunks:
                embedding = await embed_service.embed(chunk.content)
                await vector_store.add(
                    content=chunk.content,
                    embedding=embedding,
                    metadata={
                        "state": state,
                        "category": category,
                        "source": "rpp_registry"
                    }
                )
```

## 🧪 Tests para RPP Integration

```python
# backend/tests/integration/test_rpp_integration.py

@pytest.mark.asyncio
class TestRPPIntegration:
    
    async def test_search_rpp_by_state(self, test_client, authenticated_user):
        """Test: Buscar documentación RPP por estado"""
        response = await test_client.get(
            "/api/v1/rpp/search?query=usufructo&state=quintana_roo",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
    
    async def test_get_rpp_legislation(self, test_client, authenticated_user):
        """Test: Obtener legislación RPP"""
        response = await test_client.get(
            "/api/v1/rpp/states/puebla/legislation",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 200
        assert "Código Civil" in response.text
    
    async def test_compare_rpp_states(self, test_client, authenticated_user):
        """Test: Comparar información entre estados"""
        response = await test_client.get(
            "/api/v1/rpp/compare?criteria=costs",
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "quintana_roo" in data
        assert "puebla" in data
    
    async def test_chat_with_rpp_context(self, test_client, authenticated_user):
        """Test: Chat que usa contexto RPP automáticamente"""
        response = await test_client.post(
            "/api/v1/chat/sessions/123/messages",
            json={"content": "¿Cómo registro una propiedad en QRoo?"},
            headers={"Authorization": f"Bearer {authenticated_user['token']}"}
        )
        assert response.status_code == 201
        # Response debe incluir referencias a RPP docs
        assert "QPública" in response.text or "registro" in response.text.lower()
```

## 📈 Roadmap de Integración

### Fase 1 (Completado)
✅ Documentación escrita (Legislación, Procedimientos, Costos)  
✅ Estructura de directorios  
✅ Índice maestro  

### Fase 2 (En Progreso)
⏳ Endpoints de API  
⏳ Componentes frontend  
⏳ Búsqueda semántica  

### Fase 3 (Planeado)
📋 Chat con contexto RPP  
📋 Comparativas entre estados  
📋 FAQ completamente integradas  

### Fase 4 (Futuro)
📋 Actualizaciones legislativas automáticas  
📋 Alertas de cambios de aranceles  
📋 Notificaciones de nuevas guías  

## 🎯 Objetivos de Integración

| Objetivo | Estado | Nota |
|----------|--------|------|
| Documentación compilada | ✅ | 6 archivos, 3000+ líneas |
| Búsqueda por estado | ⏳ | En backend |
| Comparación entre estados | ⏳ | Tabla interactiva |
| Chat con contexto RPP | ⏳ | Integración con LLM |
| API completa | ⏳ | 8+ endpoints |
| Frontend completo | ⏳ | React components |
| Tests integración | ⏳ | 5+ tests |

---

**Documentación lista para integración**: Abril 7, 2026  
**Próximo paso**: Crear endpoints API y componentes frontend

