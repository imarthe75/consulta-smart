# Guía de Troubleshooting: Logout en Authentik para ConsultaRPP

## Problema
Los usuarios no pueden cerrar sesión correctamente en ConsultaRPP (`/consultarpp/`). Después de hacer logout, la app no redirige a la página de inicio sino que muestra la pantalla `default invalidation flow` de Authentik.

## Causa Raíz
El OAuth2 provider `consulta-smart` en Authentik está usando el `default-invalidation-flow` que no está configurado para redirigir al `post_logout_redirect_uri`.

## Solución

### Paso 1: Aplicar la configuración de logout flow personalizado

Ejecuta el script que crea el flow personalizado para consulta-smart:

```bash
cd /home/ia/ecosistema-casmarts/core-casmarts

# Opción A: Si tienes acceso a Django en el contenedor de Authentik
docker exec casmarts-core-authentik-server python manage.py shell < setup_consulta_smart_logout_flow.py

# Opción B: Si ejecutas desde el host con acceso directo
python setup_consulta_smart_logout_flow.py
```

**Resultado esperado:**
```
✓ Created flow: consulta-smart-invalidation-flow
✓ Updated OAuth2 provider 'consulta-smart-provider' to use invalidation flow

✓ Logout flow setup complete!
  - Flow slug: consulta-smart-invalidation-flow
  - Flow designation: invalidation
  - Provider: Consulta Smart Provider

  Flow behavior:
    • Users will be logged out from Authentik
    • post_logout_redirect_uri parameter will be respected
    • Redirect will happen to the post_logout_redirect_uri value
```

### Paso 2: Verificar manualmente en Authentik Admin

Si prefieres verificar/configurar manualmente:

1. **Accede a Authentik Admin:**
   - URL: `https://auth.casmart.internal/if/admin/`
   - Usuario: `akadmin`

2. **Ve a Flows & Prompts → Flows**

3. **Verifica que existe el flow `default-invalidation-flow`:**
   - Debe tener `Designation: invalidation`
   - Debe tener al menos una etapa que maneje el logout

4. **Ve a Applications → Providers → OAuth2**

5. **Selecciona "Consulta Smart Provider":**
   - Verifica que en `Invalidation flow` esté seleccionado el flow correcto
   - Debe ser `consulta-smart-invalidation-flow` (si corriste el script) o `default-invalidation-flow`

6. **En Redirect URIs, verifica que estén:**
   ```
   https://consulta.casmart.internal/
   https://consulta.casmart.internal
   http://auth.casmart.internal/
   ```

### Paso 3: Verificar configuración del cliente

En Authentik Admin → Applications → Applications, verifica la app `Consulta Smart`:

- **Name:** Consulta Smart
- **Slug:** consulta-smart
- **Provider:** Consulta Smart Provider
- **Meta Launch URL:** `https://consulta.casmart.internal/`

### Paso 4: Prueba el logout

1. Accede a `https://consulta.casmart.internal/`
2. Inicia sesión normalmente
3. Abre la consola del navegador (F12 → Console)
4. Haz logout y observa:
   - Si ves "Logging out from: `https://auth.casmart.internal/application/o/consulta-smart/end-session/?...`"
   - Deberías ser redirigido a `/consultarpp/` dentro de 3 segundos

## Debugging

Si el logout sigue sin funcionar:

### A. Revisa los logs de Authentik

```bash
# Logs del servidor de Authentik
docker logs -f casmarts-core-authentik-server | grep -i logout

# O en el worker
docker logs -f casmarts-core-authentik-worker | grep -i invalidation
```

### B. Revisa la consola del navegador

La consola del navegador debe mostrar:
```
Auth State Changed: {
  isLoading: false,
  isAuthenticated: true,
  error: null,
  pathname: "/"
}

Logging out from: https://auth.casmart.internal/application/o/consulta-smart/end-session/?post_logout_redirect_uri=https%3A%2F%2Fconsulta.casmart.internal%2F&id_token_hint=eyJ...
```

### C. Verifica el endpoint `end-session`

```bash
# Obtén la configuración OIDC
curl -s https://auth.casmart.internal/application/o/consulta-smart/.well-known/openid-configuration | grep -i "end_session"

# Resultado esperado:
# "end_session_endpoint": "https://auth.casmart.internal/application/o/consulta-smart/end-session/"
```

## Checklist de Verificación

- [ ] El script `setup_consulta_smart_logout_flow.py` se ejecutó sin errores
- [ ] En Authentik Admin, `consulta-smart-invalidation-flow` existe
- [ ] El provider `consulta-smart-provider` usa ese flow en `Invalidation flow`
- [ ] Los `Redirect URIs` incluyen `https://consulta.casmart.internal/`
- [ ] El usuario puede hacer logout sin ver la pantalla `default invalidation flow`
- [ ] El usuario es redirigido a `/consultarpp/` después del logout

## Configuración Alternativa (Sin Flow Personalizado)

Si por algún motivo el flow personalizado no funciona, puedes:

1. **Usar `signoutRedirect()` del cliente OIDC:**
   - El frontend ya está intentando esto como fallback
   - Espera 3 segundos y redirige si falla

2. **Forzar logout en el servidor:**
   - El backend puede invalidar la sesión del usuario
   - El frontend puede redirigir al login inmediatamente

## Referencias

- [Authentik OAuth2 Documentation](https://docs.goauthentik.io/docs/providers/oauth2/oauth2_provider)
- [Authentik Flows Documentation](https://docs.goauthentik.io/docs/flow/flows)
- [OIDC End Session Endpoint Spec](https://openid.net/specs/openid-connect-rpinitiated-1_0.html)

## Resumen de cambios realizados

| Archivo | Cambio |
|---------|--------|
| `frontend/src/App.jsx` | Agregado `loadUserInfo: true` y `staleStateInSeconds` para mejor session handling |
| `frontend/src/components/ChatInterface.jsx` | Mejorado logout con timeout de seguridad y fallback robusto |
| `frontend/src/components/Navigation.jsx` | Agregado `id_token_hint` en `signoutRedirect()` |
| `core-casmarts/create_apps.py` | Actualizado para usar `consulta-smart-invalidation-flow` si existe |
| `core-casmarts/setup_consulta_smart_logout_flow.py` | **NUEVO** - Script para crear custom invalidation flow |
