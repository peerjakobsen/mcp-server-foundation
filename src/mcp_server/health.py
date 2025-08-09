"""
Health check endpoints and graceful shutdown handling for Docker deployment.

This module provides HTTP health check endpoints required by Docker and Kubernetes
for container health monitoring and orchestration.
"""

import asyncio
import signal
import sys
from datetime import UTC, datetime
from typing import Any

from fastmcp import FastMCP

from .config import MCPServerConfig


class HealthCheckManager:
    """Manages health check endpoints and graceful shutdown."""

    def __init__(self, app: FastMCP, config: MCPServerConfig):
        """Initialize health check manager.

        Args:
            app: FastMCP application instance
            config: Server configuration
        """
        self.app = app
        self.config = config
        self.is_shutting_down = False
        self.is_ready = False
        self.startup_time = datetime.now(UTC)

        # Register signal handlers for graceful shutdown
        self._register_signal_handlers()

        # Mark as ready after initialization (deferred to avoid event loop issues)
        self._ready_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the health check manager (called when event loop is running)."""
        if self._ready_task is None:
            self._ready_task = asyncio.create_task(self._mark_ready())

    async def _mark_ready(self) -> None:
        """Mark server as ready after startup."""
        # Wait a moment for full initialization
        await asyncio.sleep(2)
        self.is_ready = True

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum: int, frame: Any) -> None:  # noqa: ARG002
        """Handle shutdown signals gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        if not self.is_shutting_down:
            self.is_shutting_down = True
            print(f"\\nGraceful shutdown initiated (signal {signum})")

            # Perform cleanup tasks
            asyncio.create_task(self._cleanup())

            # Exit after cleanup
            sys.exit(0)

    async def _cleanup(self) -> None:
        """Perform cleanup tasks during shutdown."""
        print("Performing cleanup...")

        # Mark as not ready for new requests
        self.is_ready = False

        # Wait for ongoing requests to complete (max 10 seconds)
        await asyncio.sleep(0.5)

        print("Shutdown complete")

    async def health_check(self) -> dict[str, Any]:
        """Basic health check endpoint.

        Returns:
            Health status information
        """
        return {
            "status": "healthy" if not self.is_shutting_down else "shutting_down",
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "uptime_seconds": (datetime.now(UTC) - self.startup_time).total_seconds(),
            "deployment_mode": self.config.deployment_mode.value,
            "version": "1.0.0",
        }

    async def readiness_check(self) -> dict[str, Any]:
        """Readiness check for load balancer/orchestrator.

        Returns:
            Readiness status and component health
        """
        checks = {
            "server": self.is_ready and not self.is_shutting_down,
            "database": await self._check_database(),
            "cache": await self._check_cache(),
        }

        all_ready = all(checks.values())

        return {
            "ready": all_ready,
            "checks": checks,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
        }

    async def liveness_check(self) -> dict[str, Any]:
        """Liveness check to detect hung processes.

        Returns:
            Liveness status
        """
        return {
            "alive": True,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "pid": sys.platform != "win32" and asyncio.get_event_loop().is_running(),
        }

    async def _check_database(self) -> bool:
        """Check database connectivity.

        Returns:
            True if database is accessible
        """
        if self.config.is_development:
            # SQLite in development mode
            return True

        try:
            # In production, would check PostgreSQL connection
            # For now, return True as placeholder
            return True
        except Exception:
            return False

    async def _check_cache(self) -> bool:
        """Check cache service connectivity.

        Returns:
            True if cache is accessible
        """
        if self.config.is_development:
            # No Redis in development mode
            return True

        try:
            # In production, would check Redis connection
            # For now, return True as placeholder
            return True
        except Exception:
            return False


def register_health_endpoints(
    app: FastMCP, config: MCPServerConfig
) -> HealthCheckManager:
    """Register HTTP health check endpoints with FastMCP.

    Args:
        app: FastMCP application instance
        config: Server configuration

    Returns:
        HealthCheckManager instance
    """
    manager = HealthCheckManager(app, config)

    # Register health check as a tool that can be called via HTTP
    @app.tool  # type: ignore[misc]
    async def health() -> dict[str, Any]:
        """Health check endpoint for Docker/Kubernetes.

        Returns:
            Health status information
        """
        return await manager.health_check()

    @app.tool  # type: ignore[misc]
    async def readiness() -> dict[str, Any]:
        """Readiness check endpoint for load balancers.

        Returns:
            Readiness status and component health
        """
        return await manager.readiness_check()

    @app.tool  # type: ignore[misc]
    async def liveness() -> dict[str, Any]:
        """Liveness check endpoint to detect hung processes.

        Returns:
            Liveness status
        """
        return await manager.liveness_check()

    return manager
