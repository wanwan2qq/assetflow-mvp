#!/bin/bash
# Test runner script

set -e

echo "🧪 Running AssetFlow tests..."

# Run code quality checks
echo "📋 Running code quality checks..."
uv run ruff check .
uv run ruff format --check .

# Run tests
echo "🔬 Running unit tests..."
uv run pytest -v

# Run tests with coverage (optional)
if [ "$1" = "--coverage" ]; then
    echo "📊 Running tests with coverage..."
    uv run pytest --cov=app --cov-report=html --cov-report=term
fi

echo "✅ All tests passed!"