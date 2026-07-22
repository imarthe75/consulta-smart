from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_session
from app.core.logger import logger
from app.core.config import settings
from app.core.auth_utils import create_access_token, verify_password, get_current_user
from app.infrastructure.repositories.user_repository import PostgresUserRepository

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Devuelve la identidad y el rol REAL del usuario autenticado, resueltos por el
    backend (fuente de verdad: tabla `users`) contra el JWT validado.

    Se agrega este endpoint porque el frontend determinaba el rol adivinando por
    substring en el email/username del perfil OIDC (hallazgo de auditoría,
    backdoor de escalación de privilegios) — ese atajo se eliminó y este es el
    reemplazo legítimo: el propio usuario consulta su rol real tras iniciar sesión.
    """
    return current_user


@router.get("/guest")
@router.post("/guest")
async def guest_login(
    db: AsyncSession = Depends(get_session)
) -> dict:
    """
    Endpoint para Login de Widget.
    Autentica al usuario widget dedicado contra la BD local para no exponer OIDC en el chat público.
    """
    try:
        user_repo = PostgresUserRepository(db)
        user = await user_repo.find_by_email(settings.WIDGET_EMAIL)

        if not user or not user.password_hash or not verify_password(settings.WIDGET_PASSWORD, user.password_hash):
            logger.error("Widget user authentication failed - user not found or password mismatch")
            raise HTTPException(status_code=500, detail="Error de autenticación del widget")
        
        # Generar JWT local para el widget (usado como fallback en auth_utils)
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),
            "username": user.username,
            "roles": ["user"],
            "is_widget": True,
        }
        access_token = create_access_token(data=token_data)
        
        logger.info("Widget guest login exitoso")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRATION_HOURS * 3600,
            "user_id": str(user.id),
            "email": settings.WIDGET_EMAIL,
            "role": "user"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en guest login: {str(e)}")
        raise HTTPException(status_code=500, detail="Error de autenticación centralizada para el widget")

