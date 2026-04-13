#!/bin/bash

# backup.sh - Script para crear backups de todos los datos persistentes

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="consulta-rpp-backup_$TIMESTAMP"

echo "💾 Iniciando backup completo - $TIMESTAMP"
echo "📁 Directorio de backup: $BACKUP_DIR"
echo ""

# Crear directorio de backup específico
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup de PostgreSQL
echo "🗄️  Haciendo backup de PostgreSQL..."
if docker ps | grep -q consultarpp-postgres; then
    docker exec consultarpp-postgres pg_dump -U consultarpp_user -d consultarpp_db | gzip > "$BACKUP_DIR/$BACKUP_NAME/postgres_dump.sql.gz"
    SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME/postgres_dump.sql.gz" | cut -f1)
    echo "   ✅ PostgreSQL backup: $SIZE"
else
    echo "   ⚠️  PostgreSQL no está ejecutándose, saltando..."
fi

# Backup de Redis
echo "🔴 Haciendo backup de Redis..."
if docker ps | grep -q consultarpp-redis; then
    docker exec consultarpp-redis redis-cli -a redis_secure_2026 BGSAVE > /dev/null 2>&1
    sleep 2
    if [[ -f "$PROJECT_ROOT/data/redis/dump.rdb" ]]; then
        cp "$PROJECT_ROOT/data/redis/dump.rdb" "$BACKUP_DIR/$BACKUP_NAME/redis_dump.rdb"
        SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME/redis_dump.rdb" | cut -f1)
        echo "   ✅ Redis backup: $SIZE"
    else
        echo "   ⚠️  redis/dump.rdb no encontrado"
    fi
else
    echo "   ⚠️  Redis no está ejecutándose, saltando..."
fi

# Backup de Attachments
echo "📎 Haciendo backup de Attachments..."
if [[ -d "$PROJECT_ROOT/data/attachments" ]]; then
    tar -czf "$BACKUP_DIR/$BACKUP_NAME/attachments.tar.gz" -C "$PROJECT_ROOT/data" attachments/ 2>/dev/null
    SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME/attachments.tar.gz" | cut -f1)
    echo "   ✅ Attachments backup: $SIZE"
else
    echo "   ⚠️  Carpeta attachments no encontrada"
fi

# Backup de Variables de Entorno
echo "🔐 Haciendo backup de configuración..."
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    cp "$PROJECT_ROOT/.env" "$BACKUP_DIR/$BACKUP_NAME/.env.backup"
    echo "   ✅ Variables de entorno backupeadas"
fi

# Backup de Configuración Docker
if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
    cp "$PROJECT_ROOT/docker-compose.yml" "$BACKUP_DIR/$BACKUP_NAME/docker-compose.yml.backup"
    echo "   ✅ Docker Compose backupeado"
fi

# Crear archivo de metadatos
cat > "$BACKUP_DIR/$BACKUP_NAME/BACKUP_INFO.txt" <<EOF
Backup ConsultaRPP
Fecha: $TIMESTAMP
Sistema: $(uname -s)
Versión Docker: $(docker --version 2>/dev/null || echo "N/A")

Contenido:
- postgres_dump.sql.gz: Dump completo de PostgreSQL
- redis_dump.rdb: Snapshot de Redis
- attachments.tar.gz: Archivos subidos por usuarios
- .env.backup: Variables de entorno
- docker-compose.yml.backup: Configuración Docker

Restauración:
1. gunzip < postgres_dump.sql.gz | docker exec -i consultarpp-postgres psql -U consultarpp_user -d consultarpp_db
2. cp redis_dump.rdb ../data/redis/dump.rdb && docker-compose restart redis
3. tar -xzf attachments.tar.gz -C ../data/
EOF

# Comprimir backup completo
echo ""
echo "📦 Comprimiendo backup..."
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"/
TOTAL_SIZE=$(du -h "$BACKUP_NAME.tar.gz" | cut -f1)
echo "   ✅ Backup comprimido: $TOTAL_SIZE"

# Limpiar carpeta descomprimida
rm -rf "$BACKUP_NAME"

echo ""
echo "✅ Backup completado exitosamente"
echo "📍 Ubicación: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo ""

# Limpieza de backups antiguos (mantener últimos 7)
echo "🧹 Limpiando backups antiguos..."
cd "$BACKUP_DIR"
ls -t1 consulta-rpp-backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -v
echo "   ✅ Limpieza completada"

echo ""
echo "💡 Tip: Configura un cron job para backups automáticos:"
echo "   # Backup diario a las 2 AM"
echo "   0 2 * * * cd $PROJECT_ROOT && ./scripts/backup.sh >> ./data/backups/backup.log 2>&1"
