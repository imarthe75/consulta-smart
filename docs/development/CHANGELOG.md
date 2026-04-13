# 📝 CHANGELOG - PropQuery

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-04-07

### 🎉 Añadido

- ✅ Estructura base del proyecto PropQuery
- ✅ Configuración de Backend Python con FastAPI
- ✅ Setup de Frontend React 19 con Vite
- ✅ Integración con múltiples LLM providers (Groq, Gemini, OpenAI, Claude)
- ✅ Sistema de ingesta de documentos con Docling
- ✅ Configuración de SeaweedFS para almacenamiento
- ✅ Setup de PostgreSQL + pgvector para embeddings
- ✅ Integración de Valkey (Redis) para cache y sesiones
- ✅ Configuración de Celery para procesamiento asíncrono
- ✅ Docker Compose con todos los servicios
- ✅ Documentación inicial (README, QUICK_START, ARCHITECTURE)
- ✅ Sistema de logging y configuración
- ✅ Scripts de inicialización de BD

### 🔄 Cambios

- N/A (versión inicial)

### 🐛 Corregido

- N/A (versión inicial)

### 🗑️ Eliminado

- N/A (versión inicial)

### 📚 Documentación

- README.md - Visión general del proyecto
- .env.example - Variables de configuración
- CHANGELOG.md - Este archivo
- QUICK_START.md - Guía de inicio rápido (próximo)
- ARCHITECTURE.md - Arquitectura técnica detallada (próximo)
- API.md - Referencia de API endpoints (próximo)

---

## Notas de Versión

### v0.1.0 (Fase Inicial)

**Objetivo**: Establecer la base del proyecto con infraestructura completa.

**Componentes Implementados**:
1. Backend modular con FastAPI
2. Ingesta de documentos con OCR
3. RAG con búsqueda vectorial
4. Chatbot con múltiples LLMs
5. Frontend React moderna
6. Docker stack completo

**Próximas Versiones**:
- v0.2.0: Integración completa chat + upload
- v0.3.0: Dashboard admin
- v0.4.0: Soporte multiidioma
- v1.0.0: Release producción

---

## Estructura del Changelog

Cada release incluye:

- **🎉 Añadido**: Nuevas características
- **🔄 Cambios**: Cambios en funcionalidad existente
- **🐛 Corregido**: Corrección de bugs
- **🗑️ Eliminado**: Características removidas
- **🚨 Deprecado**: Características que serán removidas
- **🔒 Seguridad**: Parches de seguridad

---

## Cómo Contriuir al Changelog

Cuando contribuyas cambios:

1. Crear un branch: `git checkout -b feature/mi-feature`
2. Hacer commits descriptivos
3. En el PR, describir cambios en el formato anterior
4. Actualizar CHANGELOG.md en la sección "Unreleased"
5. El maintainer fusionará y versionará

---

## Versionado

PropQuery sigue [Semantic Versioning](https://semver.org/):

- **MAJOR**: Cambios incompatibles (0.x.0)
- **MINOR**: Nueva funcionalidad compatible (x.1.0)
- **PATCH**: Fixes de bugs (x.0.1)

**Ejemplo**: v0.5.2
- 0 = MAJOR (primera versión)
- 5 = MINOR (5 features nuevas)
- 2 = PATCH (2 bugfixes)

---

## Timeline Pro Proyectado

| Versión | Fecha Est.  | Hito Principal                    |
|---------|-------------|-----------------------------------|
| 0.1.0   | 07/04/2026  | ✅ Setup inicial                  |
| 0.2.0   | 30/04/2026  | Chat + Upload funcional           |
| 0.3.0   | 31/05/2026  | Dashboard admin                   |
| 0.4.0   | 30/06/2026  | Multiidioma                       |
| 1.0.0   | 31/08/2026  | Release producción                |

---

**Última Actualización**: 07 de Abril, 2026  
**Mantenedor**: Tu Nombre/Equipo  
**Estado**: 🟢 En Desarrollo (Alpha)
