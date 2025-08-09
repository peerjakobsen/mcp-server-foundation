# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an enterprise-ready Model Context Protocol (MCP) server foundation built with FastMCP 2.11+. The project implements a dual-mode architecture supporting both local development via uvx and cloud-native production deployment with Docker/Kubernetes.

## Key Architecture Concepts

### Dual-Mode Configuration System
The entire system is built around `src/mcp_server/config.py` which provides environment-aware configuration through Pydantic Settings. The `DeploymentMode` enum drives different behaviors:
- `development`/`uvx`: SQLite database, local storage, hot reload enabled
- `docker`/`production`: PostgreSQL, cloud storage, production optimizations

Configuration auto-adapts based on deployment mode with intelligent defaults and validation.

### FastMCP Integration Pattern
The `MCPServerFoundation` class in `src/mcp_server/main.py` wraps FastMCP with enterprise features. Tools are registered using the `@app.tool` decorator pattern, and resources use `@app.resource("uri://path")`. The server automatically handles JSON-RPC 2.0 compliance and MCP protocol specifics.

### Agent OS Product Structure
This project follows Agent OS methodology with product documentation in `.agent-os/product/`:
- `mission.md`: Full product vision and user personas
- `decisions.md`: Architectural decisions with **highest override priority**
- `roadmap.md`: Development phases with trackable checkboxes
- `tech-stack.md`: Technology choices with current versions

## Essential Development Commands

### Environment Setup
```bash
# Initial setup
uv sync --all-extras

# Copy configuration
cp .env.example .env
```

### Development Server
```bash
# Start development server (auto-reload enabled)
uv run mcp-server

# Alternative: direct module execution
uv run python -m mcp_server.main
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_config.py

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test markers
uv run pytest -m unit
uv run pytest -m "not slow"
```

### Code Quality
```bash
# Format and lint (Ruff handles both)
uv run ruff format .
uv run ruff check .

# Type checking
uv run mypy src/

# Security scanning
uv run bandit -r src/

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

### Testing MCP Functionality
```bash
# Server runs on /mcp/ endpoint (not root)
# Server URL: http://localhost:8000/mcp/

# Note: FastMCP requires proper MCP clients, not raw HTTP
# Raw curl commands will return 406/400 errors (this is expected)

# Verify server is running (expect 406 Not Acceptable - this is correct!)
curl http://localhost:8000/mcp/

# For actual testing, use MCP-compatible clients:
# - Claude Desktop with MCP server configuration
# - VS Code MCP extensions
# - Custom MCP client libraries
```

## Configuration Management

### Environment Variables
All configuration flows through `MCPServerConfig` in `src/mcp_server/config.py`. Key patterns:
- Settings auto-adapt based on `DEPLOYMENT_MODE`
- Database URLs validate against deployment mode (SQLite for dev, PostgreSQL for prod)
- Debug/reload flags automatically set for development modes
- Storage backends switch between local filesystem and cloud providers

### Configuration Priority
1. Environment variables
2. `.env` files
3. Pydantic field defaults
4. Mode-specific auto-configuration

## Adding New MCP Tools

Tools are registered in `MCPServerFoundation._register_example_tools()`:

```python
@self.app.tool
async def my_new_tool(param: str) -> dict:
    """Tool description for MCP clients.

    Args:
        param: Parameter description

    Returns:
        Dictionary with results
    """
    return {"result": param}
```

## Adding New MCP Resources

Resources follow the URI pattern:

```python
@self.app.resource("resource://my-resource")
async def my_resource() -> dict:
    """Resource description."""
    return {"content": "resource data"}
```

## Deployment Modes

### Local Development (`uvx`)
- Uses SQLite database at `./data/mcp.db`
- Local file storage at `./data/storage`
- Hot reload enabled
- Debug logging active

### Production (`docker`/`production`)
- Expects PostgreSQL via `DATABASE_URL`
- Cloud storage (S3/Azure/GCS) via `STORAGE_BACKEND`
- Redis for distributed caching via `REDIS_URL`
- Security features enabled by default

## Enterprise Security Features

### Authentication System
Located in `src/mcp_server/auth/` (to be implemented):
- OAuth 2.1 with PKCE flow
- API key authentication for service accounts
- Role-Based Access Control (RBAC) with Casbin

### Configuration Requirements
Production deployments require:
- `SECRET_KEY`: Cryptographic signing key
- `OAUTH_PROVIDER_URL`: OAuth 2.1 provider endpoint
- Database and Redis connection strings
- Cloud storage credentials (via environment or IAM)

## Technology Stack (August 2025 versions)
- FastMCP 2.11+ (Enterprise authentication features)
- Python 3.13.6+ (free-threading and JIT compiler support)
- uv 0.8.6+ package manager
- Ruff 0.12.8+ (replaces Black, isort, Flake8)
- pytest 8.4.1+ with asyncio support
- Pydantic 2.0+ for configuration management

## MCP Server Development - Critical Fixes & Patterns

### Getting Started - Essential Steps
```bash
# 1. Fix Python version compatibility (if needed)
# Edit pyproject.toml: requires-python = ">=3.13.0"

# 2. Fix hatchling build configuration
# Add to pyproject.toml:
# [tool.hatch.build.targets.wheel]
# packages = ["src/mcp_server"]

# 3. Install dependencies
uv sync --all-extras

# 4. Create environment file
cp .env.example .env

# 5. Start server
uv run mcp-server
```

### FastMCP Integration - Key Patterns
- **NEVER use uvicorn directly** - FastMCP has built-in `run_http_async()` server
- **Server endpoint**: http://127.0.0.1:8000/mcp/ (note the `/mcp/` path)
- **Transport**: Streamable-HTTP (supports Server-Sent Events)
- **Testing**: Requires proper MCP clients, not raw curl commands

### MyPy Type Safety Guidelines
- Always annotate function parameters and return types: `def func(param: str) -> dict[str, Any]:`
- Use `# type: ignore[misc]` for FastMCP decorators: `@self.app.tool  # type: ignore[misc]`
- Pydantic validators need `ValidationInfo`: `def validator(cls, v: Any, info: ValidationInfo) -> Any:`
- Run `uv run mypy src/` before commits to ensure type safety

### Pydantic v2 Configuration Fixes
```python
# Fix imports in config.py
from pydantic import Field, validator  # OLD - causes import error
from pydantic import Field
from pydantic_settings import BaseSettings  # NEW - required

# Fix deprecated validators (future enhancement)
@validator("field")  # OLD - deprecated warnings
@field_validator("field")  # NEW - Pydantic v2 style
```

### Server Architecture
```python
# Correct FastMCP usage in main.py
def main():
    app = create_app(config)  # FastMCP instance
    asyncio.run(app.run_http_async(host=config.host, port=config.port))  # Built-in server
```

### Development Workflow
1. Server auto-detects development mode
2. Uses SQLite database (`./data/mcp.db`)
3. Local storage (`./data/storage`)
4. Hot reload enabled automatically
5. Debug logging active

### Common Issues & Solutions
- **"BaseSettings import error"** → Use `from pydantic_settings import BaseSettings`
- **"FastMCP object not callable"** → Use `app.run_http_async()`, not uvicorn
- **"Missing session ID" in curl tests** → Server expects MCP protocol clients
- **Build errors with hatchling** → Add wheel packages configuration

### MCP Protocol Testing
The server responds correctly to MCP clients but rejects raw HTTP:
- ✅ `406 Not Acceptable` = Server working, needs proper MCP headers
- ✅ `400 Bad Request` = Server working, needs valid MCP protocol
- ❌ Connection refused = Server not running

## Important Files to Reference
- `.agent-os/product/decisions.md`: Architectural decisions (highest override priority)
- `pyproject.toml`: All dependencies and tool configurations
- `src/mcp_server/config.py`: Complete configuration system
- `.env.example`: All available configuration options
- `.agent-os/product/roadmap.md`: Development phases with progress tracking
