#!/bin/bash

# Simple script to load sample documents into database using direct SQL

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📚 Cargando documentos de ejemplo...${NC}"

# Config
export PGPASSWORD="***DB_PASSWORD_REDACTED***"
DB_USER="consultarpp_user"
DB_NAME="consultarpp"
DB_HOST="127.0.0.1"

# Crear un documento simple de prueba
SIMPLE_CONTENT="Notarios en Quintana Roo:
- Notaría 1: Carlos Bazán Castro, Tel: 9988841293
- Notaría 2: María López García, Tel: 9981234567
- Notaría 3: Juan Pérez Ruiz, Tel: 9989876543

Derechos y Costos para Escrituras en Quintana Roo:
- Compraventa: 0.67% del valor catastral
- Poder notarial: 3,500 a 7,000 pesos
- Testamentaría: 2,000 a 5,000 pesos"

# Insertar documento
DOC_ID=$(uuidgen | tr -d '-')
docker exec consultarpp-postgres psql \
  -h localhost \
  -U "$DB_USER" \
  -d "$DB_NAME" << EOSQL
-- Insertar documento
INSERT INTO documents (id, title, category, user_id, file_type, created_at, updated_at)
VALUES (
  '$DOC_ID'::uuid,
  'Notarios y Derechos - Quintana Roo',
  'documentacion',
  NULL,
  'txt',
  NOW(),
  NOW()
);

-- Insertar algunos chunks de ejemplo (con embeddings fake por ahora)
INSERT INTO document_chunks (document_id, content, position, embedding, created_at)
VALUES 
  ('$DOC_ID'::uuid, 'Notarios en Quintana Roo: Carlos Bazán Castro - Tel 9988841293', 0, '.{383}'::vector, NOW()),
  ('$DOC_ID'::uuid, 'Notarios en Quintana Roo: María López García - Tel 9981234567', 1, '.{383}'::vector, NOW()),
  ('$DOC_ID'::uuid, 'Derechos de Compraventa: 0.67% del valor catastral', 2, '.{383}'::vector, NOW()),
  ('$DOC_ID'::uuid, 'Poder notarial cuesta 3,500 a 7,000 pesos en Quintana Roo', 3, '.{383}'::vector, NOW());

SELECT COUNT(*) as chunks_inserted FROM document_chunks;
EOSQL

echo -e "${GREEN}✅ Documento de ejemplo cargado${NC}"

# Verificar
echo -e "\n${BLUE}📊 Verificando datos...${NC}"
CHUNK_COUNT=$(docker exec consultarpp-postgres psql -h localhost -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM document_chunks;")
DOC_COUNT=$(docker exec consultarpp-postgres psql -h localhost -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM documents;")

echo -e "${GREEN}   📄 Documentos: $DOC_COUNT${NC}"
echo -e "${GREEN}   📋 Chunks: $CHUNK_COUNT${NC}"

echo -e "\n${GREEN}✅ COMPLETADO${NC}"
