"""CLI interface for Bundestag word frequency analysis."""

import click

from .commands import analyze, download, wrapped, evaluate


@click.group()
@click.option("--server", default="http://localhost:3000", help="MCP server URL")
@click.pass_context
def main(ctx, server: str):
    """Analyze word frequency by party in Bundestag speeches."""
    ctx.ensure_object(dict)
    ctx.obj["server"] = server


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool):
    """Start the FastAPI analysis server.

    Exposes NLP analysis capabilities via HTTP endpoints for integration
    with the bundestag-mcp server or direct API access.

    Example:
        noun-analysis serve --port 8000
        noun-analysis serve --reload  # Development mode
    """
    import uvicorn

    uvicorn.run(
        "noun_analysis.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


# Register commands from analyze.py
main.add_command(analyze.test)
main.add_command(analyze.analyze)

# Register commands from download.py
main.add_command(download.download_model, name="download-model")
main.add_command(download.download)
main.add_command(download.parse)
main.add_command(download.status)

# Register commands from wrapped.py
main.add_command(wrapped.wrapped)
main.add_command(wrapped.export_web)
main.add_command(wrapped.export_speakers)
main.add_command(wrapped.export_speeches)
main.add_command(wrapped.export_interruptions)
main.add_command(wrapped.export_neutral_texts)
main.add_command(wrapped.export_all)

# Register commands from evaluate.py
main.add_command(evaluate.evaluate_parser)


if __name__ == "__main__":
    main()
