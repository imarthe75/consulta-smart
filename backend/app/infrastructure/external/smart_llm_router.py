"""
Smart LLM Router - Multi-provider com fallback automático
Similar a idp-smart, pero con APIs gratuitas
"""

from typing import List, Optional, Dict, Any
from enum import Enum
import logging
from datetime import datetime, timedelta
from app.core.config import settings
from app.infrastructure.external.llm_service import (
    GroqProvider, GeminiProvider
)
from app.infrastructure.external.local_embedding_service import LocalEmbeddingService

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Estado de disponibilidad de cada proveedor"""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"


class SmartLLMRouter:
    """
    Router inteligente que elige el mejor proveedor según:
    1. Disponibilidad (rate limits, errores)
    2. Latencia
    3. Confiabilidad histórica
    """
    
    def __init__(self):
        self.providers = {
            "vertex": None,
            "groq": None,
            "gemini": None,
            "ollama": None,
        }
        
        self.embeddings_service = LocalEmbeddingService()
        
        # Estado de cada proveedor
        self.provider_status: Dict[str, Dict[str, Any]] = {
            "vertex": {
                "status": ProviderStatus.AVAILABLE,
                "last_error": None,
                "error_count": 0,
                "success_count": 0,
                "rate_limit_until": None,
            },
            "groq": {
                "status": ProviderStatus.AVAILABLE,
                "last_error": None,
                "error_count": 0,
                "success_count": 0,
                "rate_limit_until": None,
            },
            "gemini": {
                "status": ProviderStatus.AVAILABLE,
                "last_error": None,
                "error_count": 0,
                "success_count": 0,
                "rate_limit_until": None,
            },
            "ollama": {
                "status": ProviderStatus.AVAILABLE,
                "last_error": None,
                "error_count": 0,
                "success_count": 0,
                "rate_limit_until": None,
            },
        }
        
        # Preferencias de routing: Vertex (si está disponible) > Groq > Gemini
        self.priority_order: List[str] = ["vertex", "groq", "gemini"]
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Inicializa proveedores disponibles"""
        try:
            from app.infrastructure.external.llm_service import (
                GroqProvider, GeminiProvider, VertexAIProvider
            )
            
            # --- Vertex AI (Principal) ---
            if settings.GCP_PROJECT_ID:
                logger.info(f"🚀 Intentando inicializar Vertex AI con Proyecto: {settings.GCP_PROJECT_ID}")
                self.providers["vertex"] = VertexAIProvider()
                logger.info("✅ Vertex AI provider initialized (Primary)")
            else:
                self.provider_status["vertex"]["status"] = ProviderStatus.UNAVAILABLE
                logger.warning("⚠️ Vertex AI disabled (missing project ID in settings)")

            # --- Groq (Secondary) ---
            if settings.GROQ_API_KEY:
                self.providers["groq"] = GroqProvider()
                logger.info("✅ Groq provider initialized")
            else:
                self.provider_status["groq"]["status"] = ProviderStatus.UNAVAILABLE
                logger.warning("⚠️ Groq disabled (no API key)")
        
            # --- Gemini (Fallback) ---
            if settings.GOOGLE_API_KEY:
                self.providers["gemini"] = GeminiProvider()
                logger.info("✅ Gemini provider initialized")
            else:
                self.provider_status["gemini"]["status"] = ProviderStatus.UNAVAILABLE
                logger.warning("⚠️ Gemini disabled (no API key)")
        except Exception as e:
            logger.error(f"❌ Critical error initializing providers: {e}")
    
    def _get_best_provider(self) -> Optional[str]:
        """Selecciona el mejor proveedor disponible basado en estado"""
        available = []
        
        for provider_name in self.priority_order:
            status = self.provider_status[provider_name]["status"]
            
            # Skip si no está disponible
            if status == ProviderStatus.UNAVAILABLE:
                continue
            
            # Check si está en rate limit
            if status == ProviderStatus.RATE_LIMITED:
                rate_limit_until = self.provider_status[provider_name]["rate_limit_until"]
                if rate_limit_until and datetime.now() < rate_limit_until:
                    continue  # Aún en rate limit
                else:
                    # Rate limit expiró, intentar de nuevo
                    self.provider_status[provider_name]["status"] = ProviderStatus.AVAILABLE
            
            available.append(provider_name)
        
        if available:
            logger.info(f"🎯 Selected provider: {available[0]}")
            return available[0]
        else:
            logger.warning("❌ No providers available!")
            return None
    
    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Chat con fallback automático entre proveedores
        """
        provider_name = self._get_best_provider()
        
        if not provider_name:
            raise Exception("No LLM providers available. Please configure at least one.")
        
        # Intentar con el proveedor seleccionado
        for attempt in range(len(self.priority_order)):
            try:
                if provider_name not in self.providers or not self.providers[provider_name]:
                    logger.warning(f"Provider {provider_name} not initialized, skipping...")
                    provider_name = self._get_next_provider(provider_name)
                    if not provider_name:
                        break
                    continue
                
                logger.info(f"📤 Chat request to {provider_name}")
                
                provider = self.providers[provider_name]
                response = await provider.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Éxito: actualizar estadísticas
                self.provider_status[provider_name]["success_count"] += 1
                self.provider_status[provider_name]["error_count"] = 0
                self.provider_status[provider_name]["status"] = ProviderStatus.AVAILABLE
                
                logger.info(f"✅ Chat response from {provider_name}")
                return response, provider_name
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Detectar rate limit
                if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
                    self.provider_status[provider_name]["status"] = ProviderStatus.RATE_LIMITED
                    self.provider_status[provider_name]["rate_limit_until"] = datetime.now() + timedelta(minutes=1)
                    logger.warning(f"⏱️ {provider_name} rate limited, waiting 1 minute")
                
                else:
                    self.provider_status[provider_name]["error_count"] += 1
                    if self.provider_status[provider_name]["error_count"] > 3:
                        self.provider_status[provider_name]["status"] = ProviderStatus.DEGRADED
                    
                    logger.error(f"❌ {provider_name} CRITICAL ERROR: {e}")
                    # Log detallado para diagnosis de Vertex
                    if provider_name == "vertex":
                        logger.error(f"🔍 DETALLE FALLO VERTEX (Proyecto {settings.GCP_PROJECT_ID}): {str(e)}")
                
                self.provider_status[provider_name]["last_error"] = str(e)
                
                # Intentar next provider
                provider_name = self._get_next_provider(provider_name)
                if not provider_name:
                    raise Exception(f"All LLM providers failed. Last error: {e}")
        
        return response, provider_name
    
    def _get_next_provider(self, current: str) -> Optional[str]:
        """Obtiene el siguiente proveedor en la cola de prioridad"""
        try:
            current_idx = self.priority_order.index(current)
            for next_name in self.priority_order[current_idx + 1:]:
                if self.provider_status[next_name]["status"] != ProviderStatus.UNAVAILABLE:
                    return next_name
        except (ValueError, IndexError):
            pass
        return None
    
    async def embed(self, text: str) -> List[float]:
        """
        Generar embeddings LOCALES (sin APIs externas)
        - Usa Sentence Transformers (384-dim)
        - Completamente gratis y local
        """
        try:
            embedding = await self.embeddings_service.embed(text)
            return embedding
        except Exception as e:
            logger.error(f"❌ Embedding error: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna estado actual de todos los proveedores"""
        status_dict = {}
        for provider_name, status_info in self.provider_status.items():
            status_dict[provider_name] = {
                "status": status_info["status"].value,
                "success_count": status_info["success_count"],
                "error_count": status_info["error_count"],
                "last_error": status_info["last_error"],
            }
        return status_dict


# Singleton
_router = None


async def get_smart_router() -> SmartLLMRouter:
    """Factory para obtener el router singleton"""
    global _router
    if _router is None:
        _router = SmartLLMRouter()
    return _router
