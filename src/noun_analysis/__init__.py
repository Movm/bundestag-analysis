"""Bundestag Noun Analysis - Analyze word frequency by party using MCP."""

__version__ = "0.1.0"

# Re-export key functions for backwards compatibility
from .parser import parse_speeches_from_protocol
from .speech_aggregation import aggregate_speeches_by_type
from bundestag_mcp import BundestagMCPClient, test_connection

__all__ = [
    "parse_speeches_from_protocol",
    "aggregate_speeches_by_type",
    "BundestagMCPClient",
    "test_connection",
]
