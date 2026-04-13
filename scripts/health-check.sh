#!/usr/bin/env bash
# System Health Check Script for PropQuery

set -e

echo "🔍 PropQuery System Health Check"
echo "================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to check and report
check_service() {
    local name=$1
    local cmd=$2
    local is_docker=$3
    
    if [ "$is_docker" = "true" ]; then
        if docker-compose ps | grep -q "$name.*Up"; then
            echo -e "${GREEN}✅${NC} $name - Running"
            ((PASSED++))
        else
            echo -e "${RED}❌${NC} $name - Not running"
            ((FAILED++))
        fi
    else
        if eval "$cmd" > /dev/null 2>&1; then
            echo -e "${GREEN}✅${NC} $name"
            ((PASSED++))
        else
            echo -e "${RED}❌${NC} $name"
            ((FAILED++))
        fi
    fi
}

# Check Docker installation
echo "1️⃣  Environment Checks"
echo "─────────────────────"

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅${NC} Docker installed"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} Docker not installed"
    ((FAILED++))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✅${NC} Docker Compose installed"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} Docker Compose not installed"
    ((FAILED++))
fi

# Check .env file
if [ -f .env ]; then
    echo -e "${GREEN}✅${NC} .env file exists"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️${NC}  .env file missing (using .env.example)"
    ((WARNINGS++))
fi

echo ""
echo "2️⃣  Docker Services"
echo "──────────────────"

# Check if docker-compose is running
if docker-compose ps &> /dev/null; then
    check_service "postgres" "" "true"
    check_service "redis" "" "true"
    check_service "seaweedfs-master" "" "true"
    check_service "seaweedfs-volume" "" "true"
    check_service "backend" "" "true"
    check_service "frontend" "" "true"
else
    echo -e "${YELLOW}⚠️${NC}  Docker services not running"
    echo "   Run: docker-compose up -d"
    ((WARNINGS++))
fi

echo ""
echo "3️⃣  Backend API"
echo "───────────────"

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Backend health check"
    ((PASSED++))
    
    # Try to get health details
    if curl -s http://localhost:8000/health/detailed | grep -q "healthy"; then
        echo -e "${GREEN}✅${NC} Backend full health check"
        ((PASSED++))
    fi
else
    echo -e "${RED}❌${NC} Backend not responding"
    ((FAILED++))
fi

echo ""
echo "4️⃣  Database Connectivity"
echo "─────────────────────────"

if docker-compose exec -T postgres pg_isready -U $(grep DB_USER .env 2>/dev/null | cut -d= -f2) > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} PostgreSQL ready"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} PostgreSQL not ready"
    ((FAILED++))
fi

echo ""
echo "5️⃣  Cache/Message Queue"
echo "──────────────────────"

if docker-compose exec -T redis valkey-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Valkey/Redis responding"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} Valkey/Redis not responding"
    ((FAILED++))
fi

echo ""
echo "6️⃣  File Storage"
echo "────────────────"

if curl -s http://localhost:9333/cluster/status > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} SeaweedFS Master ready"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} SeaweedFS Master not ready"
    ((FAILED++))
fi

if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} SeaweedFS Volume ready"
    ((PASSED++))
else
    echo -e "${RED}❌${NC} SeaweedFS Volume not ready"
    ((FAILED++))
fi

echo ""
echo "7️⃣  Application URLs"
echo "────────────────────"

echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Frontend: http://localhost:5173"
echo "   SeaweedFS: http://localhost:9333"

echo ""
echo "════════════════════════════════════"
echo "📊 Summary"
echo "════════════════════════════════════"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ System is healthy!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ System has issues. Check logs:${NC}"
    echo "   docker-compose logs -f [service]"
    exit 1
fi
