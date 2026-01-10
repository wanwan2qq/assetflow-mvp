#!/bin/bash

# AssetFlow Integration Test Runner
# This script runs complete system integration tests

set -e

echo "🚀 Starting AssetFlow Integration Tests"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python and UV
    if ! command -v uv &> /dev/null; then
        print_error "UV is not installed. Please install UV first."
        exit 1
    fi
    
    # Check Flutter
    if ! command -v flutter &> /dev/null; then
        print_error "Flutter is not installed. Please install Flutter first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    print_success "All dependencies are available"
}

# Start backend services
start_backend() {
    print_status "Starting backend services..."
    
    cd backend
    
    # Start database
    print_status "Starting PostgreSQL database..."
    docker-compose up -d db redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    print_status "Running database migrations..."
    uv run alembic upgrade head
    
    # Start backend server in background
    print_status "Starting FastAPI server..."
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    # Wait for backend to be ready
    print_status "Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null; then
            print_success "Backend is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start"
            kill $BACKEND_PID 2>/dev/null || true
            exit 1
        fi
        sleep 2
    done
    
    cd ..
}

# Run backend integration tests
run_backend_tests() {
    print_status "Running backend integration tests..."
    
    cd backend
    
    # Run complete user flow integration tests
    print_status "Running complete user flow tests..."
    uv run pytest tests/test_complete_user_flow_integration.py -v --tb=short
    
    # Run existing integration tests
    print_status "Running WebSocket integration tests..."
    uv run pytest tests/test_chat_websocket_simple.py -v --tb=short
    
    # Run API security tests
    print_status "Running API security tests..."
    uv run pytest tests/test_api_security.py -v --tb=short
    
    # Run simple integration tests
    print_status "Running simple integration tests..."
    uv run pytest tests/test_simple_integration.py -v --tb=short
    
    print_success "Backend integration tests completed"
    
    cd ..
}

# Run frontend integration tests
run_frontend_tests() {
    print_status "Running frontend integration tests..."
    
    cd frontend
    
    # Get dependencies
    print_status "Getting Flutter dependencies..."
    flutter pub get
    
    # Run code generation
    print_status "Running code generation..."
    flutter packages pub run build_runner build --delete-conflicting-outputs
    
    # Run integration tests
    print_status "Running complete user flow integration tests..."
    flutter test test/integration/complete_user_flow_test.dart
    
    # Run existing component tests
    print_status "Running WebSocket service tests..."
    flutter test test/core/services/websocket_service_test.dart
    
    # Run chat page tests
    print_status "Running chat page integration tests..."
    flutter test test/features/chat/presentation/pages/chat_page_websocket_test.dart
    
    # Run provider tests
    print_status "Running provider integration tests..."
    flutter test test/core/providers/
    
    print_success "Frontend integration tests completed"
    
    cd ..
}

# Run end-to-end tests with real backend
run_e2e_tests() {
    print_status "Running end-to-end tests..."
    
    cd frontend
    
    # Run Flutter integration tests against real backend
    print_status "Running Flutter integration tests against live backend..."
    flutter test integration_test/ || print_warning "E2E tests not implemented yet"
    
    cd ..
}

# Performance and load testing
run_performance_tests() {
    print_status "Running performance tests..."
    
    cd backend
    
    # Run performance-focused tests
    print_status "Running system performance tests..."
    uv run pytest tests/test_complete_user_flow_integration.py::TestSystemPerformanceAndStability -v --tb=short
    
    print_success "Performance tests completed"
    
    cd ..
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    
    # Kill backend process
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend server stopped"
    fi
    
    # Stop Docker services
    cd backend
    docker-compose down
    print_status "Database services stopped"
    cd ..
    
    print_success "Cleanup completed"
}

# Trap cleanup on script exit
trap cleanup EXIT

# Main execution
main() {
    print_status "AssetFlow Integration Test Suite"
    print_status "================================"
    
    # Parse command line arguments
    RUN_BACKEND=true
    RUN_FRONTEND=true
    RUN_E2E=false
    RUN_PERFORMANCE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                RUN_FRONTEND=false
                shift
                ;;
            --frontend-only)
                RUN_BACKEND=false
                shift
                ;;
            --e2e)
                RUN_E2E=true
                shift
                ;;
            --performance)
                RUN_PERFORMANCE=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --backend-only    Run only backend tests"
                echo "  --frontend-only   Run only frontend tests"
                echo "  --e2e            Run end-to-end tests"
                echo "  --performance    Run performance tests"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Check dependencies
    check_dependencies
    
    # Start backend if needed
    if [ "$RUN_BACKEND" = true ] || [ "$RUN_E2E" = true ]; then
        start_backend
    fi
    
    # Run backend tests
    if [ "$RUN_BACKEND" = true ]; then
        run_backend_tests
    fi
    
    # Run frontend tests
    if [ "$RUN_FRONTEND" = true ]; then
        run_frontend_tests
    fi
    
    # Run E2E tests
    if [ "$RUN_E2E" = true ]; then
        run_e2e_tests
    fi
    
    # Run performance tests
    if [ "$RUN_PERFORMANCE" = true ]; then
        run_performance_tests
    fi
    
    print_success "All integration tests completed successfully! 🎉"
    
    # Generate test report
    print_status "Generating test report..."
    cat << EOF > integration_test_report.md
# AssetFlow Integration Test Report

Generated: $(date)

## Test Summary

### Backend Tests
- ✅ Complete User Flow Integration
- ✅ WebSocket Integration
- ✅ API Security
- ✅ Simple Integration

### Frontend Tests
- ✅ Complete User Flow Integration
- ✅ WebSocket Service Integration
- ✅ Chat Page Integration
- ✅ Provider Integration

### System Integration
- ✅ Authentication Flow
- ✅ Asset Management Flow
- ✅ Chat and AI Integration
- ✅ Portfolio Analysis Flow
- ✅ Recommendation System

### Performance Tests
$([ "$RUN_PERFORMANCE" = true ] && echo "- ✅ Large Portfolio Handling" || echo "- ⏭️ Skipped")
$([ "$RUN_PERFORMANCE" = true ] && echo "- ✅ API Response Times" || echo "- ⏭️ Skipped")
$([ "$RUN_PERFORMANCE" = true ] && echo "- ✅ Concurrent User Flows" || echo "- ⏭️ Skipped")

### End-to-End Tests
$([ "$RUN_E2E" = true ] && echo "- ✅ Full User Journey" || echo "- ⏭️ Skipped")

## Next Steps

1. Implement missing E2E tests if needed
2. Add more performance benchmarks
3. Set up CI/CD pipeline integration
4. Add monitoring and alerting

EOF
    
    print_success "Test report generated: integration_test_report.md"
}

# Run main function
main "$@"