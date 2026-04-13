#!/usr/bin/env python3
"""
Script: Cargar RPP Registry SIN embeddings
Solo inserta documentos en PostgreSQL sin generar embeddings (NULL)
Los embeddings pueden generarse después cuando haya LLM disponible
"""

import asyncio
import sys
import os
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Agregar backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.config import settings
from app.core.logger import logger as app_logger

logger = app_logger

# Configuración
DOCS_PATH = Path(__file__).parent.parent / "docs" / "rpp-registry"


async def load_rpp_registry_no_embeddings():
    """Carga RPP Registry sin embeddings (rápido)"""
    
    if not DOCS_PATH.exists():
        logger.error(f"❌ Ruta no encontrada: {DOCS_PATH}")
        return False
    
    logger.info("=" * 80)
    logger.info("🚀 CARGA RÁPIDA: RPP REGISTRY → POSTGRESQL (SIN EMBEDDINGS)")
    logger.info("=" * 80)
    
    # Conectar a base de datos
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Crear usuario del sistema si no existe
            logger.info("\n[STEP 1] Verificando usuario del sistema...")
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email LIMIT 1"),
                {"email": "system@rpp-registry.local"}
            )
            system_user_id = result.scalar()
            
            if not system_user_id:
                logger.info("   Creando usuario del sistema...")
                system_user_id = str(uuid.uuid4())
                await session.execute(
                    text("""
                        INSERT INTO users (id, email, username, password_hash, is_active, created_at, updated_at)
                        VALUES (:id, :email, :username, :password_hash, :is_active, NOW(), NOW())
                    """),
                    {
                        "id": system_user_id,
                        "email": "system@rpp-registry.local",
                        "username": "sistema-rpp-registry",
                        "password_hash": "disabled",
                        "is_active": True
                    }
                )
                await session.commit()
            else:
                logger.info(f"   ✓ Usuario del sistema: {system_user_id}")
            
            # Buscar archivos MD
            logger.info("\n[STEP 2] Buscando documentos MD...")
            md_files = list(DOCS_PATH.glob("**/*.md"))
            logger.info(f"   Encontrados: {len(md_files)} archivos")
            
            if not md_files:
                logger.warning("⚠️ No hay archivos MD")
                return False
            
            success = 0
            error = 0
            chunk_count = 0
            
            logger.info("\n[STEP 3] Cargando documentos...\n")
            
            # Procesar cada archivo
            for idx, md_file in enumerate(md_files, 1):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    if not content.strip():
                        logger.warning(f"   ⏭️  [{idx}/{len(md_files)}] {md_file.name} (vacío)")
                        continue
                    
                    # ID del documento
                    doc_id = str(uuid.uuid4())
                    
                    logger.info(f"   [{idx}/{len(md_files)}] {md_file.name}")
                    
                    # Determinar categoría
                    filename = md_file.name.lower()
                    if "oficial" in filename or "contacto" in filename or "delegacion" in filename:
                        category = "reglamento"
                    elif "notario" in filename:
                        category = "formulario"
                    elif "costo" in filename or "arancel" in filename or "derecho" in filename:
                        category = "ley"
                    elif "procedimiento" in filename or "requisito" in filename:
                        category = "procedimiento"
                    else:
                        category = "guia"
                    
                    # Insertar documento
                    await session.execute(
                        text("""
                            INSERT INTO documents 
                            (id, title, category, user_id, file_type, status, created_at, updated_at)
                            VALUES (:id, :title, :category, :user_id, :file_type, :status, NOW(), NOW())
                        """),
                        {
                            "id": doc_id,
                            "title": f"RPP - {md_file.name}",
                            "category": category,
                            "user_id": system_user_id,
                            "file_type": "md",
                            "status": "completed"
                        }
                    )
                    
                    # Dividir en chunks
                    chunk_size = 800
                    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                    
                    logger.info(f"       Ingestionando ({len(chunks)} chunks)...")
                    
                    # Crear chunks SIN embeddings
                    for chunk_idx, chunk_text in enumerate(chunks):
                        try:
                            # Insertar chunk SIN embedding (NULL)
                            chunk_id = str(uuid.uuid4())
                            await session.execute(
                                text("""
                                    INSERT INTO document_chunks 
                                    (id, document_id, chunk_number, text, embedding, created_at)
                                    VALUES (:id, :document_id, :chunk_number, :text, NULL, NOW())
                                """),
                                {
                                    "id": chunk_id,
                                    "document_id": doc_id,
                                    "chunk_number": chunk_idx,
                                    "text": chunk_text
                                }
                            )
                            chunk_count += 1
                        except Exception as e:
                            logger.error(f"       ❌ Error chunk {chunk_idx}: {str(e)}")
                            continue
                    
                    await session.commit()
                    logger.info(f"       ✅ Cargado ({len(chunks)} chunks)")
                    success += 1
                
                except Exception as e:
                    logger.error(f"       ❌ Error: {str(e)}")
                    await session.rollback()
                    error += 1
                    continue
            
            # Resumen
            logger.info("\n" + "=" * 80)
            logger.info(f"✅ COMPLETADO: {success} documentos ingestionados")
            if error > 0:
                logger.warning(f"⚠️  {error} errores durante la carga")
            logger.info("=" * 80)
            
            # Estadísticas
            logger.info("\n📊 Estadísticas Finales:")
            result = await session.execute(
                text("SELECT COUNT(*) FROM documents WHERE user_id = :user_id"),
                {"user_id": system_user_id}
            )
            doc_count = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE document_id IN (SELECT id FROM documents WHERE user_id = :user_id)"),
                {"user_id": system_user_id}
            )
            chunk_total = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE document_id IN (SELECT id FROM documents WHERE user_id = :user_id) AND embedding IS NOT NULL"),
                {"user_id": system_user_id}
            )
            chunks_with_embedding = result.scalar()
            
            logger.info(f"   • Documentos RPP: {doc_count}")
            logger.info(f"   • Chunks totales: {chunk_total}")
            logger.info(f"   • Chunks con embedding: {chunks_with_embedding}")
            
            logger.info("\n🔔 NOTA:")
            logger.info("   Los embeddings están en NULL (no se generaron).")
            logger.info("   Búsqueda textual disponible.")
            logger.info("   Para generar embeddings: Usar API key con créditos disponibles")
            
            return error == 0
    
    except Exception as e:
        logger.error(f"❌ Error fatal: {str(e)}", exc_info=True)
        return False
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        result = asyncio.run(load_rpp_registry_no_embeddings())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        sys.exit(1)
