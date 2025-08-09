"""Tests for the main MCP server foundation module."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastmcp import FastMCP

from mcp_server.config import DeploymentMode, MCPServerConfig, StorageBackend
from mcp_server.main import HealthResponse, MCPServerFoundation, create_app, main


class TestHealthResponse:
    """Test the HealthResponse model."""

    def test_health_response_creation(self):
        """Test creating a health response."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            deployment_mode=DeploymentMode.DEVELOPMENT,
            timestamp="2025-08-09T00:00:00Z",
        )

        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.deployment_mode == DeploymentMode.DEVELOPMENT
        assert response.timestamp == "2025-08-09T00:00:00Z"


class TestMCPServerFoundation:
    """Test the MCPServerFoundation class."""

    def test_init_with_config(self, test_config):
        """Test initialization with provided config."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        assert server.config == test_config
        assert isinstance(server.app, FastMCP)
        assert server.app.name == test_config.server_name

    def test_init_without_config(self):
        """Test initialization without config (loads from environment)."""
        with patch("mcp_server.main.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.server_name = "test-server"
            mock_config.is_development = True
            mock_config.use_file_watcher = True
            mock_config.storage_path = "./test/storage"
            mock_get_config.return_value = mock_config

            server = MCPServerFoundation()

            assert server.config == mock_config
            assert isinstance(server.app, FastMCP)
            mock_get_config.assert_called_once()

    def test_setup_development_mode(self, test_config, temp_dir):
        """Test development mode setup."""
        test_config.deployment_mode = DeploymentMode.DEVELOPMENT
        test_config.use_file_watcher = True
        test_config.storage_path = str(temp_dir / "storage")

        server = MCPServerFoundation(test_config)  # noqa: F841

        # Verify storage directory is created
        assert (temp_dir / "storage").exists()

        # Verify database directory is created
        assert Path("./data").exists()

        # Clean up
        Path("./data").rmdir() if Path("./data").exists() and not any(
            Path("./data").iterdir()
        ) else None

    def test_setup_production_mode(self, production_test_config):
        """Test production mode setup."""
        server = MCPServerFoundation(production_test_config)

        # Production setup should complete without errors
        assert server.config == production_test_config
        assert not server.config.is_development
        assert server.config.is_production

    def test_get_fastmcp_app(self, test_config):
        """Test getting the FastMCP app instance."""
        server = MCPServerFoundation(test_config)  # noqa: F841
        app = server.get_fastmcp_app()

        assert isinstance(app, FastMCP)
        assert app is server.app
        assert app.name == test_config.server_name

    @pytest.mark.asyncio
    async def test_health_check_resource(self, test_config):
        """Test health check resource registration and functionality."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Get the registered health check function
        # Note: This is a simplified test - in practice we'd need to test through FastMCP's resource system
        assert server.app is not None

        # The health check should be registered as a resource
        # We can verify the server initialized without errors
        assert server.config.deployment_mode == test_config.deployment_mode

    @pytest.mark.asyncio
    async def test_example_tools_registration(self, test_config):
        """Test example tools registration."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Verify the server has the FastMCP app with tools registered
        assert server.app is not None
        assert isinstance(server.app, FastMCP)

        # The tools should be registered but we can't easily test them directly
        # without accessing FastMCP's internal tool registry
        # This test verifies the server initializes without errors
        assert server.config == test_config


class TestCreateApp:
    """Test the create_app function."""

    def test_create_app_with_config(self, test_config):
        """Test creating app with provided config."""
        app = create_app(test_config)

        assert isinstance(app, FastMCP)
        assert app.name == test_config.server_name

    def test_create_app_without_config(self):
        """Test creating app without config."""
        with patch("mcp_server.main.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.server_name = "default-server"
            mock_config.is_development = True
            mock_config.use_file_watcher = False
            mock_config.storage_path = "./test/storage"
            mock_get_config.return_value = mock_config

            app = create_app()

            assert isinstance(app, FastMCP)
            mock_get_config.assert_called_once()

    def test_create_app_development_mode(self, test_config):
        """Test creating app in development mode."""
        test_config.deployment_mode = DeploymentMode.DEVELOPMENT

        app = create_app(test_config)

        assert isinstance(app, FastMCP)
        assert app.name == test_config.server_name

    def test_create_app_production_mode(self, production_test_config):
        """Test creating app in production mode."""
        app = create_app(production_test_config)

        assert isinstance(app, FastMCP)
        assert app.name == production_test_config.server_name


class TestMain:
    """Test the main function."""

    @patch("mcp_server.main.create_app")
    @patch("asyncio.run")
    def test_main_function(self, mock_asyncio_run, mock_create_app):
        """Test the main function execution."""
        # Mock the FastMCP app
        mock_app = Mock()
        mock_app.run_http_async = AsyncMock()
        mock_create_app.return_value = mock_app

        # Mock config
        mock_config = Mock()
        mock_config.host = "127.0.0.1"
        mock_config.port = 8000

        with patch("mcp_server.main.get_config", return_value=mock_config):
            main()

        # Verify create_app was called with config
        mock_create_app.assert_called_once_with(mock_config)

        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()

        # Verify asyncio.run was called with some callable
        # The exact structure is complex due to the async lambda
        call_args = mock_asyncio_run.call_args[0]
        assert len(call_args) == 1
        # The argument should be a coroutine or awaitable
        assert hasattr(call_args[0], "__await__") or callable(call_args[0])

    @patch("mcp_server.main.create_app")
    def test_main_function_integration(self, mock_create_app):
        """Test main function with actual config."""
        # Create a real config for testing
        test_config = MCPServerConfig(
            deployment_mode=DeploymentMode.DEVELOPMENT,
            host="127.0.0.1",
            port=8001,  # Use different port to avoid conflicts
            debug=True,
        )

        # Mock the FastMCP app
        mock_app = Mock()
        mock_app.run_http_async = AsyncMock()
        mock_create_app.return_value = mock_app

        with patch("mcp_server.main.get_config", return_value=test_config):
            with patch("asyncio.run") as mock_run:
                main()

                # Verify the app was created with the config
                mock_create_app.assert_called_once_with(test_config)

                # Verify asyncio.run was called with a coroutine
                mock_run.assert_called_once()
                args = mock_run.call_args[0]
                assert len(args) == 1
                assert hasattr(args[0], "__await__")  # It's a coroutine


class TestServerIntegration:
    """Integration tests for server components."""

    def test_server_initialization_flow(self, test_config):
        """Test the complete server initialization flow."""
        # Test that all components work together
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Verify configuration is properly set
        assert server.config == test_config

        # Verify FastMCP app is created
        assert isinstance(server.app, FastMCP)
        assert server.app.name == test_config.server_name

        # Verify setup methods were called (indirectly)
        if test_config.is_development:
            # In development mode, storage directory should be created
            storage_path = Path(test_config.storage_path)
            assert storage_path.exists()

        # Verify the app can be retrieved
        app = server.get_fastmcp_app()
        assert app is server.app

    def test_different_storage_backends(self, temp_dir):
        """Test server initialization with different storage backends."""
        storage_backends = [
            StorageBackend.LOCAL,
            StorageBackend.S3,
            StorageBackend.AZURE,
            StorageBackend.GCS,
        ]

        for backend in storage_backends:
            config = MCPServerConfig(
                deployment_mode=DeploymentMode.DEVELOPMENT,
                storage_backend=backend,
                storage_path=str(temp_dir / f"storage_{backend}"),
            )

            # Should initialize without errors regardless of backend
            server = MCPServerFoundation(config)
            assert server.config.storage_backend == backend
            assert isinstance(server.app, FastMCP)

    def test_deployment_mode_transitions(self, temp_dir):
        """Test server behavior with different deployment modes."""
        modes = [
            DeploymentMode.DEVELOPMENT,
            DeploymentMode.UVX,
            DeploymentMode.DOCKER,
            DeploymentMode.PRODUCTION,
        ]

        for mode in modes:
            config = MCPServerConfig(
                deployment_mode=mode,
                storage_path=str(temp_dir / f"storage_{mode}"),
                secret_key="test-secret-key",
            )

            # Should initialize without errors for all modes
            server = MCPServerFoundation(config)
            assert server.config.deployment_mode == mode
            assert server.config.is_development == (
                mode in [DeploymentMode.DEVELOPMENT, DeploymentMode.UVX]
            )
            assert server.config.is_production == (
                mode in [DeploymentMode.DOCKER, DeploymentMode.PRODUCTION]
            )
            assert isinstance(server.app, FastMCP)
