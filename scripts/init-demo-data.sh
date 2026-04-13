#!/bin/bash

# init-demo-data.sh - Initializar usuario demo, autenticación y cargar documentos

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Inicializando Demo Data para ConsultaRPP${NC}"
echo "==========================================="
echo ""

# ============================================================
# 1. CREAR USUARIO DEMO EN LA BASE DE DATOS
# ============================================================
echo -e "${BLUE}📝 Paso 1: Crear usuario demo...${NC}"

# Import config desde .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DEMO_USER_EMAIL=${DEMO_USER_EMAIL:-demo@example.com}
DEMO_USER_PASSWORD=${DEMO_USER_PASSWORD:-password123}
DEMO_USER_USERNAME=${DEMO_USER_USERNAME:-usuario_demo}
DB_HOST=${DB_HOST:-postgres}
DB_USER=${DB_USER:-consultarpp_user}
DB_PASSWORD=${DB_PASSWORD:-***DB_PASSWORD_REDACTED***}
DB_NAME=${DB_NAME:-consultarpp}

# Crear usuario usando psql dentro del contenedor PostgreSQL
docker exec consultarpp-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" << EOSQL
-- Crear usuario si no existe
INSERT INTO users (email, username, password_hash, is_active, is_admin, created_at, updated_at)
VALUES (
    '$DEMO_USER_EMAIL',
    '$DEMO_USER_USERNAME',
    '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5zcMvksxM3zYq', -- password123 hash
    true,
    true,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    is_active = true,
    is_admin = true;

-- Verificar usuario creado
SELECT email, username, is_admin FROM users WHERE email = '$DEMO_USER_EMAIL';
EOSQL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ Usuario demo creado/verificado${NC}"
else
    echo -e "${YELLOW}   ⚠️  Error al crear usuario (puede existir ya)${NC}"
fi
echo ""

# ============================================================
# 2. OBTENER TOKEN JWT
# ============================================================
echo -e "${BLUE}🔐 Paso 2: Autenticándose y obtener token JWT...${NC}"

LOGIN_RESPONSE=$(curl -s -X POST \
    http://localhost:3001/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$DEMO_USER_EMAIL&password=$DEMO_USER_PASSWORD")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}   ❌ Error obteniendo token${NC}"
    echo "   Respuesta: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}   ✅ Token obtenido: ${TOKEN:0:20}...${NC}"
echo ""

# ============================================================
# 3. CARGAR DOCUMENTOS
# ============================================================
echo -e "${BLUE}📚 Paso 3: Cargando documentos...${NC}"

DOCS_DIR="$PROJECT_ROOT/docs"
LOADED_COUNT=0
ERROR_COUNT=0

# Encontrar todos los archivos markdown
for file in $(find "$DOCS_DIR" -type f \( -name "*.md" -o -name "*.txt" \) ! -name "README*" ! -name "*QUICK*" | head -20); do
    FILENAME=$(basename "$file")
    FILESIZE=$(ls -lh "$file" | awk '{print $5}')
    
    echo -n "   📄 $FILENAME ($FILESIZE)... "
    
    # Cargar archivo
    UPLOAD_RESPONSE=$(curl -s -X POST \
        "http://localhost:3001/api/v1/documents/upload" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@$file" \
        -F "title=$FILENAME" \
        -F "category=guia")
    
    # Verificar respuesta
    if echo "$UPLOAD_RESPONSE" | grep -q '"error"'; then
        echo -e "${RED}❌${NC}"
        ((ERROR_COUNT++))
    elif echo "$UPLOAD_RESPONSE" | grep -q '"success"' || echo "$UPLOAD_RESPONSE" | grep -q '"document_id"'; then
        echo -e "${GREEN}✅${NC}"
        ((LOADED_COUNT++))
    else
        echo -e "${YELLOW}⚠️${NC} (sin confirmación clara)"
        ((LOADED_COUNT++))
    fi
done

echo ""
echo -e "${GREEN}   📊 Resultados:${NC}"
echo -e "      ✅ Cargados: $LOADED_COUNT"
echo -e "      ❌ Errores: $ERROR_COUNT"
echo ""

# ============================================================
# 4. VERIFICAR DATOS EN BD
# ============================================================
echo -e "${BLUE}🔍 Paso 4: Verificando datos en BD...${NC}"

CHUNK_COUNT=$(docker exec -e PGPASSWORD="$DB_PASSWORD" consultarpp-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM document_chunks;" 2>/dev/null || echo "0")

DOC_COUNT=$(docker exec -e PGPASSWORD="$DB_PASSWORD" consultarpp-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null || echo "0")

echo -e "${GREEN}   📈 Estadísticas:${NC}"
echo -e "      📄 Documentos: $DOC_COUNT"
echo -e "      📋 Chunks: $CHUNK_COUNT"
echo ""

# ============================================================
# 5. RESUMEN FINAL
# ============================================================
echo -e "${GREEN}✅ INICIALIZACIÓN COMPLETADA${NC}"
echo "==========================================="
echo ""
echo -e "${BLUE}📖 Próximos pasos:${NC}"
echo "   1. Accede a http://localhost:3000"
echo "   2. Email: $DEMO_USER_EMAIL"
echo "   3. Password: $DEMO_USER_PASSWORD"
echo ""
echo -e "${BLUE}🧪 Prueba el sistema:${NC}"
echo "   curl -X POST http://localhost:3001/api/v1/chat/query \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"query\": \"¿Notarios en Cancún?\"}'"
echo ""
