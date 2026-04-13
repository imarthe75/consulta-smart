# Database Connection & Session Management

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.core.config import settings
from app.core.logger import logger

# Base class for all ORM models
Base = declarative_base()

# Engine singleton
_engine = None


async def init_db():
    """Initialize database connection and create tables"""
    global _engine
    
    try:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=20,
            max_overflow=0,
            pool_pre_ping=True,
            connect_args={"timeout": 30}
        )
        
        # Try to enable pgvector (separate transaction, don't fail if it fails)
        try:
            async with _engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"pgvector extension not available: {e}, continuing without vector support")
        
        # Create all tables (separate transaction to ensure it runs)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """Close database connections"""
    global _engine
    
    if _engine:
        await _engine.dispose()
        logger.info("Database connections closed")


def get_session_factory() -> async_sessionmaker:
    """Get AsyncSession factory"""
    if not _engine:
        raise RuntimeError("Database not initialized")
    
    return async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )


async def get_session() -> AsyncSession:
    """Get database session (dependency for FastAPI)"""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
