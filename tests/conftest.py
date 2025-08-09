"""Test configuration and fixtures for the MCP server foundation."""

import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from fastmcp import FastMCP

from mcp_server.config import DeploymentMode, MCPServerConfig
from mcp_server.main import MCPServerFoundation, create_app


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path]:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_path:
        yield Path(temp_path)


@pytest.fixture
def test_config(temp_dir: Path) -> MCPServerConfig:
    """Create a test configuration with isolated database and storage."""
    return MCPServerConfig(
        deployment_mode=DeploymentMode.DEVELOPMENT,
        debug=True,
        host="127.0.0.1",
        port=8000,
        database_url=f"sqlite:///{temp_dir}/test.db",
        storage_path=str(temp_dir / "storage"),
        log_level="DEBUG",
        secret_key="test-secret-key-for-testing-only",
    )


@pytest.fixture
def production_test_config(temp_dir: Path) -> MCPServerConfig:
    """Create a test configuration simulating production mode."""
    return MCPServerConfig(
        deployment_mode=DeploymentMode.PRODUCTION,
        debug=False,
        host="0.0.0.0",
        port=8000,
        database_url="postgresql://test:test@localhost:5432/test",
        storage_backend="local",
        storage_path=str(temp_dir / "production_storage"),
        log_level="INFO",
        secret_key="production-test-secret-key",
        redis_url="redis://localhost:6379",
    )


@pytest.fixture
async def test_app(test_config: MCPServerConfig) -> AsyncGenerator[FastMCP]:
    """Create a test FastMCP application instance."""
    app = create_app(test_config)
    yield app


@pytest.fixture
async def test_server(
    test_config: MCPServerConfig,
) -> AsyncGenerator[MCPServerFoundation]:
    """Create a test MCP server foundation instance."""
    server = MCPServerFoundation(test_config)
    yield server


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before and after each test."""
    # Store original environment
    original_env = dict(os.environ)

    # Clear MCP-related environment variables
    mcp_env_vars = [
        "DEPLOYMENT_MODE",
        "DEBUG",
        "HOST",
        "PORT",
        "DATABASE_URL",
        "REDIS_URL",
        "STORAGE_BACKEND",
        "STORAGE_PATH",
        "LOG_LEVEL",
        "SECRET_KEY",
    ]

    for var in mcp_env_vars:
        os.environ.pop(var, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_tool_response():
    """Mock response for tool testing."""
    return {"status": "success", "result": "test result"}


@pytest.fixture
def mock_resource_data():
    """Mock data for resource testing."""
    return {
        "uri": "resource://test-resource",
        "name": "Test Resource",
        "description": "A test resource for unit testing",
        "mimeType": "application/json",
    }


# Test markers configuration
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running tests")


# Async test configuration
@pytest_asyncio.fixture(scope="session")
def event_loop_policy():
    """Use the default event loop policy for async tests."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()
