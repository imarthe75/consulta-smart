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
    Endpoint de Login compatible con OAuth2PasswordRequestForm para soportar 
    tanto JSON (frontend personalizado) como form-data (interfaz de Swagger/OpenAPI).
    """
    try:
        # form_data.username puede ser el email por convención OAuth2
        email = form_data.username
        password = form_data.password
        
        logger.info(f"Intento de login para: {email}")
        user_repo = PostgresUserRepository(db)
        
        # Buscar usuario en la base de datos
        user_entity = await user_repo.find_by_email(email)
        
        # Lógica especial para primer login (crear usuario demo si no existe)
        if not user_entity and email == settings.DEMO_USER_EMAIL and password == settings.DEMO_USER_PASSWORD:
            logger.info("Creando usuario demo por primera vez...")
            from app.domain.entities.user import User
            user_entity = User(
                email=settings.DEMO_USER_EMAIL,
                username=settings.DEMO_USER_USERNAME,
                password_hash=get_password_hash(settings.DEMO_USER_PASSWORD),
                roles=["user", "admin"]
            )
            await user_repo.create(user_entity)
            await db.commit()
            # Recargar para asegurar persistencia
            user_entity = await user_repo.find_by_email(email)
        
        if not user_entity or not verify_password(password, user_entity.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El correo o la contraseña son incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generar Token Real
        access_token = create_access_token(
            data={"sub": user_entity.email, "user_id": str(user_entity.id), "roles": user_entity.roles}
        )
        
        # Nota: Retornamos formato OAuth2 estándar para compatibilidad con librerías frontend
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user_id": str(user_entity.id),
            "email": user_entity.email
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

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
