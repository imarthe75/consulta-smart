# Application Data Transfer Objects

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ============= USER DTOs =============

class UserCreateDTO(BaseModel):
    """DTO para crear usuario"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@example.com",
                "username": "usuario2026"
            }
        }


class UserUpdateDTO(BaseModel):
    """DTO para actualizar usuario"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "nuevo_usuario"
            }
        }


class UserResponseDTO(BaseModel):
    """DTO para respuesta de usuario"""
    id: str
    email: str
    username: str
    is_active: bool
    roles: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "usr_123abc",
                "email": "usuario@example.com",
                "username": "usuario2026",
                "is_active": True,
                "roles": ["user"],
                "created_at": "2026-04-07T10:00:00",
                "updated_at": "2026-04-07T10:00:00"
            }
        }


# ============= DOCUMENT DTOs =============

class DocumentCreateDTO(BaseModel):
    """DTO para crear documento"""
    title: str = Field(..., min_length=3, max_length=255)
    category: str
    file_type: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Reglamento de Inscripción",
                "category": "reglamento",
                "file_type": "pdf"
            }
        }


class DocumentUpdateDTO(BaseModel):
    """DTO para actualizar documento"""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    category: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Reglamento de Inscripción Actualizado",
                "category": "reglamento"
            }
        }


class DocumentResponseDTO(BaseModel):
    """DTO para respuesta de documento"""
    id: str
    title: str
    category: str
    user_id: str
    file_type: str
    status: str
    chunk_count: int
    token_count: int
    group_id: Optional[str] = None
    version: int = 1
    version_label: Optional[str] = None
    is_active: bool = True
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_123abc",
                "title": "Reglamento de Inscripción",
                "category": "reglamento",
                "user_id": "usr_123abc",
                "file_type": "pdf",
                "status": "completed",
                "chunk_count": 25,
                "token_count": 8500,
                "created_at": "2026-04-07T10:00:00",
                "updated_at": "2026-04-07T10:05:00",
                "metadata": {}
            }
        }


# ============= CHAT DTOs =============

class ChatMessageDTO(BaseModel):
    """DTO para mensaje de chat"""
    role: str
    content: str
    sources: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "¿Qué requisitos necesito para inscribir una propiedad?",
                "sources": []
            }
        }


class ChatQueryDTO(BaseModel):
    """DTO para query de chat"""
    session_id: Optional[str] = None
    message: str
    conversation_history: Optional[list] = None
    filters: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_123abc",
                "message": "¿Cuál es el costo del trámite?",
                "conversation_history": []
            }
        }


class ChatResponseDTO(BaseModel):
    """DTO para respuesta de chat"""
    session_id: str
    message_id: str
    role: str
    content: str
    sources: List[str]
    tokens_used: int
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_123abc",
                "message_id": "msg_123abc",
                "role": "assistant",
                "content": "Para inscribir una propiedad necesitas...",
                "sources": ["doc_1", "doc_2"],
                "tokens_used": 250,
                "created_at": "2026-04-07T10:05:00"
            }
        }


class ChatSessionResponseDTO(BaseModel):
    """DTO para sesión de chat"""
    id: str
    user_id: str
    title: str
    messages: List[ChatMessageDTO] = []
    total_tokens_used: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "sess_123abc",
                "user_id": "usr_123abc",
                "title": "Consulta sobre propiedades",
                "messages": [],
                "total_tokens_used": 500,
                "created_at": "2026-04-07T10:00:00",
                "updated_at": "2026-04-07T10:05:00"
            }
        }


# ============= SEARCH DTOs =============

class SearchQueryDTO(BaseModel):
    """DTO para query de búsqueda"""
    query: str
    category: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "requisitos inscripción",
                "category": "reglamento",
                "top_k": 10,
                "threshold": 0.7
            }
        }


class SearchResultDTO(BaseModel):
    """DTO para resultado de búsqueda"""
    document_id: str
    chunk_id: str
    text: str
    score: float
    category: str
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123abc",
                "chunk_id": "chunk_001",
                "text": "Artículo 1: Requisitos para inscripción...",
                "score": 0.92,
                "category": "reglamento",
                "created_at": "2026-04-07T10:00:00"
            }
        }
