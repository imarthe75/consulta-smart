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
