#!/bin/bash

################################################################################
# SCRIPT: sync-repos.sh (SELECTIVO - Solo código compartible)
# PURPOSE: Sincronizar SOLO código reutilizable entre repositorios
# ⚠️  CUIDADO: consulta-rpp e idp-smart son INDEPENDIENTES
#      Solo sincronizar carpetas específicas, NO TODO
# SAFETY: Excluye .env, secretos, logs, datos de usuario/cliente
# USAGE: bash scripts/sync-repos.sh [OPTIONS]
################################################################################

set -euo pipefail

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Rutas válidas
CONSULTA_RPP="/home/ia/consulta-rpp"
IDP_SMART="/home/ia/idp-smart"

# ⚠️  CARPETAS SINCRONIZABLES (SOLO CÓDIGO COMPARTIBLE)
# NO incluir: backend app/, frontend/, workers/, docker-compose.yml
SYNC_FOLDERS=(
    "scripts/"                    # Scripts utilities (backup, healthcheck, etc)
    "infrastructure/"             # Config patterns (nginx, postgres, redis, k8s)
    "docs/EXPLICACIONES/"         # Documentación template (crear si no existe)
)

# Archivos y directorios a EXCLUIR (datos sensibles + project-specific)
EXCLUDE_PATTERNS=(
    ".env"
    ".env.local"
    ".env.*.local"
    "*.key"
    "*.pem"
    "*.pfx"
    "*.p12"
    "secrets/"
    "credentials/"
    "__pycache__/"
    "*.pyc"
    "*.pyo"
    ".pytest_cache/"
    ".coverage"
    "node_modules/"
    "venv/"
    "env/"
    ".venv"
    "*.log"
    "logs/"
    "samples/"
    "datasets/"
    ".git/"
    ".DS_Store"
    "Thumbs.db"
    "test_payload.json"
    "benchmark_docling.py"
    "campos formas precodificadas.xlsx"
)

# Función: Mostrar uso
usage() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}SINCRONIZAR REPOSITORIOS (Solo código COMPARTIBLE)${NC}"
    echo -e "${BLUE}⚠️  consulta-rpp e idp-smart son INDEPENDIENTES${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "\nUSO: bash scripts/sync-repos.sh [OPCIÓN]\n"
    echo -e "OPCIONES:"
    echo -e "  ${GREEN}status${NC}          Mostrar qué se sincronizaría (DRY RUN)"
    echo -e "  ${GREEN}check${NC}           Listar carpetas sincronizables"
    echo -e "  ${GREEN}sync${NC}            Sincronizar SOLO código compartible"
    echo -e "  ${GREEN}gitignore${NC}       Actualizar .gitignore en ambos repos"
    echo -e "  ${GREEN}help${NC}            Mostrar este mensaje"
    echo -e "\nCARPETAS SINCRONIZABLES:"
    for folder in "${SYNC_FOLDERS[@]}"; do
        echo -e "  • $folder"
    done
    echo -e "\nCARPETAS QUE NO SE SINCRONIZAN (Independientes):"
    echo -e "  ✗ backend/app/       (lógica específica por proyecto)"
    echo -e "  ✗ frontend/          (UI específica por proyecto)"
    echo -e "  ✗ localai/           (idp-smart only - inference)"
    echo -e "  ✗ database/          (schemas específicos)"
    echo -e "  ✗ docker-compose.yml (diferente por proyecto)"
    echo -e "  ✗ Dockerfile         (diferente por proyecto)"
    echo -e "\nEJEMPLOS:"
    echo -e "  bash scripts/sync-repos.sh status"
    echo -e "  bash scripts/sync-repos.sh sync"
    echo -e "\n"
}

# Función: Generar parámetros rsync EXCLUDE
build_exclude_args() {
    local args=""
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        args="$args --exclude='$pattern'"
    done
    echo "$args"
}

# Función: Validar que repos existen
validate_repos() {
    if [[ ! -d "$CONSULTA_RPP" ]]; then
        echo -e "${RED}✗ Error: $CONSULTA_RPP no existe${NC}"
        exit 1
    fi
    if [[ ! -d "$IDP_SMART" ]]; then
        echo -e "${RED}✗ Error: $IDP_SMART no existe${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Ambos repositorios validados${NC}"
}

# Función: Mostrar carpetas sincronizables
check_folders() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}CARPETAS SINCRONIZABLES${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
    
    for folder in "${SYNC_FOLDERS[@]}"; do
        if [[ -d "$CONSULTA_RPP/$folder" ]]; then
            file_count=$(find "$CONSULTA_RPP/$folder" -type f | wc -l)
            dir_count=$(find "$CONSULTA_RPP/$folder" -type d | wc -l)
            echo -e "${GREEN}✓${NC} $folder"
            echo -e "   └─ $file_count archivos, $dir_count directorios"
        else
            echo -e "${YELLOW}○${NC} $folder (no existe en consulta-rpp)"
        fi
    done
    
    echo -e "\n${BLUE}─────────────────────────────────────────────────────────────${NC}"
    echo -e "${RED}CARPETAS QUE NO SE SINCRONIZAN (Independientes):${NC}\n"
    
    independent_folders=(
        "backend/app"
        "frontend"
        "localai"
        "docker-compose.yml"
        "Dockerfile"
    )
    
    for folder in "${independent_folders[@]}"; do
        echo -e "  ${RED}✗${NC} $folder"
    done
}

# Función: Mostrar estado (qué se sincronizaría)
show_status() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}STATUS: Vista previa de cambios (DRY RUN)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
    
    local exclude_args=$(build_exclude_args)
    
    for folder in "${SYNC_FOLDERS[@]}"; do
        if [[ -d "$CONSULTA_RPP/$folder" ]]; then
            echo -e "${YELLOW}Carpeta: $folder${NC}"
            rsync -av --dry-run $exclude_args "$CONSULTA_RPP/$folder" "$IDP_SMART/${folder%/}/" 2>/dev/null | grep "^>" | head -5 || echo "  (sin cambios)"
            echo ""
        fi
    done
    
    echo -e "${BLUE}─────────────────────────────────────────────────────────────${NC}"
    echo -e "${YELLOW}⚠️  RECORDATORIO:${NC}"
    echo -e "  • Sincronización SELECTIVA SOLAMENTE"
    echo -e "  • Archivos project-specific NO se sincronizan"
    echo -e "  • .env, node_modules, logs SIEMPRE excluidos"
}

# Función: Realizar sincronización SELECTIVA
do_sync() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}⚠️  SINCRONIZACIÓN SELECTIVA - ÚLTIMA OPORTUNIDAD${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
    
    echo -e "${YELLOW}Se sincronizarán SOLO estas carpetas:${NC}"
    for folder in "${SYNC_FOLDERS[@]}"; do
        echo -e "  → $folder"
    done
    
    echo -e "\n${RED}NO se sincronizarán (protegidas):${NC}"
    echo -e "  ✗ backend/app/, frontend/, docker-compose.yml, Dockerfile"
    echo -e "\nEscribe ${RED}'confirmar'${NC} para continuar, o presiona Ctrl+C para cancelar:\n"
    
    read -p "> " confirmation
    
    if [[ "$confirmation" != "confirmar" ]]; then
        echo -e "${YELLOW}Cancelado por usuario.${NC}"
        exit 0
    fi
    
    local exclude_args=$(build_exclude_args)
    
    echo -e "\n${BLUE}Iniciando sincronización selectiva...${NC}\n"
    
    # Crear backup antes de sincronizar
    echo -e "${YELLOW}Creando backup de idp-smart...${NC}"
    if command -v git &> /dev/null && [[ -d "$IDP_SMART/.git" ]]; then
        cd "$IDP_SMART"
        git add -A
        git commit -m "backup: pre-sync selectiva de consulta-rpp $(date '+%Y-%m-%d %H:%M:%S')" --allow-empty
        cd "$CONSULTA_RPP"
        echo -e "${GREEN}✓ Backup creado en git${NC}\n"
    fi
    
    # Ejecutar rsync SELECTIVO (sin --delete para no borrar)
    for folder in "${SYNC_FOLDERS[@]}"; do
        if [[ -d "$CONSULTA_RPP/$folder" ]]; then
            echo -e "${BLUE}Sincronizando: $folder${NC}"
            rsync -av $exclude_args "$CONSULTA_RPP/$folder" "$IDP_SMART/${folder%/}/"
            echo ""
        fi
    done
    
    echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ SINCRONIZACIÓN SELECTIVA COMPLETADA${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}\n"
    
    echo -e "Próximos pasos:"
    echo -e "  1. Revisar cambios: cd $IDP_SMART && git status"
    echo -e "  2. Validar integridad: cd $IDP_SMART && docker compose up --build"
    echo -e "  3. Commit si todo bien: git add -A && git commit"
}

# Función: Actualizar .gitignore en ambos repos
update_gitignore() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}GITIGNORE: Actualizar en ambos repos${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
    
    # Crear contenido estándar de .gitignore
    local gitignore_content="# ============================================================================
# GITIGNORE - Excluye archivos sensibles y temporales
# ============================================================================

# SECRETOS Y CREDENCIALES (NUNCA COMMITEAR)
.env
.env.local
.env.*.local
.env.production.local
.env.development.local
*.key
*.pem
*.pfx
*.p12
*.jks
secrets/
credentials/
.aws/
.gcloud/
.vault/

# PYTHON
__pycache__/
*.py[cod]
*\$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.pyc
*.pyo

# VIRTUAL ENVIRONMENTS
venv/
env/
ENV/
.venv
venv.bak/
env.bak/

# NODE
node_modules/
npm-debug.log
yarn-error.log
dist/
.nuxt/
package-lock.json
yarn.lock

# IDE & EDITOR
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db
*.sublime-project
*.sublime-workspace
*.code-workspace

# TESTING
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/
.mypy_cache/
.dmypy.json
dmypy.json

# LOGS (Nunca commitear logs de ejecución)
*.log
logs/
*.log.*
lerna-debug.log*

# OS FILES
.DS_Store
.AppleDouble
.LSOverride
Thumbs.db
desktop.ini

# TEMPORAL Y CACHÉ
.cache/
.tmp/
tmp/
temp/
*.tmp
*.bak
*.swp

# DATA SENSIBLES (Bases datos locales, datos de test real)
*.db
*.sqlite
*.sqlite3
data/
samples/
datasets/
test_data/
uploads/
downloads/

# TEST PAYLOADS (Pueden contener datos de ejemplo sensibles)
test_payload.json
test_payloads/

# EXCEL/ARCHIVOS DE DATOS (Pueden contener información sensible)
campos formas precodificadas.xlsx
*.xlsx
*.csv
!docs/*.csv
!docs/*.xlsx

# OUTPUT FILES (Resultados de ejecución)
output/
results/
reports/
*.pdf
*.docx

# DOCKER (Volúmenes locales)
docker/db-data/
docker/volumes/
.dockerignore

# KUBERNETES
k8s/secrets/
helm/values-prod.yaml

# GIT
.git/
"

    echo -e "${BLUE}Actualizando .gitignore...${NC}\n"
    
    for repo in "$CONSULTA_RPP" "$IDP_SMART"; do
        echo "$gitignore_content" > "$repo/.gitignore"
        echo -e "${GREEN}✓${NC} $repo/.gitignore actualizado"
    done
    
    echo -e "\n${BLUE}─────────────────────────────────────────────────────────────${NC}"
    echo -e "${GREEN}✓ .gitignore actualizado en ambos repos${NC}"
}

# ============================================================================
# MAIN
# ============================================================================

case "${1:-help}" in
    status)
        validate_repos
        show_status
        ;;
    check)
        validate_repos
        check_folders
        ;;
    sync)
        validate_repos
        do_sync
        ;;
    gitignore)
        validate_repos
        update_gitignore
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}Error: Opción desconocida '${1}'${NC}"
        usage
        exit 1
        ;;
esac

