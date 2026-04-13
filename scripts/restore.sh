#!/bin/bash

# restore.sh - Script para restaurar desde un backup

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/data/backups"

# Mostrar backups disponibles
echo "📦 Backups disponibles:"
ls -lh "$BACKUP_DIR"/consulta-rpp-backup_*.tar.gz 2>/dev/null || echo "   No hay backups disponibles"
echo ""

# Solicitar nombre del backup
read -p "Ingresa el nombre del backup a restaurar (ej: consulta-rpp-backup_20260409_120000.tar.gz): " BACKUP_FILE

if [[ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]]; then
    echo "❌ Error: Backup no encontrado: $BACKUP_FILE"
    exit 1
fi

echo ""
echo "⚠️  ADVERTENCIA: Esta operación sobrescribirá los datos actuales."
read -p "¿Deseas continuar? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Operación cancelada."
    exit 0
fi

echo ""
echo "🔄 Restaurando desde $BACKUP_FILE..."

# Extraer backup
EXTRACT_DIR="$BACKUP_DIR/restore_temp"
mkdir -p "$EXTRACT_DIR"
tar -xzf "$BACKUP_DIR/$BACKUP_FILE" -C "$EXTRACT_DIR"

# Buscar la carpeta descomprimida
BACKUP_EXTRACTED=$(ls -d "$EXTRACT_DIR"/consulta-rpp-backup_*/ | head -1)

echo ""
echo "🛑 Deteniendo contenedores..."
docker-compose down --remove-orphans

# Restaurar PostgreSQL
if [[ -f "$BACKUP_EXTRACTED/postgres_dump.sql.gz" ]]; then
    echo "🗄️  Restaurando PostgreSQL..."
    rm -rf "$PROJECT_ROOT/data/postgres"/*
    docker-compose up -d postgres
    
    # Esperar a que PostgreSQL esté listo
    echo "   Esperando a que PostgreSQL inicie..."
    sleep 10
    for i in {1..30}; do
        if docker exec consultarpp-postgres pg_isready -U consultarpp_user > /dev/null 2>&1; then
            echo "   ✅ PostgreSQL listo"
            break
        fi
        if [[ $i -eq 30 ]]; then
            echo "   ❌ PostgreSQL no respondiendo"
            exit 1
        fi
        sleep 2
    done
    
    gunzip -c "$BACKUP_EXTRACTED/postgres_dump.sql.gz" | docker exec -i consultarpp-postgres psql -U consultarpp_user -d consultarpp_db
    echo "   ✅ PostgreSQL restaurado"
else
    echo "   ⚠️  No se encontró backup de PostgreSQL"
fi

# Restaurar Redis
if [[ -f "$BACKUP_EXTRACTED/redis_dump.rdb" ]]; then
    echo "🔴 Restaurando Redis..."
    rm -rf "$PROJECT_ROOT/data/redis"/*
    cp "$BACKUP_EXTRACTED/redis_dump.rdb" "$PROJECT_ROOT/data/redis/dump.rdb"
    echo "   ✅ Redis restaurado"
else
    echo "   ⚠️  No se encontró backup de Redis"
fi

# Restaurar Attachments
if [[ -f "$BACKUP_EXTRACTED/attachments.tar.gz" ]]; then
    echo "📎 Restaurando Attachments..."
    rm -rf "$PROJECT_ROOT/data/attachments"
    tar -xzf "$BACKUP_EXTRACTED/attachments.tar.gz" -C "$PROJECT_ROOT/data/"
    echo "   ✅ Attachments restaurados"
else
    echo "   ⚠️  No se encontró backup de Attachments"
fi

# Restaurar variables de entorno si es necesario
if [[ -f "$BACKUP_EXTRACTED/.env.backup" ]] && [[ ! -f "$PROJECT_ROOT/.env" ]]; then
    echo "🔐 Restaurando variables de entorno..."
    cp "$BACKUP_EXTRACTED/.env.backup" "$PROJECT_ROOT/.env"
    echo "   ⚠️  Revisa las variables de entorno antes de continuar"
fi

# Limpiar
rm -rf "$EXTRACT_DIR"

echo ""
echo "🚀 Iniciando contenedores..."
docker-compose up -d

echo ""
echo "✅ Restauración completada"
echo ""
echo "📋 Verificaciones recomendadas:"
echo "   1. Revisar logs: docker-compose logs -f"
echo "   2. Verificar BD: docker exec consultarpp-postgres psql -U consultarpp_user -d consultarpp_db -c 'SELECT COUNT(*) FROM document_chunks;'"
echo "   3. Probar frontend: http://localhost:3000"
