#!/bin/bash
# Script to run tests with PostgreSQL and Redis services
# Usage: ./scripts/test-with-services.sh [test-args]

set -e

echo "🐳 Starting test services (PostgreSQL + Redis)..."
docker-compose -f docker-compose.test.yml up -d postgres-test redis-test

echo "⏳ Waiting for services to be healthy..."
docker-compose -f docker-compose.test.yml exec postgres-test pg_isready -U testuser -d testdb
docker-compose -f docker-compose.test.yml exec redis-test redis-cli ping

echo "🧪 Running tests with service connections..."
export DATABASE_URL="postgresql://testuser:testpass@localhost:5432/testdb"
export REDIS_URL="redis://localhost:6379/0"
export DEPLOYMENT_MODE="docker"
export SECRET_KEY="test-secret-key"

# Run the tests
if command -v uv >/dev/null 2>&1; then
    echo "Using uv to run tests..."
    uv run pytest "$@"
else
    echo "Using python to run tests..."
    python -m pytest "$@"
fi

TEST_EXIT_CODE=$?

echo "🧹 Cleaning up test services..."
docker-compose -f docker-compose.test.yml down

exit $TEST_EXIT_CODE
