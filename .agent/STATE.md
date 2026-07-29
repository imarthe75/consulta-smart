# Estado del Proyecto - Consulta-Smart (RPP/IRCEP)

## 📅 Última actualización: 29 de Julio, 2026 (sesión Claude Code)

## 🎯 Hitos históricos
1.  **Restauración Completa**: Recuperación de manuales técnicos tras borrado accidental.
2.  **Arquitectura Híbrida**: Integración de `HeuristicsEngine` y `GroundingVerifier`.
3.  **KB Sincronizada**: 19 documentos oficiales indexados con precisión regional.
4.  **Refactor Asíncrono** ✅: Migración de rutas administrativas (`admin.py`) a `AsyncSession`.
5.  **Normalización de Infraestructura** ✅: Exposición bajo `consulta.casmart.internal` con Swagger en `/api/docs`.
6.  **CMMI Mandate (2026-07-22)**: el portafolio completo (incluido este proyecto) debe cumplir CMMI desde esta fecha. Ver `ChatbotProfileAuditLogModel` (bitácora de cambios de perfiles) como primera práctica CM añadida a raíz del incidente de ese mismo día (ver Lecciones Aprendidas).

## 🛠️ Sesión 2026-07-29 — Guardrails RPP/IRCEP, fuga de contenido RPP a perfiles genéricos, y motor LLM

### Contexto de negocio
El admin (Israel) reportó tres problemas al revisar el panel `/admin` → tema "Chatbots y Temas":
1. El perfil **'general'** devolvía el system_prompt del consultor RPP/IRCEP en vez de uno genérico.
2. La sección "Tópicos Prohibidos" (guardrail duro) vivía visualmente lejos del System Prompt, y no era claro si el generador de prompts (botón "Generar") los tomaba en cuenta.
3. La configuración del motor LLM por tema tenía huecos: sin endpoint para Ollama, proveedores listados en el selector (Anthropic/Mistral/Ollama) que en realidad no estaban implementados, y una lista de modelos sugeridos (datalist) desactualizada (ej. NVIDIA NIM apuntaba a `llama-3.1-70b-instruct` mientras el propio default global en `config.py` ya usaba `3.3`).

### Causa raíz encontrada
`chat_service.py::process_query` tenía un fallback **incondicional**: si un perfil no traía `system_prompt` propio en BD, se le inyectaba el texto completo del consultor RPP/IRCEP (con "Notario", "Registro Público", TEMAS PROHIBIDOS de RPP, etc.), sin importar el `profile_id`. El perfil `general` no tenía `system_prompt` propio → heredó ese texto → además, como el texto contenía las palabras "rpp"/"registro público", la bandera `is_custom` se evaluaba en `False`, activando por error las heurísticas y el query-rewriter específicos de RPP también para el chatbot genérico. El mismo patrón de fuga RPP→genérico existía en el default de `rejection_message` (columna ORM y DTO de `admin.py`).

### Cambios de código
- **`chat_service.py`**: el fallback de `system_prompt` ahora es genérico (7 puntos: prioridad RAG, temas válidos, temas prohibidos, no conocimiento ajeno, tono, respuesta de rechazo, formato) sin vocabulario de RPP/IRCEP. Esos temas ya tienen su propio `system_prompt` real en BD (perfiles `rpp` e `ircep`), así que el fallback genérico no les afecta.
- **`models.py`**: default de `forbidden_topics` y `rejection_message` (columna ORM) ya no mencionan RPP/Registro Público; `forbidden_topics` default ahora incluye también los temas legales/académicos que antes solo vivían en el texto del prompt de RPP (demandas legales, cultura general, tesis académicas, redacción de documentos legales, asesoría jurídica personal).
- **`admin.py`**: mismo fix en los defaults del `ChatbotProfileDTO` (Pydantic) — se usan cuando se crea un tema nuevo sin mandar esos campos explícitamente (el modal "Nuevo Tema" del frontend no incluye `forbidden_topics`).
- **`admin.py::generate_prompt`**: ahora recibe `forbidden_topics` y `rejection_message` del frontend y exige al LLM que reproduzca, numerados, los mismos 7 puntos del patrón validado en producción — antes el generador inventaba genéricamente sin ver lo que el admin ya había configurado en Guardrails.
- **`AdminPage.jsx`**: la tarjeta de Guardrails (Tópicos Prohibidos, Mensaje de Rechazo, estrictez RAG, temperatura) se movió de "casi al final" del formulario a justo debajo del textarea del System Prompt, con nota explicando que ambos mecanismos (filtro local + instrucción del prompt) deben coincidir.
- **Motor LLM (`llm_service.py`, `smart_llm_router.py`, `config.py`, `models.py`, `database.py`, `admin.py`, `AdminPage.jsx`)**:
  - Se implementaron `OllamaProvider`, `MistralProvider`, `AnthropicProvider` (antes solo existían en el selector del frontend, sin backend real — al elegirlos, el override por tema fallaba silenciosamente y caía al router global).
  - Se corrigió un bug real: `GroqProvider`, `NvidiaNimProvider` y `_OpenAICompatibleProvider` (override 'openai') recibían el `system` prompt por `**kwargs` pero nunca lo usaban — cualquier tema configurado con esos motores perdía TODOS sus guardrails/TEMAS PROHIBIDOS en producción. Corregido con el helper `_with_system()`.
  - Nueva columna `chatbot_profiles.custom_base_url` (aplicada en vivo con `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, y agregada a `_SCHEMA_PATCHES` en `database.py` para entornos futuros) — requerida para Ollama (endpoint del servidor), opcional para gateways propios de OpenAI/NVIDIA/Mistral.
  - Nuevo endpoint `POST /api/v1/admin/llm/list-models`: en vez de mantener una lista estática de modelos (que se desactualiza en cada release de cada proveedor), consulta el catálogo real vía la API de cada proveedor (Groq/OpenAI/Mistral/NVIDIA: `client.models.list()`; Anthropic: `client.models.list()`; Gemini: REST `v1beta/models`; Ollama: `GET /api/tags`). El frontend tiene un botón "Cargar modelos disponibles" que llena el datalist en vivo.
  - Se quitó 'vertex' del selector de override por tema (no acepta API key simple, requiere credenciales de proyecto GCP — solo aplica como motor global vía `GCP_PROJECT_ID`).

### Corrección directa en base de datos (con autorización explícita del admin)
El perfil `general` en la BD viva (`10.4.3.208/consultarpp_db`) tenía el `system_prompt`/`rejection_message` corruptos con contenido de RPP desde 2026-07-22 20:43:42 (mismo incidente que motivó la tabla de auditoría, pero ANTES de que esa tabla existiera — no había snapshot `before` que restaurar). Se corrigió directamente vía `UPDATE` a un prompt genérico consistente con el nuevo fallback de `chat_service.py`. No se fabricó una entrada de auditoría falsa (el changed_by_email de una entrada real debe corresponder a un usuario autenticado real); este archivo documenta el cambio en su lugar.

### 🚨 Lecciones Aprendidas
- *Un fallback hardcodeado de un dominio específico (RPP) nunca debe vivir en el código de aplicación como "valor por defecto universal" — cualquier tema mal configurado hereda ese dominio sin darse cuenta. Los valores de fábrica de un tema deben ser genéricos o no existir (forzar configuración explícita).*
- *Cuando un texto de system_prompt contiene palabras del dominio original (ej. "rpp", "registro público"), puede activar por error heurísticas condicionadas a esas palabras (`is_custom` en `chat_service.py`) en un tema que no debería tenerlas.*
- *Un selector de UI con opciones (proveedores LLM) no es evidencia de que el backend las soporte — 'anthropic'/'mistral'/'ollama' llevaban tiempo en el dropdown sin provider real; el error se tragaba silenciosamente (fallback al router global) en vez de fallar visiblemente.*
- *Los kwargs que "se aceptan pero no se usan" (`**kwargs` con `system` nunca leído) son bugs silenciosos particularmente peligrosos en un sistema de guardrails: no hay excepción, solo ausencia de la protección esperada.*
- *Preferir catálogos de modelos consultados en vivo sobre listas estáticas hardcodeadas — un provider externo puede deprecar/renombrar modelos en cualquier momento sin avisar a este repo.*
- *Antes de corregir datos corruptos directamente en una BD compartida/productiva, buscar primero el mecanismo propio de la app para revertir (audit log / restore); solo hacer `UPDATE` manual cuando ese mecanismo no tiene los datos necesarios, y documentar el cambio fuera de la tabla de auditoría si no hay un usuario real al que atribuirlo.*

## 🛠️ Sesión 2026-07-29 (continuación) — Auditoría técnica integral (SKILL_AUDITORIA / ESTANDARES_AUDITORIA)

Auditoría de 6 capas (BD, Backend API, Frontend, Seguridad, Infra/DevOps, Testing) siguiendo la metodología provista por el usuario. Detalle completo en `MANUAL_TECNICO_DESARROLLADOR.md` §16. Resumen:

**Corregido (Alta/Media):**
- Proxy `casmarts-core-proxy` (`nginx/conf.d/chat.casmart.internal.conf`) no enviaba ninguna cabecera de seguridad HTTP. Se agregaron HSTS/`X-Content-Type-Options`/`Referrer-Policy` a nivel global del vhost, y `X-Frame-Options: SAMEORIGIN` + CSP `frame-ancestors 'self'` solo en `location /admin` (el resto del sitio debe permitir framing a propósito — es como funciona el widget embebible).
- `gzip on;` global sin `gzip_types` → nginx solo comprimía `text/html` por default; el JSON de la API y los bundles JS/CSS viajaban sin comprimir. Se agregó `gzip_types` al vhost.
- 8 endpoints en `chat.py`/`search.py` devolvían `detail=str(e)` al cliente (fuga de mensajes de excepción interna) pese a ya loguear el detalle real server-side. Reemplazados por mensajes genéricos.
- Reload de nginx (`nginx -s reload`, sin downtime) y restart de `consulta-smart-backend`; ambos verificados en vivo (`curl -I` confirma cabeceras y `Content-Encoding: gzip`).

**Documentado y diferido en el momento — cerrado horas después en la pasada de seguimiento (ver bloque de sesión siguiente y manual §16.6):** ingesta sin batch, sin concurrencia optimista, cobertura de tests en cero, conflicto de peer-deps de `lucide-react`. Solo **TLS deshabilitado hacia Authentik (`CERT_NONE`) sigue diferido** — bloqueado por no tener acceso al certificado de CA real (vive en `casmarts-idp-*`, fuera de este repo).

**Revisado sin hallazgo (ver manual §16.4):** CORS wildcard (mitigado por diseño), SQL con f-strings en `knowledge_base.py` (parametrizado correctamente, no vulnerable), autorización en los 19 endpoints mutantes de `admin.py` (100% cubiertos por `require_admin`), IDOR en sesiones de chat (ya corregido en ronda previa, sin regresión), rate limiting en endpoints costosos, imágenes sin lazy-load (son logos above-the-fold, correcto no aplicarlo), `setTimeout` sin cleanup (timers de un solo disparo, sin `setInterval` en todo el frontend), bcrypt/JWT, cifrado de `custom_api_key`.

### 🚨 Lecciones Aprendidas (auditoría)
- *Un vhost de nginx puede tener `gzip on;` heredado del contexto `http {}` global y aun así no comprimir nada real, si `gzip_types` no incluye los content-types que la app efectivamente sirve (`application/json` sobre todo). Verificar con `curl -H "Accept-Encoding: gzip" -D -`, no solo revisar que la directiva `gzip on` exista.*
- *No aplicar cabeceras de seguridad "a ciegas" en todo el sitio: `X-Frame-Options`/CSP `frame-ancestors` a nivel global habría roto el widget embebible (una feature intencional). Hay que identificar qué rutas SÍ deben poder embeberse antes de endurecer.*
- *Loguear el detalle real de una excepción server-side y ADEMÁS devolverlo al cliente en el `detail` de la respuesta son dos cosas independientes — hacer la primera no obliga a hacer la segunda, y solo la primera es necesaria para debugging.*
- *Cuando un hallazgo de una ronda anterior ya está bien triado y documentado (con razón explícita de por qué se difirió), no hace falta re-investigarlo desde cero — solo verificar que la condición que justificó diferirlo siga vigente (en este caso, confirmar que `AUTHENTIK_INTERNAL_URL` real seguía siendo `https://`).*

## 🛠️ Sesión 2026-07-29 (pasada de seguimiento) — Cierre de los hallazgos diferidos + hallazgos nuevos encontrados de paso

El usuario pidió aplicar las correcciones documentadas como diferidas en la auditoría anterior. Detalle completo en `MANUAL_TECNICO_DESARROLLADOR.md` §16.6.

**Cerrado:**
- **PERF-INGEST-001:** embeddings en lote (`embed_batch()`, ya existía sin usarse) en los 4 puntos reales de ingesta. De paso se corrigieron 2 bugs no buscados: `auto_ingest_service.py`/`routes/documents.py` usaban `get_llm_provider()` en vez de `get_local_embedding_service()` para embeddings (funcionaba por casualidad porque todos los providers de chat delegan `.embed()` al mismo servicio local, pero ninguno tiene `embed_batch()`); y la ruta de Celery (`document_usecases.py::ProcessDocumentUseCase`, workers detenidos hace 4 días) llamaba `llm_service.create_embedding(...)` (no existe) y `vector_store.add(text=...)` (el kwarg real es `text_content`) — corregida sin reiniciar los workers detenidos (decisión operativa fuera de alcance de un fix de código).
- **DB-RACE-001:** columna `chatbot_profiles.version`, chequeo optimista en `save_chatbot_profile` (409 si no coincide), incrementado en cada guardado, expuesto en `admin-list`/snapshot/respuesta. `AdminPage.jsx` la carga, reenvía y actualiza tras guardar.
- **TEST-001:** se descubrió que `frontend/tests/` ya tenía una suite completa (7 archivos, MSW, README con "100+ tests") que **nunca había podido correr** por dependencias faltantes — no había 0% de intención de testear, había 0% de suite funcional. Se instalaron las dependencias y se conectó `vite.config.js`. Al correr por primera vez se encontró que `Stores.test.js` (539 líneas) redefinía cada store con `vi.fn(() => ({...}))` en vez de importar el código real — pasaba sin probar nada. Se reescribió con imports reales, incluida una prueba de regresión para el backdoor de escalación de privilegios ya eliminado en `authStore.js`. Estado: 63 pruebas corren, 34 pasan genuinamente; 29 fallan por handlers de MSW faltantes en `tests/setup.ts` (pendiente, ver abajo).
- **DEP-001 (parcial):** `lucide-react` actualizado a `^1.27.0` (soporta React 19), desbloqueando el conflicto de peer-deps que impedía correr `npm audit fix`; ese fix resolvió el CVE alto de `postcss`.

**Hallazgo nuevo, no buscado, documentado sin corregir — VITE-DEV-001 [Media]:** el contenedor `consulta-smart-frontend` corre `vite dev` (`Dockerfile: CMD npm run dev -- --host`) en lo que se presenta como producción, no una build real. Esto es lo que vuelve directamente relevante el CVE de esbuild (dev server acepta requests de cualquier origen). Convertirlo a `vite build` + estático es un cambio de infraestructura de despliegue con riesgo real (routing SPA, inyección de env vars) — no se aplicó sin confirmación explícita del usuario.

**Sigue sin corregir (genuinamente bloqueado, sin cambios desde la ronda anterior):** SEC-TLS-001 (certificado de CA fuera de este repo). **Sigue sin forzar (requiere QA manual, cambio de versión mayor):** `react-router-dom` 6→7, `vite`/`esbuild` 5→8.

### 🚨 Lecciones Aprendidas (pasada de seguimiento)
- *Buscar tests solo en `src/**` no es suficiente en un proyecto que ya tiene convención de `tests/` como directorio raíz separado — un `find` con el patrón equivocado puede reportar "0% cobertura" cuando en realidad hay una suite completa esperando sus dependencias.*
- *Una suite de tests que "pasa" no es evidencia de que prueba algo real — si un test redefine el módulo bajo prueba como un mock completo (`vi.fn(() => ({...forma falsa...}))`), las aserciones pueden pasar sin ejecutar una sola línea del código real. Vale la pena revisar si el import es del módulo real o de una redefinición local antes de confiar en el conteo de "tests pasando".*
- *Un bug puede estar dormido durante meses (o para siempre) si el proceso que lo activa está detenido (`docker ps -a`: `Exited`) — no lo vuelve inofensivo, solo invisible. Vale la pena corregirlo igual si el fix es barato, sin necesariamente reactivar el proceso detenido (esa es una decisión operativa aparte).*
- *Antes de forzar un `npm install <pkg>@latest` para resolver un conflicto de peer-deps, verificar que la nueva versión declare soporte explícito para la versión de React ya instalada (`npm view <pkg>@latest peerDependencies`) — evita otra ronda de conflictos.*

## 🚧 Pendientes
- Verificar en runtime real (login admin) el endpoint `/admin/llm/list-models` contra Groq/OpenAI/Gemini con API keys reales (solo se validó a nivel de código/ruta registrada, no end-to-end con credenciales).
- Configurar y probar un servidor Ollama real (endpoint) para validar `OllamaProvider` de punta a punta.
- Agregar los handlers de MSW faltantes en `frontend/tests/setup.ts` (`/auth/register`, `/auth/refresh`, `/documents/{id}` GET/DELETE, `/chat/sessions/{id}/messages`, variantes de `/search`) y usar `mswServer.use(...)` por test para los 2 casos que necesitan simular error en `/auth/login`; investigar la consulta de DOM que falla en `SearchResults.test.jsx`.
- Decidir si convertir el contenedor de frontend a `vite build` + servido estático (VITE-DEV-001) — requiere confirmación explícita antes de tocar el Dockerfile/despliegue.
- Evaluar el bump mayor de `react-router-dom` (6→7) y `vite`/`esbuild` (5→8) en un ciclo de desarrollo con QA manual completo.
- Investigar por qué los workers de Celery (`consulta-smart-celery-worker`/`-beat`) llevan 4 días detenidos, y decidir si reactivarlos ahora que `document_usecases.py` ya no está roto.
- Obtener el certificado de CA real de `auth.casmart.internal` para remover el bypass `ssl.CERT_NONE` en `auth_utils.py` (depende de `casmarts-idp-*`, fuera de este repo).
- Ampliar cobertura de trámites para municipios menores.
- Optimizar el tiempo de respuesta de los embeddings en búsquedas complejas.
- Integrar feedback de usuarios sobre la precisión del blindaje.
