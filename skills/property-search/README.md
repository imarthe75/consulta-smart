# Property Search & Semantic Query Skill

## Overview

Implementación de búsqueda semántica en base de datos vectorial para encontrar documentos relevantes.

## Folder Structure

```
property-search/
├── SKILL.md              # Documentación completa
├── README.md             # Este archivo
├── examples/             # Ejemplos de búsquedas
│   ├── legal_queries.json
│   └── sample_results.json
├── tests/                # Tests de búsqueda
│   ├── test_vector_search.py
│   └── test_ranking.py
└── reference/            # Referencias técnicas
    ├── pgvector_ops.md
    └── similarity_metrics.md
```

## Key Components

### 1. **Vector Indexing**
- Almacena embeddings en pgvector
- Crea índices IVFFLAT para búsquedas rápidas
- Soporta múltiples operadores de similaridad

### 2. **Query Processing**
- Convierte queries a embeddings
- Aplica filtros y técnicas de ranking
- Maneja paginación

### 3. **Result Ranking**
- Asigna scores basados en similaridad
- Filtra por threshold configurables
- Retorna metadatos relevantes

### 4. **Caching**
- Cache en Valkey para queries populares
- Invalida cache cuando documentos se actualizan

## Implementation Checklist

- [ ] Setup pgvector en PostgreSQL
- [ ] Crear índices IVFFLAT
- [ ] Implementar `PostgresVectorStore`
- [ ] Perfil y tuning de queries
- [ ] Agregar caching strategy
- [ ] Crear tests de Q&A
- [ ] Documentar query patterns

## Quick Start

```python
from app.application.usecases import SearchDocumentsUseCase

# Buscar documentos relevantes
usecase = SearchDocumentsUseCase(
    vector_store=vector_store,
    embedding_service=embedding_service,
    doc_repo=doc_repository
)

results = await usecase.execute(
    query="¿Plazos para inscripción de propiedad?",
    top_k=10,
    threshold=0.7
)
```

## Performance Targets

- **Query Search**: < 100ms
- **Top-10 Results**: Guaranteed
- **Throughput**: 1000 QPS
- **Recall@10**: > 0.95

## Related Skills

- 🔗 [Document Parsing](../document-parsing/SKILL.md)
- 🔗 [Lease Analysis](../lease-analysis/SKILL.md)

---

**Status**: 🟡 In Development  
**Last Updated**: 2026-04-07
