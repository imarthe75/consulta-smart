# Use Case Implementations for Document Management

import os
import tempfile
from typing import Optional, List, Dict, Any
from app.domain.entities.document import Document, DocumentStatus
from app.domain.interfaces.repositories import DocumentRepository
from app.domain.interfaces.repositories import Repository
from app.domain.interfaces.vector_store import VectorStore
from app.domain.interfaces.file_storage import FileStorage
from app.application.usecases.base import UseCase
from app.core.logger import logger
from app.infrastructure.external.docling_service import DoclingService, TextProcessingService
from app.infrastructure.external.llm_service import LLMService


class ProcessDocumentUseCase(UseCase):
    """Process a document: parse, chunk, embed, and store"""
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        vector_store: VectorStore,
        file_storage: FileStorage,
        llm_service: LLMService
    ):
        self.document_repo = document_repo
        self.vector_store = vector_store
        self.file_storage = file_storage
        self.llm_service = llm_service
        self.docling_service = DoclingService()
    
    async def execute(self, document_id: str) -> dict:
        """Process document through full pipeline"""
        document = None
        temp_file_path = None
        try:
            # 1. Load document from repository
            document = await self.document_repo.find_by_id(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # 2. Mark as processing
            document.mark_processing_started()
            await self.document_repo.update(document)
            logger.info(f"[UseCase] Processing started for: {document_id} - {document.title}")
            
            # 3. Download file from Storage (SeaweedFS)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{document.file_type}") as tmp:
                temp_file_path = tmp.name
            
            await self.file_storage.download(document.seaweedfs_file_id, temp_file_path)
            
            # 4. Parse document with Docling (o fallback a texto plano)
            text_content = await self.docling_service.extract_text(temp_file_path)
            
            # 5. Extract text and clean
            clean_text = TextProcessingService.clean_text(text_content)
            
            # 6. Create chunks
            chunks = TextProcessingService.extract_chunks(clean_text)
            
            # 7. Generate embeddings and store in Vector Store
            for chunk_num, chunk_text in chunks:
                embedding = await self.llm_service.create_embedding(chunk_text)
                await self.vector_store.add(
                    vector_id=f"{document_id}_{chunk_num}",
                    text=chunk_text,
                    embedding=embedding,
                    metadata={
                        "document_id": document_id, 
                        "chunk": chunk_num,
                        "title": document.title,
                        "category": document.category
                    }
                )
            
            # 8. Update document status
            total_tokens = TextProcessingService.count_tokens(clean_text)
            document.mark_processing_completed(len(chunks), total_tokens)
            await self.document_repo.update(document)
            
            logger.info(f"[UseCase] Processing completed for document: {document_id}")
            return {
                "status": "completed",
                "document_id": document_id,
                "chunks": len(chunks),
                "tokens": total_tokens
            }
        
        except Exception as e:
            logger.error(f"[UseCase] Error processing document {document_id}: {e}")
            if document:
                document.mark_processing_failed(str(e))
                await self.document_repo.update(document)
            raise
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)


class SearchDocumentsUseCase(UseCase):
    """Search documents using semantic search"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        llm_service: LLMService
    ):
        self.vector_store = vector_store
        self.llm_service = llm_service
    
    async def execute(
        self, 
        query: str, 
        top_k: int = 5, 
        threshold: float = 0.75,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks with temporal filters"""
        try:
            # Filtro por defecto: Solo documentos activos
            if filters is None:
                filters = {"is_active": True}
            
            # 1. Create embedding for query
            query_embedding = await self.llm_service.create_embedding(query)
            
            # 2. Perform search in vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                threshold=threshold,
                filters=filters
            )
            
            return results
        except Exception as e:
            logger.error(f"[UseCase] Error searching documents: {e}")
            return []
