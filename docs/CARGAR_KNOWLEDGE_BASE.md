# Cargar Knowledge Base - RPP Registry

## 📚 Descripción

Este documento describe cómo cargar la documentación del RPP Registry (oficinas, notarios, requisitos, costos) en la Knowledge Base de PostgreSQL para que el widget IA pueda responder preguntas sobre:

- **Oficinas**: Chetumal, Cancún, Playa del Carmen, Cozumel (Quintana Roo) + Puebla
- **Notarios**: 138 en Puebla, 124 en Quintana Roo
- **Requisitos**: Actos registrables, procedimientos por estado
- **Costos**: Aranceles y derechos por acto

---

## ⚙️ Pre-requisitos

1. **PostgreSQL ejecutándose**
   ```bash
   # Verificar conexión
   docker exec consulta-rpp-db psql -U postgres -d consulta_rpp -c "SELECT version();"
   ```

2. **Backend inicializado (schema creado)**
   ```bash
   # Desde el directorio backend
   python -m alembic upgrade head
   ```

3. **Archivos MD en `docs/rpp-registry/`**
   - `OFICINAS_CONTACTOS_RPP.md` ✓
   - `DIRECTORIO_NOTARIOS_NACIONAL.md` ✓
   - `REQUISITOS_POR_ACTO_*.md` ✓
   - `DERECHOS_COSTOS_*.md` ✓
   - Otros archivos de referencia

4. **Credenciales de LLM** (para generar embeddings)
   - Variable: `GEMINI_API_KEY` o `OPENAI_API_KEY`
   - Verificar en `.env`

---

## 🚀 Ejecución

### Opción 1: Script Python (Recomendado)

```bash
# Desde el directorio raíz del proyecto
cd /home/ia/consulta-rpp

# Ejecutar la carga
python scripts/load_rpp_documents.py
```

**Salida esperada:**
```
================================================================================
🚀 INICIANDO CARGA RPP REGISTRY → KNOWLEDGE BASE
================================================================================

[STEP 1] Obteniendo usuario del sistema...
   ✓ Usuario del sistema encontrado/creado

[STEP 2] Buscando documentos MD...
   Encontrados 8 documentos para cargar

[STEP 3] Cargando documentos...

   [1/8] OFICINAS_CONTACTOS_RPP.md
       Categoría: reglamentos
       Generando embeddings...
       ✅ Cargado (4 chunks)

   [2/8] DIRECTORIO_NOTARIOS_NACIONAL.md
       Categoría: reglamentos
       Generando embeddings...
       ✅ Cargado (18 chunks)
   
   [... más documentos ...]

================================================================================
✅ CARGA COMPLETADA: 8 documentos exitosos, 0 errores
================================================================================

Ahora puedes hacer preguntas sobre:
  • Oficinas en Puebla y Quintana Roo
  • Notarios disponibles
  • Requisitos por acto
  • Costos y aranceles
  • Horarios y servicios
```

### Opción 2: Makefile

```bash
# Si existe una tarea en Makefile
make load-kb
# o
make load-rpp-registry
```

---

## ✅ Validación

Después de ejecutar la carga, valida que los datos se cargaron correctamente:

### 1. Verificar en PostgreSQL

```bash
# Conectar a la BD
docker exec -it consulta-rpp-db psql -U postgres -d consulta_rpp

# Contar documentos
SELECT COUNT(*) FROM documents;
-- Expected: > 0

# Ver categorías
SELECT category, COUNT(*) FROM documents GROUP BY category;

# Ver documentos cargados
SELECT title, category, created_at FROM documents LIMIT 10;
```

### 2. Ejecutar Script de Validación

```bash
python scripts/validate_kb.py
```

**Salida esperada:**
```
======================================================================
📊 VALIDANDO KNOWLEDGE BASE
======================================================================

[1] ESTADÍSTICAS GENERALES
   Total documentos: 8

   📂 Por categoría:
      • reglamentos: 8
      • costos: 12
      • procedimientos: 6

[2] CATEGORÍAS DISPONIBLES
   • reglamentos: 8 docs
   • costos: 12 docs
   • procedimientos: 6 docs

[3] PRUEBAS DE BÚSQUEDA
   ✅ 'Oficinas en QRoo': Encontrado
      Título: RPP Registry - OFICINAS_CONTACTOS_RPP.md
      Preview: REGISTRO PÚBLICO DE QUINTANA ROO...
   
   ✅ 'Notarios': Encontrado
   ✅ 'Chetumal': Encontrado
   ✅ 'Información de horarios': Encontrado
   ✅ 'Requisitos de actos': Encontrado

======================================================================
✅ KB OPERACIONAL: 26 documentos, 5/5 búsquedas exitosas
======================================================================
```

---

## 🧪 Pruebas en el Widget

Una vez cargada la KB, prueba estas preguntas:

### Preguntas sobre Oficinas
```
P: ¿Cuáles son las oficinas disponibles en Quintana Roo?
R: Deberá retornar:
   - Chetumal (Central)
   - Cancún (Zona Turística)
   - Playa del Carmen (Zona Turística)
   - Cozumel (Isla)
   
Con horarios, servicios y contactos.
```

### Preguntas sobre Notarios
```
P: ¿Puedes decirme algunos notarios disponibles en Puebla?
R: Deberá retornar nombres, números de notaría, teléfonos.
   Ejemplos:
   - Adriana Salazar Cajica
   - Alexis Arturo Diaz
   [... más notarios ...]
```

### Preguntas sobre Requisitos
```
P: ¿Cuáles son los requisitos para una compraventa en Quintana Roo?
R: Lista de documentos, trámites, costos.
```

### Preguntas sobre Costos
```
P: ¿Cuál es el costo de una compraventa en Puebla?
R: Arancel + derechos específicos.
```

---

## 🔧 Troubleshooting

### Error: "Tabla 'documents' no existe"
**Solución:**
```bash
# Ejecutar migraciones
python -m alembic upgrade head

# O desde docker
docker exec consulta-rpp-backend python -m alembic upgrade head
```

### Error: "Usuario del sistema no encontrado"
**Solución:**
El script lo creará automáticamente. Si hay error al crear:
```sql
-- Crear manualmente
INSERT INTO users (id, email, name, password_hash, is_active, created_at, updated_at)
VALUES ('system-user-id', 'system@rpp-registry.local', 'Sistema RPP', 'disabled', true, NOW(), NOW());
```

### Error: "API key no configurada"
**Solución:**
```bash
# Verificar en .env
echo $GEMINI_API_KEY

# O configurar
export GEMINI_API_KEY="your-key-here"

# Reejecutar script
python scripts/load_rpp_documents.py
```

### KB Cargada pero sin resultados
**Posibles causas:**
1. Los embeddings no se generaron correctamente
   ```bash
   # Verificar chunks con NULL embedding
   SELECT COUNT(*) FROM document_chunks WHERE embedding IS NULL;
   ```

2. La búsqueda no utiliza pgvector
   - Revisar: `backend/app/infrastructure/knowledge_base.py`
   - Asegurar que usa `search_in_knowledge_async()`

3. El LLM no está retornando embeddings válidos
   - Verificar API key de Gemini/OpenAI
   - Checar logs del backend

---

## 📊 Estadísticas Esperadas

Después de una carga exitosa:

| Métrica | Valor Esperado |
|---------|-------|
| Total de documentos | 8+ |
| Total de chunks | 50-100 |
| Documentos con categoría "oficinas" | 2+ |
| Documentos con categoría "notarios" | 1+ |
| Documentos con categoría "costos" | 2+ |
| Embeddings generados | 50-100 |

---

## 🔄 Actualización de Datos

Si necesitas actualizar los datos (p.ej., agregar nuevos notarios):

1. **Editar archivos MD** en `docs/rpp-registry/`
2. **Borrar documentos anteriores** (opcional):
   ```sql
   DELETE FROM document_chunks WHERE document_id IN (
     SELECT id FROM documents WHERE metadata LIKE '%NOTARIOS%'
   );
   DELETE FROM documents WHERE metadata LIKE '%NOTARIOS%';
   ```
3. **Reejecutar** `python scripts/load_rpp_documents.py`

---

## 📝 Notas Importantes

- **Usuario del Sistema**: Los documentos se crean con un usuario `system@rpp-registry.local`
- **Chunks**: Se generan automáticamente (máx 800 caracteres cada uno)
- **Embeddings**: Se generan con la API configurada (Gemini/OpenAI)
- **Actualización**: Ejecutar nuevamente el script actualiza los datos
- **Performance**: Primera ejecución puede tardar 2-5 minutos (dependiendo de volumen)

---

## 🎯 Checklist Final

- [ ] PostgreSQL ejecutándose
- [ ] Backend inicializado (schema creado)
- [ ] Variables de entorno configuradas (.env)
- [ ] Script `load_rpp_documents.py` ejecutado sin errores
- [ ] Validación pasó (script `validate_kb.py`)
- [ ] Widget retorna datos de oficinas
- [ ] Widget retorna datos de notarios
- [ ] Búsqueda por requisitos funciona
- [ ] Búsqueda por costos funciona

---

**Última actualización:** 04/2026  
**Autor:** IA Assistant  
**Estado:** ✅ Documentación Completa
