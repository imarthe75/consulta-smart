#!/bin/bash
# Quality Gates Script - Run all tests and coverage

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  CONSULTA RPP - QUALITY GATES VALIDATION                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"

WORKSPACE=$(git rev-parse --show-toplevel)
cd "$WORKSPACE"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# ============================================================================
# BACKEND TESTS & COVERAGE
# ============================================================================

echo -e "\n${BLUE}📊 Running Backend Tests & Coverage...${NC}"

cd backend

# Run tests with coverage
if pytest tests \
    --cov=app \
    --cov-report=term \
    --cov-report=html \
    --cov-report=json \
    --cov-fail-under=80 \
    -v; then
    echo -e "${GREEN}✅ Backend tests passed with coverage > 80%${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Backend tests failed${NC}"
    FAILED=$((FAILED + 1))
fi

cd ..

# ============================================================================
# FRONTEND TESTS & COVERAGE
# ============================================================================

echo -e "\n${BLUE}📊 Running Frontend Tests & Coverage...${NC}"

cd frontend

if npm run test:coverage -- --run; then
    echo -e "${GREEN}✅ Frontend tests passed${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Frontend tests failed${NC}"
    FAILED=$((FAILED + 1))
fi

cd ..

# ============================================================================
# SECURITY VALIDATION
# ============================================================================

echo -e "\n${BLUE}🔒 Running Security Validation...${NC}"

# Check for hardcoded secrets (basic)
if ! grep -r "password\s*=\s*['\"]" --include="*.py" --include="*.ts" --include="*.tsx" . \
    --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=venv \
    2>/dev/null | grep -v "password_hash" | grep -v ".example"; then
    echo -e "${GREEN}✅ No hardcoded secrets detected${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Review potential hardcoded secrets${NC}"
fi

# Check for SQL injection patterns
if ! grep -r "execute.*f['\"]" --include="*.py" backend/app 2>/dev/null; then
    echo -e "${GREEN}✅ No raw SQL detected (using parameterized queries)${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Potential SQL injection risk${NC}"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# LINTING
# ============================================================================

echo -e "\n${BLUE}🎯 Running Linters...${NC}"

# Python linting
if command -v pylint &> /dev/null; then
    if pylint backend/app --disable=all --enable=E,F,C0114,C0115 -q 2>/dev/null; then
        echo -e "${GREEN}✅ Python linting passed${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${YELLOW}⚠️  Python linting issues (non-critical)${NC}"
    fi
fi

# ============================================================================
# PERFORMANCE CHECK
# ============================================================================

echo -e "\n${BLUE}⚡ Checking Performance Metrics...${NC}"

# Check bundle size
cd frontend
if [ -d "dist" ]; then
    BUNDLE_SIZE=$(du -sh dist | cut -f1)
    echo -e "${GREEN}✅ Bundle size: $BUNDLE_SIZE${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Distribution not built${NC}"
fi
cd ..

# ============================================================================
# DOCKER BUILD TEST
# ============================================================================

echo -e "\n${BLUE}🐳 Testing Docker Build...${NC}"

if docker-compose config > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Compose configuration valid${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Docker Compose configuration invalid${NC}"
    FAILED=$((FAILED + 1))
fi

# ============================================================================
# DEPLOYMENT READINESS
# ============================================================================

echo -e "\n${BLUE}🚀 Checking Deployment Readiness...${NC}"

# Check required files
REQUIRED_FILES=(
    "backend/requirements.txt"
    "frontend/package.json"
    "docker-compose.yml"
    ".env.example"
    "README.md"
    "docs/ARCHITECTURE.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ Found: $file${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing: $file${NC}"
    fi
done

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo -e "║                      QUALITY GATES SUMMARY                     ║"
echo -e "╚════════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}✅ Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Failed: $FAILED${NC}"
    echo -e "\n${RED}❌ Quality gates validation FAILED${NC}"
    exit 1
else
    echo -e "\n${GREEN}✅ All quality gates PASSED${NC}"
    echo -e "${GREEN}✅ Ready for deployment${NC}"
    
    # Show coverage reports location
    echo -e "\n${BLUE}📊 Coverage Reports:${NC}"
    echo "  Backend: file://$WORKSPACE/backend/htmlcov/index.html"
    echo "  Frontend: file://$WORKSPACE/frontend/coverage/index.html"
    
    exit 0
fi
