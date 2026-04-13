# Chat Service - Integración de LLM + Base de Conocimiento + Caché Híbrida

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.logger import logger
from app.infrastructure.knowledge_base import KnowledgeBase
from app.infrastructure.external.smart_llm_router import get_smart_router
from app.infrastructure.cache_layer import get_cache_instance
from app.core.config import settings


class ChatService:
    """
    Servicio de chat que integra:
    1. LLM con base de conocimiento de requisitos
    2. Caché híbrida (Redis + embeddings) para reducir 60% costos Groq
    """
    
    def __init__(self):
        # Lazy initialization de router (se carga cuando se necesita)
        self._llm = None
        self._cache = None
        # Inicializar knowledge_base en construcción
        self.knowledge_base = KnowledgeBase()
        self.system_prompt = self._build_system_prompt()
        logger.info("ChatService: Inicializado (LLM Router + Caché Híbrida cargará en primer uso)")
    
    async def _get_llm(self):
        """Lazy initialization del router"""
        if self._llm is None:
            self._llm = await get_smart_router()
            logger.info("✅ SmartLLMRouter inicializado (Groq → Gemini fallback)")
        return self._llm
    
    async def _get_cache(self):
        """Lazy initialization de caché híbrida"""
        if self._cache is None:
            self._cache = await get_cache_instance()
            logger.info("✅ Caché Híbrida inicializada (Redis + embeddings)")
        return self._cache

    def _build_system_prompt(self) -> str:
        """Construye el prompt del sistema con contexto de requisitos"""
        return f"""Eres un asistente CONSULTOR EXPERTO en trámites del Registro Público de la Propiedad (RPP) de México.
Tu servicio está especializado para **Notarios Públicos, Abogados Registrales y Ciudadanos** (público en general).
Tu objetivo es proporcionar asesoría legal, procedimental y de costos sobre procesos registrales con la máxima precisión.

🎯 **INSTRUCCIONES CRÍTICAS PARA TU RESPUESTA (POLÍTICA DE TOLERANCIA CERO):**

**1. ALCANCE Y PERSONALIDAD**
   ✓ Tu expertise es ÚNICA Y ESTRICTAMENTE LEGAL Y REGISTRAL.
   ✓ **PROHIBIDO:** Proporcionar información técnica de software, fragmentos de código, scripts, comandos de terminal, guías de migración tecnológica o detalles sobre arquitectura de sistemas.
   ✓ **RECHAZO MANDATORIO:** Si el usuario te envía fragmentos de código o te pregunta sobre bases de datos técnicas, APIs (Groq, Ollama, etc.), o programación (JavaScript, etc.), DEBES RESPONDER EXACTAMENTE: 
     "Mi área de dominio es exclusivamente el Derecho Registral Mexicano y trámites del RPP (Puebla y Quintana Roo). No estoy autorizado para proporcionar asistencia técnica, código o consultoría de software. El objetivo de este chat es ser su consultor experto en temas registrales."
   ✓ No importa si encuentras información técnica en los documentos adjuntos (RAG), DEBES OMITIRLA por completo.
   ✓ Si la pregunta no se refiere a trámites registrales, leyes o requisitos del RPP, genera la respuesta de rechazo indicada arriba.

**2. DIFERENCIACIÓN REGIONAL Y ORGANISMOS**
   ✓ **Identificación Precisa:** Debes usar el nombre específico del organismo según el estado consultado:
      - **Puebla:** Utiliza siempre **IRCEP** (Instituto Registral y Catastral del Estado de Puebla).
      - **Quintana Roo:** Utiliza siempre **RPP** (Registro Público de la Propiedad).
   ✓ **Consultas Generales:** Si el usuario no especifica un estado, utiliza el término genérico **"Registro Público de la Propiedad"**.
   ✓ **Comparativas y Multi-estado:** Si la respuesta abarca ambos estados, debes distinguir claramente las diferencias: "En el IRCEP (Puebla) el proceso es X, mientras que en el RPP (Quintana Roo) es Y".
   ✓ **CORRECCIÓN AMABLE:** Si el usuario utiliza las siglas "ICERP", corrígelo de manera cordial indicando que las siglas correctas son **IRCEP**.
   ✓ **TERMINOLOGÍA OBLIGATORIA:** Queda prohibido el uso de la palabra "arancel". Debes referirte a los costos de los trámites siempre como **"DERECHO"** o **"DERECHOS"**.

**3. EXTRAE INFORMACIÓN ESPECÍFICA**
   ✓ Cuando el usuario pregunta sobre directorios (notarios, oficinas), lista TODOS los elementos específicos encontrados en el contexto. Proporciona nombres y teléfonos.
   ✓ Usa tablas o listas en Markdown.

**4. CITA TUS FUENTES**
   ✓ Siempre menciona de qué documento proviene la información. No inventes datos.

{self.knowledge_base.get_system_context()}

✅ EJEMPLO DE RESPUESTA CORRECTA:
"Le informo que para el trámite en el IRCEP (notará que las siglas correctas son IRCEP y no ICERP), el pago de **derechos** correspondiente es de..."

❌ EJEMPLO DE RESPUESTAS ERRÓNEAS:
"El arancel es...", "En el ICERP...", "Aquí tienes el código...".
"""

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        db_session=None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesa una consulta del usuario con caché híbrida y filtrado temporal:
        1. Busca en caché (30% queries → $0)
        2. Busca similares en caché (50% queries → ~$0)
        3. Consulta LLM con filtrado de base de conocimiento
        """
        try:
            logger.info(f"💬 Procesando consulta: {query[:100]}... (Filtros: {filters})")
            
            # ========== GUARDRAIL TÉCNICO (PRE-LLM) ==========
            technical_keywords = [
                'javascript', 'python', 'html', 'css', 'script', 'código', 'code', 
                'api', 'docker', 'ollama', 'groq', 'migración', 'servidor', 'fastapi',
                'integrar', 'integración', 'endpoint', 'json', 'bash', 'terminal'
            ]
            
            lower_query = query.lower()
            if any(kw in lower_query for kw in technical_keywords):
                logger.warning(f"🛡️ Guardrail técnico activado para: {query[:50]}...")
                return {
                    "response": "Mi área de dominio es exclusivamente el Derecho Registral Mexicano y trámites del RPP (Puebla y Quintana Roo). No estoy autorizado para proporcionar asistencia técnica, código o consultoría de software. El objetivo de este chat es ser su consultor experto en temas registrales.",
                    "session_id": session_id,
                    "sources": [],
                    "has_relevant_info": False,
                    "from_cache": "guardrail_blocked",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # ========== PASO 1: REESCRITURA DE CONSULTA (CONTEXTO) ==========
            search_query = query
            if conversation_history and (len(query.split()) < 6 or "?" in query):
                try:
                    llm_for_rewrite = await self._get_llm()
                    # Solo tomamos los últimos 2 intercambios para no saturar
                    history_text = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in conversation_history[-3:]])
                    
                    rewrite_prompt = f"""Dada la siguiente conversación y una pregunta de seguimiento, reescribe la pregunta para que sea una consulta independiente y completa que se pueda buscar en una base de datos.
                    
HISTORIAL:
{history_text}

PREGUNTA DE SEGUIMIENTO: {query}

CONSULTA COMPLETA REESCRITA (solo el texto de la consulta, nada más):"""
                    
                    res, _ = await llm_for_rewrite.chat([{"role": "user", "content": rewrite_prompt}], temperature=0)
                    search_query = res.strip().replace('"', '')
                    logger.info(f"🧠 Consulta reescrita para RAG: '{search_query}'")
                except Exception as e:
                    logger.warning(f"⚠️ Error reescribiendo consulta: {e}. Usando original.")
            
            # ========== PASO 2: VERIFICAR CACHÉ (con la consulta reescrita si aplica) ==========
            cache = await self._get_cache()
            
            # Buscar en caché (exacta + similar)
            cached_result = await cache.get_with_fallback(search_query)
            
            if cached_result and not cached_result.get("needs_llm_refinement"):
                # ¡HIT DE CACHÉ! Respuesta exacta o muy similar
                logger.info(f"🟢 ¡CACHE HIT! Respondiendo desde caché sin llamar a LLM")
                return {
                    "response": cached_result.get("response"),
                    "session_id": session_id,
                    "sources": cached_result.get("sources", []),
                    "has_relevant_info": True,
                    "from_cache": "exact_or_similar",
                    "cached_similarity_score": cached_result.get("similarity_score"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_length": len(query),
                    "response_length": len(cached_result.get("response", ""))
                }
            
            # ========== PASO 3: SEARCH RAG + LLM (usando search_query) ==========
            logger.info(f"🔍 Buscando información para: '{search_query}'")
            
            # Buscar información relevante en la base de conocimiento (RAG con pgvector)
            relevant_docs = await self.knowledge_base.search_in_knowledge_async(
                search_query, 
                session=db_session, 
                top_k=3,
                filters=filters
            )
            
            # Preparar contexto adicional solo si hay documentos relevantes
            context_injection = ""
            if relevant_docs:
                context_injection = "\n\n---\n## INFORMACIÓN RELEVANTE DE LA BASE DE CONOCIMIENTO:\n\n"
                for doc in relevant_docs:
                    context_injection += f"**Fuente: {doc.get('source', 'Desconocida')}** ({doc.get('category', 'Categoría desconocida')})\n"
                    # Aumentar a 2000 caracteres para tener más contexto disponible
                    content = doc.get('content', '')
                    context_injection += f"{content[:2000]}" + ("...\n\n" if len(content) > 2000 else "\n\n")
            
            # Preparar mensajes para el LLM
            messages = []
            
            # Añadir historial si existe
            if conversation_history:
                for msg in conversation_history[-5:]: # Últimos 5 mensajes para contexto
                    messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
            
            # Añadir consulta actual con contexto inyectado
            user_message = query
            if context_injection:
                user_message += context_injection
            
            # Si es un refinamiento desde caché, incluir respuesta anterior
            if cached_result and cached_result.get("needs_llm_refinement"):
                user_message = f"""Aquí hay una respuesta similar de nuestro caché que puedes usar como punto de partida:
                
{cached_result.get('response')}

---

Ahora, refina o responde esta consulta más específica:
{user_message}"""
            
            messages.append({"role": "user", "content": user_message})
            
            # Llamar al LLM
            llm = await self._get_llm()
            response, provider_name = await llm.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                system=self.system_prompt
            )
            
            # ========== PASO 3: GUARDAR EN CACHÉ ==========
            sources = [doc.get("source", "Base de Conocimiento") for doc in relevant_docs]
            await cache.store_response(query, response, sources)
            
            # Retornar respuesta estructurada
            return {
                "response": response,
                "provider": provider_name,
                "session_id": session_id,
                "sources": sources,
                "has_relevant_info": bool(relevant_docs),
                "from_cache": "llm_processed",
                "cached": "newly_stored",
                "timestamp": datetime.utcnow().isoformat(),
                "query_length": len(query),
                "response_length": len(response)
            }
        
        except Exception as e:
            logger.error(f"Error procesando consulta: {e}")
            return {
                "response": f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}",
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

_chat_service = None

async def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
