# Módulo: Pages (Vistas principales de ConsultaSmart)

**Propósito:** Páginas ruteadas de la SPA — `AdminPage.jsx` (panel de administración: perfiles/temas de chatbot, generador de prompts CRAFT/CREA/ASPECCT, gestión de usuarios y roles, sandbox), `ChatPage.jsx`, `DocumentsPage.jsx`, `WidgetIntegrationPage.jsx`, `LoginPage.jsx`, `ResultsPage.jsx`, `DocumentationPage.jsx`, `WidgetPage.jsx`.
**Dependencias Clave:** `services/api.js`, `stores/authStore.js`, `stores/chatStore.js`, `stores/documentStore.js`, `components/ChatInterface.jsx`.

---

## Bitácora de Cambios Significativos (Changelog Local)

_Formato:_ `- **[YYYY-MM-DD]** ([Nombre del desarrollador]): [Descripción breve del cambio estructural]`

- **[2026-07-22]** (Claude / auditoría de seguridad): `AdminPage.jsx::handleUpdateUserRole` — se agregó confirmación explícita (`window.confirm`, mismo mecanismo ya usado en `handleDeleteProfile`) antes de otorgar o revocar el rol de administrador de un usuario. Antes el botón "Hacer Admin" ejecutaba la escalación de privilegios sin ningún paso de confirmación.
- **[2026-07-22 tarde]** (Google Antigravity): `AdminPage.jsx` agregó banner unificado (`ModuleBanner`), campos de LLM personalizado por tema (`llm_provider`/`llm_model`/`custom_api_key`) en Parámetros del tema, y `DocumentationPage.jsx`/`ResultsPage.jsx`/`WidgetIntegrationPage.jsx` se reescribieron con contenido y estructura de pestañas ampliados.
- **[2026-07-22 tarde]** (Claude, revisión): `components/admin/PromptRegressionPanel.jsx` y `components/admin/LLMObservabilityPanel.jsx` existían completos y funcionales pero **no estaban importados por ningún archivo del proyecto** (confirmado por grep). Se conectaron en `AdminPage.jsx`: `LLMObservabilityPanel` como tercera pestaña "Observabilidad", `PromptRegressionPanel` embebido bajo el panel de configuración del tema activo. Ver README de `components/admin/`.
- **[2026-07-22 tarde]** (Claude, revisión): corregidos en `DocumentationPage.jsx` dos ejemplos de payload de API que no coincidían con los DTOs reales del backend (`ChatQueryDTO.message` documentado como `query`, con un campo `documents` inexistente; `FeedbackRequest.comment` documentado como `text`) y agregadas las secciones 1.4/1.5 (Regresión de Prompts, Observabilidad) que faltaban en la pestaña de Personalización de Chatbots, ahora que ambos paneles son alcanzables desde la UI.
- **[2026-07-22 noche]** (Claude): corregido un bug real de layout — el sandbox flotante (`sticky top-6`) de `AdminPage.jsx` dejaba de "flotar" al scrollear. Causa raíz: un `overflow-y-auto` duplicado en el `<div>` raíz de la página (además del que ya aplica `App.jsx` en `<main>`) rompía el contenedor de referencia de `position: sticky`. Se quitó el `overflow-y-auto` redundante en `AdminPage.jsx` y, por consistencia, también en `DocumentsPage.jsx`, `DocumentationPage.jsx`, `ResultsPage.jsx` y `WidgetIntegrationPage.jsx` (ninguna de esas otras tenía un elemento `sticky` hoy, pero el mismo bug las habría afectado si algún día lo tuvieran).
- **[2026-07-22 noche]** (Claude, práctica CMMI CM tras incidente real): `AdminPage.jsx` conecta `ProfileAuditLogPanel` (historial de cambios + restauración del tema activo) — ver README de `components/admin/` y `docs/BITACORA_ANALISIS_CAUSAL.md`. El tema `general` ahora es de solo lectura (la UI redirige automáticamente a "Guardar como nuevo tema" si se detecta `config.id === 'general'` en `handleSaveConfig`).

### Deuda técnica identificada (no resuelta en esta ronda)

- `AdminPage.jsx` define `handleUploadDocument`, `handleDeleteDocument`, `handleToggleDocument` y `handleDocumentCategoryChange` (gestión de documentos RAG) pero ningún elemento del JSX los invoca — la gestión real de documentos ocurre en `DocumentsPage.jsx` vía `components/DocumentUpload.jsx`. Candidato a limpieza de código muerto en una futura pasada, una vez confirmado que ninguna vista pendiente los necesita.
