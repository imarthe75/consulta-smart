# Módulo: Stores (Zustand)

**Propósito:** Estado global del cliente — sesión/autenticación (`authStore.js`), sesiones y mensajes de chat (`chatStore.js`), documentos (`documentStore.js`).
**Dependencias Clave:** `zustand`, `react-oidc-context` (perfil OIDC de Authentik consumido en `App.jsx`), `services/api.js`.

---

## Bitácora de Cambios Significativos (Changelog Local)

_Formato:_ `- **[YYYY-MM-DD]** ([Nombre del desarrollador]): [Descripción breve del cambio estructural]`

- **[2026-07-22]** (Claude / auditoría de seguridad): `authStore.login()` ya no asigna el rol `admin` por coincidencia de substring (`"israelm"`) en el email/username/nombre del perfil OIDC — ese mismo backdoor existía duplicado en el backend (`auth_utils.py`, ver README de `backend/app/core/`) y fue eliminado en ambos lados. Ahora `login()` asigna un rol provisional `'user'` y resuelve el rol real de forma asíncrona contra el nuevo endpoint `GET /auth/me` (fuente de verdad: tabla `users`); si la resolución falla, se conserva `'user'` (fail-closed, nunca se asume admin por defecto).
- **[2026-07-22]** (Claude / auditoría de seguridad): se agregó `authAPI.me()` en `services/api.js` como soporte de lo anterior.
