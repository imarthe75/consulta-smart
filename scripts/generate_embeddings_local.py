#!/usr/bin/env python3
"""
Script: Generar Embeddings Locales con Sentence Transformers
Propósito: Generar embeddings (384-dim) para todos los chunks sin APIs
Usa: sentence-transformers (modelo local, sin créditos)

Uso:
    # Generar embeddings para chunks existentes sin embedding
    python scripts/generate_embeddings_local.py
    
    # O especificar documento_id
    python scripts/generate_embeddings_local.py --document-id <uuid>
    
    # O especificar cantidad máxima
    python scripts/generate_embeddings_local.py --limit 100
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path
from typing import Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Agregar backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.config import settings
from app.core.logger import logger as app_logger

logger = app_logger

# Configuración
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dim, rápido, ligero
BATCH_SIZE = 32  # Procesar 32 chunks a la vez


class EmbeddingGenerator:
    """Genera embeddings locales sin APIs"""
    
    def __init__(self):
        logger.info(f"🤖 Cargando modelo: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        logger.info(f"✓ Modelo cargado (dimensiones: {self.model.get_sentence_embedding_dimension()})")
        
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self.SessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
    
    async def get_chunks_without_embeddings(self, limit: Optional[int] = None, document_id: Optional[str] = None) -> list:
        """Obtiene chunks sin embeddings"""
        session = self.SessionLocal()
        try:
            query = "SELECT id, text FROM document_chunks WHERE embedding IS NULL"
            params = {}
            
            if document_id:
                query += " AND document_id = :document_id"
                params["document_id"] = document_id
            
            query += " ORDER BY created_at ASC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = await session.execute(text(query), params)
            return result.fetchall()
        finally:
            await session.close()
    
    async def generate_embeddings_batch(self, chunks: list) -> dict:
        """
        Genera embeddings para un batch de chunks
        Retorna: {chunk_id: embedding}
        """
        if not chunks:
            return {}
        
        # Extraer textos
        texts = [chunk[1] for chunk in chunks]
        chunk_ids = [chunk[0] for chunk in chunks]
        
        # Generar embeddings
        logger.info(f"   🔄 Generando embeddings para {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=False, batch_size=BATCH_SIZE)
        
        # Mapear chunk_id -> embedding
        result = {chunk_ids[i]: embeddings[i].tolist() for i in range(len(chunk_ids))}
        logger.info(f"   ✓ {len(result)} embeddings generados")
        
        return result
    
    async def save_embeddings(self, embeddings_dict: dict) -> int:
        """Guarda embeddings en PostgreSQL"""
        from sqlalchemy import event
        import logging
        session = self.SessionLocal()
        updated = 0
        
        try:
            for chunk_id, embedding in embeddings_dict.items():
                # Convertir embedding a formato array
                embedding_list = list(embedding)
                
                # Usar insert/update directo con raw connection
                await session.execute(
                    text("""
                        UPDATE document_chunks 
                        SET embedding = :vec::vector
                        WHERE id = :id
                    """).bindparams(
                        vec="[" + ",".join(map(str, embedding_list)) + "]",
                        id=chunk_id
                    )
                )
                updated += 1
            
            await session.commit()
            logger.info(f"   ✅ {updated} embeddings guardados en BD")
            return updated
        
        except Exception as e:
            logger.error(f"   ❌ Error guardando embeddings: {str(e)}")
            await session.rollback()
            return 0
        
        finally:
            await session.close()
    
    async def generate_all_embeddings(self, limit: Optional[int] = None, document_id: Optional[str] = None) -> tuple:
        """
        Genera y guarda todos los embeddings pendientes
        Retorna: (total_procesados, total_errores)
        """
        logger.info("=" * 80)
        logger.info("🚀 GENERANDO EMBEDDINGS LOCALES (SENTENCE-TRANSFORMERS)")
        logger.info("=" * 80)
        
        # Obtener chunks sin embeddings
        logger.info("\n[STEP 1] Buscando chunks sin embeddings...")
        chunks = await self.get_chunks_without_embeddings(limit=limit, document_id=document_id)
        
        if not chunks:
            logger.warning("⚠️  No hay chunks pendientes de embeddings")
            return 0, 0
        
        logger.info(f"   Encontrados: {len(chunks)} chunks\n")
        
        # Procesar por batches
        logger.info("[STEP 2] Generando embeddings por batches...\n")
        
        total_processed = 0
        total_errors = 0
        batch_size = 128  # Procesar 128 chunks a la vez
        
        for batch_idx in range(0, len(chunks), batch_size):
            batch_end = min(batch_idx + batch_size, len(chunks))
            batch_chunks = chunks[batch_idx:batch_end]
            
            logger.info(f"   Batch {batch_idx // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}")
            logger.info(f"   Procesando chunks {batch_idx + 1}-{batch_end} de {len(chunks)}")
            
            try:
                # Generar embeddings
                embeddings_dict = await self.generate_embeddings_batch(batch_chunks)
                
                # Guardar en BD
                updated = await self.save_embeddings(embeddings_dict)
                total_processed += updated
            
            except Exception as e:
                logger.error(f"   ❌ Error en batch: {e}")
                total_errors += len(batch_chunks)
                continue
        
        # Resumen final
        logger.info("\n" + "=" * 80)
        logger.info(f"✅ COMPLETADO: {total_processed} embeddings generados")
        if total_errors > 0:
            logger.warning(f"⚠️  {total_errors} errores")
        logger.info("=" * 80)
        
        # Estadísticas
        logger.info("\n📊 Estadísticas:")
        session = self.SessionLocal()
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
            )
            with_embedding = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM document_chunks")
            )
            total = result.scalar()
            
            logger.info(f"   • Chunks con embedding: {with_embedding}/{total}")
            logger.info(f"   • Cobertura: {(with_embedding/total*100):.1f}%")
        finally:
            await session.close()
        
        return total_processed, total_errors
    
    async def close(self):
        """Cerrar conexión a BD"""
        await self.engine.dispose()


async def main():
    parser = argparse.ArgumentParser(
        description="Generar embeddings locales con sentence-transformers"
    )
    parser.add_argument(
        "--document-id",
        help="UUID del documento para regenerar embeddings",
        type=str
    )
    parser.add_argument(
        "--limit",
        help="Límite máximo de chunks a procesar",
        type=int
    )
    
    args = parser.parse_args()
    
    generator = EmbeddingGenerator()
    
    try:
        processed, errors = await generator.generate_all_embeddings(
            limit=args.limit,
            document_id=args.document_id
        )
        
        success = errors == 0
        if processed > 0:
            logger.info(f"\n💡 Búsqueda semántica ahora disponible con {processed} embeddings")
        
        return success
    
    finally:
        await generator.close()


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)
