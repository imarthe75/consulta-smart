#!/usr/bin/env python3
"""
Script para cargar documentos del RPP-registry en la base de conocimientos
Carga archivos MD de requisitos, costos y legislación en la base de datos vectorial

Uso:
    python scripts/load_rpp_documents.py
    
Pre-requisitos:
    - PostgreSQL ejecutándose
    - Backend inicializado (DB schema creado)
    - Archivos MD en docs/rpp-registry/
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
from app.core.logger import logger
from app.domain.entities.document import Document, DocumentCategory
from app.infrastructure.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.repositories.vector_store import PostgresVectorStore
from app.infrastructure.external.seaweedfs_service import SeaweedFSFileStorage
from app.infrastructure.external.llm_service import get_llm_provider


async def get_or_create_system_user(session: AsyncSession):
    """Obtiene o crea el usuario del sistema para documentos RPP"""
    
    # Buscar usuario del sistema
    system_user_email = "system@rpp-registry.local"
    result = await session.execute(
        text("SELECT id FROM users WHERE email = :email LIMIT 1"),
        {"email": system_user_email}
    )
    existing_user = result.scalar()
    
    if existing_user:
        logger.info(f"✓ Usuario del sistema encontrado: {existing_user}")
        return existing_user
    
    # Si no existe, crear usuario del sistema
    logger.warning(f"⚠️  Usuario del sistema no encontrado. Creando: {system_user_email}")
    system_user_id = str(uuid.uuid4())
    
    await session.execute(
        text("""
            INSERT INTO users (id, email, username, password_hash, is_active, created_at, updated_at)
            VALUES (:id, :email, :username, :password_hash, :is_active, NOW(), NOW())
            ON CONFLICT (email) DO NOTHING
        """),
        {
            "id": system_user_id,
            "email": system_user_email,
            "username": "sistema-rpp-registry",
            "password_hash": "disabled",
            "is_active": True
        }
    )
    
    await session.commit()
    logger.info(f"✓ Usuario sistema creado: {system_user_id}")
    return system_user_id


async def load_rpp_documents():
    """Carga todos los documentos MD del rpp-registry en la base de conocimientos"""
    
    # Rutas de documentos
    docs_path = Path(__file__).parent.parent / "docs" / "rpp-registry"
    
    if not docs_path.exists():
        logger.error(f"❌ Ruta de documentos no encontrada: {docs_path}")
        return False
    
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO CARGA RPP REGISTRY → KNOWLEDGE BASE")
    logger.info("=" * 80)
    
    # Conectar a base de datos
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Obtener usuario del sistema
            logger.info("\n[STEP 1] Obteniendo usuario del sistema...")
            system_user_id = await get_or_create_system_user(session)
            
            repo = PostgresDocumentRepository(session)
            vector_store = PostgresVectorStore(session)
            llm_service = get_llm_provider()
            
            # Buscar todos los MD en rpp-registry
            logger.info("\n[STEP 2] Buscando documentos MD...")
            md_files = list(docs_path.glob("**/*.md"))
            logger.info(f"   Encontrados {len(md_files)} documentos para cargar\n")
            
            if not md_files:
                logger.warning("⚠️  No hay archivos MD en rpp-registry/")
                return False
            
            success_count = 0
            error_count = 0
            
            logger.info("[STEP 3] Cargando documentos...\n")
            
            for idx, md_file in enumerate(md_files, 1):
                try:
                    # Leer contenido del archivo
                    content = md_file.read_text(encoding="utf-8")
                    relative_path = md_file.relative_to(docs_path)
                    
                    if not content.strip():
                        logger.warning(f"   ⏭️  Archivo vacío: {relative_path}")
                        continue
                    
                    # Determinar categoría basada en el nombre del archivo
                    filename = md_file.name.lower()
                    if "costo" in filename or "arancel" in filename or "derecho" in filename:
                        category = DocumentCategory.OTRO
                    elif "procedimiento" in filename or "requisito" in filename:
                        category = DocumentCategory.PROCEDIMIENTO
                    elif "legislacion" in filename or "ley" in filename:
                        category = DocumentCategory.LEY
                    elif "oficina" in filename or "contacto" in filename or "delegacion" in filename:
                        category = DocumentCategory.REGLAMENTO
                    elif "notario" in filename or "registro" in filename:
                        category = DocumentCategory.REGLAMENTO
                    else:
                        category = DocumentCategory.REGLAMENTO
                    
                    logger.info(f"   [{idx}/{len(md_files)}] {relative_path}")
                    logger.info(f"       Categoría: {category.value}")
                    
                    # Crear documento
                    document = Document(
                        title=f"RPP Registry - {relative_path}",
                        content=content,
                        category=category,
                        file_type="md",
                        seaweedfs_file_id=None,
                        user_id=system_user_id
                    )
                    
                    # Guardar en BD
                    created_doc = await repo.create(document)
                    
                    # Generar embeddings del contenido
                    logger.info(f"       Generando embeddings...")
                    
                    # Dividir en chunks (max 800 caracteres por chunk)
                    chunk_size = 800
                    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                    
                    for cidx, chunk in enumerate(chunks):
                        # Generar embedding
                        embedding = await llm_service.embed(chunk)
                        
                        # Guardar chunk vectorizado
                        await vector_store.add_document_chunk(
                            document_id=created_doc.id,
                            chunk_text=chunk,
                            chunk_index=cidx,
                            embedding=embedding
                        )
                    
                    await session.commit()
                    logger.info(f"       ✅ Cargado ({len(chunks)} chunks)")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"       ❌ Error: {str(e)}")
                    await session.rollback()
                    error_count += 1
                    continue
            
            # Resumen final
            logger.info("\n" + "=" * 80)
            logger.info(f"✅ CARGA COMPLETADA: {success_count} documentos exitosos, {error_count} errores")
            logger.info("=" * 80)
            logger.info("\nAhora puedes hacer preguntas sobre:")
            logger.info("  • Oficinas en Puebla y Quintana Roo")
            logger.info("  • Notarios disponibles")
            logger.info("  • Requisitos por acto")
            logger.info("  • Costos y aranceles")
            logger.info("  • Horarios y servicios")
            
            return error_count == 0
    
    except Exception as e:
        logger.error(f"\n❌ Error fatal: {str(e)}", exc_info=True)
        return False
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        result = asyncio.run(load_rpp_documents())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)
