#!/usr/bin/env bash
# Database initialization and sample data loader

set -e

echo "🗄️  PropQuery Database Setup"
echo "============================="
echo ""

# Load .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

DB_USER=${DB_USER:-propquery_user}
DB_PASSWORD=${DB_PASSWORD:-supersecret123}
DB_NAME=${DB_NAME:-propquery_db}
DB_HOST=${DB_HOST:-localhost}

echo "📋 Database Configuration:"
echo "   Host: $DB_HOST"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo ""

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
max_attempts=30
attempt=0
while ! docker-compose exec -T postgres pg_isready -U $DB_USER -h localhost > /dev/null 2>&1; do
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ PostgreSQL failed to start"
        exit 1
    fi
    attempt=$((attempt + 1))
    sleep 1
done
echo "✅ PostgreSQL is ready"
echo ""

# Create extensions
echo "📦 Creating database extensions..."
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME << EOF
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
EOF
echo "✅ Extensions created"
echo ""

# Note about Alembic migrations
echo "📝 Note: Tables are created automatically by SQLAlchemy ORM"
echo "   Run the application to initialize schema:"
echo "   - Local: python -c 'from app.core.database import init_db; await init_db()'"
echo "   - Docker: docker-compose logs backend | grep 'database created'"
echo ""

echo "✅ Database setup complete!"
echo ""
echo "📚 Documentation:"
echo "   - PostgreSQL shell: make db-shell"
echo "   - Migrations: make db-migrate"
echo "   - Tables will be created on first app run"
