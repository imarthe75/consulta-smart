"""
Phase 4C - Integration Tests Conftest
Shared fixtures for integration tests
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine (async SQLite)"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        pool_size=0,  # Disable pool for SQLite
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_db_engine):
    """Create test session"""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()  # Cleanup


@pytest.fixture
async def authenticated_user(test_session):
    """Create authenticated user for tests"""
    from app.infrastructure.models import User
    from datetime import datetime
    
    user = User(
        email="integration.test@example.com",
        username="integration_test_user",
        password_hash="hashed_password",
        created_at=datetime.utcnow()
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "token": "mock_jwt_token_for_testing"
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
