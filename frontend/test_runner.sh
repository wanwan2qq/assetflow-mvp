#!/bin/bash

# Test runner script for AssetFlow Frontend
# This script runs all tests and generates coverage reports

set -e

echo "🧪 Running AssetFlow Frontend Tests"
echo "=================================="

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter is not installed. Please install Flutter first."
    echo "   Visit: https://flutter.dev/docs/get-started/install"
    exit 1
fi

# Get dependencies
echo "📦 Getting dependencies..."
flutter pub get

# Generate code if needed
echo "🔧 Generating code..."
flutter packages pub run build_runner build --delete-conflicting-outputs

# Run tests
echo "🧪 Running unit tests..."
flutter test --coverage

# Run widget tests
echo "🎨 Running widget tests..."
flutter test test/shared/widgets/

# Run integration tests if they exist
if [ -d "integration_test" ]; then
    echo "🔗 Running integration tests..."
    flutter test integration_test/
fi

# Generate coverage report
if [ -f "coverage/lcov.info" ]; then
    echo "📊 Generating coverage report..."
    genhtml coverage/lcov.info -o coverage/html
    echo "✅ Coverage report generated at coverage/html/index.html"
fi

echo ""
echo "🎉 All tests completed successfully!"
echo ""
echo "📋 Test Summary:"
echo "   - Unit tests: ✅"
echo "   - Widget tests: ✅"
echo "   - Integration tests: ✅"
echo ""
echo "💡 To run specific tests:"
echo "   flutter test test/core/providers/auth_provider_test.dart"
echo "   flutter test test/shared/widgets/valuation_card_test.dart"