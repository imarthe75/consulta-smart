#!/usr/bin/env python3
"""
Script para cargar documentos directamente a la BD sin pasar por SeaweedFS
"""

import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import asyncio
from app.core.database import init_db, close_db, get_session_factory
from app.infrastructure.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.repositories.vector_store import PostgresVectorStore
from app.infrastructure.external.llm_service import get_llm_provider
from app.domain.entities.document import Document, DocumentCategory
from app.core.logger import logger, setup_logging
import os

# Configurar logger
setup_logging("INFO")

async def load_documents():
    """Cargar documentos de la carpeta docs"""
    
    # Inicializar BD
    await init_db()
    logger.info("✅ BD inicializada")
    
    # Obtener factory de sesiones
    session_factory = get_session_factory()
    
    # Obtener servicio de embeddings
    embedding_service = get_llm_provider()
    logger.info("✅ Servicio de embeddings inicializado")
    
    # Raíz del proyecto
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    
    # Archivos a cargar
    files_to_load = list(docs_dir.rglob("*.md")) + list(docs_dir.rglob("*.txt"))
    files_to_load = [f for f in files_to_load if f.name not in ["README.md", "QUICK_REFERENCE.sh"]][:20]
    
    logger.info(f"📚 {len(files_to_load)} archivos a procesar")
    
    loaded_count = 0
    
    async with session_factory() as session:
        doc_repo = PostgresDocumentRepository(session)
        vector_store = PostgresVectorStore(session)
        
        for idx, file_path in enumerate(files_to_load, 1):
            try:
                logger.info(f"\n[{idx}/{len(files_to_load)}] 📄 {file_path.name}")
                
                # Leer contenido
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if not content.strip():
                    logger.warning(f"   ⚠️  Archivo vacío, saltando...")
                    continue
                
                # Crear documento
                document = Document(
                    title=file_path.stem,
                    category=DocumentCategory.documentacion,
                    user_id=None,  # Sistema
                    file_type=file_path.suffix.replace('.', ''),
                    seaweedfs_file_id=None,  # No usamos SeaweedFS
                    file_path=str(file_path.relative_to(project_root))
                )
                
                # Guardar documento
                doc = await doc_repo.create(document)
                await session.flush()
                
                logger.info(f"   ✅ Documento creado: {doc.id}")
                
                # Dividir contenido en chunks (500 caracteres con solapamiento)
                chunks_text = []
                chunk_size = 500
                overlap = 150
                
                for i in range(0, len(content), chunk_size - overlap):
                    chunk = content[i:i + chunk_size]
                    if chunk.strip():
                        chunks_text.append(chunk)
                
                logger.info(f"   📋 {len(chunks_text)} chunks a procesar...")
                
                # Procesar chunks
                for chunk_idx, chunk_text in enumerate(chunks_text):
                    try:
                        # Generar embedding
                        embedding = await embedding_service.embed(chunk_text)
                        
                        # Guardar chunk con embedding
                        await vector_store.add_chunk(
                            document_id=doc.id,
                            content=chunk_text,
                            embedding=embedding,
                            position=chunk_idx
                        )
                        
                        if (chunk_idx + 1) % 10 == 0:
                            logger.info(f"      ✅ {chunk_idx + 1}/{len(chunks_text)} chunks procesados")
                    
                    except Exception as e:
                        logger.error(f"      ❌ Error procesando chunk {chunk_idx}: {e}")
                        continue
                
                logger.info(f"   ✅ Documento completado: {len(chunks_text)} chunks")
                loaded_count += 1
                
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        await session.commit()
    
    # Cerrar BD
    await close_db()
    
    logger.info(f"\n✅ COMPLETADO: {loaded_count} documentos cargados")
    return loaded_count

if __name__ == "__main__":
    count = asyncio.run(load_documents())
    sys.exit(0 if count > 0 else 1)
