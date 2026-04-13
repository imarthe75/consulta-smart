# Repository Interfaces (Abstracciones)

from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """Interface base para todos los repositorios"""
    
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[T]:
        """Encontrar entidad por ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[T]:
        """Obtener todas las entidades"""
        pass
    
    @abstractmethod
    async def find_all_paginated(self, page: int, page_size: int) -> tuple[List[T], int]:
        """Obtener entidades con paginación"""
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Crear nueva entidad"""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Actualizar entidad existente"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Eliminar entidad"""
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """Verificar si existe una entidad"""
        pass


class UserRepository(Repository):
    """Interface para repositorio de Usuarios"""
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional['User']:
        """Encontrar usuario por email"""
        pass
    
    @abstractmethod
    async def find_by_username(self, username: str) -> Optional['User']:
        """Encontrar usuario por username"""
        pass


class DocumentRepository(Repository):
    """Interface para repositorio de Documentos"""
    
    @abstractmethod
    async def find_by_user(self, user_id: str) -> List['Document']:
        """Encontrar documentos de un usuario"""
        pass
    
    @abstractmethod
    async def find_by_category(self, category: str) -> List['Document']:
        """Encontrar documentos por categoría"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: str) -> List['Document']:
        """Encontrar documentos por estado"""
        pass
    
    @abstractmethod
    async def find_by_user_paginated(
        self, user_id: str, page: int, page_size: int
    ) -> tuple[List['Document'], int]:
        """Encontrar documentos de un usuario con paginación"""
        pass

    @abstractmethod
    async def find_latest_by_group_id(self, group_id: str) -> Optional['Document']:
        """Encontrar la versión más reciente de un grupo de documentos"""
        pass

    @abstractmethod
    async def deactivate_all_in_group(self, group_id: str) -> None:
        """Desactivar todos los documentos de un grupo"""
        pass


class ChatSessionRepository(Repository):
    """Interface para repositorio de Sesiones de Chat"""
    
    @abstractmethod
    async def find_by_user(self, user_id: str) -> List['ChatSession']:
        """Encontrar sesiones de un usuario"""
        pass
    
    @abstractmethod
    async def find_by_user_paginated(
        self, user_id: str, page: int, page_size: int
    ) -> tuple[List['ChatSession'], int]:
        """Encontrar sesiones de un usuario con paginación"""
        pass


class VectorStore(ABC):
    """Interface para almacenamiento de embeddings/vectores"""
    
    @abstractmethod
    async def add(self, vector_id: str, text: str, embedding: List[float], metadata: dict) -> bool:
        """Agregar embedding a la BD vectorial"""
        pass
    
    @abstractmethod
    async def search(
        self, query_embedding: List[float], top_k: int = 10, threshold: float = 0.7, filters: dict = None
    ) -> List[dict]:
        """Buscar embeddings similares con filtros opcionales"""
        pass
    
    @abstractmethod
    async def delete(self, vector_id: str) -> bool:
        """Eliminar embedding"""
        pass
    
    @abstractmethod
    async def delete_by_document(self, document_id: str) -> int:
        """Eliminar todos los embeddings de un documento"""
        pass


class FileStorage(ABC):
    """Interface para almacenamiento de archivos"""
    
    @abstractmethod
    async def upload(self, file_path: str, destination: str) -> str:
        """Subir archivo y retornar su ID/referencia"""
        pass
    
    @abstractmethod
    async def download(self, file_id: str, destination: str) -> bool:
        """Descargar archivo"""
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Eliminar archivo"""
        pass
    
    @abstractmethod
    async def exists(self, file_id: str) -> bool:
        """Verificar si archivo existe"""
        pass
