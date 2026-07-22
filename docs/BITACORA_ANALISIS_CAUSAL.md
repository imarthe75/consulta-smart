# Bitácora de Análisis Causal (CAR) — ConsultaSmart

Práctica CMMI Nivel 5 — Análisis Causal y Resolución (CAR): cuando algo falla, se
documenta la causa raíz y la acción para prevenir su recurrencia, no solo el
síntoma corregido. Ver `docs/ESTANDAR_CMMI_UNIVERSAL.md` §4.1.

**Formato de entrada:** Fecha · Síntoma · Causa raíz · Corrección aplicada ·
Prevención de recurrencia · Evidencia de verificación.

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
