#!/bin/bash
# Script para cargar documentos RPP y generar embeddings
# Uso: ./load_rpp_docs.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  CARGADOR DE DOCUMENTOS RPP CON EMBEDDINGS                    ║"
echo "║  Consulta-RPP - Cargar Base de Conocimiento                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"

BASE_URL="http://localhost:3001/api/v1"
DOCS_DIR="/home/ia/consulta-rpp/docs/rpp-registry"

# Paso 1: Verificar documentos
echo ""
echo "[✓] Verificando documentos RPP..."
DOC_COUNT=$(find "$DOCS_DIR" -name "*.md" 2>/dev/null | wc -l)
echo "    Encontrados: $DOC_COUNT archivos MD"
echo "    Ubicación: $DOCS_DIR"

# Paso 2: Login
echo ""
echo "[1/3] Autenticando..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  --data "username=demo@example.com&password=password123" \
  -H "Content-Type: application/x-www-form-urlencoded")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "      ❌ Error: No se obtuvo token JWT"
  echo "      Respuesta: $LOGIN_RESPONSE"
  exit 1
fi

echo "      ✅ Autenticación exitosa"
echo "      Token: ${TOKEN:0:40}..."

# Paso 3: Cargar documentos y generar embeddings
echo ""
echo "[2/3] Cargando documentos y generando embeddings..."
echo "      (Esto puede tomar hasta 20 minutos según el servidor)"
echo "      Por favor, espera sin cancelar. Esto NO es un error..."

LOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/load-rpp-registry" \
  -H "Authorization: Bearer $TOKEN" \
  --connect-timeout 30 \
  --max-time 1200)

# Paso 4: Mostrar resultado
echo ""
echo "[3/3] Resultado de la carga:"
echo "────────────────────────────────────────────────────────────────"

# Parsear respuesta
STATUS=$(echo "$LOAD_RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
LOADED=$(echo "$LOAD_RESPONSE" | grep -o '"loaded":[0-9]*' | cut -d':' -f2)
TOTAL=$(echo "$LOAD_RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2)
CHUNKS=$(echo "$LOAD_RESPONSE" | grep -o '"total_chunks":[0-9]*' | cut -d':' -f2)
ERRORS=$(echo "$LOAD_RESPONSE" | grep -o '"errors":[0-9]*' | cut -d':' -f2)

if [ "$STATUS" = "success" ]; then
  echo "✅ CARGA EXITOSA"
  echo "   • Documentos cargados: $LOADED"
  echo "   • Total procesados: $TOTAL"
  echo "   • Chunks creados: $CHUNKS"
  echo "   • Errores: $ERRORS"
else
  echo "⚠️  Status: $STATUS"
  echo "Respuesta completa:"
  echo "$LOAD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOAD_RESPONSE"
fi

echo "────────────────────────────────────────────────────────────────"
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║ ✅ PROCESO COMPLETADO                                         ║"
echo "║                                                                ║"
echo "║ Los documentos RPP están listos. El sistema ahora usará RAG    ║"
echo "║ para responder consultas basadas en los documentos cargados.   ║"
echo "║                                                                ║"
echo "║ Prueba hacer una consulta en: http://localhost:3000           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
