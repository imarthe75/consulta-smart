#!/bin/bash

# Test script for RAG verification
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkZW1vQGV4YW1wbGUuY29tIiwiZXhwIjoxNzc1ODUwMjU1fQ.1jX2rIpHeR5AqStyO2xAoHEMhQMXrS-zxkGUHeLQIfE"
API="http://localhost:3001/api/v1/chat/query"

echo "🔬 VERIFICACIÓN DEL RAG CON DOCUMENTOS LOCALES"
echo "=============================================="
echo ""

# Test 1: Notarios
echo "📋 Test 1: Notarios en Quintana Roo"
echo "---"
RESPONSE=$(curl -s "$API" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"message":"¿Cuáles son los notarios en Quintana Roo?","session_id":"rag-test-001"}')

HAS_KNOWLEDGE=$(echo "$RESPONSE" | python3 -c "import json, sys; print(json.load(sys.stdin)['data']['has_relevant_knowledge'])")
SOURCES=$(echo "$RESPONSE" | python3 -c "import json, sys; sources = json.load(sys.stdin)['data']['sources']; print(len(sources))")

echo "  ✅ Conocimiento local: $HAS_KNOWLEDGE"
echo "  📚 Fuentes usadas: $SOURCES"
echo ""

# Test 2: Costos
echo "📋 Test 2: Costos de derechos en Puebla"
echo "---"
RESPONSE=$(curl -s "$API" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"message":"¿Cuáles son los costos de derechos registrales en Puebla?","session_id":"rag-test-002"}')

HAS_KNOWLEDGE=$(echo "$RESPONSE" | python3 -c "import json, sys; print(json.load(sys.stdin)['data']['has_relevant_knowledge'])")
SOURCES=$(echo "$RESPONSE" | python3 -c "import json, sys; sources = json.load(sys.stdin)['data']['sources']; print(len(sources))")

echo "  ✅ Conocimiento local: $HAS_KNOWLEDGE"
echo "  📚 Fuentes usadas: $SOURCES"
echo ""

# Test 3: Procedimientos
echo "📋 Test 3: Procedimientos registrales"
echo "---"
RESPONSE=$(curl -s "$API" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"message":"¿Cuáles son los procedimientos para registrar un acto?","session_id":"rag-test-003"}')

HAS_KNOWLEDGE=$(echo "$RESPONSE" | python3 -c "import json, sys; print(json.load(sys.stdin)['data']['has_relevant_knowledge'])")
SOURCES=$(echo "$RESPONSE" | python3 -c "import json, sys; sources = json.load(sys.stdin)['data']['sources']; print(len(sources))")

echo "  ✅ Conocimiento local: $HAS_KNOWLEDGE"
echo "  📚 Fuentes usadas: $SOURCES"
echo ""

# Test 4: Definiciones (diccionario)
echo "📋 Test 4: Definiciones de actos registrables"
echo "---"
RESPONSE=$(curl -s "$API" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"message":"¿Qué significa inscripción de propiedad?","session_id":"rag-test-004"}')

HAS_KNOWLEDGE=$(echo "$RESPONSE" | python3 -c "import json, sys; print(json.load(sys.stdin)['data']['has_relevant_knowledge'])")
SOURCES=$(echo "$RESPONSE" | python3 -c "import json, sys; sources = json.load(sys.stdin)['data']['sources']; print(len(sources))")

echo "  ✅ Conocimiento local: $HAS_KNOWLEDGE"
echo "  📚 Fuentes usadas: $SOURCES"
echo ""

echo "=============================================="
echo "✅ PRUEBAS COMPLETADAS"
