# User Repository

from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User
from app.domain.interfaces import UserRepository
from app.domain.exceptions import EntityNotFound, DuplicateEntity
from app.infrastructure.models import UserModel
from app.core.logger import logger


class PostgresUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID"""
        try:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._model_to_entity(model)
        except Exception as e:
            logger.error(f"Error finding user by ID: {e}")
            raise
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        try:
            stmt = select(UserModel).where(UserModel.email == email.lower())
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._model_to_entity(model)
        except Exception as e:
            logger.error(f"Error finding user by email: {e}")
            raise
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        try:
            stmt = select(UserModel).where(UserModel.username == username)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._model_to_entity(model)
        except Exception as e:
            logger.error(f"Error finding user by username: {e}")
            raise
    
    async def find_all(self) -> List[User]:
        """Find all users"""
        try:
            stmt = select(UserModel)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Error finding all users: {e}")
            raise
    
    async def find_all_paginated(self, page: int, page_size: int) -> tuple[List[User], int]:
        """Find all users with pagination"""
        try:
            # Get total count
            count_stmt = select(func.count()).select_from(UserModel)
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar()
            
            # Get paginated results
            offset = (page - 1) * page_size
            stmt = select(UserModel).offset(offset).limit(page_size)
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            users = [self._model_to_entity(model) for model in models]
            return users, total
        except Exception as e:
            logger.error(f"Error finding paginated users: {e}")
            raise
    
    async def create(self, entity: User) -> User:
        """Create a new user"""
        try:
            # Check for duplicate email
            existing = await self.find_by_email(entity.email)
            if existing:
                raise DuplicateEntity(f"User with email {entity.email} already exists")
            
            # Check for duplicate username
            existing = await self.find_by_username(entity.username)
            if existing:
                raise DuplicateEntity(f"User with username {entity.username} already exists")
            
            model = self._entity_to_model(entity)
            self.session.add(model)
            await self.session.flush()
            
            logger.info(f"User created: {entity.id}")
            return entity
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    async def update(self, entity: User) -> User:
        """Update an existing user"""
        try:
            stmt = select(UserModel).where(UserModel.id == entity.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise EntityNotFound(f"User {entity.id} not found")
            
            # Update fields
            model.email = entity.email
            model.username = entity.username
            model.password_hash = entity.password_hash
            model.roles = entity.roles
            model.is_active = entity.is_active
            model.updated_at = entity.updated_at
            
            self.session.add(model)
            await self.session.flush()
            
            logger.info(f"User updated: {entity.id}")
            return entity
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating user: {e}")
            raise
    
    async def delete(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise EntityNotFound(f"User {user_id} not found")
            
            await self.session.delete(model)
            await self.session.flush()
            
            logger.info(f"User deleted: {user_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting user: {e}")
            raise
    
    async def exists(self, user_id: str) -> bool:
        """Check if user exists"""
        try:
            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking user existence: {e}")
            raise
    
    @staticmethod
    def _model_to_entity(model: UserModel) -> User:
        """Convert database model to domain entity"""
        user = User(
            email=model.email,
            username=model.username,
            password_hash=model.password_hash,
            is_active=model.is_active,
            roles=model.roles or []
        )
        user.id = model.id
        user.created_at = model.created_at
        user.updated_at = model.updated_at
        return user
    
    @staticmethod
    def _entity_to_model(entity: User) -> UserModel:
        """Convert domain entity to database model"""
        return UserModel(
            id=entity.id,
            email=entity.email,
            username=entity.username,
            password_hash=entity.password_hash,
            is_active=entity.is_active,
            roles=entity.roles or [],
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
