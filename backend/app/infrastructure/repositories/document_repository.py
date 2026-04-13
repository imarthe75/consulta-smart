# PostgreSQL Document Repository Implementation

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Document, DocumentStatus, DocumentCategory
from app.domain.interfaces import DocumentRepository
from app.domain.exceptions import EntityNotFound
from app.infrastructure.models import DocumentModel
from app.core.logger import logger


class PostgresDocumentRepository(DocumentRepository):
    """PostgreSQL implementation of DocumentRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def find_by_id(self, id: str) -> Optional[Document]:
        """Find document by ID"""
        try:
            stmt = select(DocumentModel).where(DocumentModel.id == id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._model_to_entity(model)
        except Exception as e:
            logger.error(f"Error finding document by id {id}: {e}")
            raise
    
    async def find_all(self) -> List[Document]:
        """Find all documents"""
        try:
            stmt = select(DocumentModel)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error finding all documents: {e}")
            raise
    
    async def find_all_paginated(self, page: int, page_size: int) -> tuple[List[Document], int]:
        """Find documents with pagination"""
        try:
            offset = (page - 1) * page_size
            
            # Get total count
            count_stmt = select(DocumentModel)
            count_result = await self.session.execute(count_stmt)
            total = len(count_result.scalars().all())
            
            # Get paginated results
            stmt = select(DocumentModel).offset(offset).limit(page_size)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models], total
        except Exception as e:
            logger.error(f"Error finding documents paginated: {e}")
            raise
    
    async def create(self, entity: Document) -> Document:
        """Create new document"""
        try:
            model = self._entity_to_model(entity)
            self.session.add(model)
            await self.session.flush()
            
            logger.info(f"Document created: {entity.id}")
            return entity
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            await self.session.rollback()
            raise
    
    async def update(self, entity: Document) -> Document:
        """Update existing document"""
        try:
            # Verify exists
            existing = await self.find_by_id(entity.id)
            if not existing:
                raise EntityNotFound("Document", entity.id)
            
            model = self._entity_to_model(entity)
            await self.session.merge(model)
            await self.session.flush()
            
            logger.info(f"Document updated: {entity.id}")
            return entity
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            await self.session.rollback()
            raise
    
    async def delete(self, id: str) -> bool:
        """Delete document"""
        try:
            stmt = select(DocumentModel).where(DocumentModel.id == id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            await self.session.delete(model)
            await self.session.flush()
            
            logger.info(f"Document deleted: {id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            await self.session.rollback()
            raise
    
    async def exists(self, id: str) -> bool:
        """Check if document exists"""
        try:
            stmt = select(DocumentModel).where(DocumentModel.id == id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            raise
    
    async def find_by_user(self, user_id: str) -> List[Document]:
        """Find documents by user"""
        try:
            stmt = select(DocumentModel).where(DocumentModel.user_id == user_id)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error finding documents by user {user_id}: {e}")
            raise
    
    async def find_by_category(self, category: str) -> List[Document]:
        """Find documents by category"""
        try:
            stmt = select(DocumentModel).where(DocumentModel.category == category)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error finding documents by category {category}: {e}")
            raise
    
    async def find_by_status(self, status: str) -> List[Document]:
        """Find documents by status"""
        try:
            stmt = select(DocumentModel).where(DocumentModel.status == status)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error finding documents by status {status}: {e}")
            raise
    
    async def find_by_user_paginated(
        self, user_id: str, page: int, page_size: int
    ) -> tuple[List[Document], int]:
        """Find documents by user with pagination"""
        try:
            offset = (page - 1) * page_size
            
            # Get total count
            count_stmt = select(DocumentModel).where(DocumentModel.user_id == user_id)
            count_result = await self.session.execute(count_stmt)
            total = len(count_result.scalars().all())
            
            # Get paginated results
            stmt = select(DocumentModel).where(
                DocumentModel.user_id == user_id
            ).offset(offset).limit(page_size).order_by(DocumentModel.created_at.desc())
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models], total
        except Exception as e:
            logger.error(f"Error finding documents by user paginated: {e}")
            raise

    async def find_latest_by_group_id(self, group_id: str) -> Optional[Document]:
        """Find latest version of a document group"""
        try:
            stmt = select(DocumentModel).where(
                DocumentModel.group_id == group_id
            ).order_by(DocumentModel.version.desc()).limit(1)
            
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._model_to_entity(model)
        except Exception as e:
            logger.error(f"Error finding latest by group id {group_id}: {e}")
            raise

    async def deactivate_all_in_group(self, group_id: str) -> None:
        """Deactivate all versions in a group"""
        try:
            from sqlalchemy import update
            stmt = update(DocumentModel).where(
                DocumentModel.group_id == group_id
            ).values(is_active=False)
            
            await self.session.execute(stmt)
            await self.session.flush()
            logger.info(f"Deactivated all versions for group {group_id}")
        except Exception as e:
            logger.error(f"Error deactivating group {group_id}: {e}")
            raise
    
    @staticmethod
    def _model_to_entity(model: DocumentModel) -> Document:
        """Convert ORM model to domain entity"""
        return Document(
            id=model.id,
            title=model.title,
            category=DocumentCategory(model.category),
            user_id=model.user_id,
            file_type=model.file_type,
            seaweedfs_file_id=model.seaweedfs_file_id,
            status=DocumentStatus(model.status),
            chunk_count=model.chunk_count,
            token_count=model.token_count,
            group_id=model.group_id,
            version=model.version,
            version_label=model.version_label,
            is_active=model.is_active,
            effective_date=model.effective_date,
            expiration_date=model.expiration_date,
            metadata=model.doc_metadata or {}
        )
    
    @staticmethod
    def _entity_to_model(entity: Document) -> DocumentModel:
        """Convert domain entity to ORM model"""
        return DocumentModel(
            id=entity.id,
            title=entity.title,
            category=entity.category.value,
            user_id=entity.user_id,
            file_type=entity.file_type,
            seaweedfs_file_id=entity.seaweedfs_file_id,
            status=entity.status.value,
            chunk_count=entity.chunk_count,
            token_count=entity.token_count,
            group_id=entity.group_id,
            version=entity.version,
            version_label=entity.version_label,
            is_active=entity.is_active,
            effective_date=entity.effective_date,
            expiration_date=entity.expiration_date,
            doc_metadata=entity.metadata,
            processing_error=entity.processing_error,
            processing_started_at=entity.processing_started_at,
            processing_completed_at=entity.processing_completed_at
        )
