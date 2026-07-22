# Módulo: Rutas API (FastAPI Routers)

**Propósito:** Endpoints REST de ConsultaSmart — admin (`admin.py`), documentos RAG (`documents.py`), chat (`chat.py`), búsqueda (`search.py`), autenticación (`auth.py`), salud (`health.py`).
**Dependencias Clave:** `app.core.auth_utils` (autenticación/autorización), `app.core.rate_limit`, `app.infrastructure.models`, `app.infrastructure.repositories.*`.

---

## Bitácora de Cambios Significativos (Changelog Local)

_Formato:_ `- **[YYYY-MM-DD]** ([Nombre del desarrollador]): [Descripción breve del cambio estructural]`

- **[2026-07-22]** (Claude / auditoría de seguridad): Se cerró un hallazgo crítico — 7 endpoints de `admin.py` (`GET/POST /admin/configs*`, `POST /admin/generate-prompt`, `POST /admin/chatbot/profiles`, `GET /admin/chatbot/documents`, `POST /admin/chatbot/documents/upload`, `POST /admin/chatbot/documents/{id}/toggle`, `POST /admin/chatbot/documents/{id}/category`) no requerían autenticación alguna, permitiendo a cualquiera crear/editar perfiles de chatbot y documentos RAG. Se agregó la dependencia centralizada `require_admin` (en `app.core.auth_utils`) a todos ellos, reemplazando los chequeos inline duplicados `"admin" not in current_user.get("roles", [])` que existían en `admin.py` y `documents.py`.
- **[2026-07-22]** (Claude / auditoría de seguridad): `GET /admin/chatbot/profiles` se mantiene público (lo consumen `ChatInterface.jsx` y `WidgetIntegrationPage.jsx` para el widget embebible sin login), pero ahora usa `response_model=List[ChatbotProfilePublicDTO]` para dejar de filtrar `system_prompt`, `forbidden_topics`, `rejection_message` y guardrails a cualquier visitante anónimo.
- **[2026-07-22]** (Claude / auditoría de seguridad): `documents.py::list_documents` dejó de mostrar TODOS los documentos del sistema como "fallback" a un usuario no-admin sin documentos propios (fuga de datos entre usuarios); ahora devuelve lista vacía en ese caso.
- **[2026-07-22]** (Claude / auditoría de seguridad): se agregó rate limiting (`app.core.rate_limit`, ver README de `app/core/`) a `POST /admin/generate-prompt`, `POST /admin/chatbot/documents/upload`, `POST /documents/upload` y `POST /chat/query` — antes no tenían ningún límite pese a invocar LLM/procesamiento costoso.
- **[2026-07-22]** (Claude / auditoría de seguridad): se agregó `GET /auth/me`, que devuelve la identidad/rol real del usuario autenticado (reemplazo legítimo del backdoor de rol por substring eliminado en `auth_utils.py`).
- **[2026-07-22]** (Claude / auditoría de seguridad): credenciales del widget (`auth.py::guest_login`) migradas de literales hardcodeados a `settings.WIDGET_EMAIL`/`settings.WIDGET_PASSWORD` (ver README de `app/core/`).
- **[2026-07-22]** (Claude / auditoría de seguridad): `admin.py::upload_chatbot_document` usaba `user_id="admin"` (literal, viola la FK real `documents.user_id → users.id`) porque el endpoint no tenía usuario autenticado disponible; ahora usa `current_user["id"]`.
- **[2026-07-22 tarde]** (Google Antigravity + Claude, revisión): se agregaron `GET /admin/chatbot/profiles/admin-list`, `POST /admin/chatbot/documents/{id}/reindex`, CRUD de `/admin/chatbot/profiles/{id}/test-cases` + `run-regression`, y `GET /admin/stats/llm-router` — todos protegidos con `require_admin` desde el primer commit (sin regresión del hallazgo AUTH-02). Verificado [Cierto] contra el contenedor real en ejecución.
- **[2026-07-22 tarde]** (Claude, revisión): corregido un BOLA real en `POST /chat/messages/{id}/feedback` — resolvía el mensaje solo por ID sin verificar que la sesión perteneciera al usuario autenticado; ahora hace `JOIN` con `ChatSessionModel.user_id` y valida `rating ∈ {'up','down'}` y que el mensaje sea de rol `assistant`.
- **[2026-07-22 tarde]** (Claude, revisión): corregidos ejemplos de payload incorrectos en la documentación in-app (`DocumentationPage.jsx`): `ChatQueryDTO` usa `message` (no `query`) y no tiene campo `documents`; `FeedbackRequest` usa `comment` (no `text`).
