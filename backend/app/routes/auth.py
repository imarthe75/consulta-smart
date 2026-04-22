from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import timedelta

from app.core.database import get_session
from app.core.response import APIResponse
from app.core.logger import logger
from app.core.config import settings
from app.core.auth_utils import verify_password, get_password_hash, create_access_token
from app.infrastructure.repositories.user_repository import PostgresUserRepository
from app.domain.entities.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
) -> dict:
    """
    Endpoint de Login personalizado que valida contra Authentik (OIDC).
    Evita que el usuario tenga que ver el panel de Authentik.
    """
    try:
        import requests
        
        email = form_data.username
        password = form_data.password
        
        logger.info(f"Intento de login personalizado para: {email}")
        
        # Authentik Token Endpoint (Internal)
        token_url = f"{settings.AUTHENTIK_INTERNAL_URL}/application/o/token/"
        
        # Exchange credentials for token
        data = {
            "grant_type": "password",
            "username": email,
            "password": password,
            "client_id": settings.AUTHENTIK_CLIENT_ID,
            "client_secret": settings.AUTHENTIK_CLIENT_SECRET,
            "scope": "openid profile email"
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            logger.warning(f"Fallo de autenticación en Authentik para {email}: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El correo o la contraseña son incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = response.json()
        
        # Obtener información del usuario (Internal)
        user_info_url = f"{settings.AUTHENTIK_INTERNAL_URL}/application/o/userinfo/"
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        user_info_resp = requests.get(user_info_url, headers=headers)
        user_info = user_info_resp.json()
        
        return {
            "access_token": token['access_token'], 
            "token_type": "bearer",
            "expires_in": token['expires_in'],
            "refresh_token": token.get('refresh_token'),
            "user_id": user_info.get('sub'),
            "email": email,
            "username": user_info.get('preferred_username'),
            "roles": user_info.get('realm_access', {}).get('roles', [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login personalizado: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor en la autenticación")

@router.get("/guest")
@router.post("/guest")
async def guest_login() -> dict:
    """
    Endpoint para Login de Widget.
    Autentica contra Authentik usando el usuario dedicado del widget.
    """
    try:
        import requests
        
        # Authentik Token Endpoint (Internal)
        token_url = f"{settings.AUTHENTIK_INTERNAL_URL}/application/o/token/"
        
        data = {
            "grant_type": "password",
            "username": "widget@casmarts.com",
            "password": "casmarts_widget_2026",
            "client_id": settings.AUTHENTIK_CLIENT_ID,
            "client_secret": settings.AUTHENTIK_CLIENT_SECRET,
            "scope": "openid profile email"
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            raise Exception("Failed to get widget token")
            
        token = response.json()
        
        return {
            "access_token": token['access_token'], 
            "token_type": "bearer",
            "expires_in": token['expires_in'],
            "refresh_token": token.get('refresh_token'),
            "email": "widget@casmarts.com",
            "role": "user"
        }
    except Exception as e:
        logger.error(f"Error en guest login via Keycloak: {str(e)}")
        raise HTTPException(status_code=500, detail="Error de autenticación centralizada para el widget")

@router.post("/register")
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_session)
) -> APIResponse:
    """Endpoint de Registro real"""
    try:
        user_repo = PostgresUserRepository(db)
        
        # Verificar si ya existe
        existing = await user_repo.find_by_email(request.email)
        if existing:
            return APIResponse.create_error("El correo ya está registrado")
        
        # Crear entidad
        new_user = User(
            email=request.email,
            username=request.username,
            password_hash=get_password_hash(request.password)
        )
        
        await user_repo.create(new_user)
        await db.commit()
        
        return APIResponse.success(
            data={"id": str(new_user.id), "email": new_user.email},
            meta={"message": "Usuario registrado exitosamente"}
        )
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return APIResponse.create_error(str(e))
