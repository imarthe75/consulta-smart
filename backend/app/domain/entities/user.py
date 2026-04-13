# User Entity

from typing import Optional, List
from .entity import Entity
from ..exceptions.domain_exceptions import InvalidEntity


class User(Entity):
    """Entidad de Usuario"""
    
    def __init__(
        self,
        email: str,
        username: str,
        id: Optional[str] = None,
        password_hash: Optional[str] = None,
        is_active: bool = True,
        roles: Optional[List[str]] = None
    ):
        super().__init__(id)
        
        if not email or "@" not in email:
            raise InvalidEntity("User", "email inválido")
        if not username or len(username) < 3:
            raise InvalidEntity("User", "username debe tener al menos 3 caracteres")
        
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.is_active = is_active
        self.roles = roles or ["user"]  # Default role
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "is_active": self.is_active,
            "roles": self.roles,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'User':
        user = User(
            email=data["email"],
            username=data["username"],
            id=data.get("id"),
            is_active=data.get("is_active", True),
            roles=data.get("roles", ["user"])
        )
        return user
