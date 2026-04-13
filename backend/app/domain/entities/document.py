# Document Entity

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from .entity import Entity
from ..exceptions.domain_exceptions import InvalidEntity


class DocumentStatus(str, Enum):
    """Estados posibles de un documento"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentCategory(str, Enum):
    """Categorías de documentos"""
    REGLAMENTO = "reglamento"
    LEY = "ley"
    GUIA = "guia"
    FORMULARIO = "formulario"
    PROCEDIMIENTO = "procedimiento"
    DOCUMENTACION_RPP = "documentacion_rpp"
    OTRO = "otro"


class Document(Entity):
    """Entidad de Documento"""
    
    def __init__(
        self,
        title: str,
        category: DocumentCategory,
        user_id: str,
        file_type: str,
        id: Optional[str] = None,
        seaweedfs_file_id: Optional[str] = None,
        status: DocumentStatus = DocumentStatus.PENDING,
        chunk_count: int = 0,
        token_count: int = 0,
        group_id: Optional[str] = None,
        version: int = 1,
        version_label: Optional[str] = None,
        is_active: bool = True,
        effective_date: Optional[datetime] = None,
        expiration_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(id)
        
        if not title or len(title) < 3:
            raise InvalidEntity("Document", "título debe tener al menos 3 caracteres")
        if not user_id:
            raise InvalidEntity("Document", "user_id es requerido")
        
        self.title = title
        self.category = category
        self.user_id = user_id
        self.file_type = file_type
        self.seaweedfs_file_id = seaweedfs_file_id
        self.status = status
        self.chunk_count = chunk_count
        self.token_count = token_count
        self.group_id = group_id
        self.version = version
        self.version_label = version_label
        self.is_active = is_active
        self.effective_date = effective_date
        self.expiration_date = expiration_date
        self.metadata = metadata or {}
        self.processing_error: Optional[str] = None
        self.processing_started_at: Optional[datetime] = None
        self.processing_completed_at: Optional[datetime] = None
    
    def mark_processing_started(self):
        """Marcar que inició el procesamiento"""
        self.status = DocumentStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()
        self.mark_as_updated()
    
    def mark_processing_completed(self, chunk_count: int, token_count: int):
        """Marcar que completó el procesamiento"""
        self.status = DocumentStatus.COMPLETED
        self.chunk_count = chunk_count
        self.token_count = token_count
        self.processing_completed_at = datetime.utcnow()
        self.mark_as_updated()
    
    def mark_processing_failed(self, error: str):
        """Marcar que falló el procesamiento"""
        self.status = DocumentStatus.FAILED
        self.processing_error = error
        self.processing_completed_at = datetime.utcnow()
        self.mark_as_updated()
    
    def can_be_deleted(self) -> bool:
        """Verificar si puede ser eliminado"""
        return self.status != DocumentStatus.PROCESSING
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "user_id": self.user_id,
            "file_type": self.file_type,
            "seaweedfs_file_id": self.seaweedfs_file_id,
            "status": self.status.value,
            "chunk_count": self.chunk_count,
            "token_count": self.token_count,
            "group_id": self.group_id,
            "version": self.version,
            "version_label": self.version_label,
            "is_active": self.is_active,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "metadata": self.metadata,
            "processing_error": self.processing_error,
            "processing_started_at": self.processing_started_at.isoformat() if self.processing_started_at else None,
            "processing_completed_at": self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Document':
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.fromisoformat(date_str)
            except (ValueError, TypeError):
                return None

        doc = Document(
            title=data["title"],
            category=DocumentCategory(data.get("category", "otro")),
            user_id=data["user_id"],
            file_type=data["file_type"],
            id=data.get("id"),
            seaweedfs_file_id=data.get("seaweedfs_file_id"),
            status=DocumentStatus(data.get("status", "pending")),
            chunk_count=data.get("chunk_count", 0),
            token_count=data.get("token_count", 0),
            group_id=data.get("group_id"),
            version=data.get("version", 1),
            version_label=data.get("version_label"),
            is_active=data.get("is_active", True),
            effective_date=parse_date(data.get("effective_date")),
            expiration_date=parse_date(data.get("expiration_date")),
            metadata=data.get("metadata", {})
        )
        return doc
