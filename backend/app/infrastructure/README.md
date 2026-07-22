# Módulo: Infrastructure (Persistencia, RAG, Proveedores Externos)

**Propósito:** Modelos ORM (`models.py`), motor de búsqueda RAG (`knowledge_base.py`), enrutador multiproveedor de LLM (`external/smart_llm_router.py`, `external/llm_service.py`), caché híbrida (`cache_layer.py`).
**Dependencias Clave:** SQLAlchemy Async, `pgvector`, `groq`, `google-genai`, `openai` (compatible con NVIDIA NIM).

---

## Bitácora de Cambios Significativos (Changelog Local)

_Formato:_ `- **[YYYY-MM-DD]** ([Nombre del desarrollador]): [Descripción breve del cambio estructural]`

- **[2026-07-22 tarde]** (Google Antigravity): `models.py` agregó `ChatMessageModel.feedback_rating/feedback_text`, `ChatbotProfileModel.llm_provider/llm_model/custom_api_key`, y la tabla `PromptTestCaseModel` (`prompt_test_cases`) para la batería de regresión de prompts por tema.
- **[2026-07-22 tarde]** (Google Antigravity): `knowledge_base.py` implementó retrieval híbrido — búsqueda léxica (`to_tsvector`/`ts_rank` en español, fallback `ILIKE`) en paralelo con la búsqueda vectorial (`pgvector`, distancia coseno), fusionando y deduplicando resultados. Todas las consultas usan SQL parametrizado (`sqlalchemy.text` con bind params), sin riesgo de inyección.
- **[2026-07-22 tarde]** (Claude, revisión): **bug de integración que dejaba 100% no-funcional el LLM personalizado por tema** — `chat_service.py` invocaba `SmartLLMRouter(custom_provider=..., custom_api_key=..., custom_model=...)`, pero el constructor de `SmartLLMRouter` no aceptaba esos parámetros (`TypeError` silenciosamente absorbido por el `try/except` de fallback en cada intento). Se implementó soporte real en `smart_llm_router.py` para `groq`/`gemini`/`nvidia`/`openai` (este último vía un adaptador mínimo compatible con la API de OpenAI, reutilizando el patrón ya usado por `NvidiaNimProvider`); `vertex`/`ollama` no aceptan una API key simple y lanzan `ValueError` explícito, capturado por el mismo fallback. Verificado [Cierto] construyendo cada variante dentro del contenedor real.
- **[2026-07-22 tarde]** (Claude, revisión): `custom_api_key` se guardaba y usaba en texto plano — ver README de `app/core/` (`crypto.py`). `chat_service.py` ahora descifra el valor justo antes de pasarlo al proveedor personalizado.
- **[2026-07-22 noche]** (Claude, práctica CMMI CM tras incidente real): nueva tabla/modelo `ChatbotProfileAuditLogModel` (`chatbot_profile_audit_log`) — bitácora de cambios de `chatbot_profiles` con snapshot antes/después (sin `custom_api_key`), quién y cuándo. Se agregó porque `chatbot_profiles` no tenía ningún historial cuando un tema se corrompió por error humano — ver `docs/BITACORA_ANALISIS_CAUSAL.md`. Conectada desde `admin.py` (ver README de `app/routes/`).
