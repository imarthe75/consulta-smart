# Rate limiting ligero para endpoints costosos (LLM, uploads)
#
# HALLAZGO DE AUDITORÍA: ningún endpoint tenía límite de tasa (ver
# ESTANDAR_MAESTRO_AUDITORIA_UNIVERSAL.md §1.2 OWASP #4 / API4 Unrestricted Resource
# Consumption). Esta implementación es intencionalmente auto-contenida (sin nueva
# dependencia de pip) para no introducir riesgo de romper el build/despliegue sin poder
# probarlo end-to-end.
#
# Limitación conocida y documentada: el contador vive en memoria del proceso. Con
# múltiples workers/réplicas de Uvicorn/Gunicorn, cada proceso lleva su propio balde,
# por lo que el límite efectivo se multiplica por el número de workers. Si el
# despliegue real corre con >1 worker, migrar este backend a Redis (INCR + EXPIRE)
# para compartir el contador entre procesos.

import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status

_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(max_requests: int, window_seconds: int):
    """Devuelve una dependencia FastAPI que limita a `max_requests` por `window_seconds`,
    contadas por IP de origen + ruta (sliding window real, no fixed-window — ver
    ESTANDAR_MAESTRO §5.9 sobre por qué fixed-window produce ráfagas de error en el reset).
    """

    async def _dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{request.url.path}:{client_ip}"
        now = time.monotonic()
        bucket = _hits[key]

        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()

        if len(bucket) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas solicitudes. Intenta de nuevo en unos momentos."
            )

        bucket.append(now)

    return _dependency
