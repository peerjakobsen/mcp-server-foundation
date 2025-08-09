# Tech Stack

## Context

Technical architecture decisions for the Enterprise MCP Server Foundation, optimized for dual-mode deployment (local uvx development and cloud-native production). All versions current as of August 2025.

## Core Framework & Language

**Framework**: FastMCP 2.11+
- Latest version with Enterprise-Ready Authentication
- OAuth 2.1 support with WorkOS's AuthKit integration
- Full compliance with 6/18/2025 MCP spec update
- Built-in tool, resource, and prompt management
- Transport abstraction for STDIO and HTTP+SSE

**Language**: Python 3.13.6+
- Latest stable release (August 6, 2025)
- Experimental free-threaded mode and JIT compiler
- Enhanced interactive interpreter with multi-line editing
- Type hints throughout for enterprise code quality
- Async/await for high-performance I/O operations

**Package Manager**: uv 0.8.6+
- Latest version (August 7, 2025)
- 10-100x faster than pip for large projects
- Built-in virtual environment management
- Lock file support for reproducible builds
- uvx support for easy local development execution

## Development & Local Environment

**Local Development Mode**: uvx
- Single command startup: `uvx mcp-server`
- Hot reload with file watching
- Local SQLite database for development
- In-memory caching for fast iteration

**Development Database**: SQLite 3.45+
- Zero-configuration local development
- File-based storage with full SQL support
- Migration compatibility with production PostgreSQL
- Built-in JSON support for configuration storage

**Local Storage**: File System
- Sandboxed access with path validation
- File watching and indexing capabilities
- Support for markdown, JSON, and text files
- Local secrets via Python keyring

## Production Infrastructure

**Container Platform**: Docker 28.2+
- Latest stable version (August 2025)
- Multi-stage builds (development + production)
- Non-root user execution for security
- Distroless base images for minimal attack surface
- Health check integration

**Container Orchestration**: Kubernetes 1.33+
- Current stable version (1.33.3 latest patch)
- Kubernetes 1.34 releasing August 27, 2025
- Deployment with rolling update strategy
- HorizontalPodAutoscaler for scaling
- Service mesh compatibility (Istio/Linkerd)
- NetworkPolicy for micro-segmentation

**Primary Database**: PostgreSQL 17.5+
- Latest stable version (released May 8, 2025)
- Overhauled memory management for vacuum (20x less memory)
- JSONB support for flexible configuration storage
- Connection pooling with pgbouncer
- High availability with streaming replication
- Automated backup and point-in-time recovery

**Caching**: Redis 7.4+
- Latest stable production version (August 2025)
- Memory and speed optimizations for lists, sets, sorted sets
- Distributed session storage
- Query result caching
- Rate limiting counters
- Pub/sub for real-time notifications

## Cloud Storage & CDN

**Cloud Storage**: Multi-provider abstraction
- AWS S3 with CloudFront CDN
- Azure Blob Storage with CDN
- Google Cloud Storage with Cloud CDN
- Streaming support for large files
- Signed URL generation for secure access

**File Processing**:
- Streaming uploads/downloads
- Automatic compression for text files
- Image optimization and resizing
- Document indexing and search

## Security & Authentication

**Authentication Framework**: Authlib 1.3+
- OAuth 2.1 with PKCE implementation
- JWT validation with RS256/ES256 algorithms
- Token introspection and validation
- Multi-provider support (Auth0, Okta, Azure AD)

**Authorization**: PyCasbin 1.25+
- Role-Based Access Control (RBAC)
- Policy-as-code with CSV/JSON configurations
- Hierarchical role definitions
- Dynamic permission evaluation

**Secrets Management**:
- HashiCorp Vault integration
- AWS Secrets Manager support
- Azure Key Vault integration
- Google Secret Manager compatibility
- Local development with python-keyring

## Monitoring & Observability

**Metrics**: OpenTelemetry 1.36.0+ + Prometheus
- Latest stable version (July 29, 2025)
- Custom MCP operation metrics
- Request rate, latency, and error tracking
- Business metrics (tool invocations, user sessions)
- Auto-instrumentation for HTTP and database calls

**Logging**: structlog 24.1+
- Structured JSON logging
- Correlation ID propagation
- Sensitive data masking
- Log level filtering and sampling

**Distributed Tracing**: OpenTelemetry 1.36.0+
- Jaeger and Zipkin exporter support
- Trace context propagation across services
- Custom span attributes for MCP operations
- Performance bottleneck identification

**Health Checks**: Custom implementation
- Liveness, readiness, and startup probes
- Dependency health verification
- Graceful shutdown handling
- Circuit breaker patterns

## Infrastructure as Code

**Infrastructure**: Terraform 1.6+
- Multi-cloud module structure
- State management with remote backends
- Resource tagging and cost optimization
- Environment-specific configurations

**Deployment**: Helm 3.13+
- Parameterized charts for different environments
- Secret management integration
- ConfigMap templating
- Rolling update strategies

**CI/CD**: GitHub Actions
- Multi-stage pipeline with testing gates
- Security scanning (SAST, dependency check)
- Container vulnerability scanning
- Automated deployment with approval workflows

## Development Tools & Quality

**Code Formatting**: Ruff 0.12.8+
- Latest version (August 2025)
- Replaces Black, isort, pyupgrade, autoflake, and most Flake8 plugins
- 10-100x faster than traditional tools
- 800+ built-in rules with native re-implementations
- Pre-commit hook integration

**Type Checking**: mypy 1.17.1+
- Latest version (July 31, 2025)
- Requires Python 3.9+ (dropped 3.8 support)
- Exhaustive match statement checking
- Integration with IDE for real-time feedback
- Incremental checking for large codebases

**Testing Framework**: pytest 8.4.1+
- Latest stable version (August 2025)
- pytest-asyncio for async test support
- pytest-mock for dependency mocking
- pytest-cov for coverage reporting
- pytest-benchmark for performance testing

**Pre-commit Hooks**: pre-commit 4.5.0+
- Latest version of pre-commit-hooks repository
- Automated code formatting and linting with Ruff
- Security scanning with bandit
- Dependency vulnerability checking
- Commit message validation

## Performance Optimization

**ASGI Server**: uvicorn 0.24+
- High-performance ASGI implementation
- HTTP/2 support for modern clients
- WebSocket support for real-time features
- Graceful shutdown and reload

**Connection Pooling**: asyncpg + pgbouncer
- Async PostgreSQL driver
- Connection pooling for database efficiency
- Prepared statement caching
- Transaction-level pooling

**Caching Strategy**:
- Application-level caching with TTL
- Database query result caching
- HTTP response caching with ETags
- CDN caching for static resources

## Cloud Provider Integration

**AWS**:
- ECS with Fargate for serverless containers
- EKS for Kubernetes workloads
- RDS for PostgreSQL hosting
- ElastiCache for Redis
- CloudWatch for monitoring

**Azure**:
- Container Instances for simple deployments
- AKS for enterprise Kubernetes
- PostgreSQL Flexible Server
- Azure Cache for Redis
- Azure Monitor integration

**Google Cloud**:
- Cloud Run for serverless containers
- GKE Autopilot for managed Kubernetes
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Cloud Logging and Monitoring

## API & Documentation

**API Documentation**: OpenAPI 3.1
- Automatic schema generation from FastMCP
- Interactive documentation with Swagger UI
- Client SDK generation support
- API versioning and deprecation management

**Documentation**: MkDocs Material
- Markdown-based documentation
- API reference integration
- Code example highlighting
- Search functionality

## Environment Configuration

**Development**: .env + Pydantic Settings
- Type-safe configuration management
- Environment variable validation
- Default value handling
- Configuration hot-reload in development

**Production**: Kubernetes ConfigMap/Secret
- External configuration management
- Secret encryption at rest
- Configuration versioning
- Rolling configuration updates

## Deployment Modes

**Local Development**:
- uvx execution with hot reload
- SQLite database
- File system storage
- Local caching

**Docker Development**:
- docker-compose with volume mounts
- PostgreSQL container
- Redis container
- Object storage emulation (MinIO)

**Production**:
- Kubernetes deployment
- Managed cloud services
- External monitoring
- Auto-scaling and load balancing
