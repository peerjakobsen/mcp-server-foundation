"""Test utilities and helper functions for MCP server foundation tests."""

import json
from typing import Any
from uuid import uuid4


class MCPMessageBuilder:
    """Helper class for building MCP protocol messages."""

    @staticmethod
    def create_request(
        method: str,
        params: dict[str, Any] | None = None,
        request_id: str | int | None = None,
    ) -> dict[str, Any]:
        """Create a JSON-RPC 2.0 request message.

        Args:
            method: The method name to call
            params: Optional parameters for the method
            request_id: Optional request ID (auto-generated if not provided)

        Returns:
            JSON-RPC 2.0 request message
        """
        if request_id is None:
            request_id = str(uuid4())

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id,
        }

        if params is not None:
            message["params"] = params

        return message

    @staticmethod
    def create_response(
        result: Any,
        request_id: str | int,
    ) -> dict[str, Any]:
        """Create a JSON-RPC 2.0 success response message.

        Args:
            result: The result data to return
            request_id: The ID from the original request

        Returns:
            JSON-RPC 2.0 response message
        """
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id,
        }

    @staticmethod
    def create_error_response(
        error_code: int,
        error_message: str,
        request_id: str | int | None = None,
        error_data: Any | None = None,
    ) -> dict[str, Any]:
        """Create a JSON-RPC 2.0 error response message.

        Args:
            error_code: JSON-RPC error code
            error_message: Human-readable error message
            request_id: The ID from the original request (None for parse errors)
            error_data: Optional additional error data

        Returns:
            JSON-RPC 2.0 error response message
        """
        error = {
            "code": error_code,
            "message": error_message,
        }

        if error_data is not None:
            error["data"] = error_data

        return {
            "jsonrpc": "2.0",
            "error": error,
            "id": request_id,
        }

    @staticmethod
    def create_notification(
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a JSON-RPC 2.0 notification message.

        Args:
            method: The method name to call
            params: Optional parameters for the method

        Returns:
            JSON-RPC 2.0 notification message
        """
        message = {
            "jsonrpc": "2.0",
            "method": method,
        }

        if params is not None:
            message["params"] = params

        return message

    @staticmethod
    def create_batch_request(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Create a JSON-RPC 2.0 batch request.

        Args:
            requests: List of individual request messages

        Returns:
            JSON-RPC 2.0 batch request
        """
        return requests


class MCPTestData:
    """Helper class for generating test data."""

    @staticmethod
    def get_sample_tool_request() -> dict[str, Any]:
        """Get a sample MCP tool call request."""
        return MCPMessageBuilder.create_request(
            method="tools/call",
            params={
                "name": "echo_message",
                "arguments": {
                    "message": "Hello, MCP!",
                    "include_metadata": True,
                },
            },
        )

    @staticmethod
    def get_sample_tool_response() -> dict[str, Any]:
        """Get a sample MCP tool call response."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "echoed_message": "Hello, MCP!",
                            "server_name": "test-server",
                            "deployment_mode": "development",
                            "timestamp": "2025-08-09T00:00:00Z",
                        }
                    ),
                }
            ],
            "isError": False,
        }

    @staticmethod
    def get_sample_resource_request() -> dict[str, Any]:
        """Get a sample MCP resource request."""
        return MCPMessageBuilder.create_request(
            method="resources/read",
            params={
                "uri": "resource://server-info",
            },
        )

    @staticmethod
    def get_sample_resource_response() -> dict[str, Any]:
        """Get a sample MCP resource response."""
        return {
            "contents": [
                {
                    "uri": "resource://server-info",
                    "mimeType": "application/json",
                    "text": json.dumps(
                        {
                            "name": "MCP Server Foundation",
                            "version": "1.0.0",
                            "capabilities": ["tools", "resources"],
                        }
                    ),
                }
            ],
        }

    @staticmethod
    def get_invalid_messages() -> list[dict[str, Any]]:
        """Get a list of invalid JSON-RPC messages for testing."""
        return [
            # Missing jsonrpc field
            {"method": "test", "id": 1},
            # Wrong jsonrpc version
            {"jsonrpc": "1.0", "method": "test", "id": 1},
            # Missing method field
            {"jsonrpc": "2.0", "id": 1},
            # Invalid method type
            {"jsonrpc": "2.0", "method": 123, "id": 1},
            # Invalid params type
            {"jsonrpc": "2.0", "method": "test", "params": "invalid", "id": 1},
            # Response with both result and error
            {
                "jsonrpc": "2.0",
                "result": "ok",
                "error": {"code": -1, "message": "err"},
                "id": 1,
            },
        ]


class MCPAssertions:
    """Helper class for common MCP test assertions."""

    @staticmethod
    def assert_valid_jsonrpc_request(message: dict[str, Any]) -> None:
        """Assert that a message is a valid JSON-RPC 2.0 request."""
        assert "jsonrpc" in message, "Missing jsonrpc field"
        assert message["jsonrpc"] == "2.0", (
            f"Invalid jsonrpc version: {message['jsonrpc']}"
        )
        assert "method" in message, "Missing method field"
        assert isinstance(message["method"], str), (
            f"Invalid method type: {type(message['method'])}"
        )
        assert "id" in message, "Missing id field for request"

        if "params" in message:
            assert isinstance(message["params"], (dict, list)), (
                f"Invalid params type: {type(message['params'])}"
            )

    @staticmethod
    def assert_valid_jsonrpc_response(message: dict[str, Any]) -> None:
        """Assert that a message is a valid JSON-RPC 2.0 response."""
        assert "jsonrpc" in message, "Missing jsonrpc field"
        assert message["jsonrpc"] == "2.0", (
            f"Invalid jsonrpc version: {message['jsonrpc']}"
        )
        assert "id" in message, "Missing id field for response"

        has_result = "result" in message
        has_error = "error" in message

        assert has_result or has_error, "Response must have either result or error"
        assert not (has_result and has_error), (
            "Response cannot have both result and error"
        )

        if has_error:
            error = message["error"]
            assert isinstance(error, dict), f"Invalid error type: {type(error)}"
            assert "code" in error, "Missing error code"
            assert "message" in error, "Missing error message"
            assert isinstance(error["code"], int), (
                f"Invalid error code type: {type(error['code'])}"
            )
            assert isinstance(error["message"], str), (
                f"Invalid error message type: {type(error['message'])}"
            )

    @staticmethod
    def assert_valid_jsonrpc_notification(message: dict[str, Any]) -> None:
        """Assert that a message is a valid JSON-RPC 2.0 notification."""
        assert "jsonrpc" in message, "Missing jsonrpc field"
        assert message["jsonrpc"] == "2.0", (
            f"Invalid jsonrpc version: {message['jsonrpc']}"
        )
        assert "method" in message, "Missing method field"
        assert isinstance(message["method"], str), (
            f"Invalid method type: {type(message['method'])}"
        )
        assert "id" not in message, "Notification must not have id field"

        if "params" in message:
            assert isinstance(message["params"], (dict, list)), (
                f"Invalid params type: {type(message['params'])}"
            )

    @staticmethod
    def assert_mcp_tool_response(response: dict[str, Any]) -> None:
        """Assert that a response is a valid MCP tool call response."""
        assert "content" in response, "Missing content field"
        assert isinstance(response["content"], list), (
            f"Invalid content type: {type(response['content'])}"
        )

        for content_item in response["content"]:
            assert isinstance(content_item, dict), (
                f"Invalid content item type: {type(content_item)}"
            )
            assert "type" in content_item, "Missing type field in content item"
            assert "text" in content_item, "Missing text field in content item"

        if "isError" in response:
            assert isinstance(response["isError"], bool), (
                f"Invalid isError type: {type(response['isError'])}"
            )

    @staticmethod
    def assert_mcp_resource_response(response: dict[str, Any]) -> None:
        """Assert that a response is a valid MCP resource response."""
        assert "contents" in response, "Missing contents field"
        assert isinstance(response["contents"], list), (
            f"Invalid contents type: {type(response['contents'])}"
        )

        for content_item in response["contents"]:
            assert isinstance(content_item, dict), (
                f"Invalid content item type: {type(content_item)}"
            )
            assert "uri" in content_item, "Missing uri field in content item"
            assert "mimeType" in content_item, "Missing mimeType field in content item"

            # Must have either text or blob content
            has_text = "text" in content_item
            has_blob = "blob" in content_item
            assert has_text or has_blob, "Content item must have either text or blob"
            assert not (has_text and has_blob), (
                "Content item cannot have both text and blob"
            )


def create_mock_server_response(
    status_code: int = 200,
    content: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Create a mock HTTP server response for testing.

    Args:
        status_code: HTTP status code
        content: Response body content
        headers: HTTP response headers

    Returns:
        Mock response data
    """
    if content is None:
        content = {"status": "ok"}

    if headers is None:
        headers = {"Content-Type": "application/json"}

    return {
        "status_code": status_code,
        "content": content,
        "headers": headers,
    }


def generate_test_session_id() -> str:
    """Generate a unique session ID for testing."""
    return f"test-session-{uuid4()}"


def create_test_auth_headers(api_key: str = "test-api-key") -> dict[str, str]:
    """Create test authentication headers."""
    return {
        "X-MCP-API-Key": api_key,
        "Content-Type": "application/json",
    }
