# Guía de Integración: RPP Expert Chat Widget (v2.0.0 - Premium)

Este documento describe cómo integrar el Asistente Experto en portales ciudadanos, de notarios o institucionales utilizando el script optimizado de alto rendimiento.

## 1. Archivos Requeridos
El widget es un **Web Component** que encapsula la aplicación React. Solo se requiere cargar el script:

```html
<script src="https://[TU-DOMINIO-O-IP]:3001/static/rpp-widget.js"></script>
```

## 2. Implementación Básica
Inserta la etiqueta personalizada al final del `<body>`. El sistema detectará automáticamente el modo widget y activará el acceso anónimo (sin login):

```html
<rpp-chat-widget 
    primary-color="#004a87" 
    bot-name="Consultor Experto RPP"
    endpoint="https://[TU-DOMINIO-O-IP]:3001">
</rpp-chat-widget>
```

## 3. Atributos de Personalización (Branding)

| Atributo | Descripción | Valor Ejemplo |
| :--- | :--- | :--- |
| `primary-color` | Color principal del botón y branding | `#540b0e` (Puebla) / `#004a87` (QRoo) |
| `bot-name` | Título que aparecerá en la ventana del chat | "Consultor SIQROO" |
| `endpoint` | URL base donde está alojado el backend/frontend | `https://consulta.rpp.gob.mx` |

## 4. Funcionamiento del Modo Widget
- **Acceso Anónimo:** No requiere que el usuario final ingrese usuario ni contraseña.
- **Sesiones Únicas:** Cada vez que el portal se carga, el widget inicia una **conversación nueva** para evitar cruce de datos entre ciudadanos.
- **Memoria de Contexto:** Durante la sesión activa, el asistente recuerda las preguntas previas para ofrecer respuestas coherentes.
- **Seguridad:** El widget se comunica de forma cifrada con la API mediante tokens de invitado temporales.

## 5. Consideraciones Técnicas
1.  **CORS:** Asegúrese de que el dominio del portal esté autorizado en el backend.
2.  **Responsividad:** El widget está optimizado para móviles y se ajustará automáticamente al ancho de la pantalla en dispositivos pequeños.

---
**Recursos Adicionales:** Puede ver una página de ejemplo funcional en `/static/demo_widget.html` dentro de la carpeta del servidor.
