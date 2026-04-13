# Document Parsing & Ingestion Skill

## Overview

Esta skill encapsula la lógica completa para procesar documentos legales y convertirlos en embeddings.

## Folder Structure

```
document-parsing/
├── SKILL.md              # Documentación completa
├── README.md             # Este archivo
├── examples/             # Ejemplos y casos de uso
│   ├── sample_lease.pdf
│   └── sample_regulation.pdf
├── tests/                # Tests de la skill
│   ├── test_docling_service.py
│   └── test_embedding_generation.py
└── reference/            # Documentación de referencia
    └── docling_api.md
```

## Key Components

### 1. **Docling Service**
- Parsea diversos formatos de archivo
- Extrae texto estructurado
- Detecta tablas, imágenes, layout

### 2. **Embedding Service**
- Genera vectores de documentos
- Maneja batching y rate limiting
- Soporta múltiples providers (Groq, Gemini, OpenAI)

### 3. **Vector Store**
- Almacena embeddings en pgvector
- Optimizado para búsquedas rápidas
- Mantiene metadatos

### 4. **Processing Pipeline**
- Orquesta el flujo completo
- Manejo robusto de errores
- Monitoring y logging

## Implementation Checklist

- [ ] Crear `DoclingService` 
- [ ] Crear `EmbeddingService`
- [ ] Crear `VectorStore` para pgvector
- [ ] Crear use case `ProcessDocumentUseCase`
- [ ] Crear API endpoint para upload
- [ ] Implementar Celery task para async processing
- [ ] Agregar tests unitarios
- [ ] Agregar tests de integración

## Quick Start

```python
from app.application.usecases import ProcessDocumentUseCase

# Usar el use case
usecase = ProcessDocumentUseCase(
    doc_repo=repository,
    vector_store=vector_store,
    file_storage=seaweedfs,
    docling_service=docling,
    embedding_service=embedding
)

result = await usecase.execute(document_id="doc_123")
```

## Performance Targets

- **Upload**: < 500ms
- **Parsing**: < 2s por documento
- **Embedding Gen**: < 3s per document
- **Storage**: O(1) complexity

## Related Skills

- 🔗 [Property Search & Semantic Query](../property-search/SKILL.md)
- 🔗 [Lease Analysis](../lease-analysis/SKILL.md)
- 🔗 [Requirements Extraction](../requirements-extraction/SKILL.md)

---

**Status**: 🟡 In Development  
**Last Updated**: 2026-04-07
