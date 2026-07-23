# Registro de Riesgos — ConsultaSmart

Práctica CMMI Nivel 3 — Gestión de Riesgos (RSKM): identificación proactiva y
seguimiento de riesgos conocidos, no solo reacción a incidentes. Ver
`docs/ESTANDAR_CMMI_UNIVERSAL.md` §2.5.

**Cómo usar este documento:** cada riesgo tiene probabilidad/impacto (Alto/Medio/Bajo),
estado, disparador de revisión (qué evento debería hacer que alguien vuelva a mirar
este riesgo) y dueño. Se revisa este registro completo cuando: (a) se cierra o abre
un riesgo, (b) ocurre un incidente relacionado, (c) al menos una vez por trimestre.
Los riesgos aquí provienen de auditorías reales, no de especulación — cada uno cita
su evidencia en `MANUAL_TECNICO_DESARROLLADOR.md`.

**Última revisión:** 2026-07-22.

---

## Riesgos Abiertos

| ID | Riesgo | Prob. | Impacto | Estado | Mitigación / Plan | Disparador de revisión | Evidencia |
|---|---|---|---|---|---|---|---|
| R-09 | **[Activo ahora mismo]** Vault (`10.4.3.208:8200`) no autentica (`client.is_authenticated() == False` con el `VAULT_TOKEN` real del contenedor) — ninguna API key de LLM (Groq/Gemini/Vertex/NVIDIA) llega al backend. `SmartLLMRouter` no tiene ningún proveedor activo; **toda respuesta de chat es el texto de respaldo genérico** (ignora la pregunta real y el contexto RAG recuperado), sin ningún error visible para el usuario ni, hasta esta corrección, para el administrador. Confirmado con evidencia real en los logs de producción: 3+ respuestas reales de las últimas horas, todas con el mismo texto exacto de plantilla. | Alta (ya ocurriendo) | **Crítico** | Abierto — requiere acción operativa fuera del alcance de este agente (acceso a Vault) | Verificar/rotar el `VAULT_TOKEN` del contenedor `consulta-smart-backend` contra el Vault real; como alternativa de corto plazo, definir `GROQ_API_KEY`/`GOOGLE_API_KEY` directamente como variables de entorno en `docker-compose.yml` mientras se resuelve Vault. Se agregó una alerta visible en el panel de Observabilidad (`no_llm_provider_configured`) para que este estado nunca vuelva a pasar desapercibido. | Inmediato — afecta la funcionalidad principal del producto en este momento. | `docs/BITACORA_ANALISIS_CAUSAL.md`, incidente 2026-07-22 (reportado por el usuario vía "todos los proveedores deshabilitados") |
| R-01 | Verificación TLS deshabilitada (`ssl.CERT_NONE`) al validar el JWKS de Authentik — expone a MITM dentro de la red interna. | Baja | Alto | Abierto, aceptado conscientemente | Instalar el certificado real de la CA interna de `auth.casmart.internal` en el trust store del contenedor y remover el bypass. Requiere acceso al certificado real, no disponible en el entorno de auditoría. | Si se rota/reemite el certificado de `auth.casmart.internal`, o si se detecta tráfico interno sospechoso hacia Authentik. | `MANUAL_TECNICO_DESARROLLADOR.md` §8, SEC-02 |
| R-02 | `ChatbotProfile`/`Document.category` no tienen columna owner/tenant — un admin de cualquier "tenant" puede editar el tema de cualquier otro. | Media | Alto (si el modelo de negocio cambia) | Abierto — es una decisión de producto, no un bug | Si en el futuro se requieren administradores *por tenant* (no un solo equipo central), rediseñar el esquema con `owner_id` real y scoping de autorización. Hoy el modelo real es "un equipo administra todos los tenants", consistente con `require_admin` global. | Si se incorpora un cliente/dependencia que exige administrar solo su propio tema sin ver los demás. | `MANUAL_TECNICO_DESARROLLADOR.md` §8, BOLA-01 |
| R-03 | Documento indexado con embeddings fallidos queda marcado "indexed" — riesgo mitigado con salud de indexado, pero la causa (fallo silencioso de embedding) sigue sin resolverse en el momento del upload inicial (`upload_chatbot_document`). | Baja | Bajo | Parcialmente mitigado | El indicador de salud + botón "Reintentar" (§14.1 del manual técnico) le da al admin visibilidad y remedio manual. Pendiente: decidir si el upload debería reintentar automáticamente antes de marcar "indexed". | Si se detecta un patrón recurrente de documentos con salud baja tras la carga inicial. | `MANUAL_TECNICO_DESARROLLADOR.md` §5, RAG-01 |
| R-04 | `perf_test` router expuesto sin ninguna autenticación. | Baja | Medio | Abierto | Evaluar si debe exponerse solo en `APP_ENV=development`, o requerir `require_admin` igual que el resto de rutas administrativas. | Antes de cualquier despliegue a un entorno con `APP_ENV=production`. | `MANUAL_TECNICO_DESARROLLADOR.md` §8, INFO-01 |
| R-05 | No existe prueba automatizada que hubiera detectado el bug de `SmartLLMRouter` (constructor con firma incompatible) antes de producción. | Media | Medio | Abierto | Agregar prueba de integración en `backend/tests/` que construya `SmartLLMRouter` con cada `custom_provider` soportado. | Antes de la próxima modificación a `smart_llm_router.py` o a la firma de `SmartLLMRouter.__init__`. | `docs/BITACORA_ANALISIS_CAUSAL.md`, incidente 2026-07-22 |
| R-07 | Rate limiting en memoria por-proceso (`app/core/rate_limit.py`) — si el despliegue real corre con >1 worker/réplica, el límite efectivo se multiplica por el número de procesos. | Media | Bajo | Abierto, documentado | Migrar a un backend compartido (Redis `INCR`+`EXPIRE`) si se confirma que el despliegue real usa múltiples workers. | Si se cambia la configuración de despliegue de 1 a >1 worker de Uvicorn/Gunicorn. | `MANUAL_TECNICO_DESARROLLADOR.md` §6 |
| R-08 | Credenciales del widget (`WIDGET_PASSWORD`) y otros secretos con fallback hardcodeado quedaron expuestos en el historial de git antes de moverse a configuración. | Media | Alto | Abierto — pendiente operativo | Rotar la contraseña real en la base de datos y en Vault; el valor movido a `.env`/Vault en código ya no es el riesgo — el riesgo es que el valor **anterior** siga siendo válido en algún sistema real. | Inmediato — no depende de ningún evento futuro, es una tarea operativa pendiente. | `MANUAL_TECNICO_DESARROLLADOR.md` §8, AUTH-03 |

---

## Riesgos Cerrados (histórico)

| ID | Riesgo | Fecha de cierre | Cómo se cerró |
|---|---|---|---|
| R-C01 | 7 endpoints de `admin.py` sin ninguna autenticación. | 2026-07-22 | `require_admin` agregado a los 7. Ver AUTH-02. |
| R-C02 | Backdoor de escalación de privilegios por substring de email/username. | 2026-07-22 | Eliminado en backend y frontend; reemplazado por `GET /auth/me`. Ver AUTH-01. |
| R-C03 | Fuga de datos: usuario sin documentos propios veía TODOS los documentos del sistema. | 2026-07-22 | Corregido en `documents.py::list_documents`. Ver BOLA-02. |
| R-C04 | Sin rate limiting en ningún endpoint. | 2026-07-22 | `app/core/rate_limit.py` agregado (ver R-07 para la limitación conocida de esta mitigación). |
| R-C05 | `chatbot_profiles` sin historial de cambios — causó el incidente del tema "general" corrupto sin forma de revertirlo. | 2026-07-22 (noche) | `chatbot_profile_audit_log` + restauración a un clic. Ver CM en `ESTANDAR_CMMI_UNIVERSAL.md`. |
| R-C06 | `custom_api_key` de LLM personalizado por tema en texto plano en la base de datos. | 2026-07-22 | Cifrado con Fernet (`app/core/crypto.py`). |
| R-C07 | LLM personalizado por tema completamente no-funcional (bug de integración silencioso). | 2026-07-22 | `SmartLLMRouter` corregido para aceptar `custom_provider`/`custom_api_key`/`custom_model`. |
| R-C08 | No existían skills de generación estandarizada (servicios/componentes) para el stack React + FastAPI. | 2026-07-22 (noche) | Creados `docs/skills/generacion-servicios-fastapi/SKILL.md` y `docs/skills/generacion-componentes-react/SKILL.md`, cada regla extraída de un bug/hallazgo real de esta sesión. |
| R-C09 | Panel de Observabilidad mostraba una fila conflada "GCP Vertex AI / Gemini" (chequeaba solo `GCP_PROJECT_ID`, ignorando que Gemini real usa `GOOGLE_API_KEY`) y una fila fantasma "Ollama / Local LLM" sin ningún `OllamaProvider` real en el código. | 2026-07-22 (madrugada) | Separado en 4 filas reales (Vertex/NVIDIA/Groq/Gemini) coincidiendo exactamente con `SmartLLMRouter._initialize_providers()`; fila de Ollama eliminada. Ver R-09 para el hallazgo crítico relacionado que esto ayudó a descubrir. |

---

## Procedencia

Los riesgos abiertos R-01 a R-08 provienen directamente de los hallazgos documentados
en `MANUAL_TECNICO_DESARROLLADOR.md` §8 y `docs/BITACORA_ANALISIS_CAUSAL.md` —
este documento los consolida en un solo lugar con probabilidad/impacto/plan
explícitos (antes vivían dispersos en la narrativa del manual técnico), práctica
CMMI RSKM formal (`docs/ESTANDAR_CMMI_UNIVERSAL.md` §2.5).
