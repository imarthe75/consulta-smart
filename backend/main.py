# Punto de entrada de la aplicación FastAPI para ConsultaRPP

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, CORS_ORIGINS
from app.core.logger import setup_logging, logger

# ✅ Configurar logging ANTES de importar rutas
setup_logging(settings.LOG_LEVEL)

from app.core.database import init_db as init_database, close_db
from app.routes import health, documents, chat, auth, search, admin
from fastapi.staticfiles import StaticFiles
from app.routes.perf_test import router as perf_router

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
    lifespan=lifespan,
    root_path="/api",
    servers=[{"url": "https://consulta.casmart.internal/api", "description": "Production Gateway"}]
)

# Middleware CORS - allow_origins=* para widget embebible en cualquier sitio
_cors_origins = CORS_ORIGINS
_allow_all = "*" in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _cors_origins,
    allow_credentials=False if _allow_all else True,
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
app.include_router(admin.router)

# ✅ Incluir endpoint de performance (sin auth)
app.include_router(perf_router)

# ✅ Servir archivos estáticos (Widget)
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

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
