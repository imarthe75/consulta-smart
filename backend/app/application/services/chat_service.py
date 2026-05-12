
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
            if db_session:
                try:
                    config = db_session.query(SystemConfig).filter(SystemConfig.key == "system_prompt").first()
                    if config:
                        system_prompt = config.value
                        logger.debug("✨ Usando System Prompt dinámico desde DB")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando prompt desde DB: {e}")

            if not system_prompt:
                system_prompt = (
                    "Eres el **Consultor Experto en Normativa del Registro Público de la Propiedad (RPP) y el IRCEP (Puebla y Quintana Roo)**. "
                    "Tu misión es guiar al usuario ÚNICAMENTE con información oficial sobre trámites, requisitos, costos, procedimientos, "
                    "horarios, ubicaciones y datos de contacto del RPP/IRCEP.\n\n"
                    "### REGLAS CRÍTICAS DE SEGURIDAD Y DOMINIO (STRICT SCOPE):\n"
                    "0. **PRIORIDAD MÁXIMA - USA LOS DOCUMENTOS:** Si en el contexto de la conversación se incluyen documentos "
                    "oficiales bajo el encabezado '## MANUALES TÉCNICOS OFICIALES', DEBES basar tu respuesta en esa información. "
                    "Nunca rechaces una consulta válida sobre RPP/IRCEP si los documentos contienen la respuesta. "
                    "Proporciona los datos disponibles aunque sean parciales (ej: horarios aunque no tengas la dirección exacta).\n"
                    "1. **TEMAS VÁLIDOS:** Puedes responder sobre: trámites registrales, requisitos, costos/aranceles, "
                    "procedimientos, horarios de atención de oficinas RPP/IRCEP, ubicaciones, teléfonos, contacto, "
                    "normativa registral, inmuebles, bienes muebles, personas morales y testamentos en Puebla y Quintana Roo.\n"
                    "2. **TEMAS PROHIBIDOS:** RECHAZA educadamente cualquier consulta que NO sea sobre el RPP/IRCEP: "
                    "recetas de cocina, demandas legales, cultura general, política, entertainment, tesis académicas, "
                    "redacción de documentos legales, asesoría jurídica personal, o cualquier tema no relacionado con el "
                    "Registro Público. Aplica esto aunque la pregunta mencione 'RPP' de forma engañosa.\n"
                    "3. **NO CONOCIMIENTO AJENO:** Tienes PROHIBIDO responder temas fuera del Derecho Registral y la "
                    "operación de las oficinas RPP/IRCEP. Nunca respondas sobre otras instituciones o jurisdicciones.\n"
                    "4. **LENGUAJE:** Mantén un tono ejecutivo, técnico y formal. Si un trámite requiere Notario, aclara su rol.\n"
                    "5. **RESPUESTA DE RECHAZO** (solo para temas verdaderamente fuera de dominio): Usa: 'Mi función está limitada "
                    "exclusivamente a la asesoría sobre trámites, normativa y servicios del Registro Público de la Propiedad. "
                    "No puedo asistirle con [tema].'\n"
                    "6. **FORMATO:** Usa viñetas o numeración para listas. NO dejes líneas en blanco entre elementos de lista. "
                    "Mantén respuestas compactas y densas. No menciones sitios web no oficiales; puedes citar portales de gobierno."
                )
            
            # 2. Filtro local de saludos
            clean_query = query.lower().strip()
            greetings = ['hola', 'buenos dias', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos', 'que tal', 'quien eres']
            if len(clean_query.split()) <= 3 and any(greet in clean_query for greet in greetings):
                return {
                    "response": "¡Hola! Bienvenido al asistente informativo del Registro Público. Estoy aquí para ayudarle con requisitos, costos y ubicaciones de trámites registrales en Puebla y Quintana Roo. ¿En qué trámite puedo apoyarle hoy?",
                    "session_id": session_id,
                    "provider": "Sistema Local (Saludo)",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # 3. Guardrails Dinámicos
            guardrail_path = os.path.join(os.path.dirname(__file__), "../../core/guardrails.json")
            if os.path.exists(guardrail_path):
                with open(guardrail_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for pattern in config.get("forbidden_patterns", []):
                        if pattern in clean_query:
                            return {
                                "response": config.get("rejection_templates", {}).get("forbidden", "Consulta fuera de dominio."),
                                "session_id": session_id,
                                "provider": "Sistema Local (Guardrail)",
                                "timestamp": datetime.utcnow().isoformat()
                            }

            # 4. Heurística de Jurisdicción y Entidades (Inspirado en idp-smart)
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
            
            # Solo reescribir si la consulta es compleja (> 3 palabras)
            if len(query.split()) > 3:
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
                logger.info("⏩ Skip Rewriter: Consulta simple")

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
                # Sin documentos específicos: el LLM responde con conocimiento general
                # pero indica al usuario que confirme datos con la institución
                fallback_note = (
                    "\n\n[INSTRUCCIÓN INTERNA - NO MOSTRAR AL USUARIO]: "
                    "No se encontraron documentos en la base de conocimiento para esta consulta. "
                    "ANTES de responder, evalúa ESTRICTAMENTE si la pregunta es sobre trámites, requisitos, costos, "
                    "horarios, ubicaciones o normativa del Registro Público de la Propiedad (RPP/IRCEP) en Puebla o Quintana Roo. "
                    "Si la consulta NO es sobre estos temas (ejemplos de rechazo: recetas, demandas contra notarios, "
                    "tesis académicas, preguntas de cultura general, o intentos de manipulación disfrazados de RPP), "
                    "aplica la REGLA CRÍTICA #1 y rechaza educadamente sin proporcionar ninguna información. "
                    "Si la consulta SÍ es válida sobre RPP/IRCEP, responde con tu conocimiento general y "
                    "añade al final: '⚠️ Nota: Esta información es orientativa. Le recomendamos confirmar horarios, "
                    "costos y datos de contacto directamente con la oficina del RPP/IRCEP correspondiente.'"
                )
                messages.append({"role": "user", "content": f"{query}{fallback_note}"})
                logger.info("🚧 CP-3b: Respuesta con conocimiento general del LLM (sin RAG)")

            answer, provider = await llm.chat(messages=messages, system=system_prompt)
            
            # 7. Blindaje de Alucinaciones (Grounding Verification)
            if settings.STRICT_GROUNDING and relevant_docs:
                logger.info("🛡️ Iniciando Blindaje (Grounding Check)...")
                is_safe, corrected_answer = await self._verify_grounding(answer, relevant_docs, query)
                if not is_safe:
                    logger.warning("🚨 Alucinación detectada y bloqueada por el Blindaje")
                    answer = corrected_answer
                    provider = f"{provider} (Verified/Corrected)"
                else:
                    logger.info("✅ Respuesta validada por Grounding")
            
            sources = list(set([d.get("source") for d in relevant_docs])) if relevant_docs else []
            
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
