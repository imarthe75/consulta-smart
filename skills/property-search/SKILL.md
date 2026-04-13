---
name: "Property Search & Semantic Query"
version: 1.0
domain: "search"
difficulty: "medium"
applies_to: ["python", "typescript"]
tags: ["pgvector", "rag", "semantic-search"]
---

# Skill: Property Search & Semantic Query

## 📋 Descripción General

Implementar búsqueda semántica en documentos legales usando embeddings vectoriales.

## 🎯 Objetivo

Cuando usuario pregunta: *"¿Qué requisitos necesito para inscribir una propiedad?"*

Sistema debe:
1. ✅ Convertir pregunta a vector
2. ✅ Buscar en pgvector
3. ✅ Retornar top-10 chunks relevantes
4. ✅ Filtrar por relevancia (threshold)
5. ✅ Retornar con metadatos (documento, fecha, etc)

## 🏗️ Arquitectura

```
"¿Requisitos inscripción?"
        ↓
   [Embedding] → vector(1536)
        ↓
[pgvector Search] → similarity search
        ↓
[Filter] → score > 0.7
        ↓
[Rank] → top-10
        ↓
[Enrich] → add metadata
        ↓
Return Results
```

## 💻 Implementación

### Backend: Search Service

```python
# backend/app/infrastructure/repositories/vector_store.py

from pgvector.sqlalchemy import Vector
from sqlalchemy import func

class PostgresVectorStore(VectorStore):
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        threshold: float = 0.7
    ) -> List[dict]:
        """
        Buscar embeddings similares en pgvector
        
        Using cosine similarity: 1 - (a · b) / (|a| |b|)
        Higher score = more similar
        """
        query_vector = Vector(query_embedding)
        
        # SQLAlchemy query with pgvector
        results = session.query(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.text,
            DocumentChunk.metadata,
            # Cosine distance (lower = more similar)
            DocumentChunk.embedding.cosine_distance(query_vector).label('distance')
        ).filter(
            # Cosine distance < (1 - threshold)
            DocumentChunk.embedding.cosine_distance(query_vector) < (1 - threshold)
        ).order_by(
            'distance'
        ).limit(top_k).all()
        
        # Convert distance to similarity score (0-1)
        return [
            {
                'chunk_id': r.id,
                'document_id': r.document_id,
                'text': r.text,
                'score': 1 - r.distance,  # Convert to similarity
                'metadata': r.metadata
            }
            for r in results
        ]


# backend/app/application/usecases/search_documents.py

class SearchDocumentsUseCase(UseCase):
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        doc_repo: DocumentRepository
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.doc_repo = doc_repo
    
    async def execute(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        category: Optional[str] = None
    ) -> List[dict]:
        # 1. Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # 2. Search in vector store
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            threshold=threshold
        )
        
        # 3. Filter by category if specified
        if category:
            results = [r for r in results if r['metadata'].get('category') == category]
        
        # 4. Enrich with document info
        for result in results:
            doc = await self.doc_repo.find_by_id(result['document_id'])
            result['document_title'] = doc.title
            result['document_category'] = doc.category.value
        
        return results


# backend/app/routes/search.py

@router.post("/api/v1/search")
async def search(
    query: SearchQueryDTO,
    current_user: User = Depends(get_current_user),
    usecase: SearchDocumentsUseCase = Depends(get_search_usecase)
) -> APIResponse:
    """Search for relevant documents"""
    try:
        results = await usecase.execute(
            query=query.query,
            top_k=query.top_k,
            threshold=query.threshold,
            category=query.category
        )
        
        return APIResponse.success(
            data={
                'results': results,
                'query': query.query,
                'count': len(results)
            },
            meta={'latency_ms': latency}
        )
    except Exception as e:
        return APIResponse.error(str(e))
```

### Frontend: Search Component

```typescript
// frontend/src/components/Search/SearchBar.tsx

import React, { useState } from 'react';
import * as api from '../../services/api';

export const SearchBar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await api.searchDocuments({
        query,
        top_k: 10,
        threshold: 0.7
      });
      
      setResults(response.data.results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="search-container">
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar en documentos..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Buscando...' : 'Buscar'}
        </button>
      </form>
      
      <div className="results">
        {results.map((result) => (
          <div key={result.chunk_id} className="result-card">
            <h3>{result.document_title}</h3>
            <p>{result.text.substring(0, 200)}...</p>
            <span className="score">
              Relevancia: {(result.score * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 📊 SQL Schema

```sql
-- Document chunks with embeddings
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id),
    chunk_number INT,
    text TEXT NOT NULL,
    embedding vector(1536),  -- pgvector type
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for fast similarity search
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

## 🔍 Similarity Metrics

| Métrica | Rango | Uso |
|---------|-------|-----|
| **Cosine** | [0, 1] | Default (más rápido) |
| **Euclidean** | [0, ∞] | Distancia L2 |
| **Manhattan** | [0, ∞] | Distancia L1 |

PropQuery usa **cosine** por ser faster y mejor para textos.

## 🎯 Best Practices

1. **Threshold calibration**: Ajustar threshold (0.7) según datos
2. **Batch indexing**: Crear índices IVFFLAT en chunks grandes
3. **Query optimization**: Usar EXPLAIN para ver query plans
4. **Caching**: Cache frecuentes búsquedas en Valkey
5. **Monitoring**: Medir latencia de search

## 🧪 Testing

```python
# backend/tests/usecases/test_search.py

@pytest.mark.asyncio
async def test_search_returns_relevant_documents():
    # Create test data
    embeddings = [[0.1, 0.2, ...], [0.15, 0.25, ...]]
    
    # Mock vector store
    vector_store = AsyncMock(spec=VectorStore)
    vector_store.search.return_value = [
        {'score': 0.95, 'text': '...'},
        {'score': 0.87, 'text': '...'}
    ]
    
    # Execute
    usecase = SearchDocumentsUseCase(vector_store, ...)
    results = await usecase.execute('requisitos', top_k=10)
    
    # Verify
    assert len(results) == 2
    assert results[0]['score'] > results[1]['score']
```

## 📚 Referencias

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [SQLAlchemy Vector](https://github.com/pgvector/pgvector-python)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)

---

**Version**: 1.0  
**Updated**: 2026-04-07  
**Status**: ✅ Ready for Implementation
