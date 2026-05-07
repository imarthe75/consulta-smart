# 📦 Guía de Persistencia de Datos - ConsultaRPP

## Descripción General

El proyecto ConsultaRPP utiliza una estrategia de **persistencia de datos basada en volúmenes locales** para asegurar que todos los datos se mantegan intactos incluso después de reinicios de contenedores, actualizaciones de imágenes Docker o despliegues en diferentes servidores.

---

## 🗂️ Estructura de Carpetas

```
consulta-rpp/
├── data/
│   ├── postgres/          # Base de datos PostgreSQL + pgvector
│   ├── redis/             # Caché y broker de Celery
│   ├── celery/            # Resultados y logs de Celery
│   └── attachments/       # Archivos subidos por usuarios
├── db/
├── backend/
├── frontend/
└── docker-compose.yml
```

---

## 🔧 Componentes con Persistencia

### 1. **PostgreSQL** (`./data/postgres`)

**Lo que persiste:**
- Base de datos principal (tablas, índices)
- Documentos cargados por usuarios
- Embeddings (vectores de 384 dimensiones)
- Información de usuarios y sesiones

**Ubicación:** `./data/postgres:/var/lib/postgresql/data`

**Tamaño esperado:** 500MB - 2GB (depende de documentos cargados)

```bash
# Verificar estado de la base de datos
docker exec consultarpp-postgres pg_isready

# Hacer backup
docker exec consultarpp-postgres pg_dump -U consultarpp_user -d consultarpp_db > backup_$(date +%Y%m%d).sql

# Restaurar desde backup
docker exec -i consultarpp-postgres psql -U consultarpp_user -d consultarpp_db < backup_20260409.sql
```

### 2. **Redis** (`./data/redis`)

**Lo que persiste:**
- Caché de respuestas RAG (queries frecuentes)
- Cola de tareas Celery (procesamiento en background)
- Sesiones de usuario
- Datos temporales con TTL

**Ubicación:** `./data/redis:/data`

**Tamaño esperado:** 50MB - 500MB

**Archivo AOF:** `./data/redis/appendonly.aof` (Append-Only File para durabilidad)

```bash
# Verificar estado de Redis
docker exec consultarpp-redis redis-cli ping

# Ver memoria usada
docker exec consultarpp-redis redis-cli -a redis_secure_2026 INFO memory

# Limpiar caché manualmente
docker exec consultarpp-redis redis-cli -a redis_secure_2026 FLUSHALL
```

### 3. **Celery Tasks** (`./data/celery`)

**Lo que persiste:**
- Resultados de tareas asincrónicas
- Logs de procesamiento de documentos
- Estado de trabajos en progreso

**Ubicación:** Mapeado en Celery worker para logs

```bash
# Ver logs de Celery
docker logs consultarpp-celery-worker

# Monitorear tareas
docker exec consultarpp-backend python -m celery -A app.workers.celery_app inspect active
```

### 4. **Attachments** (`./data/attachments`)

**Lo que persiste:**
- Documentos PDF/Word subidos por usuarios
- Archivos procesados

**Ubicación:** `./data/attachments`

```bash
# Listar archivos subidos
ls -la ./data/attachments/

# Calcular tamaño total
du -sh ./data/attachments/
```

---

## 🚀 Inicialización del Sistema

### Primera vez (Fresh Start)

```bash
# 1. Crear carpetas necesarias
./scripts/setup-volumes.sh

# 2. Construir imágenes
docker-compose build

# 3. Iniciar contenedores
docker-compose up -d

# 4. Cargar datos de prueba (documentos RPP)
./load_rpp_docs.sh

# 5. Verificar que todo funciona
curl http://localhost:3001/api/v1/health
```

### Reinicio del Sistema (Data Preservation)

```bash
# Los datos se conservan automáticamente
docker-compose down
docker-compose up -d

# Verificar integridad de datos
docker exec consultarpp-postgres psql -U consultarpp_user -d consultarpp_db -c "SELECT COUNT(*) FROM document_chunks;"
```

---

## 💾 Backup y Recuperación

### Backup Automático

```bash
#!/bin/bash
# backup.sh
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker exec consultarpp-postgres pg_dump -U consultarpp_user -d consultarpp_db | gzip > $BACKUP_DIR/pg_backup_$TIMESTAMP.sql.gz

# Backup Redis
docker exec consultarpp-redis redis-cli -a redis_secure_2026 BGSAVE
cp ./data/redis/dump.rdb $BACKUP_DIR/redis_backup_$TIMESTAMP.rdb

# Backup attachments
tar -czf $BACKUP_DIR/attachments_$TIMESTAMP.tar.gz ./data/attachments/

echo "✅ Backups completados en $BACKUP_DIR"
```

### Recuperación desde Backup

```bash
# Restaurar PostgreSQL
gunzip < ./backups/pg_backup_20260409_120000.sql.gz | docker exec -i consultarpp-postgres psql -U consultarpp_user -d consultarpp_db

# Restaurar Redis
docker exec consultarpp-redis redis-cli -a redis_secure_2026 SHUTDOWN
cp ./backups/redis_backup_20260409_120000.rdb ./data/redis/dump.rdb
docker-compose restart redis

# Restaurar attachments
tar -xzf ./backups/attachments_20260409_120000.tar.gz
```

---

## 🔄 Migraciones de Datos

### Entre Servidores

```bash
# En servidor origen
tar -czf consulta-rpp-data.tar.gz ./data/

# Copiar a nuevo servidor
scp consulta-rpp-data.tar.gz usuario@nuevo-servidor:/home/ia/

# En nuevo servidor
cd /home/ia/consulta-rpp
tar -xzf /home/ia/consulta-rpp-data.tar.gz
docker-compose up -d
```

### Cambio de Base de Datos

Si necesitas migrar PostgreSQL a una versión diferente:

```bash
# 1. Hacer backup
docker exec consultarpp-postgres pg_dump -U consultarpp_user > full_backup.sql

# 2. Eliminar volumen viejo
docker-compose down
rm -rf ./data/postgres/*

# 3. Cambiar versión en docker-compose.yml y reconstruir
docker-compose build postgres
docker-compose up -d postgres

# 4. Restaurar datos
docker exec -i consultarpp-postgres psql -U consultarpp_user < full_backup.sql
```

---

## 📊 Monitoreo de Almacenamiento

```bash
# Ver uso de espacio en disco
du -sh ./data/*

# Ver inodos
ls -i ./data/ | wc -l

# Monitoreo en tiempo real
watch -n 5 'du -sh ./data/*'

# Identificar carpetas grandes
find ./data -type f -size +100M -exec ls -lh {} \;
```

---

## ⚠️ Consideraciones de Seguridad

### Permisos de Carpetas

```bash
# PostgreSQL necesita acceso de lectura/escritura
chmod 700 ./data/postgres

# Redis necesita acceso de lectura/escritura
chmod 755 ./data/redis

# Attachments
chmod 755 ./data/attachments
```

### Encriptación (Opcional)

Para producción, considera encriptar los volúmenes:

```bash
# Usando LUKS en Linux
sudo cryptsetup luksFormat /dev/sdX
sudo cryptsetup luksOpen /dev/sdX consulta_rpp_data
```

### Acceso a Base de Datos

```bash
# Cambiar contraseñas en producción (actualizar .env)
DB_PASSWORD=tu_contraseña_segura_aqui
REDIS_PASSWORD=tu_contraseña_segura_aqui

# Reinciar contenedores
docker-compose restart
```

---

## 🚨 Troubleshooting

### PostgreSQL no inicia

```bash
# Ver logs
docker logs consultarpp-postgres

# Verificar permisos
ls -la ./data/postgres/

# Recrear si está corrupto
rm -rf ./data/postgres/*
docker-compose restart postgres
```

### Redis caché lleno

```bash
# Ver tamaño máximo
docker exec consultarpp-redis redis-cli -a redis_secure_2026 CONFIG GET maxmemory

# Limpiar caché antiguo
docker exec consultarpp-redis redis-cli -a redis_secure_2026 FLUSHDB

# Aumentar tamaño máximo
docker exec consultarpp-redis redis-cli -a redis_secure_2026 CONFIG SET maxmemory 1gb
```

### Recuperar de corrupción de datos

```bash
# 1. Hacer backup del estado corrupto
cp -r ./data ./data.backup_corrupted

# 2. Limpiar
rm -rf ./data/*

# 3. Recriar desde cero
docker-compose down
docker-compose up -d

# 4. Recargar documentos
./load_rpp_docs.sh
```

---

## 📋 Checklist de Producción

- [ ] Carpetas `./data/*` creadas con permisos correctos (700/755)
- [ ] Contraseñas de BD y Redis actualizadas en `.env`
- [ ] Backups automáticos configurados (cron job)
- [ ] Monitoreo de espacio en disco implementado
- [ ] Logs centralizados (ELK stack opcional)
- [ ] Plan de recuperación ante desastres documentado
- [ ] Tests de restauración desde backup realizados
- [ ] Encriptación de volúmenes habilitada (si es producción)
- [ ] Rotación de backups configurada (30+ días)
- [ ] Alertas de espacio en disco configuradas

---

## 📚 Referencias

- [Docker Volumes Documentation](https://docs.docker.com/storage/volumes/)
- [PostgreSQL Backup & Restore](https://www.postgresql.org/docs/current/backup.html)
- [Redis Persistence](https://redis.io/docs/management/persistence/)
- [Celery Task Persistence](https://docs.celeryproject.io/en/stable/getting-started/backends-and-brokers/)
