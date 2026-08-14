
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.logger import logger
from app.infrastructure.knowledge_base import KnowledgeBase
from app.infrastructure.external.smart_llm_router import get_smart_router
from app.infrastructure.models import SystemConfig
from app.infrastructure.cache_layer import get_cache_instance
from app.application.services.heuristics import heuristics
from app.core.config import settings

class ChatService:
    """
    Servicio de chat especializado en materia Registral y Catastral (RPP/IRCEP).
    Integra RAG con reglas de negocio regionales estrictas.
    """

    def __init__(self):
        self._llm = None
        self._cache = None
        self.knowledge_base = KnowledgeBase()
        logger.info("✅ ChatService: Cargado con reglas específicas RPP/IRCEP 2026")

    async def _get_llm(self):
        if self._llm is None:
            self._llm = await get_smart_router()
        return self._llm

    async def _get_cache(self):
        if self._cache is None:
            self._cache = await get_cache_instance()
        return self._cache

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        db_session=None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Procesa una consulta especializada en RPP con protocolo de autoridad"""
        try:
            logger.info(f"💬 Consulta RPP: {query[:80]}...")
                   # 1. Definición de Personalidad de Autoridad (Protocolo 2026 - Dinámico)
            system_prompt = None
            welcome_msg = "¡Hola! ¿En qué puedo apoyarle hoy?"
            profile_id = "general"  # Por defecto es el chatbot genérico

            if filters:
                if "category" in filters:
                    profile_id = filters["category"]
                elif "profile_id" in filters:
                    profile_id = filters["profile_id"]

            # ── Caché híbrida (Redis + embeddings) ───────────────────────────
            # HALLAZGO 2026-08-14: _get_cache() existía pero nunca se llamaba desde
            # aquí -- la caché estaba completamente desconectada del flujo real, así
            # que CADA consulta (incluso repetida palabra por palabra) pagaba el
            # costo/latencia completo de RAG+LLM. Solo se usa para preguntas sin
            # historial de conversación (primer turno): una respuesta cacheada de una
            # pregunta aislada puede ser incorrecta si en realidad era una continuación
            # contextual ("¿y eso cuánto cuesta?"), así que ese caso se excluye a
            # propósito. `namespace=profile_id` aísla el caché por tenant (ver
            # cache_layer.py::_generate_cache_key) para que una respuesta de un tema no
            # se sirva jamás a otro tema con una pregunta similar/idéntica.
            cache_hit = None
            if not conversation_history:
                try:
                    cache = await self._get_cache()
                    cache_hit = await cache.get_with_fallback(query, namespace=profile_id)
                except Exception as cache_err:
                    logger.warning(f"⚠️ Caché no disponible, continuando sin ella: {cache_err}")

            if cache_hit and not cache_hit.get("needs_llm_refinement"):
                logger.info(f"🟢 CACHE HIT ({profile_id}): {query[:50]}...")
                return {
                    "response": cache_hit.get("response", ""),
                    "provider": "cache",
                    "session_id": session_id,
                    "sources": cache_hit.get("sources", []),
                    "timestamp": datetime.utcnow().isoformat(),
                    "from_cache": "exact_or_similar",
                }

            if db_session:
                try:
                    from sqlalchemy import select
                    from app.infrastructure.models import ChatbotProfile
                    stmt = select(ChatbotProfile).where(ChatbotProfile.id == profile_id)
                    result = await db_session.execute(stmt)
                    profile = result.scalars().first()
                    if profile:
                        if profile.system_prompt:
                            system_prompt = profile.system_prompt
                            logger.debug(f"✨ Usando System Prompt dinámico del perfil: {profile_id}")
                        if profile.welcome_message:
                            welcome_msg = profile.welcome_message
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando perfil {profile_id} desde DB: {e}")

            is_custom = False
            if system_prompt:
                # Si el prompt no contiene RPP de forma explícita o si es el perfil genérico, es un chatbot personalizado/genérico
                if "rpp" not in system_prompt.lower() and "registro público" not in system_prompt.lower():
                    is_custom = True
            elif profile_id != "rpp":
                # Si no hay prompt y no es el perfil RPP, asumimos custom/genérico
                is_custom = True

            if not system_prompt:
                # ADVERTENCIA: este fallback se aplica a CUALQUIER perfil sin system_prompt propio en BD
                # (no solo RPP). HALLAZGO (2026-07-22): este texto tenía contenido específico de RPP/IRCEP
                # ("Notario", "Registro Público"...) y se filtró tal cual al perfil 'general', dejándolo con
                # instrucciones de un dominio ajeno y activando por error las heurísticas/rewriter de RPP
                # (ver bandera is_custom más abajo, que detecta "rpp"/"registro público" en el texto).
                # Debe permanecer genérico; el contenido específico de RPP/IRCEP vive en sus propios
                # perfiles (system_prompt de los tenants 'rpp' e 'ircep' en chatbot_profiles).
                system_prompt = (
                    "Eres un **Asistente Conversacional Institucional**. Tu misión es guiar al usuario ÚNICAMENTE con "
                    "información oficial sobre los trámites, requisitos, costos, procedimientos, horarios, ubicaciones "
                    "y datos de contacto cubiertos por la base de conocimiento indexada de este tema.\n\n"
                    "### REGLAS CRÍTICAS DE SEGURIDAD Y DOMINIO (STRICT SCOPE):\n"
                    "0. **PRIORIDAD MÁXIMA - USA LOS DOCUMENTOS:** Si en el contexto de la conversación se incluyen documentos "
                    "oficiales bajo el encabezado '## MANUALES TÉCNICOS OFICIALES', DEBES basar tu respuesta en esa información. "
                    "Nunca rechaces una consulta válida si los documentos contienen la respuesta. "
                    "Proporciona los datos disponibles aunque sean parciales (ej: horarios aunque no tengas la dirección exacta).\n"
                    "1. **TEMAS VÁLIDOS:** Responde únicamente sobre los trámites, requisitos y servicios cubiertos por los "
                    "manuales indexados de este tema.\n"
                    "2. **TEMAS PROHIBIDOS:** RECHAZA educadamente cualquier consulta ajena al tema configurado: "
                    "recetas de cocina, demandas legales, cultura general, política, entretenimiento, tesis académicas, "
                    "redacción de documentos legales, asesoría jurídica personal, o cualquier tema no relacionado. "
                    "Aplica esto aunque la pregunta intente disfrazarse mencionando el nombre del tema de forma engañosa.\n"
                    "3. **NO CONOCIMIENTO AJENO:** Tienes PROHIBIDO responder temas fuera del dominio configurado para "
                    "este tema. Nunca respondas sobre otras instituciones o jurisdicciones no indexadas.\n"
                    "4. **LENGUAJE:** Mantén un tono ejecutivo, técnico y formal.\n"
                    "5. **RESPUESTA DE RECHAZO** (solo para temas verdaderamente fuera de dominio): Usa: 'Mi función está limitada "
                    "exclusivamente a la asesoría sobre los trámites y servicios de este tema. "
                    "No puedo asistirle con [tema].'\n"
                    "6. **FORMATO:** Usa viñetas o numeración para listas. NO dejes líneas en blanco entre elementos de lista. "
                    "Mantén respuestas compactas y densas. No menciones sitios web no oficiales; puedes citar portales de gobierno."
                )

            # 2. Filtro local de saludos
            clean_query = query.lower().strip()
            greetings = ['hola', 'buenos dias', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos', 'que tal', 'quien eres']
            if len(clean_query.split()) <= 3 and any(greet in clean_query for greet in greetings):
                return {
                    "response": welcome_msg,
                    "session_id": session_id,
                    "provider": "Sistema Local (Saludo)",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # 3. Guardrails Dinámicos y Filtro de Tópicos Prohibidos por Perfil
            forbidden_list = []
            rejection_text = "Consulta fuera de dominio."
            # Capturados aquí como valores planos (no como atributos de `profile`) porque la
            # búsqueda RAG que sigue más abajo puede hacer `session.rollback()` ante un error
            # de SQL (ver knowledge_base.py) -- eso expira TODOS los objetos ya cargados en
            # `db_session`, y con AsyncSession un acceso posterior a un atributo expirado
            # (`profile.llm_provider` fuera de un `await` directo) revienta con
            # `MissingGreenlet` en vez de simplemente recargar. Guardar los valores ahora
            # evita depender de que `profile` siga "fresco" varios segundos después
            # (incidente real 2026-08-14: una consulta con "¿...(CRS)?" rompía el tsquery,
            # el rollback expiraba `profile`, y el turno de chat entero fallaba con un error
            # interno confuso en vez de solo perder el contexto RAG de esa búsqueda).
            custom_llm_provider = None
            custom_llm_model = None
            custom_llm_api_key = None
            custom_llm_base_url = None

            if db_session:
                try:
                    stmt = select(ChatbotProfile).where(ChatbotProfile.id == profile_id)
                    result = await db_session.execute(stmt)
                    profile = result.scalars().first()
                    if profile:
                        if profile.forbidden_topics:
                            forbidden_list = [t.strip().lower() for t in profile.forbidden_topics.split(',') if t.strip()]
                        if profile.rejection_message:
                            rejection_text = profile.rejection_message
                        custom_llm_provider = profile.llm_provider
                        custom_llm_model = profile.llm_model
                        custom_llm_api_key = profile.custom_api_key
                        custom_llm_base_url = profile.custom_base_url
                except Exception as e:
                    logger.warning(f"Error evaluando guardrails de perfil {profile_id}: {e}")

            # Evaluación de tópicos prohibidos en la consulta
            for topic in forbidden_list:
                if topic in clean_query:
                    logger.info(f"⛔ Consulta bloqueada por Guardrail ('{topic}'): {query}")
                    return {
                        "response": rejection_text,
                        "session_id": session_id,
                        "provider": "Sistema Local (Guardrail Tópico Prohibido)",
                        "timestamp": datetime.utcnow().isoformat()
                    }

            # Guardrails secundarios por archivo JSON si existe
            guardrail_path = os.path.join(os.path.dirname(__file__), "../../core/guardrails.json")
            if os.path.exists(guardrail_path):
                with open(guardrail_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for pattern in config.get("forbidden_patterns", []):
                        if pattern in clean_query:
                            return {
                                "response": config.get("rejection_templates", {}).get("forbidden", rejection_text),
                                "session_id": session_id,
                                "provider": "Sistema Local (Guardrail Archivo)",
                                "timestamp": datetime.utcnow().isoformat()
                            }

            # 4. Heurística de Jurisdicción y Entidades (Inspirado en idp-smart)
            h_logic = {}
            if not is_custom:
                h_logic = heuristics.apply_search_logic(query)
            h_jurisdiction = h_logic.get("jurisdiction")
            h_entities = h_logic.get("entities")

            if h_jurisdiction:
                logger.info(f"⚖️ Heurística: Jurisdicción detectada -> {h_jurisdiction}")
                if not filters: filters = {}
                filters["category"] = h_jurisdiction

            # 5. Traducción Semántica (RAG Rewrite) - OPTIMIZADO
            logger.info("🚧 CP-1: Entrando a Rewriter")
            llm = await self._get_llm()
            search_query = query

            # Boost query con entidades críticas
            if h_entities:
                search_query = f"{' '.join(h_entities)} {query}"
                logger.info(f"🚀 Boosting query con entidades: {h_entities}")

            # Solo reescribir si la consulta es compleja (> 3 palabras) y no es personalizado
            if len(query.split()) > 3 and not is_custom:
                try:
                    rewrite_prompt = f"Como experto RPP, traduce esta frase ciudadana a términos técnicos de búsqueda registral (solo el resultado): '{query}'"
                    # Timeout agresivo de 5s para el rewriter: es mejor una búsqueda subóptima que un timeout total
                    res, _ = await asyncio.wait_for(
                        llm.chat([{"role": "user", "content": rewrite_prompt}], temperature=0, system=system_prompt),
                        timeout=5.0
                    )
                    search_query = res.strip().replace('"', '')
                    logger.info(f"🧠 Rewriter: '{query}' -> '{search_query}'")
                except asyncio.TimeoutError:
                    logger.warning("⏱️ Rewriter TIMEOUT: Usando query original para no retrasar respuesta")
                    search_query = query
                except Exception as e:
                    logger.warning(f"⚠️ Error rewriter: {e}")
                    search_query = query
            else:
                logger.info("⏩ Skip Rewriter: Consulta simple o modo personalizado")

            # 5. Búsqueda RAG con Umbral Ampliado (0.70) para mayor cobertura
            logger.info("🚧 CP-2: Entrando a Búsqueda RAG")
            raw_docs = await self.knowledge_base.search_in_knowledge_async(search_query, session=db_session, top_k=3, filters=filters)

            relevant_docs = []
            for d in raw_docs:
                rel_str = d.get('relevance', '1.0')
                if "palabras clave" in rel_str.lower():
                    relevant_docs.append(d)
                else:
                    try:
                        dist = float(rel_str.split(':')[-1].strip())
                        if dist < 0.70:  # Umbral ampliado de 0.60 a 0.70
                            relevant_docs.append(d)
                    except:
                        pass

            logger.info(f"🔍 Búsqueda RAG: {len(raw_docs)} brutos, {len(relevant_docs)} relevantes con dist < 0.70")

            # 6. Generación de Respuesta con o sin contexto RAG
            messages = []
            if conversation_history:
                for m in conversation_history[-4:]:
                    messages.append({"role": m.get("role"), "content": m.get("content")})

            if relevant_docs:
                # Respuesta con contexto oficial de la base de conocimiento
                context = "\n\n## MANUALES TÉCNICOS OFICIALES:\n"
                for d in relevant_docs:
                    context += f"Fuente: {d.get('source')}\n{d.get('content')[:1500]}\n\n"
                messages.append({
                    "role": "user",
                    "content": (
                        f"{query}\n\n{context}\n\n"
                        "[INSTRUCCIÓN: Responde basándote en los documentos oficiales anteriores. "
                        "Si los documentos contienen la información solicitada (horarios, direcciones, contactos, requisitos), "
                        "DEBES proporcionarla. No rechaces la consulta si está en el contexto.]"
                    )
                })
                logger.info("🚧 CP-3a: Respuesta con contexto RAG oficial")
            else:
                # Sin documentos específicos en RAG
                if is_custom:
                    fallback_note = (
                        "\n\n[INSTRUCCIÓN INTERNA - NO MOSTRAR AL USUARIO]: "
                        "No se encontraron documentos específicos en la base de conocimiento RAG. "
                        "Responde de manera ejecutiva, útil y profesional dentro del rol definido en el System Prompt. "
                        "Si la pregunta es totalmente ajena o prohibida según tus reglas, rechaza educadamente."
                    )
                else:
                    fallback_note = (
                        "\n\n[INSTRUCCIÓN INTERNA - NO MOSTRAR AL USUARIO]: "
                        "No se encontraron documentos en la base de conocimiento para esta consulta. "
                        "ANTES de responder, evalúa ESTRICTAMENTE si la pregunta pertenece al dominio de atención. "
                        "Si la consulta NO es sobre temas válidos, aplica las reglas de rechazo del bot. "
                        "Si la consulta SÍ es válida, responde con conocimiento general y añade una nota aclaratoria orientativa."
                    )
                messages.append({"role": "user", "content": f"{query}{fallback_note}"})
                logger.info("🚧 CP-3b: Respuesta con conocimiento general del LLM (sin RAG)")

            # Evaluación de motor LLM por Tema/Perfil con Fallback Inteligente
            active_llm = llm
            if custom_llm_provider and custom_llm_provider != "default":
                try:
                    logger.info(f"🔄 Usando motor LLM personalizado para tema '{profile_id}': {custom_llm_provider}")
                    from app.infrastructure.external.smart_llm_router import SmartLLMRouter
                    from app.core.crypto import decrypt_secret
                    custom_router = SmartLLMRouter(
                        custom_provider=custom_llm_provider,
                        custom_api_key=decrypt_secret(custom_llm_api_key),
                        custom_model=custom_llm_model,
                        custom_base_url=custom_llm_base_url
                    )
                    answer, provider = await custom_router.chat(messages=messages, system=system_prompt)
                except Exception as custom_llm_err:
                    logger.warning(f"⚠️ Error en motor custom ({custom_llm_provider}), ejecutando fallback a Smart Router Global: {custom_llm_err}")
                    answer, provider = await llm.chat(messages=messages, system=system_prompt)
                    provider = f"{provider} (Fallback por error en {custom_llm_provider})"
            else:
                answer, provider = await llm.chat(messages=messages, system=system_prompt)

            # 7. Blindaje de Alucinaciones (Grounding Verification)
            if settings.STRICT_GROUNDING and relevant_docs:
                logger.info("🛡️ Iniciando Blindaje (Grounding Check)...")
                try:
                    # HALLAZGO 2026-08-14: `_verify_grounding` hace su propia llamada
                    # independiente a `_get_best_provider()`, que puede reintentar un
                    # proveedor que acaba de fallar/tardar en la respuesta principal
                    # de este mismo turno (el router solo lo marca DEGRADED tras 4
                    # timeouts acumulados, no tras el primero). En un momento de
                    # cascada degradada esto duplicaba el tiempo total de espera
                    # (~30-45s extra) para una verificación que de por sí falla
                    # "abierto" (usa la respuesta original) si no puede completarse.
                    # Se acota a un presupuesto corto: es una red de seguridad
                    # opcional sobre una respuesta que el usuario ya recibió a
                    # tiempo, no vale la pena hacerlo esperar el doble por ella.
                    is_safe, corrected_answer = await asyncio.wait_for(
                        self._verify_grounding(answer, relevant_docs, query),
                        timeout=8.0
                    )
                    if not is_safe:
                        logger.warning("🚨 Alucinación detectada y bloqueada por el Blindaje")
                        answer = corrected_answer
                        provider = f"{provider} (Verified/Corrected)"
                    else:
                        logger.info("✅ Respuesta validada por Grounding")
                except asyncio.TimeoutError:
                    logger.warning("⏱️ Blindaje excedió 8s, se usa la respuesta original sin verificar")

            # ── Construcción de fuentes para la UI ───────────────────────────
            # Se construye una lista de objetos enriquecidos (no strings planos)
            # deduplicada por documento (por 'source'/filename) conservando el
            # chunk más relevante de cada documento.
            # Retrocompat: el campo "source" (string) sigue existiendo para
            # los mensajes ya guardados en BD con formato antiguo.
            seen_sources: set = set()
            sources = []
            for d in relevant_docs:
                key = d.get("source", "")   # string legible único por doc/versión
                if key in seen_sources:
                    continue
                seen_sources.add(key)
                sources.append({
                    "filename":     key,                        # id legible (retrocompat)
                    "title":        d.get("title") or key,      # nombre del documento
                    "chunk_number": d.get("chunk_number"),      # fragmento de referencia
                    "version_label": d.get("version_label"),    # versión del reglamento
                    "relevance":    d.get("relevance", ""),     # distancia/método
                })

            # Guardar en caché para la próxima consulta idéntica/similar en este mismo
            # tenant -- solo cuando fue una pregunta de primer turno (ver condición
            # espejo al inicio de esta función) y hubo una respuesta real de un LLM
            # (nunca cachear el fallback offline, que es una plantilla genérica, no
            # una respuesta real a esta pregunta).
            if not conversation_history and provider != "fallback_offline":
                try:
                    cache = await self._get_cache()
                    await cache.store_response(
                        query, answer,
                        sources=[s["filename"] for s in sources],
                        namespace=profile_id,
                    )
                except Exception as cache_err:
                    logger.warning(f"⚠️ No se pudo guardar en caché: {cache_err}")

            return {
                "response": answer,
                "provider": f"{provider} (RAG)" if relevant_docs else f"{provider} (General)",
                "session_id": session_id,
                "sources": sources,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"❌ ERROR CRÍTICO ChatService:\n{error_trace}")
            return {
                "response": f"Lo siento, ocurrió un error interno al procesar su consulta: {str(e)}",
                "session_id": session_id,
                "provider": "Sistema de Emergencia",
                "timestamp": datetime.utcnow().isoformat(),
                "error": True
            }

    async def _verify_grounding(self, answer: str, docs: List[Dict[str, Any]], original_query: str) -> tuple[bool, str]:
        """
        Verifica que la respuesta no contenga información inventada no presente en los documentos.
        """
        try:
            llm = await self._get_llm()
            context = "\n".join([d.get('content', '') for d in docs])

            verify_prompt = (
                f"Eres un Auditor de Veracidad Legal. Tu tarea es comparar la RESPUESTA con el CONTEXTO proporcionado.\n\n"
                f"CONTEXTO OFICIAL:\n{context[:3000]}\n\n"
                f"RESPUESTA A AUDITAR:\n{answer}\n\n"
                f"REGLA: Si la respuesta menciona costos, requisitos o procedimientos que NO están en el contexto, "
                f"o si contradice una 'Regla Estricta' (como el cobro por página), marca como NO FIABLE.\n\n"
                f"Responde en formato JSON:\n"
                f"{{\"is_grounded\": true/false, \"corrected_answer\": \"(Solo si es necesario, una versión que diga que no hay información sobre los puntos inventados)\"}}"
            )

            # Usar un modelo rápido para validación
            res_json, _ = await llm.chat([{"role": "user", "content": verify_prompt}], temperature=0)

            # Intentar parsear JSON
            try:
                data = json.loads(res_json.strip())
                return data.get("is_grounded", True), data.get("corrected_answer", answer)
            except:
                # Si falla el parseo, confiar en heurística simple de heuristics.py
                is_grounded = heuristics.is_answer_grounded(answer, context)
                return is_grounded, answer

        except Exception as e:
            logger.error(f"Error en blindaje: {e}")
            return True, answer

_chat_service = None
async def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None: _chat_service = ChatService()
    return _chat_service
