#!/bin/bash

# setup-volumes.sh - Script para configurar volúmenes de persistencia

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"

echo "🔧 Configurando volúmenes de persistencia para ConsultaRPP..."
echo "📁 Raíz del proyecto: $PROJECT_ROOT"
echo ""

# Crear carpetas principales
echo "📦 Creando estructura de carpetas..."
mkdir -p "$DATA_DIR"/{postgres,redis,celery,attachments}

# PostgreSQL
echo "🗄️  Configurando PostgreSQL..."
mkdir -p "$DATA_DIR/postgres"
chmod 700 "$DATA_DIR/postgres"
echo "   ✅ Carpeta postgres creada con permisos 700"

# Redis
echo "🔴 Configurando Redis..."
mkdir -p "$DATA_DIR/redis"
chmod 755 "$DATA_DIR/redis"
echo "   ✅ Carpeta redis creada con permisos 755"

# Celery
echo "⚙️  Configurando Celery..."
mkdir -p "$DATA_DIR/celery"/{logs,results}
chmod 755 "$DATA_DIR/celery"
echo "   ✅ Carpeta celery creada con permisos 755"

# Attachments
echo "📎 Configurando Attachments..."
mkdir -p "$DATA_DIR/attachments"/{uploads,processed}
chmod 755 "$DATA_DIR/attachments"
echo "   ✅ Carpeta attachments creada con permisos 755"

# Backups
echo "💾 Creando carpeta de backups..."
mkdir -p "$DATA_DIR/backups"
chmod 755 "$DATA_DIR/backups"
echo "   ✅ Carpeta backups integrada en data/"

echo ""
echo "📊 Resumen de carpetas creadas:"
tree -L 2 "$DATA_DIR" 2>/dev/null || find "$DATA_DIR" -type d | sort

echo ""
echo "✅ Volúmenes configurados correctamente"
echo ""
echo "🚀 Próximos pasos:"
echo "   1. docker-compose build"
echo "   2. docker-compose up -d"
echo "   3. ./load_rpp_docs.sh"
