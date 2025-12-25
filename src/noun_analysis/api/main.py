"""FastAPI application for Bundestag speech analysis.

This service exposes NLP analysis capabilities via HTTP endpoints
for integration with the bundestag-mcp server.

Usage:
    uvicorn noun_analysis.api.main:app --host 0.0.0.0 --port 8000

Or via CLI:
    noun-analysis serve --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router, get_analyzer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Pre-load the spaCy model
    logger.info("Loading spaCy model de_core_news_lg...")
    try:
        analyzer = get_analyzer()
        logger.info(
            f"spaCy model loaded successfully. "
            f"Pipeline: {', '.join(analyzer.nlp.pipe_names)}"
        )
    except Exception as e:
        logger.error(f"Failed to load spaCy model: {e}")
        raise

    yield

    # Shutdown: Cleanup if needed
    logger.info("Shutting down analysis service")


app = FastAPI(
    title="Bundestag Analysis API",
    description="""
NLP analysis service for German Bundestag parliamentary speeches.

## Features

- **Speech Extraction**: Parse protocol text into individual speeches
- **Word Analysis**: Extract nouns, adjectives, verbs with lemmatization
- **Tone Analysis**: Communication style scores (aggression, collaboration, etc.)
- **Topic Classification**: Detect political topics (migration, climate, economy...)

## Architecture

This service uses spaCy's `de_core_news_lg` model (610 MB) for German NLP.
The model is loaded once at startup and reused across requests.

## Integration

Designed to be called by the bundestag-mcp server via HTTP.
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router, tags=["Analysis"])


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "bundestag-analysis-api",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
