"""Bundestag MCP client for interacting with bundestag-mcp server."""

from .client import BundestagMCPClient, test_connection

__all__ = ["BundestagMCPClient", "test_connection"]
