# Core Entity Base Class

from typing import Optional
from datetime import datetime
from uuid6 import uuid7


class Entity:
    """Base class para todas las entidades del dominio"""
    
    def __init__(self, id: Optional[str] = None):
        self.id = id or str(uuid7())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_updated(self):
        """Mark entity as updated"""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert entity to dict (implementar en subclases)"""
        raise NotImplementedError("Subclasses must implement to_dict()")
    
    @staticmethod
    def from_dict(data: dict) -> 'Entity':
        """Crear entidad desde dict (implementar en subclases)"""
        raise NotImplementedError("Subclasses must implement from_dict()")
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
