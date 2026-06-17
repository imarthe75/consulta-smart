import jwt
import ssl
from jwt import PyJWKClient
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from app.core.config import settings
from app.core.logger import logger
import uuid

# Configuration for Authentik OIDC
# ssl_context con CERT_NONE: auth.casmart.internal usa certificado autofirmado interno.
# Esta es una ca interna de la red de CASMARTS, no de internet, por lo que es seguro.
jwks_url = f"{settings.AUTHENTIK_INTERNAL_URL}/application/o/{settings.AUTHENTIK_CLIENT_ID}/jwks/"
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE
jwk_client = PyJWKClient(jwks_url, ssl_context=_ssl_ctx, cache_keys=True)

# Contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar si la contraseña coincide con el hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generar hash de la contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear un nuevo token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodificar y validar un token JWT de Authentik usando JWKS"""
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.AUTHENTIK_CLIENT_ID,
            options={"verify_exp": True}
        )
        return decoded_token
    except Exception as e:
        logger.error(f"Error decodificando JWT de Authentik: {e}")
        # Intentar fallback con JWT local (para el widget o migraciones)
        try:
            return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except:
            return None

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_session
from app.infrastructure.repositories.user_repository import PostgresUserRepository
from app.infrastructure.models import UserModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no válidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
        
    user_email: str = payload.get("email") or payload.get("sub")
    if not user_email:
        raise credentials_exception
        
    # Validar si es el widget
    is_widget = payload.get("is_widget", False)
    
    repo = PostgresUserRepository(session)
    user = await repo.find_by_email(user_email)
    
    # Auto-registro si el usuario viene de Authentik pero no está en la BD local
    if user is None and not is_widget:
        logger.info(f"Auto-registrando usuario desde Authentik: {user_email}")
        new_user = UserModel(
            id=str(uuid.uuid4()),
            email=user_email,
            username=payload.get("preferred_username") or user_email.split("@")[0],
            password_hash=None, # No password stored! Authentik manages auth
            is_active=True,
            roles='["user"]'
        )
        session.add(new_user)
        await session.commit()
        user = new_user
    elif user is None:
        raise credentials_exception
        
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "roles": user.roles
    }

