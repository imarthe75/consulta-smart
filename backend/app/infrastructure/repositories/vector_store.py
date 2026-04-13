# PostgreSQL Vector Store Implementation with pgvector support

from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from app.domain.interfaces import VectorStore
from app.infrastructure.models import DocumentChunkModel
from app.core.logger import logger


class PostgresVectorStore(VectorStore):
    """PostgreSQL implementation of VectorStore using pgvector"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(
        self,
        vector_id: str,
        text_content: str,
        embedding: Optional[List[float]],
        metadata: dict
    ) -> bool:
        """Add embedding to vector store (embedding can be None)"""
        try:
            model = DocumentChunkModel(
                id=vector_id,
                document_id=metadata.get("document_id"),
                chunk_number=metadata.get("chunk_number", 0),
                text=text_content,
                embedding=embedding,  # Can be None
                doc_metadata=metadata
            )
            
            self.session.add(model)
            await self.session.flush()
            
            logger.info(f"Vector added: {vector_id} (has_embedding: {embedding is not None})")
            return True
        except Exception as e:
            logger.error(f"Error adding vector {vector_id}: {e}")
            await self.session.rollback()
            raise
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        threshold: float = 0.5,
        filters: dict = None
    ) -> List[dict]:
        """Perform semantic search with structural filtering"""
        try:
            # Base statement joining Chunks with Documents
            stmt = select(
                DocumentChunkModel,
                DocumentModel,
                DocumentChunkModel.embedding.cosine_distance(query_embedding).label("distance")
            ).join(
                DocumentModel, DocumentChunkModel.document_id == DocumentModel.id
            ).where(
                DocumentChunkModel.embedding.cosine_distance(query_embedding) < (1 - threshold)
            )
            
            # Apply additional filters
            if filters:
                if 'is_active' in filters:
                    stmt = stmt.where(DocumentModel.is_active == filters['is_active'])
                if 'category' in filters:
                    stmt = stmt.where(DocumentModel.category == filters['category'])
                if 'version_label' in filters:
                    stmt = stmt.where(DocumentModel.version_label == filters['version_label'])
                if 'group_id' in filters:
                    stmt = stmt.where(DocumentModel.group_id == filters['group_id'])
            
            stmt = stmt.order_by(text("distance ASC")).limit(top_k)
            
            result = await self.session.execute(stmt)
            rows = result.all()
            
            return [
                {
                    'chunk_id': row[0].id,
                    'document_id': row[0].document_id,
                    'text': row[0].text,
                    'score': 1 - float(row[2]), # Distance is index 2 now
                    'metadata': {
                        **row[0].doc_metadata,
                        'document_title': row[1].title,
                        'version_label': row[1].version_label,
                        'is_active': row[1].is_active,
                        'category': row[1].category
                    }
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise
    
    async def delete(self, vector_id: str) -> bool:
        """Delete embedding"""
        try:
            stmt = select(DocumentChunkModel).where(DocumentChunkModel.id == vector_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            await self.session.delete(model)
            await self.session.flush()
            
            logger.info(f"Vector deleted: {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vector {vector_id}: {e}")
            await self.session.rollback()
            raise
    
    async def delete_by_document(self, document_id: str) -> int:
        """Delete all embeddings for a document"""
        try:
            stmt = select(DocumentChunkModel).where(
                DocumentChunkModel.document_id == document_id
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            count = 0
            for model in models:
                await self.session.delete(model)
                count += 1
            
            await self.session.flush()
            logger.info(f"Deleted {count} vectors for document {document_id}")
            return count
        except Exception as e:
            logger.error(f"Error deleting vectors for document {document_id}: {e}")
            await self.session.rollback()
            raise

    async def exists(self, vector_id: str) -> bool:
        """Check if vector exists"""
        try:
            stmt = select(DocumentChunkModel).where(DocumentChunkModel.id == vector_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking vector existence: {e}")
            raise
