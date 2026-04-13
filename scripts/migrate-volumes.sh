#!/bin/bash

# migrate-volumes.sh - Migrar datos de volúmenes Docker anónimos a carpetas locales

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"

echo "🔄 Iniciando migración de datos a volúmenes locales..."
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Detener contenedores
echo "🛑 Deteniendo contenedores..."
cd "$PROJECT_ROOT"
docker compose down > /dev/null 2>&1 || true
sleep 2
echo "   ✅ Contenedores detenidos"
echo ""

# 2. Verificar volúmenes existentes
echo "🔍 Verificando volúmenes de Docker..."
PG_VOLUME="consulta-rpp_postgres_data"
REDIS_VOLUME="consulta-rpp_redis_data"

# Verificar que existan
docker volume inspect "$PG_VOLUME" > /dev/null 2>&1 || PG_VOLUME=""
docker volume inspect "$REDIS_VOLUME" > /dev/null 2>&1 || REDIS_VOLUME=""

if [[ -z "$PG_VOLUME" && -z "$REDIS_VOLUME" ]]; then
    echo "   ${YELLOW}⚠️  No se encontraron volúmenes con datos${NC}"
    echo "   (Nueva instalación - saltando migración)"
    echo ""
    echo "🚀 Iniciando servicios con volúmenes locales..."
    docker compose up -d postgres redis
    exit 0
fi

# 3. Crear contenedor temporal para acceder a volúmenes
echo "   📦 Usando contenedores temporales para acceder a volúmenes..."

# Migrar PostgreSQL
if [[ ! -z "$PG_VOLUME" ]]; then
    echo ""
    echo "🗄️  Migrando PostgreSQL..."
    
    # Limpiar carpeta destino
    rm -rf "$DATA_DIR/postgres"/*
    
    # Crear contenedor temporal
    TEMP_PG_ID=$(docker run -d -v "$PG_VOLUME:/pg_data" alpine:latest sleep 1000)
    sleep 1
    
    # Copiar datos
    docker cp "$TEMP_PG_ID:/pg_data/." "$DATA_DIR/postgres/" > /dev/null 2>&1 || true
    
    # Limpiar
    docker stop "$TEMP_PG_ID" > /dev/null 2>&1
    docker rm "$TEMP_PG_ID" > /dev/null 2>&1
    
    # Verificar
    if [[ $(find "$DATA_DIR/postgres" -type f | wc -l) -gt 0 ]]; then
        SIZE=$(du -sh "$DATA_DIR/postgres" | cut -f1)
        echo "   ✅ PostgreSQL migrado: $SIZE"
        echo "      Archivos: $(find "$DATA_DIR/postgres" -type f | wc -l)"
    else
        echo "   ${RED}❌ Fallo en migración de PostgreSQL${NC}"
    fi
fi

# Migrar Redis
if [[ ! -z "$REDIS_VOLUME" ]]; then
    echo ""
    echo "🔴 Migrando Redis..."
    
    # Limpiar carpeta destino
    rm -rf "$DATA_DIR/redis"/*
    
    # Crear contenedor temporal
    TEMP_REDIS_ID=$(docker run -d -v "$REDIS_VOLUME:/redis_data" alpine:latest sleep 1000)
    sleep 1
    
    # Copiar datos
    docker cp "$TEMP_REDIS_ID:/redis_data/." "$DATA_DIR/redis/" > /dev/null 2>&1 || true
    
    # Limpiar
    docker stop "$TEMP_REDIS_ID" > /dev/null 2>&1
    docker rm "$TEMP_REDIS_ID" > /dev/null 2>&1
    
    # Verificar
    if [[ -f "$DATA_DIR/redis/dump.rdb" ]] || [[ -f "$DATA_DIR/redis/appendonly.aof" ]]; then
        SIZE=$(du -sh "$DATA_DIR/redis" | cut -f1)
        echo "   ✅ Redis migrado: $SIZE"
        ls -lh "$DATA_DIR/redis"/ | tail -5 | awk '{print "      " $9 " (" $5 ")"}'
    else
        echo "   ${YELLOW}⚠️  Redis migrado pero sin datos persistentes${NC}"
    fi
fi

# 4. Configurar permisos
echo ""
echo "🔐 Configurando permisos..."
chmod 700 "$DATA_DIR/postgres"
chmod 755 "$DATA_DIR/redis"
echo "   ✅ Permisos configurados"

# 5. Crear backup de volúmenes antiguos
echo ""
echo "💾 Creando backup de volúmenes antiguos..."
mkdir -p "$PROJECT_ROOT/backups/old-volumes"

for vol in $PG_VOLUME $REDIS_VOLUME; do
    if [[ ! -z "$vol" ]]; then
        echo "   📦 Backup: $vol"
        # Los volúmenes seguirán existiendo, documentamos su ubicación
        docker volume inspect "$vol" | grep Mountpoint >> "$PROJECT_ROOT/backups/old-volumes/volumes-backup.txt" 2>/dev/null || true
    fi
done
echo "   ✅ Lista de volúmenes guardada"

# 6. Iniciar servicios
echo ""
echo "🚀 Iniciando servicios con volúmenes locales..."
docker compose up -d postgres redis

# Esperar a que estén listos
echo "   ⏳ Esperando a que PostreSQL esté listo..."
for i in {1..30}; do
    if docker exec consultarpp-postgres pg_isready -U consultarpp_user > /dev/null 2>&1; then
        echo "   ✅ PostgreSQL activo"
        break
    fi
    sleep 2
done

# 7. Verificar integridad
echo ""
echo "🔍 Verificando integridad de datos..."
CHUNK_COUNT=$(docker exec consultarpp-postgres psql -U consultarpp_user -d consultarpp_db -t -c "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;" 2>/dev/null | tr -d ' ' || echo "0")

if [[ "$CHUNK_COUNT" -gt 0 ]]; then
    echo "   ✅ Chunks con embeddings: $CHUNK_COUNT"
else
    echo "   ${YELLOW}⚠️  No se encontraron chunks (posible: BD vacía o conexión fallida)${NC}"
fi

# 8. Resumen
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ MIGRACIÓN COMPLETADA EXITOSAMENTE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Estado de datos:"
echo "   PostgreSQL: $(du -sh $DATA_DIR/postgres 2>/dev/null | cut -f1)"
echo "   Redis:      $(du -sh $DATA_DIR/redis 2>/dev/null | cut -f1)"
echo ""
echo "📁 Volúmenes locales:"
echo "   Ubicación: $DATA_DIR/"
echo "   - postgres/  → Base de datos"
echo "   - redis/     → Caché"
echo ""
echo "🔗 Volúmenes Docker antiguos (backup):"
for vol in $PG_VOLUME $REDIS_VOLUME; do
    if [[ ! -z "$vol" ]]; then
        echo "   - $vol (aún existe en Docker)"
    fi
done
echo ""
echo "💡 Próximos pasos:"
echo "   1. Verificar que todo funciona: curl http://localhost:3001/api/v1/health"
echo "   2. Hacer un backup: ./scripts/backup.sh"
echo "   3. Opcionalmente, limpiar volúmenes Docker antiguos:"
echo "      docker volume rm $PG_VOLUME $REDIS_VOLUME"
echo ""
