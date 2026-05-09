#!/usr/bin/env python3
"""
Ingesta completa de la Knowledge Base de ConsultaRPP.
Carga todos los .md de docs/knowledge_base/ en la base de datos.
Los embeddings se generan asíncronamente por el worker de Celery.
"""
import asyncio
import sys
import os
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# ── Configuración ────────────────────────────────────────────────────────────
# Usuario administrador existente en la BD restaurada
SYSTEM_USER_ID = "342a1c45-fe13-4981-b90e-e31d358ac577"  # arquiteturacasmarts@gmail.com

# Directorio de documentos
DOCS_DIR = Path(__file__).parent.parent / "docs" / "knowledge_base"

# Tamaño de chunks y solapamiento
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def split_into_chunks(content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Divide el texto en chunks con solapamiento inteligente (por párrafos)."""
    chunks = []
    paragraphs = content.split('\n\n')
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Si agregar el párrafo excede el límite, guardar el chunk actual
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Mantener último trozo de solapamiento
            words = current_chunk.split()
            overlap_text = ' '.join(words[-int(overlap/5):]) if words else ""
            current_chunk = overlap_text + '\n\n' + para
        else:
            current_chunk = current_chunk + '\n\n' + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return [c for c in chunks if len(c) > 20]


async def ingest_all():
    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    md_files = sorted(DOCS_DIR.glob("**/*.md"))
    md_files = [f for f in md_files if f.name not in ("README.md", "INDEX.md", "CARGAR_KNOWLEDGE_BASE.md")]

    print(f"\n📚 Documentos encontrados: {len(md_files)}")
    print("=" * 60)

    total_docs = 0
    total_chunks = 0
    skipped = 0

    async with async_session() as session:
        # Verificar usuario
        result = await session.execute(
            text("SELECT id FROM users WHERE id = :uid"),
            {"uid": SYSTEM_USER_ID}
        )
        if not result.scalar():
            print(f"❌ Usuario {SYSTEM_USER_ID} no encontrado.")
            return

        for md_path in md_files:
            # Determinar región
            parent = md_path.parent.name
            region_tag = f"[{parent.upper()}] " if parent in ("puebla", "quintana-roo", "general") else ""
            doc_title = f"{region_tag}{md_path.stem}"

            # Verificar si ya existe
            result = await session.execute(
                text("SELECT id FROM documents WHERE title = :title LIMIT 1"),
                {"title": doc_title}
            )
            existing = result.scalar()
            if existing:
                print(f"  ⏭️  Ya existe: {doc_title}")
                skipped += 1
                continue

            content = md_path.read_text(encoding="utf-8", errors="ignore")
            if len(content.strip()) < 50:
                print(f"  ⚠️  Vacío: {md_path.name}")
                skipped += 1
                continue

            # Determinar categoría
            name_lower = md_path.stem.lower()
            if "faq" in name_lower or "frecuentes" in name_lower or "preguntas" in name_lower:
                category = "faq"
            elif "costo" in name_lower or "arancel" in name_lower:
                category = "costos"
            elif "legisl" in name_lower or "ley" in name_lower:
                category = "legislacion"
            elif "procedimiento" in name_lower or "tramite" in name_lower:
                category = "procedimiento"
            else:
                category = "documentacion_rpp"

            try:
                doc_id = str(uuid.uuid4())
                await session.execute(
                    text("""
                        INSERT INTO documents
                        (id, title, category, user_id, file_type, status, version, is_active, created_at, updated_at)
                        VALUES (:id, :title, :category, :user_id, :file_type, :status, :version, true, NOW(), NOW())
                    """),
                    {
                        "id": doc_id,
                        "title": doc_title,
                        "category": category,
                        "user_id": SYSTEM_USER_ID,
                        "file_type": "md",
                        "status": "completed",
                        "version": 1,
                    }
                )
                await session.flush()

                chunks = split_into_chunks(content)
                for idx, chunk_text in enumerate(chunks):
                    await session.execute(
                        text("""
                            INSERT INTO document_chunks
                            (id, document_id, chunk_number, text, created_at)
                            VALUES (:id, :document_id, :chunk_number, :text, NOW())
                        """),
                        {
                            "id": str(uuid.uuid4()),
                            "document_id": doc_id,
                            "chunk_number": idx,
                            "text": chunk_text,
                        }
                    )

                await session.execute(
                    text("UPDATE documents SET chunk_count = :count WHERE id = :id"),
                    {"count": len(chunks), "id": doc_id}
                )
                await session.commit()

                print(f"  ✅ {doc_title} ({len(chunks)} chunks, {len(content)} chars)")
                total_docs += 1
                total_chunks += len(chunks)

            except Exception as e:
                print(f"  ❌ Error en {md_path.name}: {e}")
                await session.rollback()
                skipped += 1

    print("\n" + "=" * 60)
    print(f"📊 RESUMEN:")
    print(f"   ✅ Documentos cargados: {total_docs}")
    print(f"   📋 Chunks creados:      {total_chunks}")
    print(f"   ⏭️  Saltados:            {skipped}")
    print("=" * 60)
    print("\n⚠️  NOTA: Los chunks se cargaron SIN embeddings vectoriales.")
    print("   Para habilitar búsqueda semántica, ejecuta el generador de embeddings.")
    print("   El chat usará búsqueda por texto hasta que los embeddings estén listos.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(ingest_all())
