"""
Smart LLM Router — Enrutador Inteligente Multiproveedor con Fallback Automático.

Orquesta las llamadas a modelos de lenguaje (Groq Llama 3, GCP Vertex/Gemini, NVIDIA NIM Cloud, Ollama),
evaluando disponibilidad en tiempo real, límites de tasa (rate limits) y degradación de latencia.
Soporta personalización de proveedor, clave API y modelo por perfil/tenant.
"""

from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import asyncio
import logging
from datetime import datetime, timedelta
from app.core.config import settings
from app.infrastructure.external.llm_service import GroqProvider, GeminiProvider
from app.infrastructure.external.local_embedding_service import LocalEmbeddingService

logger = logging.getLogger(__name__)


class _OpenAICompatibleProvider:
    """Adaptador mínimo para 'openai' como proveedor personalizado por tema.

    No existe un OpenAIProvider dedicado en llm_service.py; se reutiliza el mismo
    cliente `AsyncOpenAI` que ya usa NvidiaNimProvider (API compatible con OpenAI),
    apuntando al endpoint real de OpenAI en vez del de NVIDIA NIM.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key, timeout=30.0)
        self.chat_model = model

    async def chat(self, messages: List[dict], temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        from app.infrastructure.external.llm_service import _with_system
        response = await self.client.chat.completions.create(
            model=self.chat_model,
            messages=_with_system(messages, kwargs.get("system")),
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def embed(self, text: str) -> List[float]:
        return await LocalEmbeddingService().embed(text)


class ProviderStatus(Enum):
    """Estado de disponibilidad operativa de cada proveedor de IA."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"


class SmartLLMRouter:
    """
    Orquestador multimodelo que selecciona dinámicamente el mejor proveedor disponible:
    1. Disponibilidad (conteo de errores y bloqueos por Rate Limit).
    2. Prioridad de proveedores (Groq -> Cerebras -> Vertex AI -> NVIDIA NIM -> Gemini -> OpenRouter).
    3. Soporte para anulaciones (overrides) personalizadas por tema/tenant.
    """

    def __init__(
        self,
        custom_provider: Optional[str] = None,
        custom_api_key: Optional[str] = None,
        custom_model: Optional[str] = None,
        custom_base_url: Optional[str] = None,
    ):
        """
        Args:
            custom_provider: si se da (y no es 'default'), el router se restringe a
                UN solo proveedor específico para este tema/tenant, en vez de la
                cascada global de fallback. Valores soportados: 'groq', 'gemini',
                'nvidia', 'openai', 'anthropic', 'mistral', 'ollama', 'openrouter',
                'cerebras'. 'vertex' NO
                soporta override por tema (usa credenciales de proyecto GCP, no una
                API key simple) y lanza ValueError explícito — el llamador
                (chat_service.py) captura esto y hace fallback al router global, en
                vez de fallar en silencio.
            custom_api_key: API key específica del tema para el proveedor custom
                (no aplica a 'ollama', que no usa API key).
            custom_model: nombre de modelo específico del tema. Requerido para
                'anthropic', 'mistral' y 'ollama' (no tienen un default seguro).
            custom_base_url: endpoint del proveedor cuando aplica (obligatorio para
                'ollama'; opcional para 'openai'/'nvidia'/'mistral' si se usa un
                gateway/proxy propio en vez del endpoint público del proveedor).
        """
        # Orden de definicion = orden de prioridad por defecto (con "groq" preferido
        # movido al frente, ver mas abajo). Cerebras justo despues de groq por su
        # latencia de inferencia muy baja; openrouter al final por ser un agregador
        # (un salto de red adicional) -- agregados 2026-08-14, ver
        # BITACORA_ANALISIS_CAUSAL.md.
        self.providers = {
            "groq": None,
            "cerebras": None,
            "vertex": None,
            "nvidia": None,
            "gemini": None,
            "openrouter": None,
        }

        self.embeddings_service = LocalEmbeddingService()

        # Estado de cada proveedor
        self.provider_status: Dict[str, Dict[str, Any]] = {
            name: {
                "status": ProviderStatus.AVAILABLE,
                "last_error": None,
                "error_count": 0,
                "success_count": 0,
                "rate_limit_until": None,
            }
            for name in self.providers
        }

        if custom_provider and custom_provider.lower() != "default":
            self._init_custom_provider(custom_provider.lower(), custom_api_key, custom_model, custom_base_url)
            return

        # Preferencias de routing: Prioridad dinámica según .env
        preferred = settings.LLM_PROVIDER.lower() if hasattr(settings, 'LLM_PROVIDER') else "vertex"
        if preferred not in self.providers:
            logger.warning(f"⚠️ LLM_PROVIDER '{preferred}' no soportado. Se usará 'groq' como valor por defecto.")
            preferred = "groq" if "groq" in self.providers else next(iter(self.providers))
        others = [name for name in self.providers.keys() if name != preferred]
        self.priority_order: List[str] = [preferred] + others
        logger.info(f"🚦 SmartRouter: Prioridad establecida en {self.priority_order}")

        self._initialize_providers()

    def _init_custom_provider(
        self,
        provider_name: str,
        api_key: Optional[str],
        model: Optional[str],
        base_url: Optional[str] = None,
    ):
        """Configura el router en modo 'un solo proveedor' con credenciales personalizadas por tema."""
        from app.infrastructure.external.llm_service import (
            GroqProvider, GeminiProvider, NvidiaNimProvider, OllamaProvider,
            MistralProvider, AnthropicProvider, OpenRouterProvider, CerebrasProvider,
        )

        if provider_name == "groq":
            if not api_key:
                raise ValueError("custom_provider='groq' requiere custom_api_key")
            instance = GroqProvider(api_key=api_key)
            if model:
                instance.chat_model = model
        elif provider_name == "gemini":
            if not api_key:
                raise ValueError("custom_provider='gemini' requiere custom_api_key")
            instance = GeminiProvider(api_key=api_key)
            if model:
                instance.model_name = model
        elif provider_name == "nvidia":
            if not api_key:
                raise ValueError("custom_provider='nvidia' requiere custom_api_key")
            instance = NvidiaNimProvider(api_key=api_key)
            if model:
                instance.chat_model = model
        elif provider_name == "openai":
            if not api_key:
                raise ValueError("custom_provider='openai' requiere custom_api_key")
            instance = _OpenAICompatibleProvider(api_key=api_key, model=model or "gpt-4o-mini")
            if base_url:
                instance.client.base_url = base_url
        elif provider_name == "mistral":
            if not api_key:
                raise ValueError("custom_provider='mistral' requiere custom_api_key")
            instance = MistralProvider(api_key=api_key, base_url=base_url, model=model)
        elif provider_name == "anthropic":
            if not api_key:
                raise ValueError("custom_provider='anthropic' requiere custom_api_key")
            instance = AnthropicProvider(api_key=api_key, model=model)
        elif provider_name == "ollama":
            instance = OllamaProvider(base_url=base_url, model=model)
        elif provider_name == "openrouter":
            if not api_key:
                raise ValueError("custom_provider='openrouter' requiere custom_api_key")
            instance = OpenRouterProvider(api_key=api_key)
            if model:
                instance.chat_model = model
        elif provider_name == "cerebras":
            if not api_key:
                raise ValueError("custom_provider='cerebras' requiere custom_api_key")
            instance = CerebrasProvider(api_key=api_key)
            if model:
                instance.chat_model = model
        else:
            raise ValueError(
                f"custom_provider='{provider_name}' no soportado para override por tema "
                f"(soportados: 'groq', 'gemini', 'nvidia', 'openai', 'mistral', 'anthropic', "
                f"'ollama', 'openrouter', 'cerebras'; 'vertex' requiere credenciales de "
                f"proyecto GCP, no acepta una API key simple por tema)."
            )

        self.providers = {provider_name: instance}
        self.provider_status = {
            provider_name: {
                "status": ProviderStatus.AVAILABLE,
                "last_error": None,
                "error_count": 0,
                "success_count": 0,
                "rate_limit_until": None,
            }
        }
        self.priority_order = [provider_name]
        logger.info(f"🎯 SmartRouter en modo proveedor personalizado por tema: {provider_name}")

    def _initialize_providers(self):
        """Inicializa proveedores disponibles"""
        try:
            from app.infrastructure.external.llm_service import (
                GroqProvider, GeminiProvider, VertexAIProvider, NvidiaNimProvider,
                OpenRouterProvider, CerebrasProvider
            )

            # --- Vertex AI (Principal) ---
            if settings.GCP_PROJECT_ID:
                logger.info(f"🚀 Intentando inicializar Vertex AI con Proyecto: {settings.GCP_PROJECT_ID}")
                self.providers["vertex"] = VertexAIProvider()
                logger.info("✅ Vertex AI provider initialized (Primary)")
            else:
                self.provider_status["vertex"]["status"] = ProviderStatus.UNAVAILABLE
                logger.warning("⚠️ Vertex AI disabled (missing project ID in settings)")

            # --- NVIDIA NIM (High Performance) ---
            if settings.NVIDIA_NIM_API_KEY:
                self.providers["nvidia"] = NvidiaNimProvider()
                logger.info("✅ NVIDIA NIM provider initialized")
            else:
                self.provider_status["nvidia"]["status"] = ProviderStatus.UNAVAILABLE
                logger.warning("⚠️ NVIDIA NIM disabled (no API key)")

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
                logger.warning("⚠️ Gemini disabled (no API key)")
                self.provider_status["gemini"]["status"] = ProviderStatus.UNAVAILABLE

            # --- Cerebras (baja latencia) --- agregado 2026-08-14
            if settings.CEREBRAS_API_KEY:
                self.providers["cerebras"] = CerebrasProvider()
                logger.info("✅ Cerebras provider initialized")
            else:
                self.provider_status["cerebras"]["status"] = ProviderStatus.UNAVAILABLE
                logger.warning("⚠️ Cerebras disabled (no API key)")

            # --- OpenRouter (agregador multi-proveedor) --- agregado 2026-08-14
            if settings.OPENROUTER_API_KEY:
                self.providers["openrouter"] = OpenRouterProvider()
                logger.info("✅ OpenRouter provider initialized")
            else:
                self.provider_status["openrouter"]["status"] = ProviderStatus.UNAVAILABLE
                logger.warning("⚠️ OpenRouter disabled (no API key)")
        except Exception as e:
            logger.error(f"❌ Critical error initializing providers: {e}")

    def _get_best_provider(self) -> Optional[str]:
        """Selecciona el mejor proveedor disponible basado en estado"""
        available = []
        logger.info(f"🔍 Evaluando proveedores. Orden de prioridad: {self.priority_order}")
        for provider_name in self.priority_order:
            status = self.provider_status[provider_name]["status"]
            has_client = self.providers.get(provider_name) is not None

            # Skip si no está disponible o no tiene cliente
            if status == ProviderStatus.UNAVAILABLE or not has_client:
                continue

            # Check si está en rate limit
            if status == ProviderStatus.RATE_LIMITED:
                rate_limit_until = self.provider_status[provider_name]["rate_limit_until"]
                if rate_limit_until and datetime.now() < rate_limit_until:
                    logger.warning(f"  - {provider_name} está en Rate Limit")
                    continue
                else:
                    self.provider_status[provider_name]["status"] = ProviderStatus.AVAILABLE

            available.append(provider_name)

        if available:
            logger.info(f"🎯 Ganador definitivo: {available[0]}")
            return available[0]
        else:
            logger.error("❌ ERROR CRÍTICO: Ningún proveedor de IA está disponible.")
            return None

    def _build_offline_fallback(self, **kwargs) -> str:
        """Plantilla determinista CRAFT sin LLM -- último recurso, usada tanto cuando no
        hay ningún proveedor configurado como cuando todos fallaron con errores reales
        (antes esto último lanzaba una excepción sin capturar -> 500 crudo al usuario,
        incidente 2026-08-13)."""
        topic = kwargs.get("topic", "Sistema de Atención y Consultas")
        # `description` es el texto funcional real (puede venir vacío si el llamador no
        # lo pasa, ej. otros callers de .chat() distintos a generate_prompt); sin LLM no
        # hay forma de "resumir" nada, así que se pega literal en <contexto> para que el
        # system prompt resultante contenga información real en vez de texto inventado.
        description = kwargs.get("description") or topic
        target = kwargs.get("target_audience", "Usuarios generales")
        org = kwargs.get("organization", "la organización")
        sec = kwargs.get("sector", "General")

        return (
            f"Eres el **Consultor e Integrador Experto de {topic}** en **{org}** ({sec}).\n\n"
            f"<contexto>\n"
            f"Operas como el asistente inteligente oficial de {org}. Tu objetivo es brindar orientación precisa, confiable y oportuna a **{target}** sobre '{topic}'. A continuación se detalla el alcance funcional real de '{topic}', extraído directamente de la descripción provista por el administrador (NO la reemplaces por temas genéricos ni de otro dominio):\n\n"
            f"{description}\n\n"
            f"Responde siempre priorizando la base de datos RAG de manuales y documentos indexados de {org}.\n"
            f"</contexto>\n\n"
            f"<rol>\n"
            f"Actúa como Especialista Senior técnico de {org}, con trato empático, riguroso y altamente estructurado, usando vocabulario propio del sector ({sec}) — NO uses vocabulario burocrático/gubernamental (trámite, expediente, ventanilla, dependencia) salvo que el alcance funcional arriba realmente sea un trámite.\n"
            f"</rol>\n\n"
            f"<instrucciones>\n"
            f"1. Analiza la consulta de {target} e identifica a qué tema/funcionalidad del alcance descrito arriba corresponde.\n"
            f"2. Responde de forma clara, paso a paso y accionable, basándote en el alcance funcional real indicado arriba y en los manuales RAG indexados.\n"
            f"3. Si la información proviene de los manuales RAG indexados, cita los apartados o guías oficiales correspondientes.\n"
            f"4. Si la consulta excede el alcance documentado, indica el canal de soporte/contacto de {org} en vez de inventar una respuesta.\n"
            f"</instrucciones>\n\n"
            f"<formato>\n"
            f"- Utiliza encabezados Markdown claros (`###`), listas con viñetas y negritas para resaltar conceptos clave.\n"
            f"- Mantén respuestas ejecutivas sin bloques densos de texto.\n"
            f"</formato>\n\n"
            f"<reglas>\n"
            f"- **Cero Alucinaciones:** Responde estrictamente dentro del alcance funcional descrito arriba y la normativa de {org}.\n"
            f"- **Filtro de Dominio:** Si el usuario realiza preguntas ajenas a ese alcance, declina amablemente aclarando el propósito oficial del bot.\n"
            f"- **Tono:** Profesional, respetuoso y adaptado para **{target}**.\n"
            f"</reglas>\n\n"
            f"<ejemplos>\n"
            f"**Pregunta:** ¿Qué es '{topic}' y qué cubre?\n"
            f"**Respuesta:** {topic} es la solución de {org}. Su alcance funcional incluye: {description[:220].strip()}{'...' if len(description) > 220 else ''}\n"
            f"</ejemplos>\n\n"
            f"<!-- AVISO: este System Prompt fue generado por la PLANTILLA DETERMINISTA OFFLINE "
            f"(sin LLM disponible), no por un modelo de lenguaje. Revísalo y ajústalo manualmente; "
            f"cuando haya un proveedor de IA disponible, vuelve a presionar \"Generar\" para obtener "
            f"una versión redactada por el LLM. -->"
        )

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Chat con fallback automático entre proveedores
        """
        provider_name = self._get_best_provider()

        # La plantilla CRAFT determinista SOLO tiene sentido para el generador de
        # System Prompts del admin (admin.py::generate_prompt, que siempre manda
        # `topic`) -- NO es una respuesta valida para una consulta real de chat.
        # Incidente real 2026-08-14: con los 3 proveedores caidos, un usuario
        # preguntando algo real sobre Centinela-AI recibia literalmente el texto
        # "Eres el Consultor e Integrador Experto de Sistema de Atencion y
        # Consultas..." como si fuera la respuesta -- chat_service.py nunca manda
        # `topic`, y ya tiene su propio manejo de error honesto ("Lo siento, ocurrio
        # un error interno...") que este fallback estaba pisando silenciosamente.
        is_prompt_generation = "topic" in kwargs

        if not provider_name:
            if not is_prompt_generation:
                raise Exception("Ningún proveedor de IA está disponible en este momento.")
            logger.warning("⚠️ Sin proveedores de API externa configurados. Generando System Prompt estructurado dinámicamente con plantilla determinista CRAFT.")
            return self._build_offline_fallback(**kwargs), "fallback_offline"

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
                # Red de seguridad a nivel de router: NvidiaNimProvider/GroqProvider/
                # MistralProvider/OllamaProvider no configuran un timeout explícito en su
                # cliente AsyncOpenAI/AsyncGroq (a diferencia de Gemini/Vertex, que sí traen
                # timeout propio) y heredan el default del SDK (10 minutos). Incidente real
                # 2026-08-13: NVIDIA NIM se quedó colgado sin responder ni fallar durante más
                # de 7 minutos, bloqueando el failover al siguiente proveedor mientras el
                # usuario veía un timeout/499 en el navegador sin ninguna explicación. Este
                # wait_for garantiza que CUALQUIER proveedor (actual o futuro) falle rápido y
                # deje que el router pase al siguiente, sin depender de que cada provider
                # configure su propio timeout correctamente.
                #
                # Bajado de 45s a 15s el 2026-08-14: con 6 proveedores en la cascada, un
                # timeout de 45s por proveedor hacía que una consulta real que tuviera que
                # pasar por NVIDIA Y Gemini (ambos con problemas de disponibilidad ese día)
                # tardara 75+ segundos en total -- MÁS que el timeout del cliente HTTP del
                # frontend (60s, VITE_API_TIMEOUT), dejando al usuario viendo "Procesando
                # consulta..." colgado para siempre aunque el backend sí terminara y
                # guardara la respuesta (incidente real: petición completada en 79s, cliente
                # ya había abandonado). 15s es suficiente para una API de chat que responde
                # en producción (Groq/Gemini exitosos han respondido siempre en <2s en este
                # entorno) sin dejar que un proveedor caído consuma tiempo desproporcionado
                # del presupuesto total de espera del usuario.
                response = await asyncio.wait_for(
                    provider.chat(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system=system,
                        **kwargs
                    ),
                    timeout=15.0,
                )

                # Éxito: actualizar estadísticas
                self.provider_status[provider_name]["success_count"] += 1
                self.provider_status[provider_name]["error_count"] = 0
                self.provider_status[provider_name]["status"] = ProviderStatus.AVAILABLE

                logger.info(f"✅ Chat response from {provider_name}")
                return response, provider_name

            except asyncio.TimeoutError:
                # Incidente real 2026-08-13: sin este catch explícito, un TimeoutError
                # caía en el except genérico de abajo y no dejaba ningún rastro claro en
                # logs de que la causa fue un proveedor colgado (vs. un error de API real).
                logger.error(f"⏱️❌ {provider_name} TIMEOUT: sin respuesta tras 15s, saltando al siguiente proveedor")
                self.provider_status[provider_name]["error_count"] += 1
                if self.provider_status[provider_name]["error_count"] > 3:
                    self.provider_status[provider_name]["status"] = ProviderStatus.DEGRADED
                self.provider_status[provider_name]["last_error"] = "Timeout tras 15s sin respuesta"

                provider_name = self._get_next_provider(provider_name)
                if not provider_name:
                    if not is_prompt_generation:
                        raise Exception("Todos los proveedores de IA fallaron (timeout).")
                    # Se agotaron todos los proveedores con timeouts reales -- degradar a
                    # la plantilla offline en vez de un 500 crudo (mismo motivo que abajo),
                    # SOLO para el generador de prompts del admin (ver is_prompt_generation).
                    logger.error("❌ Todos los proveedores fallaron (último: timeout). Cayendo a plantilla determinista offline.")
                    return self._build_offline_fallback(**kwargs), "fallback_offline"

            except Exception as e:
                logger.error(f"❌ {provider_name} ERROR: {e}")
                error_str = str(e).lower()

                # Detectar autenticación fallida (401) o permisos
                if "401" in error_str or "unauthorized" in error_str or "api key" in error_str:
                    self.provider_status[provider_name]["status"] = ProviderStatus.UNAVAILABLE
                    logger.error(f"❌ Provider {provider_name} AUTH FAILURE. Disabling for session.")

                # Detectar rate limit
                elif "rate limit" in error_str or "quota" in error_str or "429" in error_str:
                    self.provider_status[provider_name]["status"] = ProviderStatus.RATE_LIMITED
                    self.provider_status[provider_name]["rate_limit_until"] = datetime.now() + timedelta(minutes=1)
                    self.provider_status[provider_name]["rate_limit_until"] = datetime.now() + timedelta(minutes=1)
                    logger.warning(f"⏱️ {provider_name} rate limited, waiting 1 minute")

                else:
                    self.provider_status[provider_name]["error_count"] += 1
                    if self.provider_status[provider_name]["error_count"] > 3:
                        self.provider_status[provider_name]["status"] = ProviderStatus.DEGRADED

                    logger.error(f"❌ {provider_name} CRITICAL ERROR: {e}")
                    # Log detallado para diagnosis de Vertex
                    if provider_name == "vertex":
                        logger.exception(f"🔴 ERROR CRITICO VERTEX (Proyecto {settings.GCP_PROJECT_ID}): {str(e)}")

                self.provider_status[provider_name]["last_error"] = str(e)

                # Intentar next provider
                provider_name = self._get_next_provider(provider_name)
                if not provider_name:
                    if not is_prompt_generation:
                        # chat_service.py (consultas reales de usuarios) NO manda `topic`
                        # -- aquí se propaga la excepción para que su propio manejo de
                        # error honesto la capture ("Lo siento, ocurrió un error
                        # interno..."), en vez de mostrarle al usuario la plantilla CRAFT
                        # de generación de System Prompt como si fuera una respuesta real
                        # (incidente real 2026-08-14).
                        raise Exception(f"Todos los proveedores de IA fallaron: {e}")
                    # Incidente real 2026-08-13: esto lanzaba una excepción sin capturar
                    # que admin.py no envolvía en try/except -> 500 crudo para el usuario
                    # (visto en logs de nginx a las 21:40:54) cada vez que TODOS los
                    # proveedores fallaban con errores reales (no solo "sin configurar").
                    # Degradar igual que el caso "ningún proveedor configurado": la
                    # plantilla offline + el aviso is_ai_generated=False es preferible a
                    # un error duro que rompe el panel sin explicación -- SOLO para el
                    # generador de prompts del admin (ver is_prompt_generation).
                    logger.error(f"❌ Todos los proveedores fallaron (último error: {e}). Cayendo a plantilla determinista offline.")
                    return self._build_offline_fallback(**kwargs), "fallback_offline"

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
