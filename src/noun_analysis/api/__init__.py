"""FastAPI service for Bundestag speech analysis.

Exposes NLP analysis capabilities via HTTP endpoints for integration
with the bundestag-mcp server.
"""

from .main import app

__all__ = ["app"]
