# Bundestag Analysis

Python NLP library for analyzing German Bundestag speeches. Extracts nouns, adjectives, verbs, and performs tone/topic analysis.

## Features

- Speech extraction from Plenarprotokolle (plenary protocols)
- Word frequency analysis using spaCy German NLP
- Tone analysis (aggressive, collaborative, solution-focused)
- Topic classification (migration, climate, economy, etc.)
- FastAPI service for real-time analysis
- CLI tools for batch processing

## Installation

```bash
pip install bundestag-analysis

# Download required spaCy model
python -m spacy download de_core_news_lg
```

## CLI Usage

```bash
# Test MCP server connection
bundestag-analysis test

# Download and analyze protocols
bundestag-analysis download ./data -w 21
bundestag-analysis parse ./data
bundestag-analysis analyze ./data -o ./results

# Export for web app
bundestag-analysis export-all ./data -r ./results -o ./web-output

# Start API service
bundestag-analysis serve --port 8000
```

## API Service

Start the FastAPI server:

```bash
bundestag-analysis serve --port 8000
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analysis/extract-speeches` | POST | Parse protocol text into speeches |
| `/analysis/analyze-text` | POST | Extract words with frequency analysis |
| `/analysis/analyze-tone` | POST | Get tone scores for text |
| `/analysis/classify-topics` | POST | Classify text by political topics |
| `/analysis/speaker-profile` | POST | Comprehensive speaker analysis |
| `/analysis/party-comparison` | POST | Compare parties by tone/topics |
| `/health` | GET | Health check |

## Python API

```python
from noun_analysis.analyzer import WordAnalyzer
from noun_analysis.parser import parse_speeches_from_protocol

# Parse protocol text
speeches = parse_speeches_from_protocol(protocol_text)

# Analyze
analyzer = WordAnalyzer(model="de_core_news_lg")
result = analyzer.analyze_speeches(speeches)

# Access results
print(result.top_nouns(20))
print(result.tone_scores)
print(result.topic_scores)
```

## Docker

```bash
docker build -f Dockerfile.api -t bundestag-analysis .
docker run -p 8000:8000 bundestag-analysis
```

## Related Repositories

- [bundestag-wrapped](https://github.com/movm/bundestag-wrapped) - React visualization app
- [bundestag-mcp](https://github.com/movm/bundestag-mcp) - MCP server for Bundestag data

## Requirements

- Python 3.10+
- spaCy with German model (de_core_news_lg)
- bundestag-mcp server (for fetching protocol data)

## License

MIT
