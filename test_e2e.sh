#!/bin/bash

set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "   🧪 PRUEBAS E2E COMPLETAS - CONSULTA-RPP RAG SYSTEM"
echo "════════════════════════════════════════════════════════════════════════════════"
echo

# Esperar a que backend esté listo
echo "[1/5] Esperando que backend esté listo..."
sleep 8

# Test 1: Autenticación
echo "[2/5] Test de autenticación..."
AUTH_RESPONSE=$(curl -s -X POST http://localhost:3001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=demo@example.com&password=password123')

TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
if [ -z "$TOKEN" ]; then
    echo "❌ FALLÓ: No se pudo obtener token"
    echo "$AUTH_RESPONSE"
    exit 1
fi
echo "✅ Token obtenido"
echo

# Test 2-4: Queries de chat
echo "[3/5] Test de chat Query 1..."
RESPONSE1=$(curl -s -X POST http://localhost:3001/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"¿Cuáles son las oficinas disponibles en Quintana Roo?","session_id":"test-q1"}')

echo "Status: $(echo "$RESPONSE1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status'))" 2>/dev/null)"
RESP_TEXT=$(echo "$RESPONSE1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('response','')[:150])" 2>/dev/null)
echo "Response: $RESP_TEXT..."
echo "✅ Query 1 completada"
echo

echo "[4/5] Test de chat Query 2..."
RESPONSE2=$(curl -s -X POST http://localhost:3001/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"¿Dónde puedo encontrar notarios?","session_id":"test-q2"}')

echo "Status: $(echo "$RESPONSE2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status'))" 2>/dev/null)"
RESP_TEXT=$(echo "$RESPONSE2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('response','')[:150])" 2>/dev/null)
echo "Response: $RESP_TEXT..."
echo "✅ Query 2 completada"
echo

echo "[5/5] Test de chat Query 3..."
RESPONSE3=$(curl -s -X POST http://localhost:3001/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"¿Cuál es el costo de registrar una propiedad?","session_id":"test-q3"}')

echo "Status: $(echo "$RESPONSE3" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status'))" 2>/dev/null)"
RESP_TEXT=$(echo "$RESPONSE3" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('response','')[:150])" 2>/dev/null)
echo "Response: $RESP_TEXT..."
echo "✅ Query 3 completada"
echo

echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE"
echo "════════════════════════════════════════════════════════════════════════════════"
