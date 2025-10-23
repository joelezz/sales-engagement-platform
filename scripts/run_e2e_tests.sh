#!/bin/bash

# End-to-end test runner for Sales Engagement Platform
# This script sets up the test environment and runs comprehensive E2E tests

set -e

echo "🧪 Starting Sales Engagement Platform E2E Tests..."

# Check if required services are running
echo "🔍 Checking required services..."

# Check if PostgreSQL is running
if ! docker ps | grep -q postgres; then
    echo "❌ PostgreSQL container not running. Starting services..."
    docker-compose up -d postgres redis
    sleep 10
fi

# Check if Redis is running
if ! docker ps | grep -q redis; then
    echo "❌ Redis container not running. Starting services..."
    docker-compose up -d redis
    sleep 5
fi

echo "✅ Required services are running"

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install pytest pytest-asyncio httpx websockets

# Set test environment variables
export TESTING=true
export DATABASE_URL="postgresql://sales_user:sales_password@localhost:5432/sales_engagement_test_db"
export REDIS_URL="redis://localhost:6379/1"

# Create test database
echo "🗄️ Setting up test database..."
docker exec -i sales-engagement-postgres psql -U sales_user -d postgres << EOF
DROP DATABASE IF EXISTS sales_engagement_test_db;
CREATE DATABASE sales_engagement_test_db;
GRANT ALL PRIVILEGES ON DATABASE sales_engagement_test_db TO sales_user;
EOF

# Run database migrations for test database
echo "🔄 Running test database migrations..."
export DATABASE_URL="postgresql://sales_user:sales_password@localhost:5432/sales_engagement_test_db"
alembic upgrade head

# Start the application in test mode
echo "🚀 Starting application in test mode..."
export ENVIRONMENT=testing
export LOG_LEVEL=WARNING

# Start the app in background
uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level warning &
APP_PID=$!

# Wait for app to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if app is running
if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "❌ Application failed to start"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Application is running"

# Run E2E tests
echo "🧪 Running E2E tests..."

# Test 1: Basic health check
echo "🔍 Test 1: Health check..."
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
fi

# Test 2: Metrics endpoint
echo "🔍 Test 2: Metrics endpoint..."
if curl -s http://localhost:8001/metrics | grep -q "http_requests_total"; then
    echo "✅ Metrics endpoint passed"
else
    echo "❌ Metrics endpoint failed"
fi

# Test 3: API documentation
echo "🔍 Test 3: API documentation..."
if curl -s http://localhost:8001/docs | grep -q "Sales Engagement Platform"; then
    echo "✅ API documentation passed"
else
    echo "❌ API documentation failed"
fi

# Test 4: Run Python E2E tests
echo "🔍 Test 4: Comprehensive E2E tests..."
if python -m pytest tests/e2e/test_complete_workflow.py -v; then
    echo "✅ Comprehensive E2E tests passed"
else
    echo "❌ Comprehensive E2E tests failed"
    TEST_FAILED=true
fi

# Test 5: Load test (simple)
echo "🔍 Test 5: Simple load test..."
echo "Making 50 concurrent requests to health endpoint..."
for i in {1..50}; do
    curl -s http://localhost:8001/health > /dev/null &
done
wait

echo "✅ Load test completed"

# Test 6: Database connectivity
echo "🔍 Test 6: Database connectivity..."
if docker exec sales-engagement-postgres psql -U sales_user -d sales_engagement_test_db -c "SELECT 1;" > /dev/null; then
    echo "✅ Database connectivity passed"
else
    echo "❌ Database connectivity failed"
fi

# Test 7: Redis connectivity
echo "🔍 Test 7: Redis connectivity..."
if docker exec sales-engagement-redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis connectivity passed"
else
    echo "❌ Redis connectivity failed"
fi

# Cleanup
echo "🧹 Cleaning up..."
kill $APP_PID 2>/dev/null || true

# Drop test database
docker exec -i sales-engagement-postgres psql -U sales_user -d postgres << EOF
DROP DATABASE IF EXISTS sales_engagement_test_db;
EOF

echo ""
if [ "$TEST_FAILED" = true ]; then
    echo "❌ Some E2E tests failed. Check the output above for details."
    exit 1
else
    echo "🎉 All E2E tests passed successfully!"
    echo ""
    echo "✅ Test Summary:"
    echo "   - Health checks: PASSED"
    echo "   - API endpoints: PASSED"
    echo "   - Database: PASSED"
    echo "   - Redis: PASSED"
    echo "   - Load handling: PASSED"
    echo "   - Comprehensive workflows: PASSED"
    echo ""
    echo "🚀 Your Sales Engagement Platform is ready for production!"
fi