"""
Tests for Docker build process and container functionality.

This module tests the Docker multi-stage build implementation including:
- Build process for development and production stages
- Security hardening validations
- Health check endpoints
- Multi-platform support
- Image optimization
"""

import subprocess
import time
from pathlib import Path

import pytest
import requests
from testcontainers.compose import DockerCompose
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs


class TestDockerBuild:
    """Test Docker build process for both development and production stages."""

    @pytest.fixture(scope="class")
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture(scope="class")
    def dockerfile_path(self, project_root: Path) -> Path:
        """Get the Dockerfile path."""
        return project_root / "Dockerfile"

    def test_dockerfile_exists(self, dockerfile_path: Path):
        """Test that Dockerfile exists in the project root."""
        assert dockerfile_path.exists(), f"Dockerfile not found at {dockerfile_path}"

    def test_development_stage_build(self, project_root: Path):
        """Test building the development stage of the Docker image."""
        result = subprocess.run(
            [
                "docker",
                "build",
                "--target",
                "development",
                "--tag",
                "mcp-server:dev-test",
                "--build-arg",
                "PYTHON_VERSION=3.13.6",
                ".",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Development build failed: {result.stderr}"

    def test_production_stage_build(self, project_root: Path):
        """Test building the production stage of the Docker image."""
        result = subprocess.run(
            [
                "docker",
                "build",
                "--target",
                "production",
                "--tag",
                "mcp-server:prod-test",
                "--build-arg",
                "PYTHON_VERSION=3.13.6",
                ".",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Production build failed: {result.stderr}"

    def test_multi_platform_build_amd64(self, project_root: Path):
        """Test multi-platform build for AMD64 architecture."""
        result = subprocess.run(
            [
                "docker",
                "build",
                "--platform",
                "linux/amd64",
                "--target",
                "production",
                "--tag",
                "mcp-server:amd64-test",
                ".",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"AMD64 build failed: {result.stderr}"

    def test_multi_platform_build_arm64(self, project_root: Path):
        """Test multi-platform build for ARM64 architecture."""
        result = subprocess.run(
            [
                "docker",
                "build",
                "--platform",
                "linux/arm64",
                "--target",
                "production",
                "--tag",
                "mcp-server:arm64-test",
                ".",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"ARM64 build failed: {result.stderr}"


class TestContainerSecurity:
    """Test container security hardening measures."""

    @pytest.fixture(scope="class")
    def production_container(self) -> DockerContainer:
        """Create and start a production container for testing."""
        container = DockerContainer("mcp-server:prod-test")
        container.with_env("DEPLOYMENT_MODE", "production")
        container.with_env("SECRET_KEY", "test-secret-key")
        container.with_env("DATABASE_URL", "postgresql://test:test@localhost/test")
        container.start()
        yield container
        container.stop()

    def test_non_root_user(self, production_container: DockerContainer):
        """Test that container runs as non-root user (UID 1000)."""
        exit_code, output = production_container.exec("id -u")
        assert output.strip() == "1000", f"Container not running as UID 1000: {output}"

        exit_code, output = production_container.exec("id -g")
        assert output.strip() == "1000", f"Container not running as GID 1000: {output}"

    def test_read_only_filesystem(self, production_container: DockerContainer):
        """Test that root filesystem is read-only in production."""
        # Try to write to root - should fail
        exit_code, output = production_container.exec("touch /test-file")
        assert exit_code != 0, "Root filesystem is writable, should be read-only"

    def test_no_shell_in_distroless(self):
        """Test that production image has no shell (distroless)."""
        # Check that common shells are not available
        result = subprocess.run(
            ["docker", "run", "--rm", "mcp-server:prod-test", "/bin/sh"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Shell found in distroless image"

    def test_image_size_optimization(self):
        """Test that production image size is optimized (<200MB target)."""
        result = subprocess.run(
            [
                "docker",
                "image",
                "inspect",
                "mcp-server:prod-test",
                "--format",
                "{{.Size}}",
            ],
            capture_output=True,
            text=True,
        )
        size_bytes = int(result.stdout.strip())
        size_mb = size_bytes / (1024 * 1024)
        assert size_mb < 200, (
            f"Production image too large: {size_mb:.2f}MB (target: <200MB)"
        )


class TestHealthChecks:
    """Test health check endpoints and graceful shutdown."""

    @pytest.fixture(scope="class")
    def running_container(self) -> DockerContainer:
        """Start a container with health checks enabled."""
        container = DockerContainer("mcp-server:prod-test")
        container.with_env("DEPLOYMENT_MODE", "production")
        container.with_env("SECRET_KEY", "test-secret-key")
        container.with_env("DATABASE_URL", "postgresql://test:test@localhost/test")
        container.with_exposed_ports(8000)
        container.start()

        # Wait for container to be ready
        wait_for_logs(container, "Application startup complete", timeout=30)
        yield container
        container.stop()

    def test_health_endpoint(self, running_container: DockerContainer):
        """Test /health endpoint returns 200 OK."""
        port = running_container.get_exposed_port(8000)
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_readiness_endpoint(self, running_container: DockerContainer):
        """Test /readiness endpoint for deployment readiness."""
        port = running_container.get_exposed_port(8000)
        response = requests.get(f"http://localhost:{port}/readiness", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "database" in data["checks"]
        assert "cache" in data["checks"]

    def test_liveness_endpoint(self, running_container: DockerContainer):
        """Test /liveness endpoint for container health."""
        port = running_container.get_exposed_port(8000)
        response = requests.get(f"http://localhost:{port}/liveness", timeout=5)
        assert response.status_code == 200
        assert response.json()["alive"] is True

    def test_graceful_shutdown(self, running_container: DockerContainer):
        """Test graceful shutdown handling with SIGTERM."""
        # Send SIGTERM signal
        running_container.exec("kill -TERM 1")

        # Check logs for graceful shutdown message
        logs = running_container.get_logs()
        assert "Graceful shutdown initiated" in logs.decode()
        assert "Shutdown complete" in logs.decode()


class TestDockerCompose:
    """Test Docker Compose configuration for local development."""

    @pytest.fixture(scope="class")
    def compose_path(self) -> Path:
        """Get docker-compose.yml path."""
        return Path(__file__).parent.parent / "docker-compose.yml"

    @pytest.fixture(scope="class")
    def compose(self, compose_path: Path) -> DockerCompose:
        """Create Docker Compose environment."""
        compose = DockerCompose(
            filepath=str(compose_path.parent),
            compose_file_name=compose_path.name,
            pull=True,
        )
        compose.start()
        yield compose
        compose.stop()

    def test_compose_file_exists(self, compose_path: Path):
        """Test that docker-compose.yml exists."""
        assert compose_path.exists(), f"docker-compose.yml not found at {compose_path}"

    def test_compose_services_start(self, compose: DockerCompose):
        """Test that all compose services start successfully."""
        # Wait for services to be ready
        time.sleep(10)

        # Check that services are running
        result = subprocess.run(
            ["docker-compose", "ps"],
            cwd=compose.filepath,
            capture_output=True,
            text=True,
        )
        assert "mcp-server" in result.stdout
        assert "postgres" in result.stdout
        assert "redis" in result.stdout

    def test_development_hot_reload(self, compose: DockerCompose):
        """Test hot reload functionality in development mode."""
        # Make a change to a source file
        test_file = Path(compose.filepath) / "src" / "mcp_server" / "test_marker.py"
        test_file.write_text("# Test hot reload")

        # Check that container detects the change
        time.sleep(2)
        logs = compose.get_logs()
        assert "Detected change" in logs.decode() or "Reloading" in logs.decode()

        # Clean up
        test_file.unlink(missing_ok=True)

    def test_volume_mounting(self, compose: DockerCompose):
        """Test that source code is properly volume mounted."""
        # Execute a command to check if source is mounted
        result = subprocess.run(
            ["docker-compose", "exec", "mcp-server", "ls", "/app/src"],
            cwd=compose.filepath,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "mcp_server" in result.stdout


class TestBuildOptimization:
    """Test Docker build optimization and caching strategies."""

    def test_layer_caching(self, project_root: Path):
        """Test that Docker layers are properly cached."""
        # First build
        result1 = subprocess.run(
            ["docker", "build", "--tag", "mcp-server:cache-test", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result1.returncode == 0

        # Second build should use cache
        result2 = subprocess.run(
            ["docker", "build", "--tag", "mcp-server:cache-test2", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result2.returncode == 0
        assert "Using cache" in result2.stdout or "CACHED" in result2.stdout

    def test_dependency_layer_separation(self, dockerfile_path: Path):
        """Test that dependencies are installed before code copy for better caching."""
        content = dockerfile_path.read_text()

        # Check that requirements/dependencies are copied and installed before source code
        req_copy_index = content.find("COPY requirements.txt") or content.find(
            "COPY pyproject.toml"
        )
        src_copy_index = content.find("COPY src/")

        assert req_copy_index < src_copy_index, (
            "Dependencies should be installed before copying source code for better layer caching"
        )

    def test_build_args_usage(self, dockerfile_path: Path):
        """Test that build arguments are properly defined and used."""
        content = dockerfile_path.read_text()

        # Check for important build arguments
        assert "ARG PYTHON_VERSION" in content
        assert "ARG BUILD_DATE" in content
        assert "ARG VCS_REF" in content
        assert "ARG VERSION" in content


class TestProductionReadiness:
    """Test production readiness features."""

    def test_environment_variables_handling(self):
        """Test that container properly handles environment variables."""
        container = DockerContainer("mcp-server:prod-test")
        container.with_env("DEPLOYMENT_MODE", "production")
        container.with_env("DATABASE_URL", "postgresql://user:pass@db:5432/mcpdb")
        container.with_env("REDIS_URL", "redis://redis:6379/0")
        container.with_env("SECRET_KEY", "production-secret-key")
        container.start()

        # Check that environment variables are accessible
        exit_code, output = container.exec("printenv DEPLOYMENT_MODE")
        assert output.strip() == "production"

        container.stop()

    def test_signal_handling(self):
        """Test proper signal handling for graceful shutdown."""
        container = DockerContainer("mcp-server:prod-test")
        container.with_env("DEPLOYMENT_MODE", "production")
        container.with_env("SECRET_KEY", "test-key")
        container.start()

        # Send SIGTERM and check for graceful shutdown
        container.stop(timeout=10)
        logs = container.get_logs()

        # Should handle SIGTERM gracefully
        assert "Forcefully killing" not in logs.decode()

    def test_resource_limits(self, project_root: Path):
        """Test that resource limits can be applied to containers."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--memory",
                "512m",
                "--cpus",
                "1.0",
                "mcp-server:prod-test",
                "echo",
                "Resource limits test",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Container failed with resource limits"
