---
name: "Document Parsing & Ingestion"
version: 1.0
domain: "document-processing"
difficulty: "high"
applies_to: ["python", "typescript"]
tags: ["docling", "ocr", "embedding", "celery"]
---

# Skill: Document Parsing & Ingestion

## 📋 Descripción General

Procesar documentos legales (PDF, DOCX, imágenes) para extraer texto estructurado, generar embeddings, y almacenarlos en la base de datos vectorial.

## 🎯 Objetivo

Convertir documentos crudos en:
1. ✅ Texto estructurado (preservando jerarquía)
2. ✅ Chunks semanticos (para RAG)
3. ✅ Embeddings (vectores para búsqueda)
4. ✅ Metadatos (tipo, categoría, fecha, etc)

## 🏗️ Arquitectura

```
PDF/Doc Upload
     ↓
[STAGE 1] Validación
     ├─ Tamaño < 100MB
     ├─ Tipo soportado
     └─ Usuario autorizado
     ↓
[STAGE 2] Parsing (Docling)
     ├─ Detectar layout
     ├─ Extraer texto
     ├─ Detectar tablas/imágenes
     └─ Preservar estructura
     ↓
[STAGE 3] Cleaning
     ├─ Normalizar espacios
     ├─ Corregir encoding
     └─ Remover duplicados
     ↓
[STAGE 4] Chunking
     ├─ Split semántico
     ├─ Overlap entre chunks
     └─ Preservar contexto
     ↓
[STAGE 5] Embeddings (Groq/Gemini API)
     ├─ Call LLM por chunk
     ├─ Get vector (1536D)
     └─ Rate limiting
     ↓
[STAGE 6] Storage
     ├─ pgvector (vectors + metadata)
     ├─ SeaweedFS (archivo original)
     └─ PostgreSQL (metadata)
     ↓
Document Ready ✅
```

## 💻 Implementación

### Backend Architecture

```python
# backend/app/infrastructure/repositories/document_repository.py

class PostgresDocumentRepository(DocumentRepository):
    async def create(self, document: Document) -> Document:
        """Crear documento en BD"""
        # ORM: INSERT INTO documents ...
        return document
    
    async def find_by_user(self, user_id: str) -> List[Document]:
        """Listar documentos del usuario"""
        # ORM: SELECT * FROM documents WHERE user_id = ?
        return documents


# backend/app/infrastructure/external/docling_service.py

class DoclingService:
    async def parse_document(self, file_path: str) -> str:
        """Parsear documento con Docling"""
        # from docling.document_converter import DocumentConverter
        # converter = DocumentConverter()
        # result = converter.convert(file_path)
        # return result.document.export_to_markdown()
        pass

    async def extract_chunks(self, text: str) -> List[str]:
        """Dividir texto en chunks semanticos"""
        # Use semantic splitter (langchain, llmsplitter)
        # Preserve context with overlap
        pass


# backend/app/infrastructure/external/embedding_service.py

class EmbeddingService:
    async def generate_embedding(self, text: str) -> List[float]:
        """Generar embedding con Groq/Gemini"""
        # client = Groq(api_key=GROQ_API_KEY)
        # response = client.embeddings.create(
        #     model="nomic-embed-text-1.5",
        #     input=text
        # )
        # return response.data[0].embedding
        pass


# backend/app/infrastructure/external/seaweedfs_service.py

class SeaweedFSService:
    async def upload(self, file_path: str) -> str:
        """Subir archivo a SeaweedFS y retornar file_id"""
        # POST to /submit endpoint
        # Return file_id from response
        pass


# backend/app/application/usecases/process_document.py

class ProcessDocumentUseCase(UseCase):
    def __init__(
        self,
        doc_repo: DocumentRepository,
        vector_store: VectorStore,
        file_storage: FileStorage,
        docling_service: DoclingService,
        embedding_service: EmbeddingService
    ):
        self.doc_repo = doc_repo
        self.vector_store = vector_store
        self.file_storage = file_storage
        self.docling_service = docling_service
        self.embedding_service = embedding_service
    
    async def execute(self, document_id: str):
        # 1. Load document
        doc = await self.doc_repo.find_by_id(document_id)
        doc.mark_processing_started()
        
        # 2. Download file from storage
        file_path = await self.file_storage.download(doc.seaweedfs_file_id, "/tmp")
        
        # 3. Parse with Docling
        text = await self.docling_service.parse_document(file_path)
        
        # 4. Split into chunks
        chunks = await self.docling_service.extract_chunks(text)
        
        # 5. Generate embeddings
        for chunk in chunks:
            embedding = await self.embedding_service.generate_embedding(chunk)
            await self.vector_store.add(
                vector_id=f"{document_id}_{hash(chunk)}",
                text=chunk,
                embedding=embedding,
                metadata={"document_id": document_id}
            )
        
        # 6. Update document status
        doc.mark_processing_completed(len(chunks), len(text.split()))
        await self.doc_repo.update(doc)
```

### Frontend Upload Component

```typescript
// frontend/src/components/DocumentUpload/UploadZone.tsx

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import * as api from '../../services/api';

export const UploadZone: React.FC = () => {
  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name);
    formData.append('category', 'otro');
    
    try {
      const response = await api.uploadDocument(formData);
      console.log('Document queued:', response.data.document_id);
      
      // Poll for status
      pollDocumentStatus(response.data.document_id);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  }, []);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'] }
  });
  
  return (
    <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
      <input {...getInputProps()} />
      <p>Arrastra documentos aquí o haz clic</p>
    </div>
  );
};
```

## 🔄 Flujo End-to-End

1. **Usuario carga PDF** desde frontend
2. **API valida** tamaño, tipo, permiso
3. **Archivo sube a SeaweedFS** → obtenemos `file_id`
4. **BD crea Document** con status `PENDING`
5. **Encolamos tarea Celery** con `document_id`
6. **Worker toma tarea**:
   - Descarga de SeaweedFS
   - Parsea con Docling
   - Genera chunks
   - Crea embeddings
   - Guarda en pgvector
7. **Actualiza BD** status → `COMPLETED`
8. **Frontend notificado** (WebSocket o polling)

## ⚙️ Configuración

```env
# .env
DOCLING_CHUNK_SIZE=auto
DOCLING_OVERLAP=0.2
EMBEDDING_MODEL=nomic-embed-text-1.5
EMBEDDING_BATCH_SIZE=10
MAX_UPLOAD_SIZE=104857600  # 100MB
```

## 🧪 Testing

```python
# backend/tests/usecases/test_process_document.py

@pytest.mark.asyncio
async def test_process_document_successfully():
    # Mock repositories
    doc_repo = AsyncMock(spec=DocumentRepository)
    vector_store = AsyncMock(spec=VectorStore)
    file_storage = AsyncMock(spec=FileStorage)
    
    # Create use case
    usecase = ProcessDocumentUseCase(
        doc_repo=doc_repo,
        vector_store=vector_store,
        file_storage=file_storage,
        docling_service=DoclingService(),
        embedding_service=EmbeddingService()
    )
    
    # Execute
    await usecase.execute(document_id="doc_123")
    
    # Verify
    doc_repo.update.assert_called_once()
    vector_store.add.assert_called()
```

## 🎯 Best Practices

1. **Batch Processing**: Procesar múltiples chunks en paralelo
2. **Error Handling**: Retry logic con exponential backoff
3. **Logging**: Log detallado de cada stage
4. **Monitoring**: Métricas de latencia y success rate
5. **Rate Limiting**: No sobrecargar APIs externas

## 📚 Referencias

- [Docling Docs](https://ds4sd.github.io/docling/)
- [LangChain Splitters](https://python.langchain.com/docs/modules/data_connection/document_loaders/)
- [pgvector](https://github.com/pgvector/pgvector)
- [SeaweedFS](https://github.com/seaweedfs/seaweedfs)

---

**Version**: 1.0  
**Updated**: 2026-04-07  
**Status**: ✅ Ready for Implementation
