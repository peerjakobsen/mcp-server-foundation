#!/bin/bash
# Test script to verify Docker health checks work correctly

set -e

echo "🔧 Testing Docker Health Checks"
echo "================================"

# Function to wait for health check
wait_for_health() {
    local container_name=$1
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for $container_name to be healthy..."

    while [ $attempt -le $max_attempts ]; do
        if docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null | grep -q "healthy"; then
            echo "✅ $container_name is healthy"
            return 0
        fi

        echo "   Attempt $attempt/$max_attempts - Status: $(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo 'unknown')"
        sleep 2
        ((attempt++))
    done

    echo "❌ $container_name failed to become healthy"
    return 1
}

# Test development build health check
echo
echo "📦 Building development Docker image..."
docker build --target development --tag mcp-server:dev-health-test .

echo
echo "🚀 Starting development container..."
docker run -d --name mcp-dev-health-test \
    -p 8001:8000 \
    -e DEPLOYMENT_MODE=development \
    -e SECRET_KEY=test-secret-key \
    mcp-server:dev-health-test

# Wait for health check
if wait_for_health "mcp-dev-health-test"; then
    echo "✅ Development health check passed"
else
    echo "❌ Development health check failed"
    echo "Container logs:"
    docker logs mcp-dev-health-test
fi

# Clean up development container
docker stop mcp-dev-health-test >/dev/null 2>&1 || true
docker rm mcp-dev-health-test >/dev/null 2>&1 || true

# Test production build health check
echo
echo "📦 Building production Docker image..."
docker build --target production --tag mcp-server:prod-health-test .

echo
echo "🚀 Starting production container..."
docker run -d --name mcp-prod-health-test \
    -p 8002:8000 \
    -e DEPLOYMENT_MODE=production \
    -e SECRET_KEY=test-production-secret-key \
    -e DATABASE_URL=sqlite:///./data/test.db \
    mcp-server:prod-health-test

# Wait for health check
if wait_for_health "mcp-prod-health-test"; then
    echo "✅ Production health check passed"
else
    echo "❌ Production health check failed"
    echo "Container logs:"
    docker logs mcp-prod-health-test
fi

# Test HTTP endpoints directly
echo
echo "🌐 Testing HTTP endpoints directly..."

# Test health endpoint
if curl -f http://localhost:8002/health >/dev/null 2>&1; then
    echo "✅ /health endpoint accessible"
    echo "   Response: $(curl -s http://localhost:8002/health | jq -c .)"
else
    echo "❌ /health endpoint failed"
fi

# Test readiness endpoint
if curl -f http://localhost:8002/readiness >/dev/null 2>&1; then
    echo "✅ /readiness endpoint accessible"
    echo "   Response: $(curl -s http://localhost:8002/readiness | jq -c .)"
else
    echo "❌ /readiness endpoint failed"
fi

# Test liveness endpoint
if curl -f http://localhost:8002/liveness >/dev/null 2>&1; then
    echo "✅ /liveness endpoint accessible"
    echo "   Response: $(curl -s http://localhost:8002/liveness | jq -c .)"
else
    echo "❌ /liveness endpoint failed"
fi

# Clean up production container
docker stop mcp-prod-health-test >/dev/null 2>&1 || true
docker rm mcp-prod-health-test >/dev/null 2>&1 || true

echo
echo "🧹 Cleaning up test images..."
docker rmi mcp-server:dev-health-test >/dev/null 2>&1 || true
docker rmi mcp-server:prod-health-test >/dev/null 2>&1 || true

echo
echo "✅ Docker health check tests completed!"
