# Traducción de Mensajes de Error y Respuestas - ConsultaRPP

## 📌 Mensajes de Error Comunes

### Autenticación
```
"No autorizado" → "Unauthorized"
"Token inválido" → "Invalid token"
"Sesión expirada" → "Session expired"
"Acceso denegado" → "Access denied"
```

### Documentos
```
"Documento no encontrado" → "Document not found"
"Documento no existe" → "Document does not exist"
"El documento se está procesando" → "Document is processing"
"Archivo demasiado grande" → "File too large"
"Nombre de archivo requerido" → "Filename required"
"El documento debe tener estado COMPLETADO para buscarse" → "Document must be COMPLETED for search"
```

### Chat
```
"Sesión de chat no encontrada" → "Chat session not found"
"Mensaje vacío no permitido" → "Empty message not allowed"
"Error procesando consulta" → "Error processing query"
```

### Base de Datos
```
"Usuario con este email ya existe" → "User with this email already exists"
"Usuario con este nombre de usuario ya existe" → "User with this username already exists"
"No se pudo conectar a la base de datos" → "Could not connect to database"
```

### Validación
```
"El campo es requerido" → "This field is required"
"El email no es válido" → "Invalid email format"
"La contraseña es muy corta" → "Password is too short"
"El email debe tener formato válido" → "Email must be valid format"
```

---

## 📋 Respuestas de API

### Success Responses
```json
{
  "status": "success",
  "data": {...},
  "error": null,
  "meta": {
    "timestamp": "2026-04-07T..."
  }
}
```

### Error Responses
```json
{
  "status": "error",
  "data": null,
  "error": "Descripción del error en español",
  "meta": {
    "timestamp": "2026-04-07T..."
  }
}
```

---

## 🔄 Estado de Documentos

```
PENDIENTE → "Pending"
PROCESANDO → "Processing"
COMPLETADO → "Completed"
ERROR → "Error"
ARCHIVADO → "Archived"
```

---

## 🗣️ Categorías de Documentos

```
REGLAMENTO → "Reglamento"
LEY → "Ley"
GUIA → "Guía"
FORMULARIO → "Formulario"
PROCEDIMIENTO → "Procedimiento"
```

---

## 💬 Mensajes de Usuario Final

### Al Cargar Documento
```
"Documento encolado para procesamiento" → "Document queued for processing"
"Cargando archivo... {0}%" → "Uploading file... {0}%"
"Documento cargado exitosamente" → "Document uploaded successfully"
```

### En Búsqueda
```
"Resultados encontrados: {N}" → "{N} results found"
"No se encontraron resultados" → "No results found"
"Buscando en {N} documentos..." → "Searching in {N} documents..."
```

### En Chat
```
"Escriba su pregunta aquí..." → "Write your question here..."
"Enviando consulta..." → "Sending query..."
"Procesando respuesta..." → "Processing response..."
```

---

## 📊 Logs del Sistema (puede estar en inglés)

```
"Starting ConsultaRPP v0.1.0" → Log de inicio
"Database initialized" → Log de BD
"Processing document: {id}" → Log de tareas
"Error processing document: {error}" → Log de errores
```

---

## Notas Importantes

- ✅ Todos los mensajes de ERROR deben estar en ESPAÑOL
- ✅ Todos los mensajes de SUCCESS deben estar en ESPAÑOL
- ✅ Validaciones deben estar en ESPAÑOL
- ✅ Labels de formularios deben estar en ESPAÑOL
- ⚠️ Logs del sistema pueden estar en INGLÉS (estándar industrial)
- ⚠️ Variable names siempre en INGLÉS
- ⚠️ Function names siempre en INGLÉS
