# Guía de Integración Técnica: Authentik Casmarts (Consolidada)

Este documento es la referencia central para administradores y desarrolladores. Combina estrategias de integración, guías administrativas y ejemplos prácticos multitecnología.

---

## 1. Estrategias de Integración

Existen tres formas principales de integrar tus aplicaciones con Authentik:

### A. OpenID Connect (OIDC) - Recomendado
Estándar industrial donde Authentik maneja la identidad y tu app recibe tokens.
*   **Uso:** Aplicaciones Web modernas (Angular, React) y Backends (Spring Boot, Python).

### B. Flujos Embebidos (Embedded Flows)
Renderiza el login de Authentik dentro de tu propia app mediante componentes oficiales o iframes controlados.

### C. Direct API (Resource Owner Password Credentials)
Tu app recolecta credenciales y las valida contra la API de Authentik. Útil para apps legacy o móviles.

---

## 2. Operaciones Administrativas (Admin Interface)

Acceso: `https://arquitectura.casmart.internal/if/admin/`

### A. Directorio (Usuarios y Roles)
*   **Users:** Gestión de identidades locales y sincronizadas.
*   **Groups:** Define roles de negocio. Se pueden usar políticas para que solo ciertos grupos vean ciertas aplicaciones.

### B. Aplicaciones y Providers
1.  **Provider:** Configura el protocolo (OIDC, SAML, LDAP). Aquí se definen los **Redirect URIs** y los **Allowed Origins (CORS)**.
2.  **Application:** El objeto visual que vincula un Provider con una marca y un slug de URL.

---

## 3. Ejemplos de Integración: Backend

### A. Python (requests - Direct API)
```python
import requests

def get_authentik_token(username, password):
    url = "https://arquitectura.casmart.internal/application/o/token/"
    payload = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': 'tu-client-id',
        'client_secret': 'tu-client-secret',
        'scope': 'openid profile email'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None
```

### B. Spring Boot (OAuth2 Client)
**application.yml:**
```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          authentik:
            client-id: ${AUTHENTIK_CLIENT_ID}
            client-secret: ${AUTHENTIK_CLIENT_SECRET}
            scope: openid, profile, email
            authorization-grant-type: authorization_code
            redirect-uri: "{baseUrl}/login/oauth2/code/authentik"
        provider:
          authentik:
            issuer-uri: https://arquitectura.casmart.internal/application/o/tu-app-slug/
```

---

## 4. Ejemplos de Integración: Frontend

### A. React (react-oidc-context)
```javascript
import { AuthProvider, useAuth } from 'react-oidc-context';

const oidcConfig = {
    authority: "https://arquitectura.casmart.internal/application/o/tu-app-slug/",
    client_id: "tu-client-id",
    redirect_uri: window.location.origin + "/callback",
    response_type: "code",
    scope: "openid profile email",
};

export function App() {
    return (
        <AuthProvider {...oidcConfig}>
            <LoginComponent />
        </AuthProvider>
    );
}
```

### B. Angular (Latest - angular-auth-oidc-client)
**auth-config.ts:**
```typescript
export const authConfig = {
  config: {
    authority: 'https://arquitectura.casmart.internal/application/o/tu-app-slug/',
    redirectUrl: window.location.origin + '/callback',
    postLogoutRedirectUri: window.location.origin,
    clientId: 'tu-client-id',
    scope: 'openid profile email',
    responseType: 'code',
    silentRenew: true,
    useRefreshToken: true,
  }
};
```

---

## 5. Documentación de API (Swagger)

*   **Swagger UI:** `https://arquitectura.casmart.internal/api/v3/`
*   **Schema:** `https://arquitectura.casmart.internal/api/v3/schema/`

---

---

## 6. Gestión Programática de Entidades (API Backend)

Para procesos de automatización o registro personalizado desde tus aplicaciones, puedes crear usuarios y roles directamente consumiendo la API de Authentik.

### A. Autenticación de Servicio-a-Servicio
Para que tu backend hable con la API de Authentik, necesitas un **Token de API**:
1.  Ve a `Directory` > `Tokens & App passwords`.
2.  Crea un Token con los permisos adecuados.
3.  Úsalo en el header: `Authorization: Bearer <tu-token>`.

### B. Ejemplo: Creación de Usuario (Python)
```python
import requests

def create_authentik_user(username, email, name):
    url = "https://arquitectura.casmart.internal/api/v3/core/users/"
    headers = {
        "Authorization": "Bearer <tu-token-de-admin>",
        "Content-Type": "application/json"
    }
    payload = {
        "username": username,
        "name": name,
        "email": email,
        "is_active": True,
        "path": "users",  # Directorio por defecto
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

### C. Ejemplo: Asignación a un Grupo/Rol
```python
def add_user_to_group(user_pk, group_pk):
    url = f"https://arquitectura.casmart.internal/api/v3/core/groups/{group_pk}/add_user/"
    headers = {"Authorization": "Bearer <tu-token-de-admin>"}
    payload = {"pk": user_pk}
    
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 204
```

---

---

## 7. Atributos Personalizados (Custom Claims)

Si tu aplicación necesita datos específicos (como `departamento`, `id_empleado` o `rol_interno`), puedes incluirlos en el ID Token mediante **Property Mappings**.

1.  Ve a `Customization` > `Property Mappings`.
2.  Crea un nuevo `Scope Mapping`.
3.  Usa una expresión de Python para devolver el dato:
    ```python
    return {
        "departamento": user.attributes.get("dept", "General"),
        "es_vip": user.group_attributes(request).get("vip", False)
    }
    ```
4.  Asocia este mapeo a tu Provider en la pestaña **Advanced protocol settings**.

---

## 8. Seguridad Avanzada: MFA y Refresh Tokens

### A. Autenticación de Doble Factor (MFA)
Authentik soporta TOTP (Google Authenticator) y WebAuthn nativamente.
*   **Configuración:** Se debe editar el `Authentication Flow` y añadir una etapa de `Authenticator Validation`.
*   **Impacto en la App:** Si el MFA es obligatorio, Authentik no emitirá el token hasta que el segundo factor sea validado, por lo que la aplicación no requiere lógica extra, solo manejar el error de "acceso denegado" si el usuario cancela el proceso.

### B. Uso de Refresh Tokens
Para evitar que el usuario tenga que iniciar sesión cada hora (duración estándar del Access Token):
1.  Habilita **Refresh Tokens** en la configuración del Provider.
2.  En el frontend (Angular/React), asegúrate de que `silentRenew` o `useRefreshToken` esté en `true`.
3.  El SDK renovará el token en segundo plano usando un `iframe` oculto o el endpoint `/token` con `grant_type: refresh_token`.

---

## 9. Notas de Seguridad y Troubleshooting

1.  **CORS:** Los dominios deben estar en "Allowed Origins" del Provider.
2.  **Redirect URIs:** Deben ser idénticos en la app y en Authentik (sensible a mayúsculas y barras finales).
3.  **Logs:** Revisa `System` > `Events` en Authentik para ver fallos de políticas en tiempo real.
