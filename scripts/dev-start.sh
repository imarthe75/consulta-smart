#!/usr/bin/env bash
# Script to start the PropQuery development environment

set -e

echo "🚀 Starting PropQuery Development Environment"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and try again."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Load environment
if [ -f .env ]; then
    echo "✅ Loading .env file"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  .env file not found. Using .env.example"
    if [ ! -f .env.example ]; then
        echo "❌ .env.example not found"
        exit 1
    fi
    cp .env.example .env
    echo "✅ Created .env from .env.example"
fi

# Start services
echo ""
echo "🐳 Starting Docker containers..."
docker-compose -f docker-compose.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check backend health
echo ""
echo "🔍 Checking services..."
if curl -s http://localhost:3001/health > /dev/null; then
    echo "✅ Backend is ready: http://localhost:3001"
    echo "✅ API Documentation: http://localhost:3001/docs"
else
    echo "⚠️  Backend is still starting. Check: docker-compose logs backend"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is ready: http://localhost:3000"
else
    echo "⚠️  Frontend is still building. Check: docker-compose logs frontend"
fi

echo ""
echo "✅ ConsultaRPP Development Environment Started!"
echo ""
echo "📚 🌐 ACCESO:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:3001/docs"
echo "  - Swagger UI: http://localhost:3001/redoc"
echo "  - PostgreSQL: localhost:3002 (user: consultarpp_user)"
echo "  - Redis: localhost:3003"
echo "  - SeaweedFS Volume: http://localhost:3004"
echo "  - SeaweedFS Master: http://localhost:3005"
echo ""
echo "🛑 Para detener: docker-compose down"
echo "📊 Ver logs: docker-compose logs -f [service]"
echo ""
