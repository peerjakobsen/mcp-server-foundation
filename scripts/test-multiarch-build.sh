#!/bin/bash
# Test script for multi-architecture Docker builds

set -e

echo "🏗️ Testing Multi-Architecture Docker Builds"
echo "============================================="

# Check if Docker buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    echo "❌ Docker buildx is not available"
    echo "Please install Docker Desktop or enable buildx"
    exit 1
fi

# Create a new builder instance for multi-arch builds
echo "🔧 Setting up buildx builder..."
docker buildx create --name multiarch-builder --platform linux/amd64,linux/arm64 --use 2>/dev/null || true
docker buildx use multiarch-builder

# Check available platforms
echo "📋 Available platforms:"
docker buildx inspect --bootstrap

# Test AMD64 build
echo
echo "🏗️ Testing AMD64 build..."
docker buildx build \
    --platform linux/amd64 \
    --target production \
    --tag mcp-server:amd64-test \
    --load \
    --build-arg PYTHON_VERSION=3.13.6 \
    .

echo "✅ AMD64 build completed successfully"

# Test ARM64 build (will be emulated on x86_64 systems)
echo
echo "🏗️ Testing ARM64 build (emulated)..."
docker buildx build \
    --platform linux/arm64 \
    --target production \
    --tag mcp-server:arm64-test \
    --build-arg PYTHON_VERSION=3.13.6 \
    . \
    --progress=plain

echo "✅ ARM64 build completed successfully"

# Test multi-platform build
echo
echo "🏗️ Testing multi-platform build..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --target production \
    --tag mcp-server:multiarch-test \
    --build-arg PYTHON_VERSION=3.13.6 \
    . \
    --progress=plain

echo "✅ Multi-platform build completed successfully"

# Test image functionality (AMD64 only since we can load it)
echo
echo "🧪 Testing AMD64 image functionality..."
docker run --rm --platform linux/amd64 \
    -e DEPLOYMENT_MODE=production \
    -e SECRET_KEY=test-key \
    -e DATABASE_URL=sqlite:///tmp/test.db \
    mcp-server:amd64-test \
    /app/.venv/bin/python -c "
import sys
print(f'✅ Python version: {sys.version}')
print('✅ Image runs successfully')

# Test that we can import the main module
try:
    from mcp_server.main import MCPServerFoundation
    from mcp_server.config import MCPServerConfig, DeploymentMode
    print('✅ Main modules import successfully')

    # Test configuration
    config = MCPServerConfig(
        deployment_mode=DeploymentMode.PRODUCTION,
        secret_key='test-key',
        database_url='sqlite:///tmp/test.db'
    )
    print(f'✅ Configuration created: {config.deployment_mode}')

except Exception as e:
    print(f'❌ Module import failed: {e}')
    sys.exit(1)
"

# Clean up test images
echo
echo "🧹 Cleaning up test images..."
docker rmi mcp-server:amd64-test >/dev/null 2>&1 || true
docker rmi mcp-server:arm64-test >/dev/null 2>&1 || true
docker rmi mcp-server:multiarch-test >/dev/null 2>&1 || true

# Clean up builder
docker buildx rm multiarch-builder >/dev/null 2>&1 || true

echo
echo "✅ Multi-architecture build tests completed successfully!"
echo
echo "📋 Summary:"
echo "   - AMD64 build: ✅ Working"
echo "   - ARM64 build: ✅ Working (emulated)"
echo "   - Multi-platform build: ✅ Working"
echo "   - Runtime functionality: ✅ Verified"
echo
echo "🚀 Ready for production multi-architecture deployment!"
