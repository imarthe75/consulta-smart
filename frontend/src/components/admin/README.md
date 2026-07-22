# Módulo: Components/Admin (Paneles del panel de administración)

**Propósito:** Componentes especializados consumidos por `pages/AdminPage.jsx` — `PromptRegressionPanel.jsx` (batería de regresión de System Prompts por tema), `LLMObservabilityPanel.jsx` (observabilidad del enrutador LLM) y `ProfileAuditLogPanel.jsx` (bitácora de cambios y restauración de un tema — CMMI CM).
**Dependencias Clave:** `services/api.js`, endpoints `admin/chatbot/profiles/{id}/test-cases`, `run-regression`, `admin/stats/llm-router`, `admin/chatbot/profiles/{id}/audit-log`, `admin/chatbot/profiles/{id}/restore/{audit_log_id}`.

---

## Bitácora de Cambios Significativos (Changelog Local)

_Formato:_ `- **[YYYY-MM-DD]** ([Nombre del desarrollador]): [Descripción breve del cambio estructural]`

- **[2026-07-22]** (Google Antigravity): creación inicial de ambos paneles, completos y funcionales contra el backend real.
- **[2026-07-22 tarde]** (Claude, revisión): **ninguno de los dos componentes estaba importado por ningún archivo del proyecto** (confirmado por grep sobre todo `frontend/src`) — el backend funcionaba, pero el administrador no tenía forma de llegar a estas pantallas. Se conectaron en `pages/AdminPage.jsx` (ver README de `pages/`). De paso, en `PromptRegressionPanel.jsx`: se limpió `k.strip ? k.strip() : k.trim()` (sintaxis de Python colada en JS — inofensiva porque `.strip` no existe en `String.prototype`, pero confusa) a simplemente `k.trim()`, y se agregó `window.confirm` antes de `handleDeleteTestCase` (antes eliminaba sin confirmación, inconsistente con el resto del panel).
- **[2026-07-22 noche]** (Claude, práctica CMMI CM tras incidente real): nuevo `ProfileAuditLogPanel.jsx` — lista el historial de cambios del tema activo con botón "Restaurar" por entrada (confirmación explícita antes de sobreescribir). Se agregó después de que el tema `general` se corrompiera sin forma de revertirlo — ver `docs/BITACORA_ANALISIS_CAUSAL.md`. Conectado en `AdminPage.jsx` junto a `PromptRegressionPanel`, con `onRestored={fetchData}` para refrescar la configuración en pantalla tras una restauración.
