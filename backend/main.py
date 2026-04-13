# Punto de entrada de la aplicación FastAPI para ConsultaRPP

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, CORS_ORIGINS
from app.core.logger import setup_logging, logger
from app.core.database import init_db as init_database, close_db
from app.routes import health, documents, chat, auth, search

# ✅ IMPORTA el router de performance (ajusta ruta si lo moviste)
from app.routes.perf_test import router as perf_router

# Configurar logging
setup_logging(settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo de eventos de inicio y apagado"""
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # ========== INICIALIZAR BASE DE DATOS ==========
    await init_database()
    logger.info("✅ Base de datos inicializada")
    
    # ========== INICIALIZAR CACHÉ HÍBRIDA ==========
    try:
        from app.infrastructure.cache_layer import get_cache_instance
        cache = await get_cache_instance()
        logger.info("✅ Caché Híbrida inicializada (Redis + embeddings)")
    except Exception as e:
        logger.warning(f"⚠️  No se pudo inicializar caché: {e}. El sistema funcionará sin caché.")
    
    yield
    
    logger.info(f"Deteniendo {settings.APP_NAME}")
    
    # ========== LIMPIAR RECURSOS ==========
    try:
        from app.infrastructure.cache_layer import get_cache_instance
        cache = await get_cache_instance()
        await cache.close()
        logger.info("✅ Caché cerrada correctamente")
    except Exception as e:
        logger.warning(f"⚠️  Error cerrando caché: {e}")
    
    await close_db()

# ✅ Crear aplicación FastAPI (SOLO parámetros)
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Chatbot inteligente para consultas sobre Registro Público de la Propiedad",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600
)

# ✅ Incluir rutas
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(search.router)

# ✅ Incluir endpoint de performance (sin auth)
app.include_router(perf_router)

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
