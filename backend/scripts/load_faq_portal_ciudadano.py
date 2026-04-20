#!/usr/bin/env python3
"""
Script específico: Cargar FAQ Portal Ciudadano RPPC Quintana Roo
Inserta el documento de preguntas frecuentes en PostgreSQL con embeddings.
Corrección: usa cast explícito mediante texto+parámetro compatible con asyncpg.
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
from app.infrastructure.external.llm_service import get_llm_provider

logger = app_logger

# Documento a cargar
FAQ_DOC_PATH = (
    Path(__file__).parent.parent
    / "docs"
    / "rpp-registry"
    / "quintana-roo"
    / "PREGUNTAS_FRECUENTES_PORTAL_CIUDADANO.md"
)

SYSTEM_EMAIL = "system@rpp-registry.local"


async def load_faq_document():
    """Carga el FAQ del Portal Ciudadano directamente en PostgreSQL."""

    if not FAQ_DOC_PATH.exists():
        logger.error(f"❌ Archivo no encontrado: {FAQ_DOC_PATH}")
        return False

    logger.info("=" * 80)
    logger.info("🚀 CARGANDO: FAQ Portal Ciudadano RPPC Quintana Roo")
    logger.info("=" * 80)
    logger.info(f"   Archivo: {FAQ_DOC_PATH.name}")

    content = FAQ_DOC_PATH.read_text(encoding="utf-8")
    if not content.strip():
        logger.error("❌ El archivo está vacío.")
        return False

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    llm = get_llm_provider()

    try:
        async with async_session() as session:

            # ── Paso 1: Verificar usuario del sistema ──────────────────────────
            logger.info("\n[PASO 1] Verificando usuario del sistema...")
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email LIMIT 1"),
                {"email": SYSTEM_EMAIL},
            )
            system_user_id = result.scalar()

            if not system_user_id:
                logger.error(f"❌ Usuario del sistema no encontrado: {SYSTEM_EMAIL}")
                logger.error("   Ejecuta primero load_rpp_registry_direct.py para crearlo.")
                return False

            logger.info(f"   ✓ Usuario: {system_user_id}")

            # ── Paso 2: Verificar si ya existe el documento ────────────────────
            logger.info("\n[PASO 2] Verificando si el documento ya existe...")
            result = await session.execute(
                text("SELECT id FROM documents WHERE title = :title LIMIT 1"),
                {"title": f"RPP - {FAQ_DOC_PATH.name}"},
            )
            existing_id = result.scalar()

            if existing_id:
                logger.warning(f"   ⚠️  El documento ya existe (id={existing_id})")
                logger.warning("   Eliminando versión anterior para re-cargar...")
                await session.execute(
                    text("DELETE FROM document_chunks WHERE document_id = :doc_id"),
                    {"doc_id": existing_id},
                )
                await session.execute(
                    text("DELETE FROM documents WHERE id = :doc_id"),
                    {"doc_id": existing_id},
                )
                await session.commit()
                logger.info("   ✓ Versión anterior eliminada.")

            # ── Paso 3: Insertar el documento ──────────────────────────────────
            logger.info("\n[PASO 3] Insertando documento...")
            doc_id = str(uuid.uuid4())
            await session.execute(
                text(
                    """
                    INSERT INTO documents
                    (id, title, category, user_id, file_type, status, created_at, updated_at)
                    VALUES (:id, :title, :category, :user_id, :file_type, :status, NOW(), NOW())
                    """
                ),
                {
                    "id": doc_id,
                    "title": f"RPP - {FAQ_DOC_PATH.name}",
                    "category": "procedimiento",
                    "user_id": system_user_id,
                    "file_type": "md",
                    "status": "completed",
                },
            )
            await session.commit()
            logger.info(f"   ✓ Documento insertado (id={doc_id})")

            # ── Paso 4: Dividir en chunks y generar embeddings ─────────────────
            chunk_size = 800
            chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]
            logger.info(f"\n[PASO 4] Generando embeddings ({len(chunks)} chunks)...")

            success_chunks = 0
            for chunk_idx, chunk_text in enumerate(chunks):
                try:
                    embedding = await llm.embed(chunk_text)

                    # CORRECCIÓN: usar text() con cast PostgreSQL compatible con asyncpg
                    # En asyncpg con SQLAlchemy se usa $N para parámetros posicionales
                    # pero al usar text() con bindparams el cast debe hacerse
                    # dentro de una función o con cast(), no con `:param::type`
                    chunk_id = str(uuid.uuid4())
                    await session.execute(
                        text(
                            """
                            INSERT INTO document_chunks
                            (id, document_id, chunk_number, text, embedding, created_at)
                            VALUES (:id, :document_id, :chunk_number, :text,
                                    CAST(:embedding AS vector), NOW())
                            """
                        ),
                        {
                            "id": chunk_id,
                            "document_id": doc_id,
                            "chunk_number": chunk_idx,
                            "text": chunk_text,
                            "embedding": str(embedding),
                        },
                    )
                    await session.commit()
                    success_chunks += 1
                    logger.info(f"   ✓ Chunk {chunk_idx + 1}/{len(chunks)} embedido")

                except Exception as e:
                    logger.error(f"   ❌ Error en chunk {chunk_idx}: {e}")
                    await session.rollback()
                    continue

            # ── Paso 5: Actualizar chunk_count ────────────────────────────────
            await session.execute(
                text("UPDATE documents SET chunk_count = :count WHERE id = :id"),
                {"count": success_chunks, "id": doc_id},
            )
            await session.commit()

            # ── Resumen ────────────────────────────────────────────────────────
            logger.info("\n" + "=" * 80)
            logger.info(f"✅ FAQ cargado: {success_chunks}/{len(chunks)} chunks con embeddings")
            logger.info("=" * 80)

            if success_chunks == 0:
                logger.warning("⚠️  Ningún chunk se procesó correctamente con embeddings.")
                logger.warning("   El documento existe en BD pero sin vectores de búsqueda.")
                return False

            return True

    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        result = asyncio.run(load_faq_document())
        if result:
            print("\n🎉 FAQ del Portal Ciudadano cargado exitosamente en la Knowledge Base.")
        else:
            print("\n❌ La carga falló. Revisa los logs para más detalles.")
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)
