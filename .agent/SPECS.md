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
- **Estado:** `PARCIAL` (2026-08-14) — 9/11 archivos pasan, 83/112 pruebas pasan; ver `MANUAL_TECNICO_DESARROLLADOR.md` §16.6 y §20.9
- **Requisitos:**
  - `npm test` debe ejecutar la suite de `frontend/tests/` (Vitest + Testing Library + MSW) sin errores de resolución de módulos.
  - Las pruebas de stores (`tests/stores/Stores.test.js`) deben importar y ejercitar el código real de `src/stores/*.js`, nunca redefinir el store completo como un mock.
  - Debe existir al menos una prueba de regresión para el backdoor de escalación de privilegios eliminado en `authStore.js` (verificar que `login()` nunca asigna rol admin por contenido de email/username).
  - Toda prueba de un componente debe mockear la forma REAL de sus dependencias (store/API) — nunca inventar una forma "razonable" sin verificar contra el código actual del componente. Ver `[CS-017]`.
- **Restricciones:**
  - `tests/setup.ts` mockea `localStorage`/`sessionStorage` con `vi.fn()` sin almacenamiento real — las aserciones sobre persistencia deben verificar la llamada (`toHaveBeenCalledWith`), no un `getItem()` posterior.
- **Criterios de Aceptación:**
  - `npm test` corre sin el error `Failed to resolve import "@testing-library/jest-dom"` (dependencias instaladas, `vite.config.js` con `test.setupFiles`).
- **Casos de Borde / pendiente:**
  - `API.test.js` (11 pruebas) requiere un servidor real en `localhost:3003` levantado aparte — no es una prueba unitaria real, es una prueba de integración sin su dependencia disponible en CI/local por defecto.
  - `SearchResults.test.jsx` (18 pruebas) tiene el mismo problema de fondo que tenían `ChatInterface.test.jsx`/`DocumentUpload.test.jsx`/`Navigation.test.jsx`/`Pages.test.jsx` antes de `[CS-017]` — probablemente prueba una API de componente/store desactualizada. No corregido esta ronda (fuera del alcance pedido).

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

### [CS-010] Insumos de generación de prompt persistidos por tema
- **Estado:** `IMPLEMENTADO` (2026-08-14)
- **Requisitos:**
  - `chatbot_profiles` guarda `prompt_topic`, `prompt_description`, `prompt_target_audience`, `prompt_organization`, `prompt_sector` — los insumos reales con los que se generó el `system_prompt` vigente, no solo el resultado final.
  - `admin.py::generate_prompt` deriva el checklist de requisitos obligatorios de `description` (texto libre del dominio real del tema), nunca de vocabulario fijo de un dominio específico (ej. "trámites").
  - `AdminPage.jsx` carga estos 5 campos al seleccionar un tema existente y los reenvía al guardar; para un tema nuevo, todos arrancan vacíos (nunca con el último valor de otro tema visto en la sesión).
- **Restricciones:**
  - Los 5 campos son `Optional[str]` — temas creados antes de este contrato no los tienen y deben degradar a cadena vacía, no a un error.
- **Criterios de Aceptación:**
  - Editar un tema ya guardado y volver a generar su prompt reutiliza los insumos guardados, no obliga a re-escribirlos desde cero.
  - Un tema de dominio no-trámite (ej. seguridad/SOC) genera un prompt sin vocabulario burocrático hardcodeado.
- **Casos de Borde:**
  - El perfil `general` es de solo lectura (ver gotcha en `CLAUDE.md`) y no participa de este flujo de guardado.

### [CS-011] Alcance del fallback offline determinista del router LLM
- **Estado:** `IMPLEMENTADO` (2026-08-14)
- **Requisitos:**
  - `SmartLLMRouter._build_offline_fallback` (plantilla CRAFT determinista) solo puede devolverse cuando la llamada es de generación de prompt (`"topic" in kwargs`, invocado desde `admin.py::generate_prompt`).
  - En cualquier otro flujo (chat real de usuario, `chat_service.py::process_query`), si los 6 proveedores fallan o agotan su timeout, `SmartLLMRouter.chat()` debe relanzar la excepción — nunca devolver la plantilla offline como si fuera una respuesta real del asistente.
- **Restricciones:**
  - El manejador de excepción ya existente en `chat_service.py::process_query` (respuesta genérica `"Sistema de Emergencia"`, `error: True`) es el único punto autorizado para responder al usuario cuando el chat real falla — no duplicar lógica de fallback ahí ni en el router.
- **Criterios de Aceptación:**
  - Con los 6 proveedores simulando fallo, `generate_prompt` devuelve la plantilla offline con `is_ai_generated: false`; un chat real en la misma condición devuelve el mensaje de error genérico, nunca texto de plantilla.
- **Casos de Borde:**
  - Incidente real que motivó este contrato: un usuario real recibió el texto completo de la plantilla CRAFT ("Eres el Consultor e Integrador Experto de Sistema de Atención y Consultas...") como respuesta de chat cuando todos los proveedores fallaron — indistinguible de una respuesta real del asistente. Ver `STATE.md` sesión 2026-08-14.

### [CS-012] Aislamiento de caché de respuestas por tenant (`namespace`)
- **Estado:** `IMPLEMENTADO` (2026-08-14)
- **Requisitos:**
  - Toda función de `HybridCacheLayer` (`cache_layer.py`) que genere o busque una clave de caché debe recibir `namespace` (el `profile_id`/tema) y usarlo en la clave real (`cache_consulta_rpp:{namespace}:{hash}`) y en el patrón de escaneo (`cache_consulta_rpp:{namespace}:*`), nunca un escaneo global entre tenants.
  - `chat_service.py::process_query` debe consultar la caché antes de invocar al LLM y almacenar la respuesta después, únicamente para consultas sin `conversation_history` y cuyo `provider` no sea `fallback_offline`.
- **Restricciones:**
  - `namespace` por defecto es `"default"` solo para compatibilidad de la firma de función — en el flujo real de `chat_service.py` siempre se pasa el `profile_id` explícito.
- **Criterios de Aceptación:**
  - Una consulta cacheada bajo el tema A produce MISS al consultarse bajo el tema B con el mismo texto, incluso siendo la misma pregunta literal.
  - Verificado con prueba real contra Redis: HIT en el mismo namespace, MISS en namespace distinto.
- **Casos de Borde:**
  - Antes de este contrato, la caché completa nunca se invocaba desde `process_query` (código muerto) — no era solo un problema de aislamiento, era una feature sin conectar. Ver `STATE.md` sesión 2026-08-14.

### [CS-013] Aislamiento de sesión del widget embebido frente al panel admin
- **Estado:** `IMPLEMENTADO` (2026-08-14)
- **Requisitos:**
  - `WidgetPage.jsx` debe invocar `guestLogin()` siempre e incondicionalmente al montar, sin importar si ya existe un token en `localStorage` (compartido por origin con el panel admin en el mismo dominio).
  - El interceptor de respuesta 401 de `services/api.js` no debe forzar `window.location.href` a `/login` cuando el contexto de ejecución es un iframe (`window.self !== window.top`) — debe limpiar el token local y dejar que el flujo del widget maneje el error, sin secuestrar la navegación del sitio anfitrión de terceros.
- **Restricciones:**
  - Este contrato aplica solo al contexto `isWidget=true`/ruta `/widget` — el panel admin en su propio contexto de ventana principal conserva el redirect normal a `/login`.
- **Criterios de Aceptación:**
  - Con un token de admin ya presente en `localStorage` (mismo origin), embeber el widget en una página de terceros muestra el chat de invitado anónimo, nunca la pantalla de login de Authentik.
- **Casos de Borde:**
  - Incidente real: el iframe del widget mostraba la tarjeta real "INICIAR SESIÓN CON CASMARTS ID" en vez de chat — causa raíz doble (guard condicional de `guestLogin` + interceptor global de 401 secuestrando el iframe). Ver `STATE.md` sesión 2026-08-14.

### [CS-014] Biblioteca de íconos de marca compartida entre admin y chat real
- **Estado:** `IMPLEMENTADO` (2026-08-14)
- **Requisitos:**
  - `frontend/src/constants/chatIcons.js` es la única fuente de verdad para `ICON_MAP`/`ICON_LIBRARY` (biblioteca de íconos con nombre seleccionables en el admin). Tanto `AdminPage.jsx` (selector + Sandbox de preview) como `ChatInterface.jsx` (chat real, escritorio y widget) deben importar desde ahí, nunca redefinir la lista localmente.
  - `ChatInterface.jsx` debe resolver el ícono mostrado (header de escritorio, header del widget, avatar de estado vacío) como `ICON_MAP[profileConfig.icon] || Bot` cuando no hay `logo_url` configurado, en todos los puntos donde se muestra el ícono del bot.
  - El header del widget embebido debe pintarse con `profileConfig.primary_color` de fondo (no un gris plano), con el ícono/logo en una insignia sobre ese fondo.
- **Restricciones:**
  - Ninguna.
- **Criterios de Aceptación:**
  - Cambiar el ícono de un tema en el admin (ej. a `ShieldCheck`) se refleja en el chat real (escritorio y widget embebido), no solo en el Sandbox de preview del panel admin.
- **Casos de Borde:**
  - Un rediseño de header que agrega una segunda instancia del mismo ícono al DOM (header + avatar de estado vacío) puede volver ambiguo un selector de prueba que asumía una sola instancia (`querySelector` singular) — acotar el selector a una clase distintiva del elemento bajo prueba (ver `ChatInterfaceWidgetTheming.test.jsx`, corregido esta sesión).
  - Incidente real que motivó este contrato: el "Probador Sandbox" del admin (mockup separado, hardcodeado aparte) ya mostraba el ícono/color correctos, dando la falsa impresión de que el chat real también lo hacía. Ver `STATE.md` sesión 2026-08-14.

### [CS-015] Búsqueda de texto RAG tolerante a puntuación, y motor LLM por tema resiliente a rollback de sesión
- **Estado:** `IMPLEMENTADO` (2026-08-14)
- **Requisitos:**
  - `knowledge_base.py::search_in_knowledge_text_async` debe limpiar cada palabra de la consulta a solo caracteres de palabra Unicode (conservando acentos/ñ) antes de compararla con stopwords y unirla al patrón de `to_tsquery` — signos de puntuación pegados a una palabra (`¿cómo`, `(crs)?`) nunca deben llegar crudos a `to_tsquery`, que los interpreta como sintaxis (paréntesis = agrupación).
  - `chat_service.py::process_query` debe capturar los valores del motor LLM personalizado por tema (`llm_provider`, `llm_model`, `custom_api_key`, `custom_base_url`) como variables planas de Python inmediatamente después de cargar `profile` desde `db_session`, antes de cualquier operación posterior (búsqueda RAG, rewriter) que pueda invocar `session.rollback()` sobre esa misma sesión. El código de después del punto de posible rollback nunca debe volver a leer esos valores directamente de `profile.*`.
- **Restricciones:**
  - Este contrato cubre específicamente el patrón "AsyncSession + rollback a mitad de request + atributo ORM leído después" — no es una prohibición general de acceder a atributos de `profile` en otras partes del flujo que no siguen a un posible rollback.
- **Criterios de Aceptación:**
  - Una consulta de usuario con signos de interrogación/paréntesis (ej. `"¿Cómo calcula Centinela el Centinela Risk Score (CRS)?"`) no produce `PostgresSyntaxError` ni `sqlalchemy.exc.MissingGreenlet`; el turno de chat se resuelve con una respuesta real (RAG o conocimiento general), no con el mensaje de "Sistema de Emergencia".
- **Casos de Borde:**
  - Incidente real que motivó este contrato: la consulta exacta de arriba encadenó los dos bugs (tsquery roto → rollback → `MissingGreenlet` al leer `profile.llm_provider`), tumbando el turno completo. Ver `MANUAL_TECNICO_DESARROLLADOR.md` §20.8 y `STATE.md` sesión 2026-08-14 (continuación).

### [CS-016] Primer mensaje de una sesión de chat nueva debe aplicar la respuesta y apagar `loading`
- **Estado:** `IMPLEMENTADO` (2026-08-14) — ver también `[CS-020]`, un segundo bug distinto encontrado en el mismo flujo
- **Requisitos:**
  - En `ChatInterface.jsx::sendMessage`, cuando no existe `currentSessionId` al invocar la función (sesión nueva creada dentro de la misma llamada), las comprobaciones que aplican la respuesta del asistente y apagan `loading` no deben depender exclusivamente de `activeSessionId === currentSessionId` — deben reconocer explícitamente el caso de sesión recién creada (`isNewSession`), ya que `currentSessionId` es un cierre de React que no refleja el `setCurrentSessionId` de la misma ejecución.
- **Restricciones:**
  - La protección original (no aplicar una respuesta a una sesión de la que el usuario ya se alejó) debe preservarse para sesiones YA EXISTENTES — este contrato solo cubre el caso de sesión nueva.
- **Criterios de Aceptación:**
  - Enviar el primer mensaje de una conversación nueva (sin sesión previa) siempre termina con `loading=false` y, si la petición tuvo éxito, con la respuesta del asistente visible — nunca con el spinner colgado indefinidamente, sin importar si el backend respondió con éxito o con error.
- **Casos de Borde:**
  - Incidente real que motivó este contrato: el widget embebido de Centinela-AI se quedó colgado en "Procesando consulta..." indefinidamente en el primer mensaje de una sesión de invitado nueva — reproducido con `frontend/tests/components/ChatInterfaceNewSessionSend.test.jsx`. Ver `STATE.md` sesión 2026-08-14 (continuación).

### [CS-017] Pruebas de frontend deben mockear la forma real de sus dependencias, no una API imaginaria
- **Estado:** `IMPLEMENTADO` (2026-08-14) — aplicado a los 4 archivos identificados; el resto de la suite (`SearchResults.test.jsx`) queda pendiente, ver `[CS-008]`
- **Requisitos:**
  - Antes de escribir o corregir una prueba que mockea un store (Zustand) o un componente, se debe leer el componente/store REAL bajo prueba y usar exactamente su forma actual (nombres de campos, acciones, mensajes de texto visibles) — nunca una forma "razonable" inferida del nombre del componente.
  - Cuando un rediseño de UI hace que el mismo texto/ícono aparezca más de una vez en el DOM (ej. dos `<select>` con las mismas opciones, un mensaje de bienvenida repetido en header + estado vacío), las pruebas deben usar las variantes `findAllBy*`/`getAllBy*` o acotar la búsqueda a un contenedor específico — no asumir que `getBy*` siempre encuentra una sola coincidencia.
- **Restricciones:**
  - Ninguna.
- **Criterios de Aceptación:**
  - `ChatInterface.test.jsx`, `DocumentUpload.test.jsx`, `Navigation.test.jsx` y `Pages.test.jsx` corren sin errores de sintaxis ni de forma de mock, y sus aserciones reflejan comportamiento real verificable del componente (no solo "no truena").
- **Casos de Borde:**
  - Los 4 archivos, previos a esta corrección, tenían DOS problemas superpuestos: (1) sintaxis TypeScript (`as any`, `as HTMLInputElement`, anotaciones de parámetro) en archivos `.jsx` puro, rechazada por el transform de Oxc/Vite; (2) una vez resuelto (1), se reveló que las aserciones probaban una API de componente/store que nunca coincidió con el código real actual — `LoginPage` real es SSO vía Authentik/OIDC (sin formulario email/password ni registro, que sí probaba la versión anterior), `Navigation` real es un sidebar fijo sin estados condicionales de "autenticado/no autenticado", `DocumentUpload`/`documentStore` reales no tienen `uploadDocument`/`isUploading`/`getDocuments`. Reescritos contra el código real, verificados con `docker exec consulta-smart-frontend npx vitest run`. Ver `STATE.md` sesión 2026-08-14 (continuación 3).

### [CS-018] Presupuesto de tiempo acotado para el Blindaje anti-alucinación (Grounding Check)
- **Estado:** `IMPLEMENTADO` (2026-08-14)
- **Requisitos:**
  - `chat_service.py::process_query` debe envolver la llamada a `_verify_grounding` en `asyncio.wait_for(timeout=8.0)`. Si se excede, se usa la respuesta original sin verificar (mismo comportamiento de "fail open" que el except interno de `_verify_grounding`).
- **Restricciones:**
  - Este timeout es independiente de los timeouts por-proveedor del router (15s cada uno) — el Blindaje puede intentar como máximo un proveedor completo antes de que este límite lo corte, no una cascada completa.
- **Criterios de Aceptación:**
  - En un escenario de cascada de proveedores degradada (ej. 2+ proveedores fallando por timeout/rate-limit), el Blindaje nunca añade más de ~8s al tiempo total de respuesta del turno, sin importar cuántos proveedores intente internamente.
- **Casos de Borde:**
  - Incidente real que motivó este contrato: `_verify_grounding` hace su propia llamada independiente a `_get_best_provider()`, sin memoria de que un proveedor (ej. NVIDIA) acababa de fallar por timeout segundos antes en el mismo turno para la respuesta principal — lo reintentaba igual, duplicando ~30s de espera para una verificación opcional que de por sí ya falla abierto. Ver `STATE.md` sesión 2026-08-14 (continuación 4).

### [CS-019] Deduplicación de documentos RAG por hash de contenido, por tenant
- **Estado:** `IMPLEMENTADO` (2026-08-14) — protección hacia adelante; documentos ya existentes antes de este contrato no tienen `content_hash` retroactivo
- **Requisitos:**
  - `DocumentModel.content_hash` (SHA-256 hex del contenido crudo del archivo subido, no del texto extraído) debe calcularse y persistirse en cada subida vía `admin.py::upload_chatbot_document`.
  - Antes de procesar (parsear/chunkear/embeber) un archivo subido, se debe rechazar con `409 Conflict` si ya existe un `Document` **activo** (`is_active=True`) con el mismo `content_hash` **en el mismo `category` (tenant)**.
- **Restricciones:**
  - El alcance de la deduplicación es POR TENANT, no global — subir el mismo archivo a dos temas distintos a propósito es un caso de uso válido, no un duplicado accidental.
  - Documentos subidos ANTES de este contrato tienen `content_hash IS NULL` — no cuentan como duplicado de nada hasta que alguien los vuelva a subir (momento en el que sí queda registrado su hash real).
- **Criterios de Aceptación:**
  - Subir el mismo archivo (bytes idénticos) dos veces al mismo tema devuelve `409` en el segundo intento, con el título y fecha del documento ya existente en el mensaje de error.
  - Subir el mismo archivo a un tema DISTINTO no se bloquea.
- **Casos de Borde:**
  - Motivado por sospecha del usuario de un documento duplicado para Centinela-AI — verificado contra la BD real que NO había duplicado activo en ese momento (`SELECT` directo: 1 documento, 112 chunks distintos); la funcionalidad de prevención se implementó de todos modos por ser una petición explícita y válida hacia el futuro. Verificado con un script real (no mockeado) que inserta/consulta/limpia contra Postgres, confirmando aislamiento por tenant (mismo hash en categoría distinta → MISS). Ver `STATE.md` sesión 2026-08-14 (continuación 4).

### [CS-020] El mensaje del usuario no debe borrarse por la carga de historial al crear una sesión nueva
- **Estado:** `IMPLEMENTADO` (2026-08-14)
- **Requisitos:**
  - El `useEffect` de `ChatInterface.jsx` que carga el historial de la sesión activa (keyed en `currentSessionId`) no debe ejecutarse la primera vez que `currentSessionId` cambia como consecuencia de que `sendMessage` acaba de crear una sesión nueva para el envío en curso — en ese instante el backend aún no tiene guardado el mensaje del usuario, y cargar el historial "vacío" borra la burbuja agregada de forma optimista.
  - El mismo efecto SÍ debe seguir ejecutándose normalmente para cualquier otro cambio de `currentSessionId` (el usuario selecciona una conversación existente distinta desde la barra lateral).
- **Restricciones:**
  - La bandera que controla esto (`skipNextHistoryFetchRef`) debe ser un `useRef`, no un `useState` — no debe disparar un render adicional ni competir en el orden de aplicación de efectos.
- **Criterios de Aceptación:**
  - Enviar el primer mensaje de una sesión nueva nunca invoca `clearMessages()`/`setMessages()` como resultado de la carga de historial, ni llama a `chatAPI.getSession()` en absoluto para esa sesión recién creada.
- **Casos de Borde:**
  - Incidente real que motivó este contrato: el usuario reportó "cada que hago una pregunta sigue desapareciendo del chat" — confirmado con logs reales del backend (`GET /chat/sessions/{id}` 700ms después de `POST /chat/sessions`, antes de que `POST /chat/query` completara) que cada pregunta probada creaba una sesión nueva y disparaba la carrera. Es un bug DISTINTO e independiente de `[CS-016]` (cierre obsoleto de React) y del Blindaje duplicando tiempo de espera (`[CS-018]`) — los tres coexistían con síntomas distintos. Prueba de regresión en `ChatInterfaceNewSessionSend.test.jsx`, verificada como capaz de detectar el bug (falla real al revertir el fix temporalmente, pasa al restaurarlo). Ver `STATE.md` sesión 2026-08-14 (continuación 5).

### [CS-021] Dominio público dedicado por tenant (multi-dominio, no solo multi-tema)
- **Estado:** `IMPLEMENTADO` (2026-08-19/20)
- **Requisitos:**
  - Un dominio público nuevo (ej. `chat.teca.ca-smarts.com`) debe poder servir el mismo build de frontend que `chat.casmart.internal`, forzando un `profile_id` fijo (sin selector visible) y autenticando contra un Authentik potencialmente distinto — todo resuelto en runtime por `window.location.hostname`, sin variables de build por dominio.
  - `frontend/src/config/domainLock.js` centraliza dos mapas: `DOMAIN_LOCKED_PROFILE` (hostname → profile_id fijo) y `DOMAIN_AUTHORITY`/`resolveAuthority()` (hostname → issuer OIDC), con default seguro (`auth.casmart.internal`, sin bloqueo de tema) para cualquier hostname no listado.
  - El login por dominio bloqueado NUNCA debe respetar `profile_id`/`tenant` de query string — el hostname manda siempre.
- **Restricciones:**
  - El backend NO valida el `profile_id` contra el dominio de origen de la petición — el bloqueo es puramente de UI/UX en `ChatInterface.jsx` (mismo nivel de garantía que el resto de interruptores `config_metadata`, ver `[CS-024]`).
  - Requiere, fuera de este repo: alta en el nginx de `.26` (vhost del dominio nuevo, cert propio), Pi-hole si el nombre debe resolver en la LAN interna, y alta explícita del origen en la lista blanca de CORS del gateway de Authentik en `.208` (`subdomains.conf`, bloque `auth.casmart.internal`) — sin eso el login falla en el navegador aunque el código de este repo esté perfecto.
- **Criterios de Aceptación:**
  - `resolveAuthority('chat.teca.ca-smarts.com')` devuelve el issuer de `auth.teca.ca-smarts.com`; cualquier otro hostname cae al default.
  - Con el hostname bloqueado, el chat ignora `?profile_id=` de la URL y oculta el selector "Asistente Activo".
- **Casos de Borde:**
  - Ver `docs/BITACORA_ANALISIS_CAUSAL.md` para la cadena completa de incidentes reales encontrados al desplegar el primer dominio nuevo (CORS, Signing Key vaciado en Authentik, certificado autofirmado bloqueando el intercambio de token en segundo plano).

### [CS-022] Aislamiento de resultados RAG por `category` en TODAS las ramas de búsqueda
- **Estado:** `IMPLEMENTADO` (2026-08-19)
- **Requisitos:**
  - `KnowledgeBase.search_in_knowledge_async` (búsqueda híbrida: vectorial + texto) debe aplicar `filters["category"]` como filtro SQL duro en las 3 consultas crudas involucradas: la vectorial (pgvector `<=>`), la de texto (`to_tsvector`/`to_tsquery`) y su fallback `ILIKE`.
  - Ningún resultado de una categoría/tenant distinta al solicitado debe poder aparecer en `sources`/contexto RAG de otro tenant, sin importar por cuál de las 3 ramas se recuperó.
- **Restricciones:**
  - Ninguna.
- **Criterios de Aceptación:**
  - Con `filters={"category": "teca"}`, una consulta genérica ("requisitos y procedimiento para este trámite") solo devuelve chunks con `category='teca'`.
  - La MISMA consulta sin filtro de categoría sí devuelve otras categorías (`starter`, `rpp`, `procedimiento`, `general`) — confirma que la fuga era real antes del fix, no solo teórica.
- **Casos de Borde:**
  - Bug encontrado al desplegar el primer tenant nuevo (`teca`): documentos de otros temas (ej. `DIRECTORIO_NOTARIOS_FULL_2026`, de RPP/IRCEP) aparecían citados como "Fuentes Oficiales" en el chat de `teca`. Causa raíz: la rama vectorial nunca había tenido filtro de `category` desde su implementación original — no es una regresión de este cambio, es el estado real hasta este fix. Verificado con `scripts/verify_rag_category_isolation.py` contra la BD real (antes/después, con y sin filtro).

### [CS-023] Comportamiento conversacional configurable por tema (aclaración, sugerencias, estilo, saludo)
- **Estado:** `IMPLEMENTADO` (2026-08-20)
- **Requisitos:**
  - `chat_service.py` debe poder instruir al LLM, vía sufijos de `system_prompt` concatenados DESPUÉS de resolver el prompt base (custom o fallback, nunca reemplazándolo), a: (a) pedir aclaración cuando una consulta es ambigua-pero-válida en dominio, priorizando SIEMPRE responder con contenido ya recuperado del RAG sobre preguntar si el RAG ya tiene la respuesta; (b) anexar 2-4 sugerencias de seguimiento en un marcador `SUGERENCIAS_JSON:` al final de la respuesta, extraído por regex+`json.loads` con degradación a `[]` si el LLM no siguió el formato, y SIEMPRE recortado del texto visible al usuario; (c) aplicar un estilo de respuesta (`concise`/`detailed`) opcional.
  - Cada uno de los 4 comportamientos (aclaración, sugerencias, estilo, saludo-vía-LLM) debe ser activable/desactivable de forma independiente por tema vía `config_metadata` (`enable_clarifying_questions`, `enable_suggestions`, `response_style`, `greeting_via_llm`), todos con default que preserva el comportamiento previo a este contrato (`True`/`True`/`"default"`/`False`).
  - El rewriter de búsqueda RAG (`chat_service.py`, sección "Traducción Semántica") debe anteponer el contexto de los últimos 2 mensajes de `conversation_history` a la query de búsqueda antes de decidir si reescribe y antes de construir `search_query` — para que una respuesta corta de seguimiento (ej. "Puebla", tras una pregunta de aclaración del propio asistente) no pierda el tema original de la conversación en la recuperación RAG.
- **Restricciones:**
  - Los sufijos de comportamiento deben permanecer 100% agnósticos de dominio/tenant (misma restricción de `[CS-002]`) — nunca texto específico de un perfil particular.
  - Este mecanismo es aditivo sobre el `system_prompt` propio de cada tema: si el prompt propio de un tema ya induce una conducta similar por su cuenta (ej. un bot de mesa de ayuda que ya pide datos faltantes), desactivar `enable_clarifying_questions` apaga SOLO la instrucción agregada por este contrato, no la tendencia del prompt base del tema.
- **Criterios de Aceptación:**
  - Verificado en vivo contra los 11 perfiles reales de producción: aclaración funciona (perfiles que reciben una consulta ambigua piden el dato faltante, con prioridad de RAG-real-sobre-preguntar confirmada para `general`/`rpp`), sugerencias no vacías y sin fuga del marcador en 10/11 perfiles (1 timeout de infraestructura LLM, no del feature), rechazo de temas fuera de dominio sigue firme en 9/11 (2 excepciones son perfiles de prueba `probando`/`prueba-chat`, eliminados de la BD el mismo día).
  - `response_style=concise` vs `detailed` sobre la misma pregunta: 719 vs 2040 caracteres (verificación real, no estimada).
  - `greeting_via_llm=True` cambia `provider` de `"Sistema Local (Saludo)"` a un proveedor LLM real, con respuesta generada en vivo.
- **Casos de Borde:**
  - Un cache-hit (`[CS-025]`) para una pregunta de primer turno nunca dispara el rewriter con contexto (no aplica, no hay LLM call en un hit).

### [CS-024] Interruptores de visibilidad y disponibilidad por tema (`config_metadata`)
- **Estado:** `IMPLEMENTADO` (2026-08-19/20)
- **Requisitos:**
  - `show_sources`, `show_provider_debug`, `enable_feedback_buttons`, `enable_widget_embed`: cuatro flags booleanos en `ChatbotProfile.config_metadata` (columna JSON ya existente, sin migración), todos `True` por defecto (preserva el comportamiento anterior a este contrato en cualquier tema que no los configure explícitamente).
  - `show_provider_debug=False` debe omitir el sufijo `"\n\n---\n*LLM: ...*"` que `chat.py` concatena al texto de la respuesta ANTES de guardarla en BD (no es un post-proceso de despliegue, es al momento de generar la respuesta).
  - `show_sources=False` y `enable_feedback_buttons=False` son gates puramente de renderizado en `ChatInterface.jsx` (`profileConfig.show_sources`/`profileConfig.enable_feedback_buttons`, poblados desde `GET /chat/profiles/{id}`) — el backend sigue calculando/devolviendo esos datos siempre.
  - `enable_widget_embed=False` debe bloquearse en DOS capas: (a) `WidgetPage.jsx` verifica el flag ANTES de invocar `guestLogin()` y muestra un mensaje de bloqueo en vez de montar el chat (falla abierto si la verificación misma da error de red); (b) `POST /chat/query` rechaza con `403` cualquier mensaje cuando `current_user.is_widget=True` (JWT del login de invitado, ver `auth_utils.py::get_current_user`) Y el perfil objetivo tiene `enable_widget_embed=False` -- un usuario autenticado normal (no invitado) nunca se ve afectado por este flag.
- **Restricciones:**
  - El refuerzo de backend de `enable_widget_embed` es la ÚNICA de estas 4 flags con una barrera real de API (no solo de UI) — las otras 3 dependen de que el cliente honre lo que el backend le indica/genera, mismo nivel de garantía que el resto de esta app.
- **Criterios de Aceptación:**
  - `curl` real con JWT de invitado contra `POST /chat/query` en un perfil con `enable_widget_embed=False`: `403`. Mismo perfil sin el flag (o en `True`): `200`.
  - Panel admin (`AdminPage.jsx`) expone las 4 flags como checkboxes/select junto al resto de Guardrails, ya incluidas en el payload de guardado existente (`configToSave = {...config, ...}`, sin cambios adicionales de fontanería).
- **Casos de Borde:**
  - Un usuario autenticado normal (admin/staff) que use un tema con `enable_widget_embed=False` desde `/` (no desde `/widget`) nunca es bloqueado — el flag solo restringe el canal de invitado/embebible.

### [CS-025] Caché híbrida consciente de la configuración vigente del tema
- **Estado:** `IMPLEMENTADO` (2026-08-20)
- **Requisitos:**
  - El namespace de caché (`cache_layer.py::_generate_cache_key`) debe incorporar, además del `profile_id`, los flags de `config_metadata` que cambian el CONTENIDO de la respuesta generada: `response_style`, `enable_clarifying_questions`, `enable_suggestions` (`cache_namespace = f"{profile_id}:{response_style}:{int(enable_clarifying_questions)}:{int(enable_suggestions)}"` en `chat_service.py`).
  - La carga de `config_metadata` del perfil debe ocurrir ANTES del chequeo de caché (reordenado respecto al flujo previo), para poder construir ese namespace antes de la primera consulta a Redis.
  - `HybridCacheLayer.store_response`/`get_with_fallback` deben persistir y restaurar `suggestions` igual que ya hacían con `sources` — un cache-hit debe devolver las mismas sugerencias que se generaron y cachearon junto con la respuesta original.
- **Restricciones:**
  - Ninguna funcionalmente nueva; el namespace más granular reduce en la práctica la tasa de aciertos de caché solo si un mismo tema cambia de configuración con frecuencia (caso raro — normalmente un admin fija una config y la deja estable).
- **Criterios de Aceptación:**
  - Misma pregunta exacta, `response_style=concise` primero y `response_style=detailed` después: la segunda llamada NO debe venir de caché (`provider` real de LLM, no `"cache"`), y debe diferir sustancialmente en longitud/tono de la primera.
  - Repetir la pregunta con el MISMO `response_style` que una llamada previa sí debe pegar en caché (`provider: "cache"`) y traer `suggestions` no vacío si la respuesta original las tenía.
- **Casos de Borde:**
  - Verificado en vivo con las 3 llamadas encadenadas descritas arriba contra `mesa_ayuda` real: concise (621 chars, LLM real) → detailed (2222 chars, LLM real, NO cache) → concise repetida (621 chars, `provider: cache`, `suggestions` restauradas).

### [CS-026] El widget nunca debe desbordarse horizontalmente de su contenedor
- **Estado:** `IMPLEMENTADO` (2026-08-20)
- **Requisitos:**
  - Cualquier texto sin puntos de quiebre naturales (ej. un nombre de archivo largo en "Fuentes Oficiales") debe truncarse con elipsis dentro del ancho del widget, nunca desbordarlo visualmente.
  - El contenedor de mensajes del chat debe tener `overflow-x: hidden` como barrera final, independiente de si algún contenido puntual logra evadir la regla anterior.
- **Restricciones:**
  - El elemento con `truncate` (Tailwind: `overflow:hidden; text-overflow:ellipsis; white-space:nowrap`) DEBE llevar también `min-w-0` cuando es hijo directo de un contenedor flex — sin eso, el mínimo de ancho de un flex item por defecto (`min-width:auto`, que para texto `nowrap` equivale a su ancho completo) impide que el truncado tenga efecto, sin importar que un ancestro más arriba sí tenga `min-w-0`.
- **Criterios de Aceptación:**
  - Un nombre de archivo largo sintético (`CA-PGO-D-E-05-Manual_de_usuario_Administracion_Privilegios_Muy_Largo.pdf`) renderiza con las clases `truncate`+`min-w-0` presentes en el span correspondiente (verificado en DOM real de test, no solo por inspección visual).
- **Casos de Borde:**
  - Reportado independientemente por dos personas en dos equipos distintos viendo el widget embebido en `teca-frontend-dev.teca.ca-smarts.com`; la causa real (bug de flexbox) solo se confirmó tras descartar por evidencia real (computed styles en DevTools: `transform: none`, `zoom: 1` en `body`/`app-root`) la hipótesis inicial de un `transform`/`zoom` heredado del layout Angular del sitio host.
