# API Response Envelope Estándar

from typing import Optional, Any, Dict, List
from datetime import datetime
from uuid6 import uuid7
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


def _generate_uuid() -> str:
    """Generar UUID para request_id"""
    return str(uuid7())


def _generate_timestamp() -> str:
    """Generar timestamp actual"""
    return datetime.utcnow().isoformat()


class ResponseStatus(str, Enum):
    """Estados de respuesta"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class APIResponse(BaseModel):
    """Envelope estándar para todas las respuestas de API"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Any] = None
    error: Optional[str] = None
    details: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=_generate_uuid)
    timestamp: str = Field(default_factory=_generate_timestamp)
    version: str = "0.1.0"
    
    model_config = ConfigDict(use_enum_values=True)
    
    @staticmethod
    def success(data: Any = None, meta: Optional[Dict[str, Any]] = None, request_id: str = None) -> 'APIResponse':
        """Crear respuesta exitosa"""
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            data=data,
            meta=meta or {},
            request_id=request_id or str(uuid7())
        )
    
    @staticmethod
    def create_error(error: str, details: Optional[List[str]] = None, request_id: str = None) -> 'APIResponse':
        """Crear respuesta de error"""
        return APIResponse(
            status=ResponseStatus.ERROR,
            error=error,
            details=details or [],
            meta={},
            request_id=request_id or str(uuid7())
        )
