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

# Parches idempotentes de esquema para columnas agregadas a tablas YA EXISTENTES.
#
# HALLAZGO DE AUDITORÍA: este proyecto no usa Alembic (aunque está en requirements.txt,
# nunca se inicializó — no hay carpeta migrations/ ni alembic.ini). `Base.metadata.create_all`
# solo crea tablas que no existen; nunca altera una tabla ya existente para agregarle una
# columna nueva. Se confirmó en vivo: `chatbot_profiles.llm_provider/llm_model/custom_api_key`
# ya estaban en la tabla real (aparentemente creada después de agregar esas columnas al
# modelo), pero `chat_messages.feedback_rating/feedback_text` NO estaban — cualquier request
# a /stats/llm-router o POST /chat/messages/{id}/feedback fallaba con un error real de
# PostgreSQL (columna inexistente). Este bloque agrega, de forma segura e idempotente
# (ADD COLUMN IF NOT EXISTS), cualquier columna nueva declarada en los modelos ORM que
# `create_all` no pueda crear por sí solo. Si el proyecto migra a Alembic en el futuro,
# este bloque puede retirarse.
_SCHEMA_PATCHES = [
    ("chat_messages", "feedback_rating", "VARCHAR(10)"),
    ("chat_messages", "feedback_text", "TEXT"),
]


async def _apply_schema_patches(conn):
    for table, column, coltype in _SCHEMA_PATCHES:
        try:
            await conn.execute(
                text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {coltype}')
            )
        except Exception as e:
            logger.warning(f"No se pudo aplicar el parche de esquema {table}.{column}: {e}")


async def init_db():
    """Initialize database connection and create tables"""
    global _engine
    
    try:
        logger.info(f"Connecting to database at {settings.DB_HOST}:{settings.DB_PORT}")
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

        # Agregar columnas nuevas a tablas ya existentes (ver _SCHEMA_PATCHES arriba)
        async with _engine.begin() as conn:
            await _apply_schema_patches(conn)

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
