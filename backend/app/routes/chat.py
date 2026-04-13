# Rutas del Chatbot para ConsultaRPP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_session
from app.core.response import APIResponse
from app.application.dtos.common_dtos import ChatQueryDTO
from app.application.services.chat_service import get_chat_service
from app.core.logger import logger
from app.core.auth_utils import get_current_user

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

class CreateSessionRequest(BaseModel):
    title: str

class UpdateSessionRequest(BaseModel):
    title: str

@router.put("/sessions/{session_id}")
async def update_session_title(
    session_id: str,
    request: UpdateSessionRequest,
    db_session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Actualizar el título de una sesión de chat"""
    try:
        from app.infrastructure.repositories.chat_session_repository import PostgresChatSessionRepository
        repo = PostgresChatSessionRepository(db_session)
        session = await repo.find_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        if str(session.user_id) != str(current_user["id"]):
            raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta sesión")
            
        session.title = request.title
        await repo.update(session)
        await db_session.commit()
        
        return {
            "status": "success",
            "message": "Título de sesión actualizado correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando sesión {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions")
async def create_chat_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Crear una nueva sesión de chat"""
    try:
        from app.infrastructure.repositories.chat_session_repository import PostgresChatSessionRepository
        from app.domain.entities.chat_session import ChatSession
        
        repo = PostgresChatSessionRepository(db)
        new_session = ChatSession(
            user_id=str(current_user["id"]),
            title=request.title
        )
        await repo.create(new_session)
        await db.commit()
        
        return {
            "status": "success",
            "data": {
                "id": str(new_session.id),
                "title": new_session.title,
                "created_at": new_session.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error creando sesión: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def list_user_sessions(
    db_session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Listar todas las sesiones del usuario autenticado"""
    try:
        from app.infrastructure.repositories.chat_session_repository import PostgresChatSessionRepository
        
        repo = PostgresChatSessionRepository(db_session)
        sessions = await repo.find_by_user(str(current_user["id"]))
        
        return {
            "status": "success",
            "data": {
                "total": len(sessions),
                "sessions": [
                    {
                        "id": str(s.id),
                        "title": s.title,
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                        "message_count": len(s.messages) if hasattr(s, 'messages') else 0
                    }
                    for s in sessions
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error listando sesiones: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def chat_query(
    query: ChatQueryDTO,
    db_session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Procesar una consulta de chat con:
    - RAG (base de conocimiento)
    - Caché híbrida (Redis + embeddings)
    - Fallback a LLM cuando es necesario
    - Persistencia de sesión en BD
    """
    try:
        from app.infrastructure.repositories.chat_session_repository import PostgresChatSessionRepository
        from app.domain.entities.chat_session import ChatSession
        import uuid
        from datetime import datetime
        
        logger.info(f"🔵 Chat query from {current_user['email']}: {query.message[:80]}...")
        
        # ========== 1. CREAR O RECUPERAR SESIÓN ==========
        session_repo = PostgresChatSessionRepository(db_session)
        
        # Si no tiene session_id, crear nueva
        if not query.session_id:
            query.session_id = str(uuid.uuid4())
            new_session = ChatSession(
                id=query.session_id,
                user_id=str(current_user["id"]),
                title=query.message[:100] or "Nueva conversación"
            )
            await session_repo.create(new_session)
            logger.info(f"✅ Nueva sesión creada: {query.session_id}")
        
        # Recuperar sesión existente o crear si no existe
        existing_session = await session_repo.find_by_id(query.session_id)
        if not existing_session:
            logger.warning(f"⚠️ Sesión {query.session_id} no encontrada, creando nueva...")
            new_session = ChatSession(
                id=query.session_id,
                user_id=str(current_user["id"]),
                title=query.message[:100] or "Nueva conversación"
            )
            await session_repo.create(new_session)
        
        # ========== 2. GUARDAR MENSAJE DEL USUARIO INMEDIATAMENTE ==========
        from app.domain.entities.chat_session import ChatMessage
        
        user_message = ChatMessage(
            role='user',
            content=query.message
        )
        
        try:
            await session_repo.add_message(query.session_id, user_message)
            await db_session.commit()
            logger.info(f"✅ Mensaje de usuario guardado y confirmado ({len(query.message)} chars)")
        except Exception as e:
            await db_session.rollback()
            logger.error(f"❌ Error crítico al guardar mensaje de usuario: {e}")
            # Continuamos aunque falle el guardado para no bloquear al usuario
        
        # ========== 3. PROCESAR CONSULTA CON RAG + LLM ==========
        # Obtener instancia del servicio
        chat_service = await get_chat_service()
        
        # Procesar con el servicio de IA + caché
        result = await chat_service.process_query(
            query=query.message,
            session_id=query.session_id,
            conversation_history=query.conversation_history or [],
            db_session=db_session, # Se pasará una sesión limpia tras el commit
            filters=query.filters
        )
        
        # ========== 4. GUARDAR RESPUESTA DEL ASISTENTE ==========
        response_text = result.get("response", "")
        # Añadir debug de proveedor si es necesario
        provider = result.get("provider")
        if provider:
            response_text += f"\n\n---\n*LLM: {provider}*"
        elif result.get("from_cache") == "exact_or_similar":
            response_text += f"\n\n---\n*LLM: Caché Híbrida*"

        assistant_message = ChatMessage(
            role='assistant',
            content=response_text,
            sources=result.get("sources", [])
        )
        
        try:
            await session_repo.add_message(query.session_id, assistant_message)
            await db_session.commit()
            logger.info(f"✅ Respuesta del asistente guardada y confirmada ({len(result.get('response', ''))} chars)")
        except Exception as e:
            await db_session.rollback()
            logger.error(f"❌ Error al guardar respuesta del asistente: {e}")
        
        # ========== 5. OBTENER HISTORIAL ACTUALIZADO ==========
        try:
            updated_messages = await session_repo.get_messages(query.session_id, limit=50)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo obtener historial: {e}")
            updated_messages = []
        
        # Log situación de caché
        from_cache = result.get("from_cache", "unknown")
        if from_cache == "exact_or_similar":
            logger.info(f"🟢 CACHE HIT: Respondiendo desde caché sin LLM")
        else:
            logger.info(f"🔴 CACHE MISS: Consultando LLM y guardando en caché")
        
        # Retornar diccionario plano con el mismo formato que se guarda
        return {
            "status": "success",
            "data": {
                "session_id": query.session_id,
                "response": response_text,
                "sources": result.get("sources", []),
                "has_relevant_knowledge": result.get("has_relevant_info", False),
                # Historial completo de la sesión
                "conversation_history": [
                    {
                        "role": msg.role if hasattr(msg, 'role') else 'user',
                        "content": msg.content if hasattr(msg, 'content') else '',
                        "timestamp": msg.created_at.isoformat() if hasattr(msg, 'created_at') and msg.created_at else None
                    }
                    for msg in (updated_messages or [])
                ],
                # Nuevos campos para monitoreo de caché
                "cache_info": {
                    "from_cache": result.get("from_cache"),
                    "similarity_score": result.get("cached_similarity_score"),
                    "query_length": result.get("query_length"),
                    "response_length": result.get("response_length")
                }
            }
        }
    except Exception as e:
        logger.error(f"Error en chat_query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    db_session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Obtener detalles completos de una sesión incluyendo historial"""
    try:
        from app.infrastructure.repositories.chat_session_repository import PostgresChatSessionRepository
        
        repo = PostgresChatSessionRepository(db_session)
        session = await repo.find_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Verificar que el usuario es propietario de la sesión
        if str(session.user_id) != str(current_user["id"]):
            raise HTTPException(status_code=403, detail="No tienes acceso a esta sesión")
        
        # Obtener mensajes
        messages = await repo.get_messages(session_id, limit=100)
        
        return {
            "status": "success",
            "data": {
                "id": str(session.id),
                "title": session.title,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "sources": msg.sources or [],
                        "timestamp": msg.created_at.isoformat() if msg.created_at else None
                    }
                    for msg in messages  # Ya vienen ordenados cronológicamente del repo
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo sesión {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db_session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Eliminar una sesión de chat"""
    try:
        from app.infrastructure.repositories.chat_session_repository import PostgresChatSessionRepository
        
        repo = PostgresChatSessionRepository(db_session)
        session = await repo.find_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Verificar que el usuario es propietario
        if str(session.user_id) != str(current_user["id"]):
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta sesión")
        
        # Eliminar sesión
        success = await repo.delete(session_id)
        await db_session.commit()
        
        if success:
            logger.info(f"✅ Sesión {session_id} eliminada por usuario {current_user['email']}")
            return {
                "status": "success",
                "message": "Sesión eliminada correctamente"
            }
        else:
            raise HTTPException(status_code=500, detail="No se pudo eliminar la sesión")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando sesión {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def chat_health():
    return {"status": "ok", "service": "chat"}
