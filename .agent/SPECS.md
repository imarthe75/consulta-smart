# 📜 System Specifications (SPECS.md)

Este archivo actúa como la capa persistente de especificaciones de OpenSpec. Todo desarrollo, modificación o característica debe estar respaldada por un contrato definido en este documento antes de escribir código.

---

## 📋 Especificaciones Activas

### [EJEMPLO-001] Integración de Memoria Dual (Valkey + Postgres)
- **Estado:** `APROBADO`
- **Requisitos:**
  - El backend debe conectarse a Valkey en el puerto `6379` para almacenamiento de caché semántica a corto plazo.
  - El backend debe conectarse a PostgreSQL para persistencia de largo plazo utilizando `pgvector`.
- **Restricciones:**
  - Las llaves primarias de las tablas deben ser de tipo `uuid` (UUIDv7 preferido).
- **Criterios de Aceptación:**
  - Tiempo de respuesta de caché menor a 10ms.
- **Casos de Borde:**
  - Degradación elegante si Valkey o Postgres no están disponibles.

### [CS-002] Fallback genérico de System Prompt por perfil (sin fuga de dominio RPP)
- **Estado:** `IMPLEMENTADO` (2026-07-29)
- **Requisitos:**
  - Si un `ChatbotProfile` no tiene `system_prompt` propio en BD, el fallback de `chat_service.py` debe ser genérico y no mencionar RPP/IRCEP/Notario ni ningún otro dominio específico de un tenant particular.
  - El fallback debe conservar los 7 puntos del patrón validado (prioridad RAG, temas válidos, temas prohibidos, no conocimiento ajeno, tono, respuesta de rechazo, formato).
  - Los defaults de `forbidden_topics`/`rejection_message` (columna ORM en `models.py` y DTO en `admin.py`) tampoco deben mencionar RPP/Registro Público.
- **Restricciones:**
  - Los perfiles `rpp` e `ircep` mantienen su propio `system_prompt` real en BD; este fallback nunca debe pisarlos (solo aplica cuando el campo está vacío).
- **Criterios de Aceptación:**
  - Un perfil nuevo sin `system_prompt` configurado no debe activar `is_custom = False` por contener "rpp"/"registro público" heredado del fallback.
- **Casos de Borde:**
  - Perfil `general`: es de solo lectura para `POST /chatbot/profiles` (no se puede corregir vía UI); su corrección de datos corruptos requiere `UPDATE` directo en BD, documentado en `STATE.md` en vez de en la tabla de auditoría (no hay usuario real al que atribuirlo).

### [CS-003] Motor LLM por tema: proveedores completos y catálogo de modelos en vivo
- **Estado:** `IMPLEMENTADO` (2026-07-29)
- **Requisitos:**
  - Todo proveedor listado en el selector del frontend (`AdminPage.jsx`) debe tener una implementación real en `llm_service.py`/`smart_llm_router.py` (groq, openai, anthropic, mistral, gemini, nvidia, ollama). 'vertex' se excluye del override por tema por no soportar API key simple.
  - `ollama` requiere `custom_base_url` (endpoint del servidor); `openai`/`nvidia`/`mistral` lo admiten opcionalmente para gateways propios.
  - El `system` prompt debe llegar efectivamente al proveedor en TODOS los casos (bug encontrado: Groq/NVIDIA/OpenAI-compatible lo ignoraban).
  - El listado de modelos sugeridos debe reflejar el catálogo real del proveedor (`POST /admin/llm/list-models`), no una lista estática mantenida a mano.
- **Restricciones:**
  - `custom_api_key` sigue viajando cifrado (`encrypt_secret`/`decrypt_secret`); `custom_base_url` no es secreto, se guarda en claro.
- **Criterios de Aceptación:**
  - Seleccionar un proveedor sin implementación real debe ser imposible desde la UI (ya no aparece en el `<select>`) en vez de fallar silenciosamente en runtime.
- **Casos de Borde:**
  - Si `POST /admin/llm/list-models` falla (proveedor caído, key inválida), el formulario debe seguir permitiendo escribir el modelo a mano (no bloquea el guardado).

### [CS-004] Cabeceras de seguridad HTTP y compresión en el borde público
- **Estado:** `IMPLEMENTADO` (2026-07-29) — ver `MANUAL_TECNICO_DESARROLLADOR.md` §16.2
- **Requisitos:**
  - El proxy público (`chat.casmart.internal`) debe enviar `Strict-Transport-Security`, `X-Content-Type-Options: nosniff` y `Referrer-Policy` en todas las respuestas.
  - `/admin` debe enviar además `X-Frame-Options: SAMEORIGIN` y CSP `frame-ancestors 'self'`.
  - Las respuestas JSON/JS/CSS deben viajar comprimidas (`gzip_types` explícito, no solo `gzip on`).
- **Restricciones:**
  - NO aplicar `X-Frame-Options`/CSP `frame-ancestors` a `/` ni `/api/` de forma global — rompería el widget embebible en sitios de terceros (feature intencional, misma razón que `CORS_ORIGINS=*` en el backend).
  - El cambio vive en `nginx/conf.d/chat.casmart.internal.conf` (scope: solo este vhost), nunca en el `nginx.conf` global compartido con `idp`/`lexivault`.
- **Criterios de Aceptación:**
  - `curl -I` contra `/`, `/api/` y `/admin` reales confirma las cabeceras esperadas en cada uno.
  - `curl -H "Accept-Encoding: gzip"` contra un endpoint JSON real responde `Content-Encoding: gzip`.
- **Casos de Borde:**
  - Cambios al vhost requieren `nginx -s reload` (no `docker restart`) para no afectar disponibilidad de los otros satélites (`idp.casmart.internal`, `lexivault.casmart.internal`) que comparten el mismo contenedor proxy.

### [CS-005] Mensajes de error genéricos hacia el cliente (sin fuga de detalle interno)
- **Estado:** `IMPLEMENTADO` (2026-07-29)
- **Requisitos:**
  - Ningún endpoint de `chat.py`/`search.py` debe devolver `detail=str(e)` (u otro texto derivado directamente de la excepción) en una respuesta 500 al cliente.
  - El detalle real de la excepción debe seguir registrándose server-side vía `logger.error(...)` para diagnóstico — solo cambia lo que se expone en el body de la respuesta HTTP.
- **Restricciones:**
  - No aplica a bloques `except HTTPException: raise` (esos ya llevan mensajes controlados definidos explícitamente en el propio endpoint).
- **Criterios de Aceptación:**
  - `grep -rn "detail=str(e)" app/routes/` no debe arrojar resultados en `chat.py`/`search.py`.
- **Casos de Borde:**
  - Nuevos endpoints que se agreguen a futuro en cualquier archivo de `app/routes/` deben seguir el mismo patrón (loguear detalle real, responder mensaje genérico) — agregar esta regla a la revisión de PRs.

### [CS-006] Embeddings en lote en toda la ingesta de documentos
- **Estado:** `IMPLEMENTADO` (2026-07-29) — ver `MANUAL_TECNICO_DESARROLLADOR.md` §16.6
- **Requisitos:**
  - Todo punto que genere embeddings para múltiples chunks de un mismo documento debe usar `LocalEmbeddingService.embed_batch()`, nunca un `.embed()` por chunk en un bucle.
  - Debe preservar tolerancia a fallo parcial: si el lote completo falla, los chunks se guardan igual con `embedding=None` (no bloquea la subida/indexado).
  - Todo servicio que solo necesite generar embeddings debe obtenerlo vía `get_local_embedding_service()`, no `get_llm_provider()` (este último no expone `embed_batch()`).
- **Restricciones:**
  - Aplica a los 4 puntos reales: `admin.py::upload_chatbot_document`, `admin.py::reindex_chatbot_document`, `routes/documents.py::load_rpp_registry`, `auto_ingest_service.py`.
- **Criterios de Aceptación:**
  - Subir un documento con N chunks debe invocar el modelo de embeddings 1 vez (lote), no N veces.
- **Casos de Borde:**
  - `app/application/usecases/document_usecases.py` (ruta de Celery, workers detenidos) se corrigió por consistencia pero no se probó end-to-end (no hay worker corriendo para ejercitarla).

### [CS-007] Concurrencia optimista en `chatbot_profiles`
- **Estado:** `IMPLEMENTADO` (2026-07-29)
- **Requisitos:**
  - `ChatbotProfile.version` (INTEGER, default 1) se incrementa en cada `UPDATE` exitoso vía `save_chatbot_profile`.
  - Si el cliente envía `version` y no coincide con la versión actual en BD, el backend responde `409 Conflict` con un mensaje explicando que otro administrador ya guardó cambios, sin aplicar el `UPDATE`.
  - El frontend (`AdminPage.jsx`) carga la versión al seleccionar un tema, la reenvía al guardar, y actualiza su copia local con la versión devuelta tras un guardado exitoso.
- **Restricciones:**
  - `version` es opcional en el DTO (`Optional[int] = None`) — si el cliente no la envía, no se aplica el chequeo (compatibilidad con integraciones que no la conozcan).
  - No aplica a la creación de un tema nuevo (`is_new`), solo a `UPDATE`.
- **Criterios de Aceptación:**
  - Dos guardados concurrentes sobre el mismo tema, con la misma versión de partida: el primero en llegar tiene éxito e incrementa la versión; el segundo recibe 409, no sobreescribe en silencio.
- **Casos de Borde:**
  - El tema `general` nunca llega a este chequeo (bloqueado antes, por ser de solo lectura).

### [CS-008] Suite de pruebas de frontend funcional (`frontend/tests/`)
- **Estado:** `PARCIAL` (2026-07-29) — 63 pruebas corren, 34 pasan; ver `MANUAL_TECNICO_DESARROLLADOR.md` §16.6
- **Requisitos:**
  - `npm test` debe ejecutar la suite de `frontend/tests/` (Vitest + Testing Library + MSW) sin errores de resolución de módulos.
  - Las pruebas de stores (`tests/stores/Stores.test.js`) deben importar y ejercitar el código real de `src/stores/*.js`, nunca redefinir el store completo como un mock.
  - Debe existir al menos una prueba de regresión para el backdoor de escalación de privilegios eliminado en `authStore.js` (verificar que `login()` nunca asigna rol admin por contenido de email/username).
- **Restricciones:**
  - `tests/setup.ts` mockea `localStorage`/`sessionStorage` con `vi.fn()` sin almacenamiento real — las aserciones sobre persistencia deben verificar la llamada (`toHaveBeenCalledWith`), no un `getItem()` posterior.
- **Criterios de Aceptación:**
  - `npm test` corre sin el error `Failed to resolve import "@testing-library/jest-dom"` (dependencias instaladas, `vite.config.js` con `test.setupFiles`).
- **Casos de Borde / pendiente:**
  - 29 pruebas siguen fallando por handlers de MSW faltantes en `tests/setup.ts` para varios endpoints, y 2 aserciones de `API.test.js` que necesitan `mswServer.use(...)` por test para simular errores del handler compartido de `/auth/login` — no se completó esta ronda, ver pendientes en `STATE.md`.

### [CS-009] Resiliencia de arranque ante Postgres externo transitoriamente inalcanzable
- **Estado:** `IMPLEMENTADO` (2026-08-12)
- **Requisitos:**
  - `init_db()` (`app/core/database.py`) debe reintentar la conexión inicial a Postgres (`SELECT 1`) hasta 5 veces con 5s de espera entre intentos antes de abortar el arranque, en vez de fallar en el primer intento.
  - Si tras agotar los reintentos sigue sin conectar, debe seguir fallando ruidosamente (`raise`) — este contrato cubre una ventana de arranque, no un modo "arrancar sin BD".
- **Restricciones:**
  - `uvicorn --reload` (modo dev de este contenedor, ver `CLAUDE.md`) no reinicia el proceso worker cuando `lifespan` falla en el arranque — solo lo hace ante un cambio de archivo. Esto hace inútil `restart: always` de Docker para este caso específico (el proceso reloader, PID 1, no muere). El retry con backoff es la mitigación real; no depender de que Docker reinicie el contenedor solo.
- **Criterios de Aceptación:**
  - Con Postgres inalcanzable durante los primeros ~20s de arranque (p.ej. host recién reiniciado y la ruta de red aún no lista) y disponible después, el backend debe terminar arrancando sin intervención manual.
- **Casos de Borde:**
  - Incidente real que motivó este contrato: reinicio del host el 2026-08-10 dejó `consulta-smart-backend` con `docker ps` en estado "Up" durante 2 días sin servir tráfico (el reloader vivo, el worker muerto tras `OSError: [Errno 113] Connect call failed ('10.4.3.208', 5432)`), causando que el selector de "Tema Activo" y el resto del panel admin aparecieran vacíos sin ningún error 500 visible (nginx devolvía 502 por upstream inalcanzable). Corregido con restart manual + este retry. Ver `STATE.md` sesión 2026-08-12.
