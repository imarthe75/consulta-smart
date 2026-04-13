#!/usr/bin/env python3
"""
generate-embeddings.py - Generar embeddings para todos los chunks existentes en la BD
Esto es CRÍTICO para que el RAG funcione correctamente con búsqueda vectorial
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import init_db, close_db, get_session_factory
from app.infrastructure.external.llm_service import get_llm_provider
from app.core.logger import logger, setup_logging
from sqlalchemy import text as sql_text

setup_logging("INFO")


async def generate_embeddings():
    """Generar embeddings para todos los chunks"""
    
    # Inicializar DB
    await init_db()
    logger.info("✅ BD inicializada")
    
    # Obtener factory de sesiones
    session_factory = get_session_factory()
    
    # Obtener servicio de embeddings
    embedding_service = get_llm_provider()
    logger.info("✅ Servicio de embeddings inicializado")
    
    async with session_factory() as session:
        try:
            # 1. Contar chunks sin embeddings
            result = await session.execute(sql_text("""
                SELECT COUNT(*) FROM document_chunks 
                WHERE embedding IS NULL
            """))
            count_without = result.scalar() or 0
            logger.info(f"📊 Chunks sin embeddings: {count_without}")
            
            # 2. Obtener todos los chunks sin embeddings
            result = await session.execute(sql_text("""
                SELECT id, text FROM document_chunks 
                WHERE embedding IS NULL
                ORDER BY created_at DESC
            """))
            
            chunks_to_process = result.fetchall()
            logger.info(f"📋 Procesando {len(chunks_to_process)} chunks...")
            
            if not chunks_to_process:
                logger.info("✅ Todos los chunks ya tienen embeddings")
                await close_db()
                return 0
            
            # 3. Generar embeddings
            processed_count = 0
            error_count = 0
            
            for idx, (chunk_id, text) in enumerate(chunks_to_process, 1):
                try:
                    # Generar embedding
                    embedding = await embedding_service.embed(text)
                    
                    # Guardar en BD
                    await session.execute(sql_text("""
                        UPDATE document_chunks 
                        SET embedding = :embedding::vector
                        WHERE id = :chunk_id
                    """), {
                        "embedding": embedding,
                        "chunk_id": chunk_id
                    })
                    
                    processed_count += 1
                    
                    # Log cada 10 chunks
                    if idx % 10 == 0:
                        logger.info(f"   ✅ {idx}/{len(chunks_to_process)} chunks procesados")
                
                except Exception as e:
                    logger.error(f"   ❌ Error procesando chunk {chunk_id}: {e}")
                    error_count += 1
            
            # Confirmar cambios
            await session.commit()
            
            # Contar embeddings generados
            result = await session.execute(sql_text("""
                SELECT COUNT(*) FROM document_chunks 
                WHERE embedding IS NOT NULL
            """))
            total_with_embeddings = result.scalar() or 0
            
            logger.info(f"\n✅ COMPLETADO")
            logger.info(f"   📈 Procesados: {processed_count}/{len(chunks_to_process)}")
            logger.info(f"   ❌ Errores: {error_count}")
            logger.info(f"   🎯 Total con embeddings: {total_with_embeddings}")
            
            return processed_count
        
        except Exception as e:
            logger.error(f"❌ Error fatal: {e}")
            import traceback
            traceback.print_exc()
            return -1
        
        finally:
            await close_db()
            logger.info("✅ Conexión cerrada")


if __name__ == "__main__":
    logger.info("🚀 Iniciando generación de embeddings...")
    count = asyncio.run(generate_embeddings())
    
    if count > 0:
        logger.info(f"✅ {count} embeddings generados exitosamente")
        sys.exit(0)
    elif count == 0:
        logger.info("ℹ️ No hay chunks sin embeddings")
        sys.exit(0)
    else:
        logger.error("❌ Error durante generación de embeddings")
        sys.exit(1)
