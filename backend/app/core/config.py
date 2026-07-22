# Configuración Centralizada para ConsultaRPP

import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración global de la aplicación"""
    
    # App Settings
    APP_NAME: str = os.getenv("APP_NAME", "ConsultaRPP")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_ENV: str = os.getenv("APP_ENV", "production")
    DEBUG: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Prefix
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")

    # Heuristics & Grounding (Blindage)
    HEURISTICS_ENABLED: bool = os.getenv("HEURISTICS_ENABLED", "true").lower() == "true"
    STRICT_GROUNDING: bool = os.getenv("STRICT_GROUNDING", "true").lower() == "true"
    GROUNDING_THRESHOLD: float = float(os.getenv("GROUNDING_THRESHOLD", "0.85"))

    # Identity & Access (Authentik - 100% Open Source)
    AUTHENTIK_URL: str = os.getenv("AUTHENTIK_URL", "https://auth.casmart.internal")
    AUTHENTIK_CLIENT_ID: str = os.getenv("AUTHENTIK_CLIENT_ID", "consulta-smart")
    AUTHENTIK_CLIENT_SECRET: Optional[str] = os.getenv("AUTHENTIK_CLIENT_SECRET")
    
    # Database (PostgreSQL 18 + asyncpg)
    DB_HOST: str = os.getenv("DB_HOST", "postgres")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "consultarpp_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "SuperSecure_ConsultaRPP_2026!")
    DB_NAME: str = os.getenv("DB_NAME", "consultarpp")
    DB_MAX_CONNECTIONS: int = int(os.getenv("DB_MAX_CONNECTIONS", "100"))
    
    @property
    def DATABASE_URL(self) -> str:
        # Mask password for safety
        masked_url = f"postgresql+asyncpg://{self.DB_USER}:****@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        # We can't use logger here easily if it's not initialized, so we use print or wait until init_db
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis / Celery / Cache
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_TTL_SECONDS: int = int(os.getenv("REDIS_TTL_SECONDS", "86400"))
    
    @property
    def REDIS_URL(self) -> str:
        # Si existe REDIS_URL en el .env, usarla directamente
        url_env = os.getenv("REDIS_URL")
        if url_env:
            return url_env
        # Si no, construirla
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def CELERY_BROKER(self) -> str:
        broker_env = os.getenv("CELERY_BROKER")
        if broker_env:
            return broker_env
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"
    
    @property
    def CELERY_BACKEND(self) -> str:
        backend_env = os.getenv("CELERY_BACKEND")
        if backend_env:
            return backend_env
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/2"
    
    WORKER_LOG_LEVEL: str = os.getenv("WORKER_LOG_LEVEL", "INFO")
    
    # Security & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "casmarts_super_secret_key_rpp_2026")  # Fallback secure key
    JWT_SECRET: str = os.getenv("JWT_SECRET", "casmarts_jwt_secret_key_rpp_2026")  # Fallback secure key
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # LLM & RAG
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Vertex AI (Google Cloud)
    GCP_PROJECT_ID: Optional[str] = os.getenv("GCP_PROJECT_ID")
    GCP_LOCATION: str = os.getenv("GCP_LOCATION", "us-central1")
    GCP_CREDENTIALS_JSON: Optional[str] = os.getenv("GCP_CREDENTIALS_JSON")
    VERTEX_MODEL: str = os.getenv("VERTEX_MODEL", "gemini-1.5-pro")
    
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL")  # For OpenRouter
    
    # NVIDIA NIM
    NVIDIA_NIM_API_KEY: Optional[str] = os.getenv("NVIDIA_NIM_API_KEY")
    NVIDIA_NIM_BASE_URL: str = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_NIM_MODEL: str = os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.3-70b-instruct")

    TOP_P: float = float(os.getenv("TOP_P", "0.95"))
    
    EMBEDDING_DIMENSION: int = 384
    VECTOR_SIMILARITY_THRESHOLD: float = 0.75
    
    # Storage (SeaweedFS)
    SEAWEEDFS_MASTER_URL: str = os.getenv("SEAWEEDFS_MASTER_URL", "http://seaweedfs:9333")
    SEAWEEDFS_VOLUME_URL: str = os.getenv("SEAWEEDFS_VOLUME_URL", "http://seaweedfs:8080")
    
    # Demo User (Development Only)
    DEMO_USER_EMAIL: str = os.getenv("DEMO_USER_EMAIL", "demo@example.com")
    DEMO_USER_PASSWORD: str = os.getenv("DEMO_USER_PASSWORD", "password123")
    DEMO_USER_USERNAME: str = os.getenv("DEMO_USER_USERNAME", "usuario_demo")

    # Widget Guest Login (usuario técnico dedicado para el widget embebible público)
    # HALLAZGO DE AUDITORÍA: estas credenciales vivían como literales en auth.py,
    # visibles en el repo/historial de git. Se mueven a configuración; el valor por
    # defecto preserva el que ya está hasheado en la BD para no romper el widget en
    # producción, pero DEBE rotarse (nueva contraseña + nuevo hash en BD + WIDGET_PASSWORD
    # vía Vault/env) ya que el valor actual quedó expuesto en el historial del repositorio.
    WIDGET_EMAIL: str = os.getenv("WIDGET_EMAIL", "widget@casmarts.com")
    WIDGET_PASSWORD: str = os.getenv("WIDGET_PASSWORD", "casmarts_widget_2026")

    # Authentik / OIDC (Centralizada en Core)
    AUTHENTIK_INTERNAL_URL: str = os.getenv("AUTHENTIK_INTERNAL_URL", "http://casmarts-core-authentik-server:9000")
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        origins = os.getenv("CORS_ORIGINS", "*")
        return [o.strip() for o in origins.split(",")]

# Initialize settings and override with Vault if possible
settings = Settings()

# HALLAZGO DE AUDITORÍA corregido: si Vault falla o no devuelve los secretos críticos,
# el código anterior seguía arrancando con los fallbacks hardcodeados de arriba
# (DB_PASSWORD/SECRET_KEY/JWT_SECRET), que son predecibles y están en el repo. En
# producción eso es inaceptable: es preferible que el proceso no arranque a que
# arranque con credenciales públicas conocidas. En desarrollo (APP_ENV != "production")
# se conserva el comportamiento anterior para no romper el flujo local.
_REQUIRED_VAULT_KEYS = ("SECRET_KEY", "JWT_SECRET", "DB_PASSWORD")

try:
    from app.core.vault import vault_client
    vault_secrets = vault_client.get_secrets()
    if vault_secrets:
        # Override critical secrets
        if "SECRET_KEY" in vault_secrets: settings.SECRET_KEY = vault_secrets["SECRET_KEY"]
        if "JWT_SECRET" in vault_secrets: settings.JWT_SECRET = vault_secrets["JWT_SECRET"]
        if "DB_PASSWORD" in vault_secrets: settings.DB_PASSWORD = vault_secrets["DB_PASSWORD"]
        if "GOOGLE_API_KEY" in vault_secrets: settings.GOOGLE_API_KEY = vault_secrets["GOOGLE_API_KEY"]
        if "GROQ_API_KEY" in vault_secrets: settings.GROQ_API_KEY = vault_secrets["GROQ_API_KEY"]
        if "WIDGET_PASSWORD" in vault_secrets: settings.WIDGET_PASSWORD = vault_secrets["WIDGET_PASSWORD"]
        print(f"🔒 Config loaded from Vault for {settings.APP_NAME}")
        missing = [k for k in _REQUIRED_VAULT_KEYS if k not in vault_secrets]
        if missing and settings.APP_ENV == "production":
            raise RuntimeError(
                f"Vault respondió pero no incluyó los secretos requeridos {missing} "
                f"en un entorno de producción. Abortando arranque."
            )
    elif settings.APP_ENV == "production":
        raise RuntimeError(
            "Vault no devolvió ningún secreto en un entorno de producción. "
            "Abortando arranque para evitar usar las credenciales por defecto "
            "(predecibles y presentes en el repositorio)."
        )
except Exception as e:
    print(f"⚠️ Vault integration skipped: {e}")
    if settings.APP_ENV == "production":
        raise RuntimeError(
            "No se pudieron cargar los secretos desde Vault en producción. "
            "Abortando arranque para evitar usar credenciales por defecto inseguras."
        ) from e

CORS_ORIGINS = settings.CORS_ORIGINS
