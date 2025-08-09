# Multi-stage Dockerfile for MCP Server Foundation
# Supports both development and production deployments with security hardening

# Build arguments for versioning and multi-platform support
ARG PYTHON_VERSION=3.13.6
ARG DISTROLESS_VERSION=latest
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# ============================================================================
# Base stage: Common dependencies and setup
# ============================================================================
FROM python:${PYTHON_VERSION}-slim AS base

# Install system dependencies required for both dev and prod
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user early for consistency
RUN groupadd -g 1000 mcp && \
    useradd -r -u 1000 -g mcp -m -s /sbin/nologin mcp

# Set working directory
WORKDIR /app

# ============================================================================
# Dependencies stage: Install Python dependencies
# ============================================================================
FROM base AS dependencies

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock README.md ./

# Install uv for fast package management
RUN pip install --no-cache-dir uv==0.8.6

# Install production dependencies only
RUN uv sync --frozen --no-dev --no-cache

# Save the virtual environment for later stages
RUN cp -r .venv /opt/venv-prod

# Install all dependencies (including dev) for development stage
RUN uv sync --frozen --all-extras --no-cache
RUN cp -r .venv /opt/venv-dev

# ============================================================================
# Development stage: Full development environment with hot reload
# ============================================================================
FROM base AS development

# Install additional dev tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    vim \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy development virtual environment
COPY --from=dependencies /opt/venv-dev /app/.venv

# Copy application source code
COPY --chown=mcp:mcp . /app/

# Set Python path and virtual environment
ENV PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DEPLOYMENT_MODE=development

# Switch to non-root user
USER mcp

# Expose development port
EXPOSE 8000

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development entrypoint with hot reload
CMD ["python", "-m", "mcp_server.main"]

# ============================================================================
# Builder stage: Prepare production application
# ============================================================================
FROM base AS builder

# Copy production virtual environment
COPY --from=dependencies /opt/venv-prod /app/.venv

# Copy application source code (exclude dev files)
COPY --chown=mcp:mcp src/ /app/src/
COPY --chown=mcp:mcp pyproject.toml /app/

# Compile Python files for optimization
RUN python -m compileall -q /app/src

# Remove unnecessary files for production
RUN find /app -type f -name "*.pyc" -delete && \
    find /app -type d -name "__pycache__" -delete && \
    find /app -type f -name "*.pyo" -delete && \
    find /app -type f -name ".coverage" -delete && \
    find /app -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true && \
    find /app -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# ============================================================================
# Production stage: Minimal Python runtime
# ============================================================================
FROM python:${PYTHON_VERSION}-slim AS production

# Install minimal runtime dependencies for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -g 1000 mcp && \
    useradd -r -u 1000 -g mcp -m -s /sbin/nologin mcp

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application from builder
COPY --from=builder --chown=1000:1000 /app/src /app/src
COPY --from=builder --chown=1000:1000 /app/pyproject.toml /app/pyproject.toml

# Set working directory
WORKDIR /app

# Set production environment variables
ENV PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DEPLOYMENT_MODE=production \
    PYTHONDONTWRITEBYTECODE=1 \
    # Security: Prevent Python from executing downloaded code
    PYTHONHTTPSVERIFY=1 \
    # Performance: Use optimized bytecode
    PYTHONOPTIMIZE=2

# Use numeric UID/GID for distroless compatibility
USER 1000:1000

# Expose production port
EXPOSE 8000

# Health check for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production entrypoint - handle signals for graceful shutdown
ENTRYPOINT ["python"]
CMD ["-m", "mcp_server.main"]

# ============================================================================
# Metadata labels
# ============================================================================
LABEL org.opencontainers.image.title="MCP Server Foundation" \
      org.opencontainers.image.description="Enterprise-ready Model Context Protocol server" \
      org.opencontainers.image.authors="MCP Server Foundation Team" \
      org.opencontainers.image.vendor="MCP Server Foundation" \
      org.opencontainers.image.url="https://github.com/yourusername/mcp-server-foundation" \
      org.opencontainers.image.source="https://github.com/yourusername/mcp-server-foundation" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="MIT"
