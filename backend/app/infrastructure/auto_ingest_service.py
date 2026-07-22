import os
import asyncio
import logging
from pathlib import Path
from uuid import uuid4
import fitz  # PyMuPDF

from app.core.database import get_session_factory
from app.infrastructure.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.repositories.vector_store import PostgresVectorStore
from app.infrastructure.external.llm_service import get_llm_provider
from app.domain.entities.document import Document, DocumentCategory

logger = logging.getLogger(__name__)

# Directorio a monitorizar
VAULT_INPUT_DIR = Path("/app/vault_input")
PROCESSED_DIR = VAULT_INPUT_DIR / "processed"

async def extract_text_from_file(file_path: Path) -> str:
    """Extrae texto del archivo según su extensión"""
    ext = file_path.suffix.lower()
    if ext == '.pdf':
        logger.info(f"📄 Extrayendo texto de PDF usando PyMuPDF: {file_path.name}")
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        return text
    elif ext == '.md' or ext == '.txt':
        logger.info(f"📄 Leyendo archivo de texto: {file_path.name}")
        return file_path.read_text(encoding='utf-8', errors='ignore')
    return ""

async def process_single_file(file_path: Path):
    """Procesa un archivo individual: extracción, chunking, embeddings e indexación"""
    session_factory = get_session_factory()
    embedding_service = get_llm_provider()
    
    logger.info(f"🚀 Iniciando procesamiento automático para: {file_path.name}")
    
    # Asegurar directorio de procesados
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    async with session_factory() as session:
        doc_repo = PostgresDocumentRepository(session)
        vector_store = PostgresVectorStore(session)
        
        try:
            content = await extract_text_from_file(file_path)
            if not content.strip():
                logger.warning(f"⚠️ El archivo {file_path.name} está vacío. Saltando.")
                # Mover a procesados de todos modos para no re-procesar
                file_path.rename(PROCESSED_DIR / file_path.name)
                return
            
            # Determinar categoría básica
            category = DocumentCategory.OTRO
            filename = file_path.name.lower()
            if "costo" in filename or "arancel" in filename:
                category = DocumentCategory.FORMULARIO
            elif "procedimiento" in filename or "requisito" in filename:
                category = DocumentCategory.PROCEDIMIENTO
            elif "ley" in filename or "legislacion" in filename:
                category = DocumentCategory.LEY
            elif "reglamento" in filename:
                category = DocumentCategory.REGLAMENTO
            
            # Crear documento lógico en DB
            document = Document(
                title=file_path.stem,
                category=category,
                user_id="019d73a6-d320-7c49-bee7-b19f368473ec",  # usuario demo
                file_type=file_path.suffix.replace('.', ''),
                is_active=True
            )
            
            created_doc = await doc_repo.create(document)
            await session.flush()
            
            # Chunking
            chunks_text = []
            chunk_size = 800
            overlap = 200
            for i in range(0, len(content), chunk_size - overlap):
                chunk = content[i:i + chunk_size]
                if chunk.strip():
                    chunks_text.append(chunk)
            
            # Generar Embeddings y Guardar Chunks
            logger.info(f"🧠 Generando embeddings para {len(chunks_text)} chunks del archivo: {file_path.name}")
            for idx, chunk_text in enumerate(chunks_text):
                try:
                    embedding = await embedding_service.embed(chunk_text)
                except Exception as embed_err:
                    logger.warning(f"⚠️ Error generando embedding para chunk {idx}: {embed_err}. Se guardará sin embedding.")
                    embedding = None
                
                from uuid6 import uuid7
                await vector_store.add(
                    vector_id=str(uuid7()),
                    text_content=chunk_text,
                    embedding=embedding,
                    metadata={
                        "document_id": created_doc.id,
                        "chunk_number": idx
                    }
                )
            
            # Guardar cambios
            await session.commit()
            logger.info(f"✅ Archivo {file_path.name} indexado correctamente con ID: {created_doc.id}")
            
            # Mover archivo a procesados
            target_path = PROCESSED_DIR / file_path.name
            if target_path.exists():
                target_path.unlink()
            file_path.rename(target_path)
            
        except Exception as e:
            logger.error(f"❌ Error procesando archivo {file_path.name}: {e}", exc_info=True)
            await session.rollback()

async def start_watcher():
    """Bucle infinito para monitorizar el directorio de entrada"""
    logger.info(f"👁️ Iniciando monitor de carpeta en: {VAULT_INPUT_DIR}")
    
    # Crear directorio si no existe
    VAULT_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            # Escanear archivos en el directorio
            for item in VAULT_INPUT_DIR.iterdir():
                if item.is_file() and item.suffix.lower() in ('.pdf', '.md', '.txt'):
                    await process_single_file(item)
        except Exception as scan_err:
            logger.error(f"Error escaneando directorio de entrada: {scan_err}")
            
        # Esperar 10 segundos antes de volver a escanear
        await asyncio.sleep(10)
