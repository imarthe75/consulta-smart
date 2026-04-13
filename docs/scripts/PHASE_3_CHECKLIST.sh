#!/bin/bash

# 🎉 ConsultaRPP - Phase 3 Completion Checklist
# Frontend React 19 Implementation Verification
# April 7, 2026

echo ""
echo "╔═════════════════════════════════════════════════════════════╗"
echo "║        ConsultaRPP Phase 3 - Checklist & Verification      ║"
echo "║              Frontend React 19 Implementation               ║"
echo "╚═════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

score=0
total=0

check_item() {
    local name=$1
    local condition=$2
    total=$((total + 1))
    
    if eval "$condition"; then
        echo -e "${GREEN}✅${NC} $name"
        score=$((score + 1))
    else
        echo -e "${RED}❌${NC} $name"
    fi
}

echo -e "${BLUE}📦 PROJECT STRUCTURE${NC}"
check_item "frontend/ directory exists" "[ -d frontend ]"
check_item "src/ directory exists" "[ -d frontend/src ]"
check_item "public/ directory exists" "[ -d frontend/public ]"

echo ""
echo -e "${BLUE}📋 CONFIGURATION FILES${NC}"
check_item "package.json exists" "[ -f frontend/package.json ]"
check_item "package.json contains React 19" "grep -q 'react.*19' frontend/package.json"
check_item "vite.config.js exists" "[ -f frontend/vite.config.js ]"
check_item "tailwind.config.js exists" "[ -f frontend/tailwind.config.js ]"
check_item "tsconfig.json exists" "[ -f frontend/tsconfig.json ]"
check_item ".eslintrc.json exists" "[ -f frontend/.eslintrc.json ]"
check_item "postcss.config.js exists" "[ -f frontend/postcss.config.js ]"
check_item "index.html exists" "[ -f frontend/index.html ]"

echo ""
echo -e "${BLUE}🔧 REACT COMPONENTS${NC}"
check_item "App.jsx exists" "[ -f frontend/src/App.jsx ]"
check_item "main.jsx exists" "[ -f frontend/src/main.jsx ]"
check_item "Navigation.jsx exists" "[ -f frontend/src/components/Navigation.jsx ]"
check_item "ChatInterface.jsx exists" "[ -f frontend/src/components/ChatInterface.jsx ]"
check_item "DocumentUpload.jsx exists" "[ -f frontend/src/components/DocumentUpload.jsx ]"
check_item "SearchResults.jsx exists" "[ -f frontend/src/components/SearchResults.jsx ]"

echo ""
echo -e "${BLUE}📄 PAGE LAYOUTS${NC}"
check_item "ChatPage.jsx exists" "[ -f frontend/src/pages/ChatPage.jsx ]"
check_item "LoginPage.jsx exists" "[ -f frontend/src/pages/LoginPage.jsx ]"
check_item "DocumentsPage.jsx exists" "[ -f frontend/src/pages/DocumentsPage.jsx ]"
check_item "ResultsPage.jsx exists" "[ -f frontend/src/pages/ResultsPage.jsx ]"

echo ""
echo -e "${BLUE}🗂️  STATE MANAGEMENT${NC}"
check_item "authStore.js exists" "[ -f frontend/src/stores/authStore.js ]"
check_item "chatStore.js exists" "[ -f frontend/src/stores/chatStore.js ]"
check_item "documentStore.js exists" "[ -f frontend/src/stores/documentStore.js ]"
check_item "authStore uses Zustand" "grep -q 'zustand' frontend/src/stores/authStore.js"

echo ""
echo -e "${BLUE}🔌 API INTEGRATION${NC}"
check_item "api.js exists" "[ -f frontend/src/services/api.js ]"
check_item "API uses Axios" "grep -q 'axios' frontend/src/services/api.js"
check_item "Auth endpoints defined" "grep -q 'authAPI' frontend/src/services/api.js"
check_item "Documents endpoints defined" "grep -q 'documentsAPI' frontend/src/services/api.js"
check_item "Chat endpoints defined" "grep -q 'chatAPI' frontend/src/services/api.js"
check_item "Search endpoints defined" "grep -q 'searchAPI' frontend/src/services/api.js"

echo ""
echo -e "${BLUE}🌐 INTERNATIONALIZATION${NC}"
check_item "translations.js exists" "[ -f frontend/src/i18n/translations.js ]"
check_item "i18n hooks exist" "[ -f frontend/src/i18n/hooks.js ]"
check_item "Spanish translations present" "grep -q 'Iniciar sesión' frontend/src/i18n/translations.js"
check_item "Chat translations present" "grep -q 'Nueva Sesión' frontend/src/i18n/translations.js"
check_item "Document translations present" "grep -q 'Gestión de Documentos' frontend/src/i18n/translations.js"

echo ""
echo -e "${BLUE}🎨 STYLING & ASSETS${NC}"
check_item "index.css exists" "[ -f frontend/src/index.css ]"
check_item "Tailwind CSS imported" "grep -q '@tailwind' frontend/src/index.css"
check_item "Custom animations defined" "grep -q 'animate-fadeIn' frontend/src/index.css"
check_item "public/ folder exists" "[ -d frontend/public ]"

echo ""
echo -e "${BLUE}📚 DOCUMENTATION${NC}"
check_item "README.md exists" "[ -f frontend/README.md ]"
check_item "README mentions React 19" "grep -q 'React 19' frontend/README.md"
check_item ".env.example exists" "[ -f frontend/src/.env.example ]"
check_item ".gitignore exists" "[ -f frontend/.gitignore ]"
check_item ".gitignore excludes node_modules" "grep -q 'node_modules' frontend/.gitignore"

echo ""
echo -e "${BLUE}✏️  CODE QUALITY${NC}"
check_item "ESLint config present" "[ -f frontend/.eslintrc.json ]"
check_item "React plugin in eslint" "grep -q 'react' frontend/.eslintrc.json"
check_item "TypeScript config present" "[ -f frontend/tsconfig.json ]"
check_item "App requires Router" "grep -q 'BrowserRouter\\|useAuthStore' frontend/src/App.jsx"

echo ""
echo -e "${BLUE}🔐 SECURITY${NC}"
check_item "JWT token handling" "grep -q 'localStorage.getItem.*token' frontend/src/stores/authStore.js"
check_item "Auth interceptors" "grep -q 'Authorization' frontend/src/services/api.js"
check_item "Protected routes" "grep -q 'protected\\|isAuthenticated' frontend/src/App.jsx"
check_item "Login form has password field" "grep -q 'type=\"password\"' frontend/src/pages/LoginPage.jsx"

echo ""
echo -e "${BLUE}📊 DEPENDENCIES${NC}"
check_item "React dependency" "grep -q '\"react\"' frontend/package.json"
check_item "Vite dependency" "grep -q '\"vite\"' frontend/package.json"
check_item "Tailwind CSS dependency" "grep -q 'tailwindcss' frontend/package.json"
check_item "React Router dependency" "grep -q 'react-router-dom' frontend/package.json"
check_item "Zustand dependency" "grep -q 'zustand' frontend/package.json"
check_item "Axios dependency" "grep -q 'axios' frontend/package.json"

echo ""
echo "╔═════════════════════════════════════════════════════════════╗"
echo -e "║           ${BLUE}PHASE 3 COMPLETION REPORT${NC}                    ║"
echo "╠═════════════════════════════════════════════════════════════╣"
echo -e "║ Items Passed: ${GREEN}$score / $total${NC}                                 ║"

percentage=$((score * 100 / total))
echo -e "║ Completion: ${BLUE}${percentage}%${NC}                                    ║"

if [ $score -eq $total ]; then
    echo -e "║ Status: ${GREEN}✅ COMPLETE${NC}                                     ║"
else
    missing=$((total - score))
    echo -e "║ Missing: ${RED}$missing items${NC}                                      ║"
fi

echo "╚═════════════════════════════════════════════════════════════╝"
echo ""

if [ $score -eq $total ]; then
    echo -e "${GREEN}🎉 Phase 3 is COMPLETE and READY for integration testing!${NC}"
    echo ""
    echo "📝 Next Steps:"
    echo "1. npm install dependencies"
    echo "2. Configure .env variables"
    echo "3. npm run dev to test frontend"
    echo "4. Run backend API server"
    echo "5. Test all API integrations"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  Please review failed items above${NC}"
    exit 1
fi
