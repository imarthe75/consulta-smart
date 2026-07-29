# ConsultaSmart (RPP/IRCEP) — guía para Claude Code

Backend FastAPI (`backend/`) + Frontend React/Vite (`frontend/`) para un chatbot RAG multitenant.
El tenant original es el Registro Público de la Propiedad / IRCEP (Puebla y Quintana Roo), pero
la plataforma soporta múltiples "temas" (`chatbot_profiles`) independientes — RPP, IRCEP, Catastro,
Control Escolar, Mesa de Ayuda, etc. — cada uno con su propio system_prompt, guardrails y motor LLM.

Memoria agéntica extendida en `.agent/` (`AGENT.md` = reglas, `STATE.md` = bitácora de sesiones,
`SPECS.md` = contratos de features). Lee `STATE.md` al empezar una sesión de trabajo aquí.

## Arranque rápido
- Contenedores: `consulta-smart-backend` (puerto host 8202→8000), `consulta-smart-frontend` (8201→3000, Vite con HMR).
- Backend corre con `uvicorn --reload`: los cambios en `backend/app/**` se recargan solos, no hace falta reiniciar el contenedor salvo que cambies dependencias o quieras forzar un reinicio limpio (`docker restart consulta-smart-backend`).
- Frontend: Vite HMR también recarga solo; revisa `docker logs consulta-smart-frontend` si un cambio en JSX no se refleja.
- Credenciales de BD en `.env` (raíz del repo `consulta-smart/`): Postgres externo en `10.4.3.208:5432`, NO en un contenedor local. Acceso vía `docker exec -e PGPASSWORD=... consulta-smart-backend psql -h 10.4.3.208 ...`.

## Gotchas específicos de este proyecto
- **No hay Alembic real** (está en `requirements.txt` pero nunca se inicializó). `Base.metadata.create_all` solo crea tablas nuevas, nunca les agrega columnas. Toda columna nueva en un modelo ORM que ya exista en producción DEBE agregarse también a `_SCHEMA_PATCHES` en `app/core/database.py` (ADD COLUMN IF NOT EXISTS) — si no, el modelo y la tabla real quedan desincronizados en silencio.
- **El perfil `general` es de solo lectura** en `POST /api/v1/admin/chatbot/profiles` (ver `admin.py::save_chatbot_profile`) — sirve de plantilla base y no se puede sobreescribir desde la UI, solo "Guardar como tema nuevo". Si su contenido queda corrupto, la única vía de arreglo es un `UPDATE` directo en BD (documentar el porqué en `.agent/STATE.md`, no fabricar una entrada falsa en `chatbot_profile_audit_log` — esa tabla asume `changed_by_email` real).
- **Nunca hardcodear contenido de un tenant específico (RPP/IRCEP) como fallback universal.** Ya pasó una vez: el fallback de `system_prompt` en `chat_service.py::process_query` era el texto completo del consultor RPP aplicado a CUALQUIER perfil sin prompt propio, y "fugó" al perfil `general` (incidente 2026-07-22, corregido 2026-07-29 — ver `.agent/STATE.md`). Los fallbacks de `system_prompt`/`forbidden_topics`/`rejection_message` deben ser genéricos.
- **Guardrail dual, deben coincidir:** el `system_prompt` de un tema puede describir "TEMAS PROHIBIDOS" en texto libre (instrucción blanda al LLM), pero el bloqueo duro real ocurre antes de llamar al LLM, comparando la consulta contra `ChatbotProfile.forbidden_topics` (CSV, coincidencia de substring en `chat_service.py`). Si cambias uno, revisa el otro.
- **Motor LLM por tema:** `ChatbotProfile.llm_provider` soporta override por tema para `groq`, `openai`, `anthropic`, `mistral`, `gemini`, `nvidia`, `ollama` (implementados en `llm_service.py` + `smart_llm_router.py::_init_custom_provider`). `vertex` NO admite override por tema (requiere credenciales de proyecto GCP, no una API key) — solo existe como motor global vía `GCP_PROJECT_ID`. `ollama` requiere `custom_base_url`; los demás lo admiten opcional para gateways propios.
- **No mantengas listas estáticas de "modelos disponibles"** en el frontend — se desactualizan cada vez que un proveedor libera/descontinúa un modelo. Usa `POST /api/v1/admin/llm/list-models`, que consulta el catálogo real del proveedor en vivo.
- **Todo provider debe usar el `system` kwarg.** Ya hubo un bug real donde `GroqProvider`/`NvidiaNimProvider`/el adaptador OpenAI-compatible recibían `system` por `**kwargs` y lo ignoraban — el system_prompt (y por tanto TODOS los guardrails) se perdía en runtime sin ningún error visible. Usa el helper `_with_system()` de `llm_service.py` en cualquier provider OpenAI-compatible nuevo.

- **El proxy público vive fuera de este repo:** `nginx/conf.d/chat.casmart.internal.conf` (en la raíz del monorepo `/opt/casmart/nginx/`, montado en el contenedor compartido `casmarts-core-proxy`). Es el único punto que sirve HTTPS/cabeceras de seguridad/gzip hacia afuera — el backend FastAPI no las setea. Editar SOLO el vhost de consulta-smart, nunca `nginx.conf` global (lo comparten `idp.casmart.internal` y `lexivault.casmart.internal`). Aplicar cambios con `docker exec casmarts-core-proxy nginx -s reload` (reload, no restart — evita downtime a los otros satélites). No apliques `X-Frame-Options`/CSP `frame-ancestors` a `/` ni `/api/` — el widget embebible depende de poder framearse en sitios de terceros; esas cabeceras solo van en `location /admin`.
- **Nunca devuelvas `detail=str(e)` en una `HTTPException`.** Loguea el detalle real con `logger.error(...)` (server-side) y responde un mensaje genérico al cliente — patrón ya establecido en todo `app/routes/`.
- **Embeddings siempre en lote.** Usa `get_local_embedding_service().embed_batch(textos)`, nunca `.embed(texto)` en un `for`. `get_llm_provider()` (Groq/Vertex/NVIDIA/Gemini) NO expone `embed_batch()` — si solo necesitas embeddings, usa `get_local_embedding_service()` directamente, no un provider de chat.
- **`chatbot_profiles.version` implementa concurrencia optimista.** `save_chatbot_profile` rechaza con 409 si `data.version` no coincide con la BD. Cualquier UPDATE nuevo sobre este modelo debe incrementar `profile.version`.
- **El pipeline de Celery (`app/workers/celery_app.py` → `document_usecases.py`) está roto y los workers llevan días detenidos** (`docker ps -a` los muestra `Exited`). Se corrigieron bugs de nombres de método/kwarg ahí (2026-07-29) pero nunca se probó end-to-end ni se reactivaron los workers — no asumas que esa ruta funciona sin verificarla primero.
- **El frontend corre `vite dev` en "producción"** (`frontend/Dockerfile`: `CMD npm run dev -- --host`, sin `vite build`). Es una decisión existente, no un error de esta sesión — pero significa que el CVE del dev server de esbuild es real, no teórico. No conviertas esto a una build de producción sin confirmar con el usuario primero (riesgo real de romper routing SPA / inyección de env vars).
- **`frontend/tests/` es el directorio real de pruebas** (no `frontend/src/**/*.test.js`). Antes de asumir "sin cobertura", revisa ahí — ya tiene MSW + Testing Library configurados en `tests/setup.ts`. Si escribes un test de un store Zustand, importa el store real (`import { useXStore } from '../../src/stores/xStore'`) — nunca lo redefinas como `vi.fn(() => ({...}))`, eso prueba el mock, no el código.

## Cumplimiento CMMI
Desde 2026-07-22, todo el portafolio (incluido este proyecto) debe cumplir CMMI. La primera práctica
de Configuration Management añadida fue `ChatbotProfileAuditLogModel` (bitácora antes/después de cada
create/update/delete de `chatbot_profiles`, con endpoint de restore). Antes de invertir esfuerzo grande
en un cambio, aclarar con el usuario el alcance/profundidad CMMI esperado.

## Documentación relacionada
- `MANUAL_TECNICO_DESARROLLADOR.md` — manual técnico para desarrolladores.
- `CA-CS-M-01_Manual_de_usuario_ConsultaSmart_Admin.docx` — manual de usuario del panel admin (formato institucional, ver plantilla `CA-PGO-D-E-06-Manual_de_usuario_Authentik_Login_Manager.docx` en la raíz del monorepo).
