"""Main entry point for the MCP Server Foundation.

Provides dual-mode deployment support with FastMCP integration
for enterprise-ready MCP server applications.
"""

import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel

from .config import DeploymentMode, MCPServerConfig, get_config


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    deployment_mode: str
    timestamp: str


class MCPServerFoundation:
    """Enterprise MCP Server Foundation."""

    def __init__(self, config: MCPServerConfig | None = None):
        """Initialize the MCP server foundation.

        Args:
            config: Optional configuration. If None, loads from environment.
        """
        self.config = config or get_config()
        self.app = FastMCP(self.config.server_name)
        self._setup_server()

    def _setup_server(self) -> None:
        """Set up the MCP server with configuration."""
        # Configure based on deployment mode
        if self.config.is_development:
            self._setup_development_mode()
        else:
            self._setup_production_mode()

        # Register core endpoints
        self._register_health_checks()
        self._register_example_tools()

    def _setup_development_mode(self) -> None:
        """Configure for development mode."""
        # Enable hot reload and file watching
        if self.config.use_file_watcher:
            # File watching setup would go here
            pass

        # Set up local storage
        storage_path = Path(self.config.storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)

        # Set up local database directory
        db_path = Path("./data")
        db_path.mkdir(parents=True, exist_ok=True)

    def _setup_production_mode(self) -> None:
        """Configure for production mode."""
        # Production-specific setup
        # This would include cloud storage, external auth, etc.
        pass

    def _register_health_checks(self) -> None:
        """Register health check endpoints."""

        @self.app.resource("health://status")
        async def health_status() -> HealthResponse:
            """Health status endpoint."""
            from datetime import datetime

            from . import __version__

            return HealthResponse(
                status="healthy",
                version=__version__,
                deployment_mode=self.config.deployment_mode,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

    def _register_example_tools(self) -> None:
        """Register example tools for demonstration."""

        @self.app.tool
        async def echo_message(message: str) -> dict[str, Any]:
            """Echo a message back to the client.

            Args:
                message: The message to echo

            Returns:
                Dictionary containing the echoed message and metadata
            """
            return {
                "echoed_message": message,
                "server_name": self.config.server_name,
                "deployment_mode": self.config.deployment_mode,
                "timestamp": "2025-08-09T00:00:00Z",  # Would use actual timestamp
            }

        @self.app.tool
        async def get_server_info() -> dict[str, Any]:
            """Get information about the MCP server.

            Returns:
                Dictionary containing server information
            """
            from . import __version__

            return {
                "server_name": self.config.server_name,
                "version": __version__,
                "deployment_mode": self.config.deployment_mode,
                "debug": self.config.debug,
                "max_connections": self.config.max_connections,
                "auth_enabled": self.config.auth_enabled,
                "storage_backend": self.config.storage_backend,
            }

    def get_fastmcp_app(self) -> FastMCP:
        """Get the FastMCP application instance."""
        return self.app


def create_app(config: MCPServerConfig | None = None) -> FastMCP:
    """Create and configure the MCP server application.

    Args:
        config: Optional configuration. If None, loads from environment.

    Returns:
        Configured FastMCP application instance
    """
    server = MCPServerFoundation(config)
    return server.get_fastmcp_app()


def main() -> None:
    """Main entry point for the MCP server."""
    config = get_config()

    # Print startup information
    print("🚀 Starting MCP Server Foundation")
    print(f"   Server Name: {config.server_name}")
    print(f"   Deployment Mode: {config.deployment_mode}")
    print(f"   Host: {config.host}:{config.port}")
    print(f"   Debug: {config.debug}")
    print(f"   Auth Enabled: {config.auth_enabled}")
    print(f"   Storage: {config.storage_backend}")

    # Create the application
    app = create_app(config)

    # Handle different deployment modes
    if config.deployment_mode == DeploymentMode.UVX:
        # For uvx execution, we might want different behavior
        print("   Mode: uvx execution")
        print("   Use Ctrl+C to stop the server")

    # Development mode with hot reload
    if config.is_development and config.reload:
        print("   🔄 Hot reload enabled")

    # Start the server using FastMCP's built-in HTTP server
    try:
        import asyncio

        asyncio.run(app.run_http_async(host=config.host, port=config.port))
    except KeyboardInterrupt:
        print("\n🛑 Shutting down MCP Server Foundation")
        sys.exit(0)


if __name__ == "__main__":
    main()
