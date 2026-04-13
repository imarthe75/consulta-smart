#!/usr/bin/env bash
# Setup script for PropQuery

set -e

echo "📦 Setting up PropQuery Project"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/app/{core,domain,application,infrastructure,routes,workers}
mkdir -p backend/app/domain/{entities,interfaces,exceptions}
mkdir -p backend/app/application/{dtos,usecases,services}
mkdir -p backend/app/infrastructure/{repositories,external,models}
mkdir -p frontend/src/{components,pages,services,utils}
mkdir -p docs
mkdir -p assets/images
mkdir -p logs
mkdir -p scripts

# Check if .env exists
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cp .env.example .env
    echo "✅ .env created. Please update with your actual values."
    echo "⚠️  Make sure to add your API keys:"
    echo "   - GROQ_API_KEY"
    echo "   - GOOGLE_API_KEY"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
else
    echo "✅ .env already exists"
fi

# Make scripts executable
echo "🔐 Making scripts executable..."
chmod +x scripts/*.sh 2>/dev/null || true

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Update .env with your API keys"
echo "   2. Run: ./scripts/dev-start.sh"
echo ""
