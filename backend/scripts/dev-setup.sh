#!/bin/bash
# Development environment setup script

set -e

echo "🚀 Setting up AssetFlow development environment..."

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV is not installed. Please install UV first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment and install dependencies
echo "📦 Installing dependencies with UV..."
uv venv
uv pip install -e ".[dev]"

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual API keys"
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations (when we have them)
echo "🗄️  Database will be initialized automatically on first run"

echo "✅ Development environment setup complete!"
echo ""
echo "To start the development server:"
echo "  uv run uvicorn app.main:app --reload"
echo ""
echo "To run tests:"
echo "  uv run pytest"
echo ""
echo "To check code quality:"
echo "  uv run ruff check ."
echo "  uv run ruff format ."