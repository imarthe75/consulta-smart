# Rutas de Administración de Documentos para ConsultaRPP

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.database import get_session
from app.core.response import APIResponse
from app.infrastructure.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.repositories.vector_store import PostgresVectorStore
from app.infrastructure.external.seaweedfs_service import SeaweedFSFileStorage
from app.infrastructure.external.llm_service import get_llm_provider
from app.domain.entities.document import Document, DocumentCategory
from app.workers.celery_app import process_document_task
from app.core.logger import logger
from app.core.auth_utils import get_current_user  # Asumiendo que existe o lo crearemos

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form("Documento sin título"),
    category: str = Form("otro"),
    group_id: Optional[str] = Form(None),
    version_label: Optional[str] = Form(None),
    effective_date_str: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> APIResponse:
    """Cargar un documento para procesamiento RAG completo"""
    # Restricción de Roles: Solo administradores pueden subir archivos
    if "admin" not in current_user.get("roles", []):
        logger.warning(f"Intento de carga no autorizado por parte de: {current_user['email']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permisos para subir documentos. Solo administradores pueden realizar esta acción."
        )
    
    temp_path = None
    try:
        # 1. Validaciones básicas
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo requerido")
        
        file_ext = file.filename.split('.')[-1].lower()
        
        # 2. Guardar archivo temporalmente para subirlo a Storage
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
            contents = await file.read()
            tmp.write(contents)
            temp_path = tmp.name
        
        # 3. Subir a SeaweedFS
        async with SeaweedFSFileStorage() as storage:
            seaweedfs_fid = await storage.upload(temp_path)
        
        # 4. Crear registro en Base de Datos (PostgreSQL)
        repo = PostgresDocumentRepository(session)
        
        # Lógica de versionado
        final_group_id = group_id
        final_version = 1
        
        if final_group_id:
            latest_doc = await repo.find_latest_by_group_id(final_group_id)
            if latest_doc:
                final_version = latest_doc.version + 1
                # Si estamos subiendo una nueva versión, desactivamos las anteriores (opcional, depende de la política)
                # await repo.deactivate_all_in_group(final_group_id)
        
        effective_date = None
        if effective_date_str:
            try:
                effective_date = datetime.fromisoformat(effective_date_str)
            except:
                pass

        document = Document(
            title=title,
            category=DocumentCategory(category),
            user_id=current_user["id"],
            file_type=file_ext,
            seaweedfs_file_id=seaweedfs_fid,
            group_id=final_group_id,
            version=final_version,
            version_label=version_label or f"v{final_version}",
            is_active=True,
            effective_date=effective_date
        )
        
        created_doc = await repo.create(document)
        await session.commit()
        
        # 5. Encolar tarea de procesamiento asíncrono en Celery
        task = process_document_task.delay(str(created_doc.id))
        
        logger.info(f"Documento '{title}' (ID: {created_doc.id}) subido y encolado. Task: {task.id}")
        
        return APIResponse.success(
            data={
                "document_id": str(created_doc.id),
                "task_id": task.id,
                "status": "processing",
                "message": "Archivo recibido. Iniciando extracción de texto y generación de vectores."
            }
        )
        
    except Exception as e:
        logger.error(f"Error en el flujo de carga de documento: {str(e)}")
        return APIResponse.create_error(f"Error al procesar la subida: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_session)
) -> APIResponse:
    """Obtener estado y detalles del documento"""
    repo = PostgresDocumentRepository(session)
    document = await repo.find_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    return APIResponse.success(data=document.to_dict())


@router.get("")
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> APIResponse:
    """Listar documentos del usuario actual"""
    repo = PostgresDocumentRepository(session)
    page = (skip // limit) + 1
    documents, total = await repo.find_by_user_paginated(current_user["id"], page, limit)
    
    return APIResponse.success(
        data={
            "documents": [doc.to_dict() for doc in documents],
            "total": total,
            "page": page,
            "limit": limit
        }
    )


@router.post("/load-rpp-registry")
async def load_rpp_registry(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> APIResponse:
    """Cargar documentos del RPP-registry en la base de conocimientos (solo admin)"""
    
    # Restricción de Roles: Solo administradores
    if "admin" not in current_user.get("roles", []):
        logger.warning(f"Intento de carga de RPP-registry no autorizado: {current_user['email']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden cargar el RPP-registry"
        )
    
    try:
        # Rutas de documentos
        base_path = Path(__file__).parent.parent.parent / "docs"
        registry_path = base_path / "rpp-registry"
        expert_path = base_path / "rpp_expert"
        
        md_files = []
        if registry_path.exists():
            md_files.extend(list(registry_path.glob("**/*.md")))
        if expert_path.exists():
            md_files.extend(list(expert_path.glob("**/*.md")))
            
        md_files = sorted(list(set(md_files)))
        
        repo = PostgresDocumentRepository(session)
        vector_store = PostgresVectorStore(session)
        llm_service = get_llm_provider()
        
        logger.info(f"Encontrados {len(md_files)} documentos MD para cargar")
        
        loaded_count = 0
        error_count = 0
        
        for md_file in md_files:
            try:
                # Leer contenido
                content = md_file.read_text(encoding="utf-8")
                relative_path = md_file.relative_to(base_path)
                
                # Determinar categoría
                filename = md_file.name.lower()
                if "costo" in filename or "arancel" in filename:
                    category = DocumentCategory.FORMULARIO  # Costos/Aranceles como formularios
                elif "procedimiento" in filename or "requisito" in filename:
                    category = DocumentCategory.PROCEDIMIENTO
                elif "legislacion" in filename or "ley" in filename:
                    category = DocumentCategory.LEY
                else:
                    category = DocumentCategory.REGLAMENTO
                
                # Crear documento con soporte de versiones
                # Usar el nombre del archivo (sin extensión) como group_id para agrupar versiones futuras
                doc_group_id = md_file.stem
                
                document = Document(
                    title=f"RPP Registry - {str(relative_path).replace('/', ' > ')}",
                    category=category,
                    file_type="md",
                    user_id=current_user["id"],
                    seaweedfs_file_id=None,
                    group_id=doc_group_id,
                    version=1,
                    version_label="2024-V1", # Versión inicial por defecto
                    is_active=True
                )
                
                # Guardar en BD
                created_doc = await repo.create(document)
                logger.info(f"Documento creado: {relative_path} (ID: {created_doc.id})")
                
                # Generar embeddings - dividir en chunks
                chunk_size = 1000
                chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                
                for idx, chunk in enumerate(chunks):
                    embedding_vector = None
                    try:
                        # Intentar generar embedding
                        embedding_vector = await llm_service.embed(chunk)
                        logger.info(f"✅ Embedding generado para chunk {idx}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error en embedding del chunk {idx}: {e} - salvando sin embedding")
                        # Continuar sin embedding, pero guardar el chunk
                    
                    try:
                        # Guardar chunk (con o sin embedding)
                        from uuid import uuid4
                        chunk_id = str(uuid4())
                        await vector_store.add(
                            vector_id=chunk_id,
                            text_content=chunk,
                            embedding=embedding_vector,
                            metadata={
                                "document_id": created_doc.id,
                                "chunk_number": idx,
                                "chunk_size": len(chunk)
                            }
                        )
                        logger.info(f"✅ Chunk {idx} guardado (ID: {chunk_id})")
                    except Exception as e:
                        logger.error(f"❌ Error guardando chunk {idx}: {e}")
                
                await session.commit()
                loaded_count += 1
                logger.info(f"✅ {relative_path} ({len(chunks)} chunks)")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error con {md_file}: {str(e)}")
                await session.rollback()
                continue
        
        return APIResponse.success(
            data={
                "loaded": loaded_count,
                "errors": error_count,
                "total": len(md_files),
                "message": f"Cargados {loaded_count} documentos del RPP-registry"
            }
        )
    
    except Exception as e:
        logger.error(f"Error general en load_rpp_registry: {str(e)}")
        return APIResponse.create_error(f"Error al cargar RPP-registry: {str(e)}")
