# Cifrado simétrico para secretos almacenados en columnas de la base de datos.
#
# HALLAZGO DE AUDITORÍA (SC-28, cifrado de datos sensibles en reposo):
# `ChatbotProfileModel.custom_api_key` guarda una API key de un proveedor LLM externo
# (OpenAI/Anthropic/Gemini/etc.) por tema, y `chat_service.py` la usa activamente para
# llamadas reales — no es un campo decorativo. Antes se guardaba en texto plano en
# PostgreSQL; un volcado de la base o acceso de solo lectura a la BD exponía
# credenciales de terceros con facturación asociada. Se cifra con Fernet (AES-128 +
# HMAC autenticado) usando una clave derivada de SECRET_KEY para no requerir
# aprovisionar un secreto nuevo.
#
# Compatibilidad hacia atrás: `decrypt_secret` devuelve el valor tal cual si no puede
# descifrarlo (valores legados guardados en texto plano antes de este cambio) en vez
# de fallar — evita romper temas ya configurados hasta que se vuelvan a guardar.

import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def _get_fernet() -> Fernet:
    key_material = getattr(settings, "FIELD_ENCRYPTION_KEY", None) or settings.SECRET_KEY
    derived_key = base64.urlsafe_b64encode(hashlib.sha256(key_material.encode()).digest())
    return Fernet(derived_key)


def encrypt_secret(plaintext: str) -> str:
    """Cifra un valor sensible. Devuelve el valor tal cual si viene vacío."""
    if not plaintext:
        return plaintext
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(value: str) -> str:
    """Descifra un valor cifrado con encrypt_secret.

    Si el valor no es un token Fernet válido (legado en texto plano, o dato corrupto),
    lo devuelve sin modificar en vez de lanzar una excepción.
    """
    if not value:
        return value
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError):
        return value
