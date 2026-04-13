# Celery Configuration for ConsultaRPP

import asyncio
from celery import Celery
from app.core.config import settings
from app.core.logger import logger

# App Initialization
celery_app = Celery(
    "consultarpp_workers",
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_prefetch_multiplier=1,
)

# Task definitions helper to run async in Celery
def run_async(coro):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # This shouldn't happen in Celery worker but just in case
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    else:
        return loop.run_until_complete(coro)

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """
    Process document asynchronously using the UseCase pattern.
    This task orchestrates the entire RAG pipeline: Storage -> Parsing -> Embedding -> Vector DB.
    """
    from app.core.database import SessionLocal
    from app.infrastructure.repositories.document_repository import PostgresDocumentRepository
    from app.infrastructure.repositories.vector_store import PostgresVectorStore
    from app.infrastructure.external.seaweedfs_service import SeaweedFSFileStorage
    from app.infrastructure.external.llm_service import get_llm_provider
    from app.application.usecases.document_usecases import ProcessDocumentUseCase

    logger.info(f"[Celery] Received document processing task: {document_id}")
    
    try:
        # 1. Setup dependencies manually since Celery is outside FastAPI DI
        db = SessionLocal()
        document_repo = PostgresDocumentRepository(db)
        vector_store = PostgresVectorStore(db)
        file_storage = SeaweedFSFileStorage()
        llm_service = get_llm_provider()
        
        # 2. Initialize UseCase
        use_case = ProcessDocumentUseCase(
            document_repo=document_repo,
            vector_store=vector_store,
            file_storage=file_storage,
            llm_service=llm_service
        )
        
        # 3. Execute processing (blocking call due to run_async)
        result = run_async(use_case.execute(document_id))
        
        db.close()
        logger.info(f"[Celery] Successfully processed document {document_id}")
        return result
        
    except Exception as e:
        logger.error(f"[Celery] Fatal error processing document {document_id}: {str(e)}")
        # Exponential backoff retry
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=countdown)

@celery_app.task
def cleanup_old_sessions_task():
    """Cleanup old chat sessions logic (periodic)"""
    logger.info("[Celery] Running periodic cleanup task")
    return {"status": "skipped", "message": "Not implemented yet"}


@celery_app.task(bind=True, max_retries=2)
def generate_embeddings_local_task(self, document_id: str = None, limit: int = None):
    """
    Generar embeddings locales con sentence-transformers
    Se ejecuta automáticamente después de procesar un documento
    
    Args:
        document_id: UUID del documento (opcional, para documentos específicos)
        limit: Máximo de chunks a procesar (opcional)
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    from app.infrastructure.external.local_embedding_service import LocalEmbeddingService
    
    logger.info(f"[Celery] Iniciando generación de embeddings locales (doc: {document_id})")
    
    try:
        # Inicializar servicio de embeddings
        embedding_service = LocalEmbeddingService()
        
        # Conectar a BD
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Ejecutar generación
        processed = run_async(
            _generate_embeddings_async(
                SessionLocal, 
                embedding_service, 
                document_id, 
                limit
            )
        )
        
        logger.info(f"[Celery] ✓ Generados {processed} embeddings locales")
        return {"status": "success", "embeddings_generated": processed}
    
    except Exception as e:
        logger.error(f"[Celery] Error generando embeddings: {str(e)}")
        # Reintentar con backoff
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=countdown)


async def _generate_embeddings_async(
    SessionLocal,
    embedding_service,
    document_id: str = None,
    limit: int = None
) -> int:
    """Helper async para generar embeddings"""
    from sqlalchemy import text
    
    async with SessionLocal() as session:
        # Obtener chunks sin embeddings
        query = "SELECT id, text FROM document_chunks WHERE embedding IS NULL"
        params = {}
        
        if document_id:
            query += " AND document_id = :document_id"
            params["document_id"] = document_id
        
        query += " ORDER BY created_at ASC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        result = await session.execute(text(query), params)
        chunks = result.fetchall()
        
        if not chunks:
            logger.debug("[Celery] No hay chunks pendientes")
            return 0
        
        logger.info(f"[Celery] Procesando {len(chunks)} chunks")
        
        # Generar embeddings en batch
        texts = [chunk[1] for chunk in chunks]
        chunk_ids = [chunk[0] for chunk in chunks]
        
        embeddings_list = await embedding_service.embed_batch(texts, batch_size=32)
        
        # Guardar embeddings
        updated = 0
        for chunk_id, embedding in zip(chunk_ids, embeddings_list):
            # Convertir a array de PostgreSQL (formato: [1.0, 2.0, 3.0, ...])
            embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
            
            # Usar CAST directo en la query, no en el parámetro
            await session.execute(
                text("""
                    UPDATE document_chunks 
                    SET embedding = CAST(:embedding_val AS vector)
                    WHERE id = :chunk_id_val
                """),
                {
                    "embedding_val": embedding_str,
                    "chunk_id_val": chunk_id
                }
            )
            updated += 1
        
        await session.commit()
        logger.info(f"[Celery] ✓ {updated} embeddings guardados")
        
        return updated
