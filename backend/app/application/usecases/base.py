# Application Use Cases / Services

from typing import List, Optional
from abc import ABC, abstractmethod


class UseCase(ABC):
    """Base class para todos los use cases (servicios de aplicación)"""
    
    @abstractmethod
    async def execute(self, **kwargs):
        """Ejecutar el use case"""
        pass


class UploadDocumentUseCase(UseCase):
    """Use case: Subir y procesar documento"""
    
    async def execute(
        self,
        file_path: str,
        title: str,
        category: str,
        user_id: str,
        **kwargs
    ):
        """
        Subir documento y encolarlo para procesamiento
        
        Steps:
        1. Validar archivo
        2. Guardar en storage temporal
        3. Crear entidad Document
        4. Encolar tarea Celery de procesamiento
        5. Retornar documento con status PENDING
        """
        pass


class ProcessDocumentUseCase(UseCase):
    """Use case: Procesar documento (async task)"""
    
    async def execute(self, document_id: str, **kwargs):
        """
        Procesar documento completamente
        
        Steps:
        1. Cargar documento desde BD
        2. Descargar archivo desde SeaweedFS
        3. Parsear con Docling
        4. Chunking de texto
        5. Generar embeddings con Groq/Gemini
        6. Guardar en pgvector
        7. Actualizar status a COMPLETED
        """
        pass


class SearchDocumentsUseCase(UseCase):
    """Use case: Buscar documentos por semántica"""
    
    async def execute(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        **kwargs
    ):
        """
        Buscar documentos relevantes
        
        Steps:
        1. Generar embedding de query
        2. Buscar en pgvector
        3. Filtrar por threshold
        4. Retornar top-K resultados
        """
        pass


class ChatQueryUseCase(UseCase):
    """Use case: Procesar query de chat"""
    
    async def execute(
        self,
        session_id: str,
        user_id: str,
        message: str,
        **kwargs
    ):
        """
        Procesar pregunta en chat
        
        Steps:
        1. Cargar sesión
        2. Buscar documentos relevantes
        3. Construir context window
        4. Llamar LLM (Groq/Gemini)
        5. Guardar mensaje y respuesta
        6. Retornar respuesta con sources
        """
        pass


class CreateChatSessionUseCase(UseCase):
    """Use case: Crear sesión de chat"""
    
    async def execute(self, user_id: str, title: Optional[str] = None, **kwargs):
        """
        Crear nueva sesión de chat
        
        Steps:
        1. Validar usuario
        2. Crear entidad ChatSession
        3. Guardar en BD
        4. Retornar sesión
        """
        pass


class DeleteDocumentUseCase(UseCase):
    """Use case: Eliminar documento"""
    
    async def execute(self, document_id: str, user_id: str, **kwargs):
        """
        Eliminar documento de forma segura
        
        Steps:
        1. Cargar documento
        2. Verificar permisos (debe ser propietario)
        3. Verificar que no esté procesando
        4. Eliminar embeddings de pgvector
        5. Eliminar archivo de SeaweedFS
        6. Eliminar documento de BD
        """
        pass
