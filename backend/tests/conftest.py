"""
Pytest Configuration and Shared Fixtures
Backend Testing Setup
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

# Load .env for testing
load_dotenv()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create an async database session for testing.
    Uses in-memory SQLite by default.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.infrastructure.models import Base
    
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_local = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_local() as session:
        yield session
    
    await engine.dispose()


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def test_user_data():
    """Test user data for authentication tests."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
    }


@pytest.fixture
def test_document_data():
    """Test document data."""
    return {
        "title": "Test Document",
        "category": "reglamentos",
        "content": "This is test content for document processing.",
        "metadata": {
            "source": "test",
            "created_at": "2026-04-07",
        }
    }


@pytest.fixture
def test_chat_session():
    """Test chat session data."""
    return {
        "title": "Test Session",
        "user_id": 1,
    }


@pytest.fixture
def test_query():
    """Test query for chat."""
    return {
        "session_id": 1,
        "query": "¿Cuáles son los requisitos para un trámite?",
        "document_ids": [1],
    }


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    return {
        "content": "Los requisitos principales son: identificación, comprobante de domicilio...",
        "tokens_used": 150,
        "model": "llama-3.1-70b-versatile",
    }


@pytest.fixture
def mock_embeddings():
    """Mock embeddings for vector database."""
    import random
    # Simulated 1536-dimensional embeddings (matching pgvector setup)
    return [random.uniform(-1, 1) for _ in range(1536)]


# ============================================================================
# ASYNC CONTEXT MANAGERS
# ============================================================================

@pytest.fixture
async def db_session(async_session):
    """Provide database session for tests."""
    return async_session


# ============================================================================
# MARKERS & CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Register pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "async: marks tests as async"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# ============================================================================
# PYTEST HOOKS
# ============================================================================

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Custom test reporting."""
    pass


# ============================================================================
# CACHE LAYER FIXTURES (new)
# ============================================================================

@pytest.fixture
def mock_redis_client():
    """Mock pour client Redis async"""
    from unittest.mock import AsyncMock
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)
    mock_client.hset = AsyncMock(return_value=1)
    mock_client.hgetall = AsyncMock(return_value={})
    mock_client.expire = AsyncMock(return_value=True)
    mock_client.flushdb = AsyncMock(return_value=True)
    mock_client.close = AsyncMock(return_value=None)
    return mock_client


@pytest.fixture
def sample_queries():
    """Sample queries for cache tests"""
    return [
        "¿Cuál es el costo de una escritura pública?",
        "¿Requisitos para vender una propiedad?",
        "¿Cuánto tiempo tarda un trámite?",
        "¿Documentos necesarios para hipoteca?",
        "¿Costo del cambio de domicilio?",
    ]


@pytest.fixture
def sample_responses():
    """Sample responses for cache tests"""
    return {
        "escritura": "El costo de una escritura pública varía según la jurisdicción. En promedio: $500-1500 MXN.",
        "venta": "Para vender una propiedad necesitas: 1. Identificación 2. Títulos de propiedad 3. Comprobante de domicilio.",
        "plazo": "Los trámites típicamente tardan 15-30 días hábiles dependiendo del tipo de acto.",
        "hipoteca": "Documentos necesarios: Identificación, comprobantes de ingresos, avalúo, títulos de propiedad.",
        "domicilio": "El cambio de domicilio cuesta aproximadamente $200-400 MXN y toma 5-10 días.",
    }


@pytest.fixture
def sample_cache_data():
    """Sample cache data for tests"""
    from datetime import datetime
    return {
        "cache_key": "a1b2c3d4e5f6g7h8",
        "query": "¿Costo de escritura?",
        "response": "El costo es de $500 MXN",
        "embedding": "[0.1, 0.2, 0.3]",
        "sources": '["REQUISITOS.md", "COSTOS.md"]',
        "timestamp": datetime.utcnow().isoformat(),
        "ttl": 86400  # 24 horas
    }
