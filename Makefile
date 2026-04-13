# PropQuery Makefile

.PHONY: help setup install start stop logs clean test lint format

help:
	@echo "ConsultaRPP Project - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Initial project setup"
	@echo "  make install        - Install dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make start          - Start all services with docker-compose"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs (use: make logs SERVICE=backend)"
	@echo ""
	@echo "Backend:"
	@echo "  make backend-dev    - Start backend in development mode"
	@echo "  make backend-shell  - Open Python shell"
	@echo "  make backend-test   - Run backend tests"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-dev   - Start frontend in development mode"
	@echo ""
	@echo "Database:"
	@echo "  make db-init        - Initialize database"
	@echo "  make db-migrate     - Run migrations (Alembic)"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo ""
	@echo "Quality:"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make test           - Run all tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Clean up containers and volumes"
	@echo "  make health         - Check service health"
	@echo ""

setup:
	@echo "🚀 Running setup..."
	bash scripts/setup.sh

install:
	@echo "📦 Installing dependencies..."
	pip install -r backend/requirements.txt
	cd frontend && npm install

start:
	@echo "🐳 Starting services..."
	docker-compose up -d

stop:
	@echo "🛑 Stopping services..."
	docker-compose down

restart:
	@echo "🔄 Restarting services..."
	docker-compose restart

logs:
	@echo "📊 Viewing logs..."
	docker-compose logs -f $(SERVICE)

backend-dev:
	@echo "💻 Starting backend development server..."
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

backend-shell:
	@echo "🐍 Opening Python shell..."
	cd backend && python -c "import IPython; IPython.embed()"

backend-test:
	@echo "🧪 Running backend tests..."
	cd backend && pytest -v

frontend-dev:
	@echo "💻 Starting frontend development server..."
	cd frontend && npm run dev

frontend-build:
	@echo "🔨 Building frontend for production..."
	cd frontend && npm run build

frontend-lint:
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint

frontend-preview:
	@echo "👀 Preview production build..."
	cd frontend && npm run preview

db-init:
	@echo "🗄️  Initializing database..."
	docker-compose exec postgres psql -U $(DB_USER) -d $(DB_NAME) -f /docker-entrypoint-initdb.d/init.sql

db-migrate:
	@echo "🔄 Running migrations..."
	cd backend && alembic upgrade head

db-shell:
	@echo "🗄️  Opening PostgreSQL shell..."
	docker-compose exec postgres psql -U $(DB_USER) -d $(DB_NAME)

lint:
	@echo "🔍 Running linters..."
	cd backend && flake8 app --max-line-length=120
	cd backend && mypy app

format:
	@echo "✨ Formatting code..."
	cd backend && black app --line-length=120
	cd backend && isort app

test:
	@echo "🧪 Running all tests..."
	cd backend && pytest -v tests/

clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	cd frontend && rm -rf node_modules .dist

health:
	@echo "🔍 Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "Backend: ❌"
	@curl -s http://localhost:5173 > /dev/null && echo "Frontend: ✅" || echo "Frontend: ❌"
	@docker-compose ps

# Knowledge Base Management
kb-load:
	@echo "📚 Cargando RPP Registry → Knowledge Base..."
	cd backend && python ../scripts/load_rpp_documents.py

kb-validate:
	@echo "✅ Validando Knowledge Base..."
	cd backend && python ../scripts/validate_kb.py

kb-status:
	@echo "📊 Estado de Knowledge Base..."
	@docker exec consulta-rpp-db psql -U postgres -d consulta_rpp -c \
		"SELECT category, COUNT(*) as count FROM documents GROUP BY category ORDER BY count DESC;" || echo "❌ BD no accesible"

kb-clear:
	@echo "🗑️  Limpiando Knowledge Base..."
	@docker exec consulta-rpp-db psql -U postgres -d consulta_rpp -c \
		"DELETE FROM document_chunks; DELETE FROM documents;" && echo "✅ KB limpiada" || echo "❌ Error al limpiar KB"

kb-embeddings:
	@echo "🤖 Generando embeddings locales con Sentence Transformers..."
	docker exec consultarpp-backend python /app/scripts/generate_embeddings_local.py

kb-embeddings-status:
	@echo "📈 Estado de embeddings..."
	@docker exec consultarpp-postgres psql -U consultarpp_user -d consultarpp -c \
		"SELECT COUNT(*) as total, COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embeddings FROM document_chunks;"

.PHONY: help setup install start stop logs clean test lint format kb-load kb-validate kb-status kb-clear kb-embeddings kb-embeddings-status
