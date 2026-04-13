# Chat Session Repository

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import ChatSession, ChatMessage
from app.domain.interfaces import ChatSessionRepository
from app.domain.exceptions import EntityNotFound
from app.infrastructure.models import ChatSessionModel, ChatMessageModel
from app.core.logger import logger


class PostgresChatSessionRepository(ChatSessionRepository):
    """PostgreSQL implementation of ChatSessionRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def find_by_id(self, session_id: str) -> Optional[ChatSession]:
        """Find chat session by ID"""
        try:
            stmt = select(ChatSessionModel).where(ChatSessionModel.id == session_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._model_to_entity(model)
        except Exception as e:
            logger.error(f"Error finding chat session: {e}")
            raise
    
    async def find_by_user(self, user_id: str) -> List[ChatSession]:
        """Find all chat sessions for a user"""
        try:
            stmt = select(ChatSessionModel).where(
                ChatSessionModel.user_id == user_id
            ).order_by(ChatSessionModel.created_at.desc())
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error finding user chat sessions: {e}")
            raise

    async def find_by_user_paginated(
        self, user_id: str, page: int, page_size: int
    ) -> tuple[List[ChatSession], int]:
        """Find chat sessions for a user with pagination"""
        try:
            from sqlalchemy import func
            
            # Count
            count_stmt = select(func.count()).select_from(ChatSessionModel).where(ChatSessionModel.user_id == user_id)
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar()
            
            # Results
            offset = (page - 1) * page_size
            stmt = select(ChatSessionModel).where(
                ChatSessionModel.user_id == user_id
            ).order_by(ChatSessionModel.created_at.desc()).offset(offset).limit(page_size)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            sessions = [self._model_to_entity(model) for model in models]
            return sessions, total
        except Exception as e:
            logger.error(f"Error finding paginated user chat sessions: {e}")
            raise
    
    async def find_all(self) -> List[ChatSession]:
        """Find all chat sessions"""
        try:
            stmt = select(ChatSessionModel)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error finding all chat sessions: {e}")
            raise
    
    async def find_all_paginated(self, page: int, page_size: int) -> tuple[List[ChatSession], int]:
        """Find all chat sessions with pagination"""
        try:
            from sqlalchemy import func
            
            # Get total count
            count_stmt = select(func.count()).select_from(ChatSessionModel)
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar()
            
            # Get paginated results
            offset = (page - 1) * page_size
            stmt = select(ChatSessionModel).offset(offset).limit(page_size)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            sessions = [self._model_to_entity(model) for model in models]
            return sessions, total
        except Exception as e:
            logger.error(f"Error finding paginated chat sessions: {e}")
            raise
    
    async def create(self, entity: ChatSession) -> ChatSession:
        """Create a new chat session"""
        try:
            model = self._entity_to_model(entity)
            self.session.add(model)
            await self.session.flush()
            
            logger.info(f"Chat session created: {entity.id}")
            return entity
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating chat session: {e}")
            raise
    
    async def update(self, entity: ChatSession) -> ChatSession:
        """Update an existing chat session"""
        try:
            stmt = select(ChatSessionModel).where(ChatSessionModel.id == entity.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise EntityNotFound(f"Chat session {entity.id} not found")
            
            # Update fields
            model.title = entity.title
            model.doc_metadata = entity.metadata
            model.total_tokens_used = entity.total_tokens_used
            model.updated_at = entity.updated_at
            
            self.session.add(model)
            await self.session.flush()
            
            logger.info(f"Chat session updated: {entity.id}")
            return entity
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating chat session: {e}")
            raise
    
    async def delete(self, session_id: str) -> bool:
        """Delete a chat session"""
        try:
            stmt = select(ChatSessionModel).where(ChatSessionModel.id == session_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise EntityNotFound(f"Chat session {session_id} not found")
            
            await self.session.delete(model)
            await self.session.flush()
            
            logger.info(f"Chat session deleted: {session_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting chat session: {e}")
            raise
    
    async def exists(self, session_id: str) -> bool:
        """Check if chat session exists"""
        try:
            stmt = select(ChatSessionModel).where(ChatSessionModel.id == session_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking chat session existence: {e}")
            raise
    
    async def add_message(self, session_id: str, message: ChatMessage) -> bool:
        """Add a message to a chat session"""
        try:
            # Create message model
            message_model = ChatMessageModel(
                session_id=session_id,
                role=message.role,
                content=message.content,
                sources=message.sources or [],
                tokens_used=message.tokens_used,
                created_at=message.created_at
            )
            
            self.session.add(message_model)
            await self.session.flush()
            
            logger.info(f"Message added to session {session_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding message to session: {e}")
            raise
    
    async def get_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get messages from a chat session"""
        try:
            stmt = select(ChatMessageModel).where(
                ChatMessageModel.session_id == session_id
            ).order_by(ChatMessageModel.created_at.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # Convert to entities and reverse order
            messages = [self._message_model_to_entity(m) for m in reversed(models)]
            return messages
        except Exception as e:
            logger.error(f"Error getting messages from session: {e}")
            raise
    
    @staticmethod
    def _model_to_entity(model: ChatSessionModel) -> ChatSession:
        """Convert database model to domain entity"""
        session = ChatSession(
            user_id=model.user_id,
            title=model.title,
            metadata=model.doc_metadata or {}
        )
        session.id = model.id
        session.total_tokens_used = model.total_tokens_used
        session.created_at = model.created_at
        session.updated_at = model.updated_at
        return session
    
    @staticmethod
    def _entity_to_model(entity: ChatSession) -> ChatSessionModel:
        """Convert domain entity to database model"""
        return ChatSessionModel(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            doc_metadata=entity.metadata or {},
            total_tokens_used=entity.total_tokens_used,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    @staticmethod
    def _message_model_to_entity(model: ChatMessageModel) -> ChatMessage:
        """Convert database message model to domain entity"""
        message = ChatMessage(
            role=model.role,
            content=model.content,
            sources=model.sources or [],
            tokens_used=model.tokens_used
        )
        message.created_at = model.created_at
        return message
