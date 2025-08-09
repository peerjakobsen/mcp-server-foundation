"""Configuration management for MCP Server Foundation.

Provides type-safe configuration with Pydantic Settings supporting
environment variables, .env files, and dual-mode deployment.
"""

from enum import Enum
from typing import Any

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class DeploymentMode(str, Enum):
    """Deployment mode enumeration."""

    DEVELOPMENT = "development"
    UVX = "uvx"
    DOCKER = "docker"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StorageBackend(str, Enum):
    """Storage backend enumeration."""

    LOCAL = "local"
    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"


class MCPServerConfig(BaseSettings):
    """Main configuration for the MCP Server Foundation."""

    # Core Settings
    server_name: str = Field(default="mcp-server-foundation", description="Server name")
    deployment_mode: DeploymentMode = Field(
        default=DeploymentMode.DEVELOPMENT, description="Deployment mode"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")

    # Server Settings
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload in development")
    workers: int = Field(default=1, ge=1, description="Number of worker processes")

    # Security Settings
    auth_enabled: bool = Field(default=True, description="Enable authentication")
    oauth_provider_url: str | None = Field(
        default=None, description="OAuth provider URL"
    )
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for signing",
    )

    # Performance Settings
    max_connections: int = Field(
        default=100, ge=1, description="Maximum concurrent connections"
    )
    request_timeout: float = Field(
        default=30.0, ge=1.0, description="Request timeout in seconds"
    )
    cache_ttl: int = Field(default=3600, ge=0, description="Cache TTL in seconds")

    # Database Settings
    database_url: str = Field(
        default="sqlite:///./data/mcp.db", description="Database connection URL"
    )
    database_echo: bool = Field(
        default=False, description="Enable database query logging"
    )
    database_pool_size: int = Field(
        default=10, ge=1, description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=20, ge=0, description="Database pool overflow"
    )

    # Redis Settings
    redis_url: str | None = Field(default=None, description="Redis connection URL")
    redis_ssl: bool = Field(default=False, description="Enable Redis SSL")
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis database number")

    # Storage Settings
    storage_backend: StorageBackend = Field(
        default=StorageBackend.LOCAL, description="Storage backend"
    )
    storage_path: str = Field(
        default="./data/storage", description="Local storage path"
    )
    storage_bucket: str | None = Field(
        default=None, description="Cloud storage bucket name"
    )
    storage_region: str | None = Field(default=None, description="Cloud storage region")

    # Observability Settings
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_tracing: bool = Field(
        default=True, description="Enable OpenTelemetry tracing"
    )
    tracing_endpoint: str | None = Field(
        default=None, description="Tracing export endpoint"
    )
    metrics_path: str = Field(
        default="/metrics", description="Prometheus metrics endpoint path"
    )

    # Development Settings
    use_file_watcher: bool = Field(
        default=False, description="Enable file watching in development"
    )
    auto_create_tables: bool = Field(
        default=True, description="Auto-create database tables"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @field_validator("deployment_mode", mode="before")
    def validate_deployment_mode(cls, v: Any) -> Any:
        """Validate and normalize deployment mode."""
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: Any, info: ValidationInfo) -> Any:
        """Validate database URL based on deployment mode."""
        mode = info.data.get("deployment_mode", DeploymentMode.DEVELOPMENT)

        if mode in (
            DeploymentMode.DEVELOPMENT,
            DeploymentMode.UVX,
        ) and not v.startswith("sqlite"):
            # Ensure SQLite for local development
            return "sqlite:///./data/mcp.db"

        return v

    @field_validator("debug", mode="before")
    @classmethod
    def validate_debug(cls, v: Any, info: ValidationInfo) -> Any:
        """Set debug based on deployment mode if not explicitly set."""
        mode = info.data.get("deployment_mode", DeploymentMode.DEVELOPMENT)

        if v is None or v == "":
            return mode in (DeploymentMode.DEVELOPMENT, DeploymentMode.UVX)

        return bool(v)

    @field_validator("reload", mode="before")
    @classmethod
    def validate_reload(cls, v: Any, info: ValidationInfo) -> Any:
        """Set reload based on deployment mode if not explicitly set."""
        mode = info.data.get("deployment_mode", DeploymentMode.DEVELOPMENT)

        if v is None or v == "":
            return mode in (DeploymentMode.DEVELOPMENT, DeploymentMode.UVX)

        return bool(v)

    @field_validator("use_file_watcher", mode="before")
    @classmethod
    def validate_file_watcher(cls, v: Any, info: ValidationInfo) -> Any:
        """Set file watcher based on deployment mode if not explicitly set."""
        mode = info.data.get("deployment_mode", DeploymentMode.DEVELOPMENT)

        if v is None or v == "":
            return mode in (DeploymentMode.DEVELOPMENT, DeploymentMode.UVX)

        return bool(v)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.deployment_mode in (DeploymentMode.DEVELOPMENT, DeploymentMode.UVX)

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.deployment_mode in (
            DeploymentMode.DOCKER,
            DeploymentMode.PRODUCTION,
        )

    def get_storage_config(self) -> dict[str, Any]:
        """Get storage configuration for the selected backend."""
        config = {
            "backend": self.storage_backend,
            "path": self.storage_path,
        }

        if self.storage_backend != StorageBackend.LOCAL:
            # Only add non-None values to avoid type issues
            if self.storage_bucket is not None:
                config["bucket"] = self.storage_bucket
            if self.storage_region is not None:
                config["region"] = self.storage_region

        return config


def get_config() -> MCPServerConfig:
    """Get application configuration."""
    return MCPServerConfig()
