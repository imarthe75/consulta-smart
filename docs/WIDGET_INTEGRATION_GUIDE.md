# Guía de Integración: Widget Embebible de ConsultaSmart

Este documento describe cómo integrar el asistente en portales de terceros (ciudadanos,
notarios, institucionales, o cualquier otro sitio interno como Centinela-AI) mediante el
script embebible real.

> **Nota de vigencia (2026-08-14):** esta guía reemplaza una versión anterior que describía
> un mecanismo de dos pasos (`rpp-widget.js` + elemento personalizado `<rpp-chat-widget>`)
> que nunca llegó a construirse — el archivo `rpp-widget.js` no existía en el repositorio.
> Lo que se documenta aquí es el `widget.js` real, servido desde
> `frontend/public/widget.js`, verificado en producción.

## 1. Archivo Requerido
El widget es una burbuja flotante inyectada por un único script vanilla JS (sin
dependencias, no reempaqueta React). Solo se requiere cargarlo:

```html
<script src="https://chat.casmart.internal/widget.js"
        data-tenant-id="rpp"
        data-primary-color="#004a87"
        data-title="Consultor Experto RPP"
        async>
</script>
```

Colóquelo antes del cierre de `</body>`. No requiere ninguna otra etiqueta ni elemento
adicional — el script crea el botón flotante y el panel del chat por sí mismo.

## 2. Atributos de Personalización (Branding)

| Atributo | Descripción | Valor por defecto |
| :--- | :--- | :--- |
| `data-tenant-id` | Identificador del tema/perfil de ConsultaSmart a mostrar (ej. `rpp`, `ircep`, `mesa_ayuda`, `centinela-ai`) | `general` |
| `data-primary-color` | Color de marca del botón flotante y de la UI del chat (hex) | `#3b82f6` |
| `data-title` | Título mostrado en la cabecera del chat y en el `aria-label` del botón | Título configurado en el tema |

## 3. Funcionamiento

- **Portable a cualquier dominio:** el script detecta su propio origen a partir de su
  `src` (no del dominio que lo embebe), así que apunta siempre de vuelta a
  ConsultaSmart sin necesidad de configurar CORS ni endpoints separados en el sitio host.
- **Burbuja flotante + panel bajo demanda:** el botón se inyecta de inmediato; el
  `<iframe>` con el chat real solo se crea la primera vez que el usuario hace clic
  (no gasta la sesión de invitado ni carga recursos si nunca se abre).
- **Persistencia de sesión al cerrar:** cerrar el panel solo lo oculta (no destruye el
  `<iframe>`) — reabrir no reinicia la conversación de esa visita.
- **Acceso Anónimo:** no requiere que el usuario final ingrese usuario ni contraseña
  (autenticación de invitado manejada internamente por la ruta `/widget`).
- **Responsivo:** en viewports ≤480px el panel ocupa toda la pantalla; en desktop es un
  panel flotante de 380×600px en la esquina inferior derecha.

## 4. Consideraciones Técnicas
1. **`src` debe ser una URL pública real** donde esté desplegado ConsultaSmart (ej.
   `https://chat.casmart.internal`), no una IP/puerto interno de desarrollo.
2. **`X-Content-Type-Options: nosniff`** está activo globalmente en el proxy — esto es
   seguro porque `widget.js` se sirve con `Content-Type: text/javascript` real (no es
   necesario ni se debe desactivar ese header para que el widget funcione).
3. **Clickjacking:** el sitio (`/`, incluida la ruta `/widget`) permite deliberadamente
   ser embebido en `<iframe>`/`<script>` de terceros — es el comportamiento esperado del
   widget, no una brecha. Solo `/admin` bloquea el framing (ver
   `nginx/conf.d/chat.casmart.internal.conf`).

---
**Recursos Adicionales:** puede ver una página de ejemplo funcional (con el widget real
cargado en vivo) en `/demo_widget.html` dentro del `public/` del frontend.
