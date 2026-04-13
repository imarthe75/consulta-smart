# Chat Session Entity

from typing import Optional, List, Dict, Any
from datetime import datetime
from .entity import Entity
from ..exceptions.domain_exceptions import InvalidEntity


class ChatMessage:
    """Mensaje individual en una sesión de chat"""
    
    def __init__(
        self,
        role: str,
        content: str,
        id: Optional[str] = None,
        sources: Optional[List[str]] = None,
        tokens_used: int = 0,
        created_at: Optional[datetime] = None
    ):
        if role not in ["user", "assistant", "system"]:
            raise InvalidEntity("ChatMessage", "role debe ser user, assistant o system")
        
        from uuid6 import uuid7
        self.id = id or str(uuid7())
        self.role = role
        self.content = content
        self.sources = sources or []
        self.tokens_used = tokens_used
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at.isoformat()
        }


class ChatSession(Entity):
    """Sesión de Chat"""
    
    def __init__(
        self,
        user_id: str,
        title: Optional[str] = None,
        id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(id)
        
        if not user_id:
            raise InvalidEntity("ChatSession", "user_id es requerido")
        
        self.user_id = user_id
        self.title = title or "New Chat"
        self.messages: List[ChatMessage] = []
        self.metadata = metadata or {}
        self.total_tokens_used = 0
    
    def add_message(self, message: ChatMessage):
        """Agregar mensaje a la sesión"""
        self.messages.append(message)
        self.total_tokens_used += message.tokens_used
        self.mark_as_updated()
    
    def get_messages(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """Obtener mensajes (últimos N si limit está especificado)"""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def is_empty(self) -> bool:
        """Verificar si la sesión está vacía"""
        return len(self.messages) == 0
    
    def get_context_window(self, max_messages: int = 10) -> List[ChatMessage]:
        """Obtener ventana de contexto para enviar al LLM"""
        return self.get_messages(max_messages)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "total_tokens_used": self.total_tokens_used,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'ChatSession':
        session = ChatSession(
            user_id=data["user_id"],
            title=data.get("title", "New Chat"),
            id=data.get("id"),
            metadata=data.get("metadata", {})
        )
        
        # Restaurar mensajes si existen
        if "messages" in data:
            for msg_data in data["messages"]:
                msg = ChatMessage(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    id=msg_data.get("id"),
                    sources=msg_data.get("sources", []),
                    tokens_used=msg_data.get("tokens_used", 0),
                    created_at=datetime.fromisoformat(msg_data["created_at"]) if "created_at" in msg_data else None
                )
                session.messages.append(msg)
        
        return session
