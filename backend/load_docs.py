#!/usr/bin/env python3
"""
Script robusto para cargar documentos de expertos (2026) en la BD
"""

import sys
import asyncio
from pathlib import Path
import uuid

# Añadir backend al path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.core.database import init_db, close_db, get_session_factory
from app.infrastructure.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.repositories.vector_store import PostgresVectorStore
from app.infrastructure.external.llm_service import get_local_embedding_service
from app.domain.entities.document import Document, DocumentCategory
from app.core.logger import logger, setup_logging

# Configurar logger
setup_logging("INFO")

async def load_documents():
    """Cargar documentos de la carpeta docs/rpp_expert"""
    
    await init_db()
    session_factory = get_session_factory()
    embedding_service = get_local_embedding_service()
    
    docs_dir = Path(__file__).parent / "docs"
    files_to_load = list(docs_dir.rglob("*.md"))
    # Priorizar mis nuevos documentos
    files_to_load = [f for f in files_to_load if "2026" in f.name or "GUIA" in f.name]
    
    logger.info(f"📚 {len(files_to_load)} manuales expertos encontrados para procesar")
    
    loaded_count = 0
    
    async with session_factory() as session:
        doc_repo = PostgresDocumentRepository(session)
        vector_store = PostgresVectorStore(session)
        
        # Obtener un usuario real existente
        user_result = await session.execute(text("SELECT id FROM users LIMIT 1"))
        first_user = user_result.scalar_one_or_none()
        valid_user_id = first_user if first_user else "00000000-0000-0000-0000-000000000000"

        for idx, file_path in enumerate(files_to_load, 1):
            try:
                logger.info(f"[{idx}/{len(files_to_load)}] 📄 Procesando: {file_path.name}")
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if not content.strip():
                    continue
                
                # Crear Entidad
                document = Document(
                    title=file_path.stem,
                    category=DocumentCategory.PROCEDIMIENTO,
                    user_id=valid_user_id,
                    file_type="md"
                )
                
                # Guardar en DB (Documents)
                doc = await doc_repo.create(document)
                await session.flush()
                
                # Crear Chunks
                chunks_text = []
                chunk_size = 800
                overlap = 200
                for i in range(0, len(content), chunk_size - overlap):
                    chunk = content[i:i + chunk_size]
                    if chunk.strip():
                        chunks_text.append(chunk)
                
                # Generar Embeddings y Guardar (Chunks)
                for chunk_idx, chunk_text in enumerate(chunks_text):
                    embedding = await embedding_service.embed(chunk_text)
                    await vector_store.add(
                        vector_id=str(uuid.uuid4()),
                        text_content=chunk_text,
                        embedding=embedding,
                        metadata={
                            "document_id": doc.id,
                            "chunk_number": chunk_idx
                        }
                    )
                
                logger.info(f"   ✅ ÉXITO: {file_path.name} ({len(chunks_text)} chunks)")
                loaded_count += 1
                
            except Exception as e:
                logger.error(f"   ❌ ERROR en {file_path.name}: {str(e)}")
                await session.rollback()
                continue
        
        await session.commit()
    
    await close_db()
    logger.info(f"\n🎯 CARGA FINALIZADA: {loaded_count} documentos nuevos disponibles.")
    return loaded_count

if __name__ == "__main__":
    count = asyncio.run(load_documents())
    sys.exit(0 if count > 0 else 1)
