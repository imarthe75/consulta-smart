# Rutas de Verificación de Salud del Sistema

from fastapi import APIRouter, Depends
from app.core.config import settings
from app.core.response import APIResponse

router = APIRouter(tags=["salud"])


@router.get("/health")
async def health_check() -> dict:
    """Verificación básica de salud del sistema"""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }


@router.get("/health/detailed")
async def health_check_detailed() -> APIResponse:
    """Verificación detallada de la salud del sistema"""
    return APIResponse.success(
        data={
            "status": "saludable",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "llm_provider": settings.LLM_PROVIDER,
            "database": "configurada",
            "cache": "configurada"
        }
    )
