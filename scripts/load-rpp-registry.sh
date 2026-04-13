#!/bin/bash

# load-rpp-registry.sh - Trigger the RAG registry loading process

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Triggering RPP Registry Loading...${NC}"

# Import config
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DEMO_USER_EMAIL=${DEMO_USER_EMAIL:-demo@example.com}
DEMO_USER_PASSWORD=${DEMO_USER_PASSWORD:-password123}

# Step 1: Get Token
echo -e "${BLUE}🔐 Authenticating...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST \
    http://localhost:3001/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$DEMO_USER_EMAIL&password=$DEMO_USER_PASSWORD")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Error obtaining token${NC}"
    exit 1
fi

# Step 2: Trigger Registry Load
echo -e "${BLUE}📚 Loading RPP Registry Documents...${NC}"
LOAD_RESPONSE=$(curl -s -X POST \
    "http://localhost:3001/api/v1/documents/load-rpp-registry" \
    -H "Authorization: Bearer $TOKEN")

echo -e "${GREEN}✅ Load triggered! Response:${NC}"
echo "$LOAD_RESPONSE" | python3 -m json.tool

echo ""
echo -e "${GREEN}Done! The documents are being processed into chunks and embeddings.${NC}"
