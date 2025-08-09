"""Enterprise MCP Server Foundation.

An enterprise-ready Model Context Protocol server foundation with dual-mode deployment
supporting local development via uvx and cloud-native production environments.
"""

__version__ = "0.1.0"
__author__ = "Peer Jakobsen"
__email__ = "peer.jakobsen@gmail.com"

from .main import create_app, main

__all__ = ["create_app", "main", "__version__"]
