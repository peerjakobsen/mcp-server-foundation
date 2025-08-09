# Enterprise MCP Server Foundation

An enterprise-ready Model Context Protocol (MCP) server foundation that enables organizations to rapidly build, deploy, and manage MCP server applications with production-ready features.

## Features

- **Dual-Mode Architecture**: Support for both local development (uvx) and cloud-native production deployment
- **Enterprise Security**: OAuth 2.1, API key authentication, and role-based access control
- **Observability**: Built-in metrics, tracing, and structured logging
- **Storage Flexibility**: Local filesystem or cloud storage (S3, Azure Blob, Google Cloud Storage)
- **Configuration Management**: Environment-aware configuration with intelligent defaults

## Quick Start

1. Install dependencies:
   ```bash
   uv sync --all-extras
   ```

2. Run the development server:
   ```bash
   uv run mcp-server
   ```

The server will start at http://127.0.0.1:8000 with auto-reload enabled for development.

## Development

- `uv run pytest` - Run tests
- `uv run ruff check .` - Lint code
- `uv run ruff format .` - Format code
- `uv run mypy src/` - Type check

## License

MIT
