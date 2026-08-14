# Bitácora de Análisis Causal (CAR) — ConsultaSmart

Práctica CMMI Nivel 5 — Análisis Causal y Resolución (CAR): cuando algo falla, se
documenta la causa raíz y la acción para prevenir su recurrencia, no solo el
síntoma corregido. Ver `docs/ESTANDAR_CMMI_UNIVERSAL.md` §4.1.

**Formato de entrada:** Fecha · Síntoma · Causa raíz · Corrección aplicada ·
Prevención de recurrencia · Evidencia de verificación.

---

## 2026-07-22 — Ningún proveedor de IA activo: el chat responde con texto genérico sin que nadie lo note

**Síntoma reportado por el usuario:** "la matriz de observabilidad está incompleta, veo todos los proveedores deshabilitados".

**Investigación:** se verificó primero si era un bug de visualización. Se confirmó que **no**: `settings.GROQ_API_KEY`, `GCP_PROJECT_ID`, `GOOGLE_API_KEY` y `NVIDIA_NIM_API_KEY` están efectivamente vacíos en el contenedor real. Se revisaron los logs de producción de las últimas horas: **cada respuesta de asistente registrada terminaba en el mismo texto exacto de plantilla** ("Eres el Consultor e Integrador Experto del Sistema de Atención y Consultas..."), sin relación con la pregunta real del usuario ni con el contexto RAG recuperado (que sí era correcto y variaba por consulta).

**Causa raíz (identificada con precisión, no solo "token inválido"):** `docker-compose.yml` define `VAULT_URL` para los 3 contenedores de `consulta-smart` pero **nunca define `VAULT_TOKEN`**. `app/core/vault.py::VaultClient.__init__` hace `self.token = os.getenv("VAULT_TOKEN", "root")` — al no existir la variable de entorno, usa literalmente el string `"root"` (un valor pensado únicamente como token por defecto de un servidor `vault dev` local de un solo desarrollador, nunca válido en un Vault real). Se confirmó explícitamente:
- El usuario aportó el dato de que Vault vive en el mismo servidor que Authentik (`10.4.3.208`) — se verificó el endpoint público `/v1/sys/seal-status`: Vault está **inicializado y desellado** (`sealed: false`), es decir, la infraestructura de Vault en sí funciona correctamente. El problema no es una caída de Vault.
- `client.lookup_token()` con el token real usado por el contenedor devuelve `Forbidden: permission denied / invalid token`, y el propio valor del token resultó ser la cadena literal `"root"` (4 caracteres) — confirmando que nunca se configuró un token real para este despliegue, ni para `idp-smart` ni `lexivault-ai` (mismo gap verificado en los 3 `docker-compose.yml` del portafolio).

Como `GROQ_API_KEY`/`GOOGLE_API_KEY`/`NVIDIA_NIM_API_KEY` no tienen ningún valor por defecto en `docker-compose.yml` (a diferencia de `DB_PASSWORD`/`SECRET_KEY`, que sí tienen fallback), dependen **por completo** de que Vault los entregue — al fallar la autenticación, quedan vacíos silenciosamente. `SmartLLMRouter._get_best_provider()` no encuentra ningún proveedor disponible y cae al texto de respaldo determinista (pensado originalmente solo como red de seguridad para el generador de prompts del admin, pero aplicado también a cada consulta real de chat).

**Por qué nadie lo notó:** el fallback está diseñado para "no truene la respuesta" — genera un texto con formato correcto y aspecto profesional, por lo que a simple vista no parece un error. El panel de Observabilidad ya existía, pero mostraba los proveedores como "deshabilitados" sin ninguna alerta que explicara la consecuencia real (que el chat no está generando respuestas reales).

**Corrección aplicada (parcial — ver limitación):**
1. Se corrigió un bug real y separado de visualización en `GET /admin/stats/llm-router`: la fila "GCP Vertex AI / Gemini" conflaba dos proveedores reales distintos (chequeaba solo `GCP_PROJECT_ID`, ignorando `GOOGLE_API_KEY` de Gemini), y existía una fila fantasma "Ollama / Local LLM" sin ningún `OllamaProvider` real en el código — corregido a 4 filas reales coincidentes con `SmartLLMRouter._initialize_providers()`.
2. Se agregó el campo `no_llm_provider_configured` a la respuesta del endpoint, y una alerta roja explícita en `LLMObservabilityPanel.jsx` cuando los 4 proveedores están deshabilitados — explicando en lenguaje claro que el chat sigue funcionando en apariencia pero sin generar respuestas reales.

**Limitación — esto NO resuelve el problema de fondo:** la causa raíz (Vault no autentica) requiere acceso administrativo real a Vault (rotar/verificar el `VAULT_TOKEN`) que está fuera del alcance de este agente. Se documenta como **R-09 en `docs/REGISTRO_DE_RIESGOS.md`, severidad Crítica, activo ahora mismo** — es el riesgo de mayor prioridad de todo el registro porque afecta la funcionalidad principal del producto en producción en este momento, no una brecha teórica.

**Prevención de recurrencia:** la alerta visible en el panel de Observabilidad convierte este tipo de falla de "silenciosa e indetectable" a "visible con un vistazo al panel de administración" — la próxima vez que Vault falle (o cualquier proveedor quede sin configurar), el administrador lo verá de inmediato en vez de que se descubra por casualidad al revisar logs.

**Evidencia de verificación:** `client.is_authenticated()` ejecutado contra el Vault real devuelve `False`; 3 entradas de log reales con el mismo texto de respaldo exacto en respuestas de asistente de las últimas horas; `GET /admin/stats/llm-router` ejecutado directamente tras el fix devuelve las 4 filas reales con `no_llm_provider_configured: true`.

**Actualización 2026-07-22/23 — stopgap aplicado (mitiga el síntoma, no la causa raíz):**

El usuario aportó 4 API keys de distintos proveedores de LLM para evaluar como
alternativa mientras se resuelve el acceso administrativo real a Vault. Cada una se
probó con una llamada real y mínima al proveedor (nunca simulada), enmascarando el
valor de la key en toda salida impresa:

| Proveedor | Resultado | Detalle del error (sin exponer la key) |
|---|---|---|
| **Groq** | ✅ Funciona | Respuesta real del modelo recibida correctamente. |
| Gemini | ❌ Falla | Error de autenticación real de la API ("API key not valid" / `INVALID_ARGUMENT`), no es un problema de cuota. |
| NVIDIA NIM | ❌ Falla | El nombre de modelo aportado no existe (`404`); reintentado con el nombre corregido → `403 Forbidden`, confirmando que la key en sí (no solo el modelo) es inválida. |
| OpenRouter | ❌ Falla | `401 User not found` — la key no corresponde a ninguna cuenta válida. |

**Causa raíz — sigue sin resolverse:** este resultado no cambia el diagnóstico de
arriba. Vault sigue sin un token real configurado; de las 4 alternativas evaluadas
como bypass temporal, solo una resultó válida.

**Corrección aplicada (stopgap, no la corrección de fondo):** se configuró
`GROQ_API_KEY` directamente en `.env` (bypass de Vault únicamente para este
proveedor) y se recreó el contenedor con `docker compose up -d --force-recreate`
— se confirmó que `docker restart` por sí solo **no** relee `.env`/`env_file`, y
por eso una recreación previa "exitosa" seguía sin tener la variable disponible en
el proceso.

**Evidencia de verificación post-stopgap:**
- `GET /admin/stats/llm-router` real: `Groq Llama-3: active`, `no_llm_provider_configured: false`.
- Prueba de extremo a extremo directa contra `SmartLLMRouter.chat()` (sin mocks, contenedor real): devolvió una respuesta genuina del modelo (`("PRUEBA-OK", "groq")`), no el texto de plantilla de respaldo.

**Limitación que persiste:** el chat depende ahora de una **única** API key de un
**único** proveedor puesta directamente en un archivo `.env`, sin la redundancia
multi-proveedor ni la rotación centralizada que Vault estaba pensado para dar. Si
esta key de Groq se invalida o se agota su cuota, el sistema vuelve a caer al texto
de respaldo genérico sin ningún proveedor de respaldo real. R-09 se actualiza a
"mitigado, no resuelto" en `docs/REGISTRO_DE_RIESGOS.md` — la corrección de fondo
(token de Vault real) sigue pendiente y fuera del alcance de este agente.

---

## 2026-07-22 — Tema "general" con System Prompt corrupto

**Síntoma:** el chatbot del tema `general` empezó a responder de forma incoherente;
al inspeccionar la configuración, el `system_prompt` contenía texto duplicado y
autoreferencial.

**Causa raíz:** un administrador usó el "Generador de System Prompt" ingresando una
instrucción larga en el campo "tema" (en vez de un tema corto como "Trámites RPP"),
que quedó embebida repetidamente en la plantilla CRAFT. La causa raíz *estructural*
detrás de esto: `chatbot_profiles` no tenía historial de cambios ni protección contra
sobreescribir el tema base/plantilla — cualquier edición, buena o mala, se aplicaba
de inmediato y de forma irreversible.

**Corrección aplicada:**
1. Se restauró `system_prompt` del tema `general` al texto de fábrica (el mismo que
   usa `chat_service.py` como fallback canónico), verificado con coincidencia exacta
   contra la base de datos real.
2. El tema `general` se volvió de solo lectura a nivel de backend
   (`admin.py::save_chatbot_profile` / `delete_chatbot_profile` rechazan la
   operación con 400 si `id == "general"` y el perfil ya existe) — antes solo el
   frontend bloqueaba el borrado, y nada bloqueaba la edición.
3. El frontend, al detectar que se intenta guardar sobre `general`, redirige
   automáticamente al flujo de "Guardar como tema nuevo" sin perder la edición.

**Prevención de recurrencia (causa raíz estructural):** se agregó
`chatbot_profile_audit_log` (bitácora de cambios con snapshot antes/después, quién y
cuándo) y un endpoint de restauración a un punto anterior con un clic — para que la
*próxima* vez que cualquier tema (no solo `general`) se corrompa por error humano,
la recuperación sea inmediata y no requiera reconstruir el valor "de fábrica" a mano
desde el código fuente.

**Evidencia de verificación:** prueba real de extremo a extremo ejecutada contra el
contenedor en producción (`consulta-smart-backend`): crear tema de prueba → editar →
verificar 2 entradas en el historial → restaurar al estado original → verificar que
`system_prompt` volvió exactamente al valor esperado → borrar → verificar 4 entradas
totales incluyendo el borrado. Resultado: **todas las aserciones pasaron**.

---

## 2026-07-22 — LLM personalizado por tema completamente no funcional

**Síntoma:** ninguno reportado por un usuario — se encontró durante una revisión de
código proactiva del feature de "LLM personalizado por tema" (implementado por
Google Antigravity), antes de que un administrador lo usara en producción.

**Causa raíz:** `chat_service.py` invocaba
`SmartLLMRouter(custom_provider=..., custom_api_key=..., custom_model=...)`, pero el
constructor real de `SmartLLMRouter` no aceptaba esos parámetros. Cada intento
lanzaba `TypeError`, absorbido silenciosamente por el `try/except` de fallback —
la función *parecía* funcionar (nunca crasheaba, siempre respondía), pero el
proveedor personalizado configurado por el administrador **nunca se usaba
realmente**, sin ningún error visible. Este es exactamente el patrón de "falla
silenciosa" documentado en `ESTANDAR_MAESTRO_AUDITORIA_UNIVERSAL.md` §5.4: un
`try/except` de buena intención (evitar que un proveedor caído tumbe la respuesta)
enmascaró un bug de integración real.

**Corrección aplicada:** se implementó soporte real en `SmartLLMRouter.__init__`
para `custom_provider`/`custom_api_key`/`custom_model`, con proveedores soportados
(`groq`, `gemini`, `nvidia`, `openai`) y rechazo explícito (`ValueError`, no
silencioso) para los no soportados (`vertex`, `ollama`), capturado por el mismo
`try/except` existente — ahora el fallback ocurre solo ante errores reales, no ante
un mismatch de firma.

**Prevención de recurrencia:** ninguna automatizada todavía — **brecha abierta**:
no existe una prueba automatizada que hubiera detectado este bug antes de llegar a
producción (una prueba de integración que construya `SmartLLMRouter` con cada
`custom_provider` soportado habría fallado inmediatamente). Candidato real para
`backend/tests/` en una próxima iteración.

**Evidencia de verificación:** construcción real de `SmartLLMRouter` con cada
variante de proveedor (`groq`, `ollama` rechazado correctamente) ejecutada dentro
del contenedor real, sin mocks.

---

## 2026-08-13 — Generador de System Prompt "hablando de trámites" para un tema que no lo es, y fallback silencioso enmascarando que no hubo LLM real

**Síntoma reportado por el usuario:** al generar el System Prompt para el tema
"Centinela-AI" (plataforma SOC/SOAR de seguridad, sin relación con trámites
gubernamentales) usando el Generador de System Prompt del panel admin, el
resultado seguía hablando de "trámite o procedimiento exacto", "Registro de
expediente oficial", "Documentación comprobatoria vigente" y "ventanillas
digitales" — vocabulario burocrático de RPP/gobierno, no de un producto técnico.

**Investigación (en capas, cada una destapó la siguiente):**

1. **Capa 1 — meta-prompt sesgado:** `admin.py::generate_prompt` (el endpoint que
   arma las instrucciones que se le mandan al LLM para que redacte el System
   Prompt) tenía el checklist "obligatorio de 7 puntos" y las 3 metodologías
   (CRAFT/ASPECCT/CREA) calcadas del patrón de bots de trámites RPP/IRCEP, con
   frases como *"enumera los trámites/servicios/temas..."* hardcodeadas sin
   importar el `sector`/`topic` recibido. Corregido a vocabulario neutro al
   dominio, con instrucción explícita de derivar los temas válidos y los
   ejemplos de una `description` funcional real (campo nuevo, separado del
   nombre corto `topic`, que antes no existía y forzaba a repetir la
   descripción completa hasta 5 veces dentro del mismo meta-prompt).

2. **Capa 2 — LOV con default de tenant hardcodeado (mismo patrón que el
   incidente de `chat_service.py` del 2026-07-22 arriba):** `AdminPage.jsx`
   inicializaba los campos "Audiencia/Empresa/Sector" con los valores del
   tenant RPP (`useState('Registro Público / Catastro')`, etc.), y el
   `useEffect` de auto-selección por perfil no tenía una rama `else` — al
   crear el perfil nuevo de Centinela-AI (no catalogado en la lista de 5
   perfiles conocidos), el formulario se quedó silenciosamente con esos
   valores de RPP sin que el administrador lo notara. Corregido: sin default
   de tenant, rama `else` que resetea el LOV al cambiar a un perfil no
   catalogado.

3. **Capa 3 — la causa raíz real, más grave que las dos anteriores:** incluso
   con el meta-prompt y el LOV ya corregidos, el System Prompt generado seguía
   siendo *byte-idéntico* en estructura entre ejecuciones con temas distintos.
   Investigado con logs reales del contenedor: Groq (único proveedor con key
   válida desde el stopgap del 2026-07-22/23) tenía la cuota diaria de tokens
   agotada (`429 - Rate limit... Limit 100000, Used 99578`), y
   `SmartLLMRouter.chat()` — al no encontrar ningún proveedor disponible —
   caía silenciosamente a la plantilla determinista offline (ver
   `smart_llm_router.py:296-336`, la misma plantilla ya identificada como
   causa raíz del incidente del 2026-07-22 de arriba). **Ninguno de los 3
   "Generar" que el usuario ejecutó hoy (15:37, 16:38, 16:58) pasó realmente
   por un LLM.** Agravante nuevo: `admin.py::generate_prompt` descartaba la
   señal de fallback con `response_text, _ = await llm.chat(...)` — el panel
   nunca informaba que el "prompt generado por IA" en realidad era una
   plantilla fija. Mismo patrón de "falla silenciosa" que el incidente de LLM
   personalizado por tema documentado arriba.

4. **Capa 4 — al investigar por qué no había un segundo proveedor de
   respaldo:** el usuario aportó 2 API keys nuevas (Gemini, NVIDIA NIM) en
   `.env`, pero con nombres que el código no lee (`GEMINI_API_KEY` en vez de
   `GOOGLE_API_KEY`; `NVIDIA_API_KEY` en vez de `NVIDIA_NIM_API_KEY` — ver
   `config.py:88` y `:103`), cada una duplicada con 2 valores distintos, más
   un tercer bloque `OPENAI_API_KEY`/`OPENAI_BASE_URL`/`OPENAI_MODEL` cuyo
   endpoint (`https://integrate.api.nvidia.com/v1`), modelo
   (`meta/llama-3-71b-instruct`) y formato de key (prefijo `nvapi-`, no
   `sk-`) correspondían a NVIDIA, no a OpenAI real — confirmado con el
   usuario: era la key de NVIDIA pegada por error bajo el nombre equivocado.

**Causa raíz consolidada:** (a) meta-prompt con vocabulario de dominio
hardcodeado a RPP; (b) UI con default de tenant hardcodeado sin rama de
reseteo, mismo patrón que el incidente de `chat_service.py`; (c) fallback
determinista silencioso combinado con el descarte de su propia señal de
origen — el mismo patrón de "falla silenciosa" ya documentado dos veces en
este archivo, ahora confirmado en un tercer punto del código; (d) variables
de entorno con nombres incorrectos/duplicados/mal etiquetados que dejaban al
sistema dependiendo de un único proveedor (Groq) sin redundancia real, pese a
que el usuario ya había aportado credenciales válidas para dos más.

**Corrección aplicada:**
1. `admin.py`: meta-prompt reescrito sin vocabulario de trámite/gobierno
   hardcodeado; nuevo campo `description` (descripción funcional, separado
   del `topic` corto); `source`/`is_ai_generated` ya no se descartan y se
   devuelven al frontend.
2. `smart_llm_router.py`: plantilla de fallback offline reescrita para usar
   la `description` real (cita el texto real del administrador en vez de
   inventar "trámite/expediente") y para incluir un aviso explícito
   (`<!-- AVISO: ... PLANTILLA DETERMINISTA OFFLINE ... -->`) dentro del
   propio texto generado.
3. `AdminPage.jsx`: LOV sin default de tenant, rama `else` de reseteo,
   campo nuevo de "Descripción Funcional/Capacidades", y mensaje visible
   (`type: 'error'`, no `'success'`) cuando `is_ai_generated === false`.
4. `.env`: `GEMINI_API_KEY`→`GOOGLE_API_KEY`, `NVIDIA_API_KEY`→
   `NVIDIA_NIM_API_KEY`, duplicados eliminados, bloque OpenAI mal etiquetado
   descartado (documentado en el propio `.env` por qué). Ambas keys
   verificadas con una llamada real (list-models, sin gastar tokens de
   generación) antes de aplicarlas: **válidas las 2** — a diferencia del
   stopgap del 2026-07-22/23, donde Gemini/NVIDIA/OpenRouter habían fallado
   con errores de autenticación reales.
5. `docker compose up -d --force-recreate backend` — recreación necesaria
   porque (confirmado también en el incidente del 2026-07-22/23 de arriba)
   ni `docker restart` ni el `--reload` de uvicorn releen `.env`.

**Prevención de recurrencia:**
- El aviso visible en el panel (`is_ai_generated === false`) aplica la misma
  lección del incidente de Observabilidad del 2026-07-22: una falla de
  proveedor debe ser visible de inmediato para el administrador, no
  descubrirse por casualidad comparando dos generaciones que se ven
  sospechosamente idénticas.
- Con Groq + NVIDIA NIM + Gemini como proveedores reales simultáneos (antes
  solo Groq), la ventana en la que **cualquier** fallo/rate-limit de un solo
  proveedor tumba silenciosamente todo el sistema se reduce sustancialmente,
  aunque no desaparece (Vertex sigue sin configurar; la causa raíz de Vault
  —sin `VAULT_TOKEN` real— sigue abierta, ver R-09 en
  `docs/REGISTRO_DE_RIESGOS.md`, actualizado en esta misma fecha).
- Sigue sin existir una prueba automatizada que detecte que el meta-prompt
  de `generate_prompt` cae en vocabulario de un dominio distinto al
  `sector`/`topic` recibido — brecha abierta, candidata a `backend/tests/`.

**Evidencia de verificación:**
- Test de integración real (interceptando solo el límite externo del LLM,
  sin mockear la lógica bajo prueba) confirmando que el meta-prompt generado
  para Centinela-AI ya no contiene vocabulario de trámite y sí deriva los
  temas válidos de la `description` real.
- Logs reales del contenedor confirmando el `429` de Groq
  (`Used 99578/100000`) y las 3 ejecuciones de hoy cayendo a
  `fallback_offline`.
- Llamada real (list-models) contra Gemini y NVIDIA NIM con las 4 variantes
  de key encontradas en `.env`: **las 4 autenticaron correctamente**
  (50 modelos en Gemini, 102 en NVIDIA NIM).
- Prueba de extremo a extremo real, sin mocks, contra `SmartLLMRouter.chat()`
  con Groq forzado a estado `RATE_LIMITED`: el failover real ocurrió hacia
  `nvidia`, con una respuesta genuina del modelo (`"PRUEBA-FAILOVER-OK"`),
  no la plantilla de respaldo.
- `docker logs consulta-smart-backend` tras la recreación: `Application
  startup complete` sin errores; `settings.GOOGLE_API_KEY`/
  `settings.NVIDIA_NIM_API_KEY` confirmados presentes en el proceso real.

---

## 2026-08-14 — Caché desconectada del flujo real + expansión de proveedores (OpenRouter, Cerebras)

**Síntoma reportado por el usuario:** "está tardando en responder, ¿es por la IA? ¿si está
funcionando el caché?" — tras varias sesiones viendo timeouts/rate-limits en cascada
entre Groq/NVIDIA/Gemini.

**Hallazgo 1 — la caché híbrida (Redis + embeddings) nunca se usaba:**
`ChatService._get_cache()` existía y funcionaba, pero **ninguna otra función del
archivo la invocaba** — código muerto. Cada consulta, incluso una pregunta idéntica
repetida palabra por palabra, pagaba el costo/latencia completo de RAG+LLM. Al revisar
`cache_layer.py` para conectarla se encontró un segundo problema más serio: la clave de
caché (`_generate_cache_key`) era solo `hash(query)`, **sin aislamiento por tenant** —
de haberse conectado tal cual, la respuesta cacheada de una pregunta en el perfil `rpp`
se habría servido textualmente a la misma pregunta hecha en `centinela-ai` (o cualquier
otro tenant), sin relación de dominio alguna. `get_similar_match` tenía el mismo
problema a nivel de búsqueda por embeddings (`redis.keys("cache_consulta_rpp:*")` sin
filtro).

**Corrección aplicada:**
1. `cache_layer.py`: `_generate_cache_key`/`get_exact_match`/`get_similar_match`/
   `store_response`/`get_with_fallback` ahora reciben `namespace` (= `profile_id`) y lo
   incluyen en la clave de Redis y en el filtro de búsqueda por similitud — cada tenant
   tiene su propio espacio de caché aislado.
2. `chat_service.py::process_query`: se conecta la caché al inicio (antes de RAG+LLM) y
   al final (tras obtener una respuesta real). Deliberadamente **excluida cuando hay
   `conversation_history`** (preguntas de seguimiento) — una respuesta cacheada de una
   pregunta aislada puede ser incorrecta si en realidad dependía del contexto previo de
   la conversación.

**Hallazgo 2 — el fallback offline se filtraba al chat normal (bug introducido por un
fix anterior de este mismo día):** el cambio del 2026-08-13 que hace que
`SmartLLMRouter.chat()` degrade a la plantilla CRAFT en vez de lanzar una excepción sin
capturar (pensado para `admin.py::generate_prompt`) se aplicaba también cuando
`chat_service.py` llamaba a `llm.chat()` para una consulta real de usuario — con los 3
proveedores caídos, un usuario preguntando algo real sobre Centinela-AI recibía
literalmente el texto *"Eres el Consultor e Integrador Experto de Sistema de Atención y
Consultas..."* como si fuera la respuesta. **Corregido:** el fallback a plantilla ahora
solo se activa si `kwargs` contiene `topic` (señal exclusiva del generador de prompts
del admin); en cualquier otro caso se relanza la excepción para que
`chat_service.py` la capture con su propio manejo honesto ya existente
(`"Lo siento, ocurrió un error interno..."`).

**Expansión de redundancia de proveedores:** el usuario aportó 5 keys nuevas
(NVIDIA NIM, 3× OpenRouter, Cerebras), todas probadas con una llamada real de
list-models antes de usarse — **las 5 autenticaron correctamente** (a diferencia del
stopgap de julio, donde solo Groq funcionó de las 4 aportadas). Se agregaron
`OpenRouterProvider` y `CerebrasProvider` (API compatible con OpenAI) a
`llm_service.py`, con timeout explícito de 30s, y se conectaron a la cascada global de
`SmartLLMRouter` (`groq → cerebras → vertex → nvidia → gemini → openrouter`), además de
como `custom_provider` soportado para override por tema. Se reemplazó la key de NVIDIA
por la nueva.

**Limitación real descubierta al probar con una llamada de CHAT (no solo
list-models):** las keys de OpenRouter y Cerebras autentican pero **las cuentas no
tienen cuota utilizable para generar respuestas todavía** —
OpenRouter: `429 Rate limit exceeded: free-models-per-day... Add 10 credits to unlock
1000 free model requests per day`; Cerebras: `402 Payment required to access this
resource`. El wiring de código se confirmó correcto (failover real cayendo
correctamente hasta el último proveedor vivo en la cascada, incluido el manejo honesto
de error cuando todos fallan), pero ninguno de los dos puede servir tráfico real hasta
que el usuario agregue crédito/facturación a esas cuentas — fuera del alcance de este
agente.

**Evidencia de verificación:**
- `router.priority_order == ['groq', 'cerebras', 'vertex', 'nvidia', 'gemini', 'openrouter']`,
  `providers['cerebras']`/`providers['openrouter']` inicializados — confirmado real.
- Prueba real forzando groq/cerebras/nvidia/gemini caídos: la cadena llegó hasta
  `openrouter`, que respondió con el error real de cuota (`429`) documentado arriba —
  no un mock.
- Prueba real sin forzar nada: `source: groq`, `response: 'PRUEBA-CASCADA-REAL-OK'` —
  confirma que en ese momento (post-cambios) un usuario real sí recibió respuesta.
- **Actualización, minutos después:** al probar la caché end-to-end vía
  `chat_service.process_query()`, los 5 proveedores fallaron simultáneamente en tiempo
  real (Groq cuota, Cerebras sin crédito, NVIDIA timeout, Gemini saturado, OpenRouter
  rate-limited) — coincidencia real de mala suerte, no un artefacto de la prueba.
  Confirma en vivo el síntoma original del usuario ("está tardando, ¿es por la IA?").
- Dado que ese intento no dejó nada real que cachear, se verificó la caché de forma
  aislada contra Redis real (sin depender de que un LLM externo responda):
  `store_response(query, respuesta, namespace="centinela-ai")` →
  `get_exact_match(query, namespace="centinela-ai")` → HIT con la respuesta exacta;
  `get_exact_match(query, namespace="general")` → MISS (aislamiento real, sin fuga
  cross-tenant); `get_with_fallback()` end-to-end → HIT. Las 4 aserciones pasaron.

## 2026-08-14 (continuación) — Widget embebido pidiendo login real, timeout del cliente más corto que la cascada del servidor, e ícono/color de marca ignorados por el chat real

**Síntoma 1 (widget pidiendo login):** al embeber el widget de Centinela-AI en una
página de terceros, el panel del widget mostraba la tarjeta real de Authentik
"INICIAR SESIÓN CON CASMARTS ID" en vez de abrir un chat anónimo de invitado —
pese a que la sesión de invitado ya existía como mecanismo (`/api/v1/auth/guest`)
y se usó exitosamente al construir `widget.js` en la ronda anterior.

**Causa raíz (doble):**
1. `WidgetPage.jsx` solo invocaba `guestLogin()` si `!isAuthenticated`. El iframe del
   widget carga desde el mismo origin que el panel admin (`chat.casmart.internal`),
   así que comparte `localStorage` — si el administrador tenía sesión abierta en
   otra pestaña del panel admin, el widget heredaba ese token de admin y se saltaba
   el login de invitado, pero sin realmente completar un flujo de auth funcional
   para el contexto del iframe.
2. El interceptor de respuesta 401 global de `services/api.js` hacía
   `window.location.href = '/login'` incondicionalmente ante cualquier 401 —
   incluido dentro del iframe, secuestrando la navegación del sitio anfitrión de
   terceros hacia la pantalla de login real de Authentik.

**Corrección:** `WidgetPage.jsx` invoca `guestLogin()` siempre e incondicionalmente
al montar (sin importar `isAuthenticated`); el interceptor de `api.js` no redirige
cuando `window.self !== window.top` (contexto de iframe) — solo limpia el token
local y deja que el flujo propio del widget muestre su error, si lo hay. Contrato
formal: `[CS-013]` en `SPECS.md`.

**Síntoma 2 (chat "colgado"):** el widget se quedaba indefinidamente en "Procesando
consulta..." sin responder ni mostrar error, más allá de lo que un usuario
esperaría de una respuesta lenta.

**Causa raíz:** el timeout por-proveedor de `SmartLLMRouter.chat()`
(`asyncio.wait_for(..., timeout=45.0)`, agregado en una ronda previa para un bug
distinto de NVIDIA colgándose indefinidamente) permitía que una cascada de 2
proveedores lentos en secuencia (ej. NVIDIA + Gemini, cada uno tardando cerca de
su propio timeout interno antes de fallar) sumara hasta ~79s reales medidos en
logs — más que el timeout HTTP del cliente axios (60s). El cliente abortaba la
request y el backend seguía trabajando sin nadie escuchando la respuesta, dejando
el spinner colgado sin error visible.

**Corrección:** timeout por-proveedor reducido de 45.0s a 15.0s en
`smart_llm_router.py::chat()`, dejando margen real para que incluso una cascada de
varios proveedores lentos termine (con error honesto si corresponde) antes de que
el cliente HTTP agote su propio budget.

**Síntoma 3 (ícono/color ignorados):** el selector de íconos con nombre del panel
admin (biblioteca de 12 íconos) y el color de marca (`primary_color`) se
reflejaban correctamente en el "Probador Sandbox" de vista previa del propio
panel admin, pero el chat real (tanto en modo escritorio como dentro del widget
embebido) seguía mostrando el emoji 🤖 genérico y un header sin ningún
tratamiento de color, sin importar la configuración guardada.

**Causa raíz:** el Sandbox del admin era un mockup separado, escrito aparte, que
sí implementaba la lógica de ícono con nombre — pero `ChatInterface.jsx` (el
componente real compartido por el chat de escritorio y el widget embebido) nunca
leía `profileConfig.icon`, y su header en modo widget usaba un fondo gris plano
sin relación con `profileConfig.primary_color`. Los dos árboles de UI divergieron
en silencio porque no compartían código.

**Corrección:** extraída la biblioteca de íconos a
`frontend/src/constants/chatIcons.js` (única fuente para `AdminPage.jsx` y
`ChatInterface.jsx`); `ChatInterface.jsx` resuelve
`ICON_MAP[profileConfig.icon] || Bot` en los 3 puntos donde se muestra el ícono
del bot (header de escritorio, header del widget, avatar de estado vacío); el
header del widget rediseñado para usar `profileConfig.primary_color` de fondo con
una insignia de ícono, igualando el mockup del Sandbox. Contrato formal:
`[CS-014]` en `SPECS.md`.

**Prevención:** cuando un mockup/preview en el panel admin muestra el resultado
correcto, no asumir que el componente real usado por usuarios lo hace igual — si
son árboles de componentes separados, verificar explícitamente contra el
componente real y, de encontrarse duplicación, extraer una única fuente de
verdad compartida en vez de mantener las dos copias sincronizadas a mano.

**Evidencia de verificación:**
- `ChatInterfaceProfileIcon.test.jsx` (nuevo): perfil con `icon: 'ShieldCheck'`
  renderiza `svg.lucide-shield-check`, nunca el emoji — 1/1 pasa.
- `WidgetPageGuestSession.test.jsx` (nuevo): `guestLogin()` se invoca siempre
  aunque `isAuthenticated` ya sea `true` por un token viejo; si `guestLogin()`
  falla, se muestra el error del widget, nunca la pantalla de login real — 2/2
  pasan.
- `ChatInterfaceWidgetTheming.test.jsx` (existente, 3 pruebas): confirmó que el
  rediseño del header agregó una segunda instancia de `svg.lucide-bot` al DOM
  (insignia del header, además del avatar de estado vacío), volviendo ambiguo el
  selector `querySelector('svg.lucide-bot')` original — corregido acotándolo a
  `.w-16.h-16 svg.lucide-bot` (clase distintiva del avatar real bajo prueba).
  3/3 pasan tras la corrección.
- Las 3 suites juntas: `Test Files 3 passed (3) / Tests 6 passed (6)`.

## 2026-08-14 (continuación 2) — Reporte en vivo del usuario: 3 bugs reales encadenados en una sola consulta, y reversión de OpenRouter/Cerebras

**Síntoma reportado por el usuario (con captura de pantalla):** desde el widget embebido de Centinela-AI en producción, envió "¿Cómo calcula Centinela el Centinela Risk Score (CRS)?"; el mensaje se limpió del input pero la UI quedó colgada indefinidamente en "Procesando consulta...".

**Investigación (logs reales de `consulta-smart-backend`, no suposiciones):**

1. **`knowledge_base.py::search_in_knowledge_text_async`:** el filtro de stopwords (`{"¿", "?", ...}`) solo eliminaba tokens que coincidían EXACTAMENTE con esos símbolos — no separaba puntuación pegada a una palabra (`"¿cómo"`, `"(crs)?"`, producto de `.split()` por espacios). Esos tokens llegaban intactos al patrón OR de `to_tsquery`, que interpreta paréntesis como sintaxis de agrupación, no como texto: `PostgresSyntaxError: syntax error in tsquery: "¿cómo | calcula | centinela | centinela | risk | score | (crs)?"`.

2. **`chat_service.py::process_query`:** el manejador de esa excepción en `knowledge_base.py` hace `await session.rollback()` (correcto y necesario para poder seguir usando la conexión). Efecto secundario real de `AsyncSession`: el rollback expira TODOS los objetos ya cargados en esa sesión, incluido `profile` (cargado varios segundos antes, al inicio del turno). El acceso posterior a `profile.llm_provider` (para resolver el motor LLM personalizado del tema) disparó un intento de recarga perezosa fuera de un contexto async válido: `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called`. El manejador de excepción general de `process_query` capturó esto y devolvió "Lo siento, ocurrió un error interno..." con `provider: Sistema de Emergencia` — un error confuso que oculta la causa real (la sintaxis rota de `to_tsquery`).

3. **`ChatInterface.jsx::sendMessage`:** independientemente de si el backend respondía bien o mal, el primer mensaje de una sesión de chat NUEVA (el caso típico del widget: cada visita de invitado empieza sin `currentSessionId`) nunca aplicaba la respuesta ni apagaba `loading`. `currentSessionId` es un cierre de React (`useState`) capturado en el render que invocó `sendMessage`; `setCurrentSessionId(nuevoId)`, llamado dentro de la misma ejecución, no se refleja en ese cierre hasta el siguiente render. Las comprobaciones de después (`activeSessionId === currentSessionId`, pensadas para descartar una respuesta si el usuario cambió de sesión mientras la petición estaba en curso) comparaban el id nuevo contra el `null` capturado en el cierre — siempre falso para una sesión recién creada. Este es el bug que explica el síntoma EXACTO reportado por el usuario: la UI se queda colgada sin importar el resultado del backend.

**Corrección:**
1. Cada palabra se limpia con `re.sub(r"[^\w]", "", w, flags=re.UNICODE)` (conserva acentos/ñ) antes de compararla con stopwords y unirla al patrón de `to_tsquery`.
2. `llm_provider`/`llm_model`/`custom_api_key`/`custom_base_url` se capturan como variables planas de Python inmediatamente después de cargar `profile`, antes de la búsqueda RAG que puede hacer rollback.
3. Bandera local `isNewSession` en `sendMessage`; las comprobaciones posteriores usan `isNewSession || activeSessionId === currentSessionId`.

**Evidencia de verificación:**
- `POST /api/v1/chat/query` con la consulta exacta reportada, vía un guest token real obtenido de `/api/v1/auth/guest`: respuesta grounded citando `BASE_CONOCIMIENTO_CHATBOT.md`, `provider: gemini (RAG)`, sin error.
- `docker logs consulta-smart-backend` para esa misma request: sin `PostgresSyntaxError` ni `MissingGreenlet`, solo las queries SQL normales.
- Nueva prueba de regresión de frontend `tests/components/ChatInterfaceNewSessionSend.test.jsx`: reproduce el envío del primer mensaje de una sesión sin `currentSessionId` previo, mockeando `createSession`+`sendQuery`, y confirma que `addMessage` (con la respuesta del asistente) y `setLoading(false)` se invocan — 1/1 pasa. Corrida junto con las 3 suites de la sesión anterior: `Test Files 4 passed (4) / Tests 7 passed (7)`.

**Nota aparte (no un bug):** una captura intermedia del usuario mostró "Error al enviar mensaje: Request aborted". Confirmado por timestamp que fue colateral de que el agente estuviera editando `ChatInterface.jsx` en ese momento — Vite HMR recargó el módulo (`docker logs consulta-smart-frontend`: "hmr update /src/components/ChatInterface.jsx" a las 15:31:23) justo cuando la petición del usuario estaba en curso, abortándola client-side. No requirió corrección de código.

**Lección de diagnóstico:** un `session.rollback()` correcto para recuperar una transacción abortada tiene un efecto secundario real con `AsyncSession` — expira objetos ya cargados, y accederlos después fuera de un `await` directo falla con un error (`MissingGreenlet`) que no menciona la causa original. Cuando un error de infraestructura async parece "sin relación" con el síntoma reportado, conviene revisar el log completo de la request de principio a fin, no solo la última excepción — la causa raíz suele estar unas líneas más arriba.

## 2026-08-14 (continuación 2) — Reversión de OpenRouter/Cerebras

**Decisión del usuario:** "elimina openroute/cerebras" — tras confirmar en la sesión anterior que ambas cuentas tenían credenciales válidas pero sin cuota utilizable (OpenRouter `429 free-models-per-day`, Cerebras `402 Payment required`), el usuario decidió no mantener el código de integración mientras no tengan capacidad real de servir tráfico.

**Cambios:** removidos por completo de `smart_llm_router.py` (dict `self.providers`, `_init_custom_provider`, `_initialize_providers`, docstrings de prioridad), `llm_service.py` (clases `OpenRouterProvider`/`CerebrasProvider` eliminadas enteras) y `config.py` (settings `OPENROUTER_*`/`CEREBRAS_*` eliminados). La cascada global vuelve a 4 proveedores: Groq → Vertex → NVIDIA → Gemini. El timeout por-proveedor de 15s (reducido de 45s en la sesión anterior, para la cascada de 6) se mantuvo sin cambios — sigue siendo un valor razonable para la cascada de 4.

**Evidencia de verificación:** backend recargado sin errores de import (`docker logs consulta-smart-backend`, `Application startup complete`); `grep -rin "openrouter|cerebras" backend/` sin resultados tras el cambio; prueba real de chat (saludo simple) tras el cambio responde correctamente (`provider: Sistema Local (Saludo)`, sin errores).

## 2026-08-14 (continuación 3) — El Blindaje anti-alucinación duplicaba el tiempo de espera en cascadas degradadas

**Síntoma reportado por el usuario:** tras confirmar que los 3 bugs anteriores ya estaban corregidos ("ya contestó... pero tardó"), preguntas reales seguían tomando ~50s en responder incluso cuando un proveedor SÍ lograba generar una respuesta útil.

**Investigación (logs reales):** la respuesta principal de una consulta ("¿Qué diferencia hay entre EDR y XDR?") tardó ~22s en resolverse (Groq 429 por cuota, NVIDIA timeout 15s, Gemini exitoso). Pero el log mostraba un SEGUNDO ciclo completo de fallos inmediatamente después: "🛡️ Iniciando Blindaje" → NVIDIA timeout otra vez (15s) → Gemini timeout (15s) → "Error en blindaje". El paso de Blindaje (`chat_service.py::_verify_grounding`, una verificación anti-alucinación que compara la respuesta contra los documentos RAG usando un segundo llamado al LLM) hace su propia llamada independiente a `_get_best_provider()` del router, sin ningún conocimiento de que NVIDIA acababa de fallar por timeout 6 segundos antes en el mismo turno — el router solo marca un proveedor como `DEGRADED` tras 4 timeouts acumulados (`error_count > 3`), no tras el primero, así que lo reintentó de inmediato y volvió a fallar.

**Causa raíz:** dos llamadas independientes al mismo router compartido (`self._llm`, singleton por `ChatService`) sin que la segunda tenga forma barata de saber "el proveedor X acaba de fallar hace unos segundos, no lo intentes de nuevo todavía" más allá del umbral de 4 fallos acumulados. El resultado: cuando la cascada está degradada, CUALQUIER llamada adicional al router (como el Blindaje) paga el mismo costo completo de reintentos que la llamada principal, duplicando el tiempo total — para una verificación que, además, ya está diseñada para fallar "abierto" (usar la respuesta original) si no puede completarse.

**Corrección:** se acotó el Blindaje a un presupuesto de tiempo total de 8 segundos (`asyncio.wait_for` alrededor de la llamada a `_verify_grounding` en `process_query`), en vez de dejar que agote su propia cascada completa de proveedores. Si se excede, se usa la respuesta original sin verificar — mismo comportamiento de fallback que ya tenía internamente, solo que ahora con un límite de tiempo explícito en vez de implícito (el tiempo que tome fallar en N proveedores).

**Prevención de recurrencia:** cualquier llamada adicional al router LLM que no sea la generación de la respuesta principal de un turno (verificaciones, reescrituras, resúmenes, etc.) debe tener su propio presupuesto de tiempo acotado y explícito, independiente de los timeouts internos del router — un paso "best effort" nunca debería poder duplicar el tiempo de espera de un usuario real.

**Evidencia de verificación:** prueba real con la consulta del CRS tras el fix — el log muestra `⏱️ Blindaje excedió 8s, se usa la respuesta original sin verificar` exactamente a los 8s de iniciado el paso, y el turno completo terminó en 33s (vs. los ~53s observados minutos antes con el mismo estado de proveedores degradados, antes del fix).

## 2026-08-14 (continuación 3) — Deduplicación de documentos RAG por hash de contenido

**Contexto:** el usuario reportó sospecha de un documento fuente duplicado para Centinela-AI y pidió prevención real por hash de contenido, no solo por nombre de archivo.

**Investigación:** verificado contra Postgres real (`SELECT` directo, no supuesto) que **no existía duplicado activo en ese momento** — 1 solo documento (`BASE_CONOCIMIENTO_CHATBOT.md`) bajo `category='centinela-ai'`, 112 chunks todos con texto distinto entre sí. La sospecha del usuario no correspondía al estado actual de la BD (posiblemente residual de la duplicación real que sí ocurrió y se corrigió en una sesión anterior — ver incidente de `DocumentUpload.jsx` del mismo día). La petición de agregar prevención real hacia el futuro seguía siendo válida y se implementó de todos modos.

**Implementación:** columna nueva `documents.content_hash` (SHA-256 hex del contenido CRUDO del archivo, calculado antes de parsear/chunkear/embeber) + índice; `admin.py::upload_chatbot_document` rechaza con `409 Conflict` si ya existe un documento activo con el mismo hash **en el mismo tenant** (`category`) — subir el mismo archivo a propósito a dos temas distintos sigue siendo válido y no se bloquea.

**Limitación conocida y honesta:** el documento ya existente no tiene `content_hash` retroactivo, porque solo se conserva el texto ya extraído/chunkeado en BD, no los bytes originales de la subida — no es posible recalcular el hash exacto que habría tenido el archivo original sin volver a subirlo. La protección aplica desde ahora en adelante, no retroactivamente sobre lo ya indexado.

**Evidencia de verificación:** script real ejecutado dentro del contenedor backend contra la base de datos real (sin mocks): (1) hash de un contenido de prueba → MISS correcto (sin duplicado); (2) tras insertar un documento de prueba con ese hash bajo `category='centinela-ai'` → HIT correcto, mismo documento encontrado; (3) mismo hash pero `category='rpp'` → MISS correcto, confirmando aislamiento por tenant; (4) limpieza — documento de prueba eliminado, `count(*) = 0` confirmado después. Columna e índice reales verificados en Postgres vía `\d documents`.

## 2026-08-14 (continuación 4) — El mensaje del usuario desaparecía en CADA pregunta (tercer bug real, distinto a los dos ya corregidos)

**Síntoma reportado por el usuario:** "por qué cada que hago una pregunta sigue desapareciendo del chat? y se queda procesando consulta? no deberían ocultarse/desaparecer las preguntas, aunque no reaccione el LLM" — reportado DESPUÉS de que los 2 bugs anteriores (cierre obsoleto de React, Blindaje duplicando tiempo de espera) ya estaban corregidos y verificados funcionando.

**Investigación:** `docker logs -t consulta-smart-backend` mostró el patrón de tráfico exacto: `POST /api/v1/chat/sessions` (18:21:18.13) → `GET /api/v1/chat/sessions/{id}` apenas **700ms después** (18:21:18.84) → `POST /api/v1/chat/query` que no completó hasta 31 segundos más tarde (18:21:49.40). El `GET` de lectura de historial se disparaba casi inmediatamente después de crear la sesión, mucho antes de que la petición de envío del mensaje siquiera terminara.

**Causa raíz:** `ChatInterface.jsx` tiene `useEffect(() => {...fetchHistory...}, [currentSessionId])`, pensado para recargar los mensajes cuando el usuario cambia a una conversación YA EXISTENTE desde la barra lateral. Pero este mismo efecto se dispara también cuando `currentSessionId` cambia porque `sendMessage` acaba de crear una sesión NUEVA para el mensaje que se está enviando en ese momento. En ese instante el backend todavía no tiene el mensaje del usuario guardado — `chatAPI.getSession()` devuelve la sesión sin mensajes, y el efecto llama `clearMessages()`, borrando la burbuja del mensaje del usuario que se había agregado de forma optimista segundos antes con `addMessage(userMessage)`.

Como cada interacción del usuario con el widget de invitado crea una sesión nueva (no hay sesión persistida entre aperturas del widget), este bug se disparaba en **cada** pregunta que el usuario probaba, no solo "la primera vez en general" — de ahí el "cada que hago una pregunta" del reporte.

**Corrección:** `skipNextHistoryFetchRef` (`useRef`, no state) se marca `true` justo antes de `setCurrentSessionId(activeSessionId)` en la rama de creación de sesión nueva de `sendMessage`; el efecto de carga de historial lo consume (y resetea) la primera vez que se dispara tras esa creación, sin ejecutar `fetchHistory`. Cualquier cambio posterior de `currentSessionId` (cambio real de conversación) sigue disparando la carga normalmente.

**Prevención de recurrencia:** un `useEffect` keyed en un id que representa dos situaciones distintas ("cambié de conversación" vs. "acabo de crear una para este envío") necesita distinguir explícitamente esos dos casos — no asumir que todo cambio del id significa lo mismo.

**Evidencia de verificación:** nueva prueba de regresión (`ChatInterfaceNewSessionSend.test.jsx`) mockeando `chatAPI.getSession` para devolver `{ messages: [] }` (reproduciendo la carrera real): confirma que `clearMessages`/`setMessages` nunca se invocan y `chatAPI.getSession` nunca se llama tras el primer mensaje de una sesión nueva. **Verificación adicional de que la prueba detecta el bug de verdad:** se revirtió temporalmente la línea del fix (`skipNextHistoryFetchRef.current = true`), se re-corrió la prueba y falló exactamente como se esperaba (`setMessages` llamado 1 vez con `[]`); se restauró el fix y volvió a pasar. Suite combinada de 6 archivos relacionados: `Test Files 6 passed (6) / Tests 28 passed (28)`.
