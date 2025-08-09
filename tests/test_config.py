"""Tests for the MCP server configuration module."""

import os
from unittest.mock import patch

import pytest

from mcp_server.config import (
    DeploymentMode,
    LogLevel,
    MCPServerConfig,
    StorageBackend,
    get_config,
)


class TestDeploymentMode:
    """Test the DeploymentMode enum."""

    def test_deployment_mode_values(self):
        """Test deployment mode enum values."""
        assert DeploymentMode.DEVELOPMENT == "development"
        assert DeploymentMode.UVX == "uvx"
        assert DeploymentMode.DOCKER == "docker"
        assert DeploymentMode.PRODUCTION == "production"


class TestLogLevel:
    """Test the LogLevel enum."""

    def test_log_level_values(self):
        """Test log level enum values."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"


class TestStorageBackend:
    """Test the StorageBackend enum."""

    def test_storage_backend_values(self):
        """Test storage backend enum values."""
        assert StorageBackend.LOCAL == "local"
        assert StorageBackend.S3 == "s3"
        assert StorageBackend.AZURE == "azure"
        assert StorageBackend.GCS == "gcs"


class TestMCPServerConfig:
    """Test the MCPServerConfig class."""

    def test_default_configuration(self):
        """Test configuration with default values."""
        config = MCPServerConfig()

        # Core settings
        assert config.server_name == "mcp-server-foundation"
        assert config.deployment_mode == DeploymentMode.DEVELOPMENT
        assert config.debug is True  # From .env file
        assert config.log_level == LogLevel.DEBUG  # From .env file

        # Server settings
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.reload is True  # Auto-set based on development mode
        assert config.workers == 1

        # Security settings
        assert config.auth_enabled is False  # From .env file
        assert config.oauth_provider_url == ""  # From .env file
        assert config.api_key_header == "X-API-Key"
        assert config.secret_key == "dev-secret-key-change-in-production"

        # Performance settings
        assert config.max_connections == 100
        assert config.request_timeout == 30.0
        assert config.cache_ttl == 3600

        # Database settings
        assert config.database_url == "sqlite:///./data/mcp.db"
        assert config.database_echo is False
        assert config.database_pool_size == 10
        assert config.database_max_overflow == 20

        # Redis settings
        assert config.redis_url == ""  # From .env file
        assert config.redis_ssl is False
        assert config.redis_db == 0

        # Storage settings
        assert config.storage_backend == StorageBackend.LOCAL
        assert config.storage_path == "./data/storage"
        assert config.storage_bucket == ""  # From .env file
        assert config.storage_region == ""  # From .env file

        # Observability settings
        assert config.enable_metrics is True
        assert config.enable_tracing is True
        assert config.tracing_endpoint == ""  # From .env file
        assert config.metrics_path == "/metrics"

        # Development settings
        assert config.use_file_watcher is True  # From .env file
        assert config.auto_create_tables is True

    def test_development_mode_configuration(self):
        """Test configuration in development mode."""
        config = MCPServerConfig(deployment_mode=DeploymentMode.DEVELOPMENT)

        assert config.deployment_mode == DeploymentMode.DEVELOPMENT
        assert config.is_development is True
        assert config.is_production is False
        assert config.debug is True
        assert config.reload is True
        assert config.use_file_watcher is True
        assert config.database_url == "sqlite:///./data/mcp.db"

    def test_uvx_mode_configuration(self):
        """Test configuration in uvx mode."""
        config = MCPServerConfig(deployment_mode=DeploymentMode.UVX)

        assert config.deployment_mode == DeploymentMode.UVX
        assert config.is_development is True
        assert config.is_production is False
        assert config.debug is True
        assert config.reload is True
        assert config.use_file_watcher is True

    def test_production_mode_configuration(self):
        """Test configuration in production mode."""
        # Explicitly set debug to override .env file
        config = MCPServerConfig(
            deployment_mode=DeploymentMode.PRODUCTION,
            debug=False,
            reload=False,
            use_file_watcher=False,
        )

        assert config.deployment_mode == DeploymentMode.PRODUCTION
        assert config.is_development is False
        assert config.is_production is True
        assert config.debug is False
        assert config.reload is False
        assert config.use_file_watcher is False

    def test_docker_mode_configuration(self):
        """Test configuration in docker mode."""
        config = MCPServerConfig(
            deployment_mode=DeploymentMode.DOCKER,
            debug=False,
            reload=False,
            use_file_watcher=False,
        )

        assert config.deployment_mode == DeploymentMode.DOCKER
        assert config.is_development is False
        assert config.is_production is True
        assert config.debug is False
        assert config.reload is False
        assert config.use_file_watcher is False

    def test_custom_configuration(self):
        """Test configuration with custom values."""
        config = MCPServerConfig(
            server_name="custom-server",
            deployment_mode=DeploymentMode.PRODUCTION,
            debug=True,  # Explicitly set despite production mode
            host="0.0.0.0",
            port=9000,
            database_url="postgresql://user:pass@localhost/db",
            redis_url="redis://localhost:6379/1",
            storage_backend=StorageBackend.S3,
            storage_bucket="my-bucket",
            storage_region="us-west-2",
        )

        assert config.server_name == "custom-server"
        assert config.deployment_mode == DeploymentMode.PRODUCTION
        assert config.debug is True  # Explicitly set value preserved
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.database_url == "postgresql://user:pass@localhost/db"
        assert config.redis_url == "redis://localhost:6379/1"
        assert config.storage_backend == StorageBackend.S3
        assert config.storage_bucket == "my-bucket"
        assert config.storage_region == "us-west-2"

    def test_deployment_mode_string_normalization(self):
        """Test deployment mode string normalization."""
        config = MCPServerConfig(deployment_mode="DEVELOPMENT")
        assert config.deployment_mode == "development"

        config = MCPServerConfig(deployment_mode="Production")
        assert config.deployment_mode == "production"

    def test_database_url_validation_development(self):
        """Test database URL validation for development modes."""
        # Should force SQLite for development mode
        config = MCPServerConfig(
            deployment_mode=DeploymentMode.DEVELOPMENT,
            database_url="postgresql://localhost/test",
        )
        assert config.database_url == "sqlite:///./data/mcp.db"

        # Should force SQLite for uvx mode
        config = MCPServerConfig(
            deployment_mode=DeploymentMode.UVX,
            database_url="postgresql://localhost/test",
        )
        assert config.database_url == "sqlite:///./data/mcp.db"

    def test_database_url_validation_production(self):
        """Test database URL validation for production modes."""
        # Should preserve non-SQLite URLs in production
        config = MCPServerConfig(
            deployment_mode=DeploymentMode.PRODUCTION,
            database_url="postgresql://localhost/prod",
        )
        assert config.database_url == "postgresql://localhost/prod"

    def test_port_validation(self):
        """Test port number validation."""
        with pytest.raises(ValueError):
            MCPServerConfig(port=0)

        with pytest.raises(ValueError):
            MCPServerConfig(port=70000)

        # Valid ports should work
        config = MCPServerConfig(port=8080)
        assert config.port == 8080

    def test_workers_validation(self):
        """Test workers validation."""
        with pytest.raises(ValueError):
            MCPServerConfig(workers=0)

        config = MCPServerConfig(workers=4)
        assert config.workers == 4

    def test_redis_db_validation(self):
        """Test Redis database number validation."""
        with pytest.raises(ValueError):
            MCPServerConfig(redis_db=-1)

        with pytest.raises(ValueError):
            MCPServerConfig(redis_db=16)

        config = MCPServerConfig(redis_db=5)
        assert config.redis_db == 5

    def test_get_storage_config_local(self):
        """Test storage configuration for local backend."""
        config = MCPServerConfig(
            storage_backend=StorageBackend.LOCAL,
            storage_path="/tmp/storage",
        )

        storage_config = config.get_storage_config()
        expected = {
            "backend": StorageBackend.LOCAL,
            "path": "/tmp/storage",
        }
        assert storage_config == expected

    def test_get_storage_config_s3(self):
        """Test storage configuration for S3 backend."""
        config = MCPServerConfig(
            storage_backend=StorageBackend.S3,
            storage_path="/tmp/storage",
            storage_bucket="my-bucket",
            storage_region="us-east-1",
        )

        storage_config = config.get_storage_config()
        expected = {
            "backend": StorageBackend.S3,
            "path": "/tmp/storage",
            "bucket": "my-bucket",
            "region": "us-east-1",
        }
        assert storage_config == expected

    def test_get_storage_config_partial_cloud_settings(self):
        """Test storage configuration with partial cloud settings."""
        config = MCPServerConfig(
            storage_backend=StorageBackend.AZURE,
            storage_path="/tmp/storage",
            storage_bucket="my-bucket",
            # storage_region is None
        )

        storage_config = config.get_storage_config()
        expected = {
            "backend": StorageBackend.AZURE,
            "path": "/tmp/storage",
            "bucket": "my-bucket",
            # region should not be included when None
        }
        assert storage_config == expected

    @pytest.mark.parametrize(
        "env_var,expected_value",
        [
            ("DEPLOYMENT_MODE", "production"),
            ("DEBUG", True),
            ("HOST", "0.0.0.0"),
            ("PORT", 9000),
            ("SERVER_NAME", "test-server"),
            ("LOG_LEVEL", "DEBUG"),
            ("DATABASE_URL", "postgresql://localhost/test"),
            ("REDIS_URL", "redis://localhost:6379"),
            ("STORAGE_BACKEND", "s3"),
            ("STORAGE_BUCKET", "test-bucket"),
            ("SECRET_KEY", "test-secret"),
        ],
    )
    def test_environment_variable_loading(self, env_var, expected_value):
        """Test loading configuration from environment variables."""
        env_vars = {env_var: str(expected_value)}

        # For DATABASE_URL with PostgreSQL, we need production mode
        if env_var == "DATABASE_URL" and "postgresql" in str(expected_value):
            env_vars["DEPLOYMENT_MODE"] = "production"

        with patch.dict(os.environ, env_vars):
            config = MCPServerConfig()

            # Convert env var name to config field name
            field_name = env_var.lower()
            if hasattr(config, field_name):
                actual_value = getattr(config, field_name)

                # Handle type conversion
                if isinstance(expected_value, bool):
                    # Environment variables come as strings
                    assert actual_value == expected_value
                elif env_var == "PORT":
                    assert actual_value == expected_value
                else:
                    assert actual_value == expected_value


class TestGetConfig:
    """Test the get_config function."""

    def test_get_config_returns_instance(self):
        """Test that get_config returns a MCPServerConfig instance."""
        config = get_config()
        assert isinstance(config, MCPServerConfig)

    def test_get_config_singleton_behavior(self):
        """Test that get_config returns the same instance (singleton-like behavior)."""
        config1 = get_config()
        config2 = get_config()
        # Note: This may not be truly singleton depending on implementation
        # but both should have the same configuration values
        assert config1.server_name == config2.server_name
        assert config1.deployment_mode == config2.deployment_mode

    def test_get_config_with_environment_override(self):
        """Test get_config with environment variable overrides."""
        with patch.dict(
            os.environ,
            {
                "DEPLOYMENT_MODE": "production",
                "DEBUG": "false",
                "PORT": "9000",
            },
        ):
            config = get_config()
            assert config.deployment_mode == DeploymentMode.PRODUCTION
            assert config.debug is False
            assert config.port == 9000
