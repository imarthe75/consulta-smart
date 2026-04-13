#!/bin/bash

# load-rpp-docs.sh - Cargar toda la documentación RPP a la base de datos
# Esto es CRÍTICO para que el RAG funcione correctamente con información específica

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📚 Cargando documentación RPP a la base de datos${NC}"
echo "=================================================="
echo ""

# Config
export PGPASSWORD="***DB_PASSWORD_REDACTED***"
DB_USER="consultarpp_user"
DB_NAME="consultarpp"
DB_HOST="127.0.0.1"
RPP_DOCS_DIR="$PROJECT_ROOT/docs/rpp-registry"

# ID del usuario sistema
SYSTEM_USER_ID=$(docker exec -e PGPASSWORD="$PGPASSWORD" consultarpp-postgres psql -h localhost -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT id FROM users LIMIT 1;" 2>/dev/null | head -1 || echo "019d73a6-d320-7c49-bee7-b19f368473ec")

echo -e "${BLUE}🔍 Etapa 1: Descubriendo documentos RPP${NC}"
echo ""

# Encuentra documentos únicamente en el nivel correcto (evita duplicados)
# Incluye archivos en raíz Y en subdirectorios, pero solo una vez
declare -a UNIQUE_FILES
declare -A SEEN_NAMES

# Buscar todos ls .md files
while IFS= read -r file; do
    if [[ -z "$file" ]]; then
        continue
    fi
    # Obtener solo el nombre del archivo (sin ruta)
    filename=$(basename "$file")
    
    # Si ya vimos este nombre, saltamos (es un duplicado)
    if [[ -n "${SEEN_NAMES[$filename]}" ]]; then
        continue
    fi
    
    # Marcar como visto y agregar a lista
    SEEN_NAMES[$filename]=1
    UNIQUE_FILES+=("$file")
done < <(find "$RPP_DOCS_DIR" -type f -name "*.md" ! -name "README.md" ! -name "INDEX.md" | sort)

DOC_COUNT=${#UNIQUE_FILES[@]}
UNIQUE_DOCS=$(printf '%s\n' "${UNIQUE_FILES[@]}")

echo -e "${GREEN}   📄 Documentos encontrados: $DOC_COUNT${NC}"
echo ""

echo -e "${BLUE}🔍 Etapa 2: Insertando documentos en BD${NC}"
echo ""

LOADED_DOCS=0
LOADED_CHUNKS=0

for doc_file in $UNIQUE_DOCS; do
    if [[ ! -f "$doc_file" ]]; then
        continue
    fi
    
    # Generar ID único para documento
    DOC_ID=$(echo -n "$doc_file" | md5sum | cut -d' ' -f1 | head -c 36)
    # Convertir a UUID format: 8-4-4-4-12
    DOC_ID="${DOC_ID:0:8}-${DOC_ID:8:4}-${DOC_ID:12:4}-${DOC_ID:16:4}-${DOC_ID:20:12}"
    
    DOC_NAME=$(basename "$doc_file" .md)
    DOC_SIZE=$(wc -c < "$doc_file")
    
    echo -n "   📄 $DOC_NAME ($(numfmt --to=iec-i --suffix=B $DOC_SIZE 2>/dev/null || echo ${DOC_SIZE}B))... "
    
    # Leer contenido del archivo
    DOC_CONTENT=$(cat "$doc_file" 2>/dev/null || echo "")
    
    if [[ -z "$DOC_CONTENT" ]]; then
        echo -e "${RED}VACÍO${NC}"
        continue
    fi
    
    # Escapar comillas para SQL
    DOC_CONTENT_ESCAPED=$(echo "$DOC_CONTENT" | sed "s/'/''/g")
    DOC_NAME_ESCAPED=$(echo "$DOC_NAME" | sed "s/'/''/g")
    
    # Insertar documento
    docker exec -e PGPASSWORD="$PGPASSWORD" consultarpp-postgres psql -h localhost -U "$DB_USER" -d "$DB_NAME" << EOSQL > /dev/null 2>&1
INSERT INTO documents (id, title, category, user_id, file_type, status, created_at, updated_at)
VALUES (
    '$DOC_ID',
    '$DOC_NAME_ESCAPED',
    'documentacion',
    '$SYSTEM_USER_ID',
    'md',
    'processed',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;
EOSQL
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅${NC}"
        ((LOADED_DOCS++))
        
        # Dividir en chunks (1000 caracteres con solapamiento)
        CHUNK_SIZE=1000
        OVERLAP=200
        CHUNK_NUM=0
        
        for ((i=0; i<${#DOC_CONTENT}; i+=$((CHUNK_SIZE-OVERLAP)))); do
            CHUNK="${DOC_CONTENT:$i:$CHUNK_SIZE}"
            if [[ -z "$CHUNK" ]]; then
                break
            fi
            
            CHUNK_ESCAPED=$(echo "$CHUNK" | sed "s/'/''/g")
            CHUNK_ID=$(echo -n "$DOC_ID-$CHUNK_NUM" | md5sum | cut -d' ' -f1 | head -c 36)
            CHUNK_ID="${CHUNK_ID:0:8}-${CHUNK_ID:8:4}-${CHUNK_ID:12:4}-${CHUNK_ID:16:4}-${CHUNK_ID:20:12}"
            
            docker exec -e PGPASSWORD="$PGPASSWORD" consultarpp-postgres psql -h localhost -U "$DB_USER" -d "$DB_NAME" << EOSQL > /dev/null 2>&1
INSERT INTO document_chunks (id, document_id, chunk_number, text, created_at)
VALUES (
    '$CHUNK_ID',
    '$DOC_ID',
    $CHUNK_NUM,
    '$CHUNK_ESCAPED',
    NOW()
) ON CONFLICT DO NOTHING;
EOSQL
            
            ((CHUNK_NUM++))
            ((LOADED_CHUNKS++))
        done
        
    else
        echo -e "${RED}❌${NC}"
    fi
done

echo ""
echo -e "${BLUE}🔍 Etapa 3: Verificando datos en BD${NC}"
echo ""

TOTAL_DOCS=$(docker exec -e PGPASSWORD="$PGPASSWORD" consultarpp-postgres psql -h localhost -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null || echo "0")
TOTAL_CHUNKS=$(docker exec -e PGPASSWORD="$PGPASSWORD" consultarpp-postgres psql -h localhost -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM document_chunks;" 2>/dev/null || echo "0")

echo -e "${GREEN}   📊 Documentos en BD: $TOTAL_DOCS${NC}"
echo -e "${GREEN}   📋 Chunks en BD: $TOTAL_CHUNKS${NC}"
echo ""

echo -e "${BLUE}🎯 Etapa 4: Generando embeddings${NC}"
echo ""

echo -e "${YELLOW}   ⚠️ IMPORTANTE: Los embeddings se generarán cuando el backend procese queries${NC}"
echo -e "${YELLOW}      La búsqueda funcionará por texto hasta que se generen los embeddings${NC}"
echo ""

echo -e "${GREEN}✅ CARGA COMPLETADA${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}📖 Próximos pasos:${NC}"
echo "   1. Hacer queries al sistema para generar embeddings"
echo "   2. El RAG tendrá acceso a TODA la documentación RPP"
echo "   3. Las respuestas serán mucho más específicas"
echo ""
echo -e "${BLUE}🧪 Prueba el sistema:${NC}"
echo "   curl -X POST http://localhost:3001/api/v1/chat/query \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"message\": \"¿Cuáles son los notarios en Quintana Roo?\", \"session_id\": \"test\"}'"
echo ""
