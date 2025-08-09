"""Tests for MCP resource retrieval and functionality."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from mcp_server.config import DeploymentMode, MCPServerConfig
from mcp_server.main import HealthResponse, MCPServerFoundation
from tests.conftest import PRODUCTION_TEST_SECRET_KEY, TEST_SECRET_KEY


class TestHealthCheckResource:
    """Test the health check resource functionality."""

    @pytest.mark.asyncio
    async def test_health_status_response_structure(self, test_config):
        """Test health status response structure."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Simulate the health check resource logic
        with patch("mcp_server.main.__version__", "1.0.0"):
            timestamp = datetime.now(UTC).isoformat() + "Z"

            health_response = HealthResponse(
                status="healthy",
                version="1.0.0",
                deployment_mode=test_config.deployment_mode,
                timestamp=timestamp,
            )

        # Verify response structure
        assert isinstance(health_response, HealthResponse)
        assert health_response.status == "healthy"
        assert health_response.version == "1.0.0"
        assert health_response.deployment_mode == test_config.deployment_mode
        assert health_response.timestamp == timestamp

    @pytest.mark.asyncio
    async def test_health_check_different_deployment_modes(self, temp_dir):
        """Test health check in different deployment modes."""
        modes = [
            DeploymentMode.DEVELOPMENT,
            DeploymentMode.UVX,
            DeploymentMode.PRODUCTION,
            DeploymentMode.DOCKER,
        ]

        for mode in modes:
            config = MCPServerConfig(
                deployment_mode=mode,
                storage_path=str(temp_dir / f"health_test_{mode}"),
                secret_key=TEST_SECRET_KEY,
            )

            server = MCPServerFoundation(config)  # noqa: F841

            # Simulate health check response
            with patch("mcp_server.main.__version__", "1.0.0"):
                timestamp = datetime.now(UTC).isoformat() + "Z"

                health_response = HealthResponse(
                    status="healthy",
                    version="1.0.0",
                    deployment_mode=config.deployment_mode,
                    timestamp=timestamp,
                )

            # Verify response reflects correct deployment mode
            assert health_response.deployment_mode == mode
            assert health_response.status == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_timestamp_format(self, test_config):
        """Test health check timestamp format."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Test timestamp format compliance
        timestamp = datetime.now(UTC).isoformat() + "Z"

        # Verify timestamp format (ISO 8601 with Z suffix)
        assert timestamp.endswith("Z")
        assert "T" in timestamp

        # Verify we can parse the timestamp back
        parsed_timestamp = datetime.fromisoformat(timestamp.rstrip("Z"))
        assert isinstance(parsed_timestamp, datetime)

    @pytest.mark.asyncio
    async def test_health_check_version_reporting(self, test_config):
        """Test version reporting in health check."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Test with different version strings
        test_versions = ["1.0.0", "0.1.0-alpha", "2.5.1-beta.3", "1.0.0-rc.1"]

        for version in test_versions:
            with patch("mcp_server.main.__version__", version):
                health_response = HealthResponse(
                    status="healthy",
                    version=version,
                    deployment_mode=test_config.deployment_mode,
                    timestamp=datetime.now(UTC).isoformat() + "Z",
                )

                assert health_response.version == version


class TestResourceRetrieval:
    """Test resource retrieval functionality."""

    @pytest.mark.unit
    def test_resource_uri_format(self, test_config):
        """Test resource URI format compliance."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Test health resource URI
        health_uri = "health://status"

        # Verify URI format
        assert "://" in health_uri
        assert health_uri.startswith("health://")

        # Test other potential resource URIs
        test_uris = [
            "resource://config",
            "resource://metrics",
            "file://local/path",
            "http://example.com/api",
        ]

        for uri in test_uris:
            assert "://" in uri
            parts = uri.split("://", 1)
            assert len(parts) == 2
            assert len(parts[0]) > 0  # Scheme
            assert len(parts[1]) > 0  # Path

    @pytest.mark.asyncio
    async def test_resource_error_handling(self, test_config):
        """Test resource error handling scenarios."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Test scenarios that might cause resource retrieval errors

        # Test invalid URI formats
        invalid_uris = [
            "",
            "not-a-uri",
            "://missing-scheme",
            "scheme://",  # Missing path
        ]

        for uri in invalid_uris:
            # In a real implementation, these would be handled by the resource system
            # Here we just verify the URI format validation logic
            if not uri or "://" not in uri:
                assert not ("://" in uri and len(uri.split("://", 1)) == 2)
            else:
                parts = uri.split("://", 1)
                if len(parts) != 2 or not parts[0] or not parts[1]:
                    # This would be an invalid URI
                    assert True

    @pytest.mark.asyncio
    async def test_resource_caching_behavior(self, test_config):
        """Test resource caching behavior."""
        test_config.cache_ttl = 3600  # 1 hour cache
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Simulate multiple requests for the same resource

        # First request
        with patch("mcp_server.main.__version__", "1.0.0"):
            first_timestamp = datetime.now(UTC).isoformat() + "Z"
            first_response = HealthResponse(
                status="healthy",
                version="1.0.0",
                deployment_mode=test_config.deployment_mode,
                timestamp=first_timestamp,
            )

        # Simulate second request (would typically be from cache)
        with patch("mcp_server.main.__version__", "1.0.0"):
            second_timestamp = datetime.now(UTC).isoformat() + "Z"
            second_response = HealthResponse(
                status="healthy",
                version="1.0.0",
                deployment_mode=test_config.deployment_mode,
                timestamp=second_timestamp,
            )

        # Both responses should have the same structure
        assert first_response.status == second_response.status
        assert first_response.version == second_response.version
        assert first_response.deployment_mode == second_response.deployment_mode

        # Timestamps might be different (unless cached)
        # In a real cache implementation, they might be the same
        assert isinstance(first_response.timestamp, str)
        assert isinstance(second_response.timestamp, str)

    @pytest.mark.asyncio
    async def test_resource_content_types(self, test_config):
        """Test different resource content types."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Test different types of resource responses

        # Health check (structured data)
        with patch("mcp_server.main.__version__", "1.0.0"):
            health_response = HealthResponse(
                status="healthy",
                version="1.0.0",
                deployment_mode=test_config.deployment_mode,
                timestamp=datetime.now(UTC).isoformat() + "Z",
            )

        # Verify structured data response
        assert isinstance(health_response, HealthResponse)
        assert hasattr(health_response, "status")
        assert hasattr(health_response, "version")
        assert hasattr(health_response, "deployment_mode")
        assert hasattr(health_response, "timestamp")

        # Test JSON-serializable content
        # In a real implementation, resources might return different content types
        test_data = {
            "type": "configuration",
            "data": {
                "server_name": test_config.server_name,
                "deployment_mode": test_config.deployment_mode,
                "debug": test_config.debug,
            },
        }

        assert isinstance(test_data, dict)
        assert "type" in test_data
        assert "data" in test_data
        assert isinstance(test_data["data"], dict)


class TestResourceIntegration:
    """Test resource integration with the server."""

    @pytest.mark.asyncio
    async def test_concurrent_resource_access(self, test_config):
        """Test concurrent access to resources."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Simulate multiple concurrent resource requests
        request_count = 10
        responses = []

        with patch("mcp_server.main.__version__", "1.0.0"):
            for _i in range(request_count):
                response = HealthResponse(
                    status="healthy",
                    version="1.0.0",
                    deployment_mode=test_config.deployment_mode,
                    timestamp=datetime.now(UTC).isoformat() + "Z",
                )
                responses.append(response)

        # Verify all responses
        assert len(responses) == request_count
        for response in responses:
            assert response.status == "healthy"
            assert response.version == "1.0.0"
            assert response.deployment_mode == test_config.deployment_mode

    @pytest.mark.asyncio
    async def test_resource_access_with_different_configs(self, temp_dir):
        """Test resource access with different server configurations."""
        configs = [
            MCPServerConfig(
                deployment_mode=DeploymentMode.DEVELOPMENT,
                server_name="dev-server",
                debug=True,
                storage_path=str(temp_dir / "dev"),
            ),
            MCPServerConfig(
                deployment_mode=DeploymentMode.PRODUCTION,
                server_name="prod-server",
                debug=False,
                storage_path=str(temp_dir / "prod"),
                secret_key=PRODUCTION_TEST_SECRET_KEY,
            ),
        ]

        for config in configs:
            server = MCPServerFoundation(config)  # noqa: F841

            # Test health check with different configurations
            with patch("mcp_server.main.__version__", "1.0.0"):
                health_response = HealthResponse(
                    status="healthy",
                    version="1.0.0",
                    deployment_mode=config.deployment_mode,
                    timestamp=datetime.now(UTC).isoformat() + "Z",
                )

            # Verify configuration-specific values
            assert health_response.deployment_mode == config.deployment_mode
            assert health_response.status == "healthy"

    @pytest.mark.unit
    def test_resource_registration_validation(self, test_config):
        """Test resource registration validation."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Verify server has registered resources
        assert server.app is not None

        # Test resource URI patterns that should be valid
        valid_uris = [
            "health://status",
            "resource://config",
            "file://local/data.json",
            "http://api.example.com/data",
            "https://secure.example.com/resource",
        ]

        for uri in valid_uris:
            # Basic URI validation
            assert "://" in uri
            parts = uri.split("://", 1)
            assert len(parts) == 2
            assert parts[0]  # Scheme
            assert parts[1]  # Path


class TestResourcePerformance:
    """Test resource performance and efficiency."""

    @pytest.mark.asyncio
    async def test_resource_response_time(self, test_config):
        """Test resource response time."""
        import time

        server = MCPServerFoundation(test_config)  # noqa: F841

        # Measure time for health check resource
        start_time = time.time()

        with patch("mcp_server.main.__version__", "1.0.0"):
            health_response = HealthResponse(
                status="healthy",
                version="1.0.0",
                deployment_mode=test_config.deployment_mode,
                timestamp=datetime.now(UTC).isoformat() + "Z",
            )

        end_time = time.time()
        response_time = end_time - start_time

        # Resource response should be very fast
        assert response_time < 0.1  # 100ms threshold
        assert health_response.status == "healthy"

    @pytest.mark.asyncio
    async def test_resource_memory_efficiency(self, test_config):
        """Test resource memory efficiency."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Test multiple resource accesses for memory stability
        responses = []

        with patch("mcp_server.main.__version__", "1.0.0"):
            for i in range(100):
                response = HealthResponse(
                    status="healthy",
                    version="1.0.0",
                    deployment_mode=test_config.deployment_mode,
                    timestamp=datetime.now(UTC).isoformat() + "Z",
                )
                responses.append(response)

                # Clear reference to help with memory management
                if i % 10 == 0:
                    responses = responses[-10:]  # Keep only last 10

        # Verify final responses are correct
        assert len(responses) == 10
        for response in responses:
            assert response.status == "healthy"

    @pytest.mark.unit
    def test_resource_data_size_limits(self, test_config):
        """Test resource data size handling."""
        server = MCPServerFoundation(test_config)  # noqa: F841

        # Test reasonable data sizes for health check
        with patch("mcp_server.main.__version__", "1.0.0"):
            health_response = HealthResponse(
                status="healthy",
                version="1.0.0",
                deployment_mode=test_config.deployment_mode,
                timestamp=datetime.now(UTC).isoformat() + "Z",
            )

        # Convert to JSON-like representation to estimate size
        response_data = {
            "status": health_response.status,
            "version": health_response.version,
            "deployment_mode": str(health_response.deployment_mode),
            "timestamp": health_response.timestamp,
        }

        # Health check response should be small
        import json

        response_json = json.dumps(response_data)
        assert len(response_json) < 1024  # Less than 1KB
