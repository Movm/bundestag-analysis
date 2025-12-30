# Bundestag Analysis

Python NLP library for analyzing German Bundestag speeches. Extracts nouns, adjectives, verbs, and performs tone/topic analysis.

## Features

- Speech extraction from Plenarprotokolle (plenary protocols)
- Word frequency analysis using spaCy German NLP
- Tone analysis (aggressive, collaborative, solution-focused)
- Topic classification (migration, climate, economy, etc.)
- Gender and coalition/opposition analysis
- FastAPI services:
  - **NLP API** - Real-time text analysis (requires spaCy)
  - **Wrapped API** - Pre-computed speaker/party data (lightweight)
- CLI tools for batch processing
- Export to JSON for web visualization

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

# Find who uses a specific word most often
bundestag-analysis word-rank ukraine --top 20
bundestag-analysis word-rank klimaschutz --formal-only

# Start NLP analysis API (requires spaCy model)
bundestag-analysis serve --port 8000

# Start Wrapped API (serves pre-computed data, no spaCy required)
bundestag-analysis serve-wrapped --port 8001 --data-dir ./web-output
```

### Export Commands

Generate JSON files for web apps, research, and transparency:

| Command | Description |
|---------|-------------|
| `export-all` | Batch export all files at once (recommended) |
| `export-web` | Export wrapped.json for web app |
| `export-speakers` | Export individual speaker profile JSON files |
| `export-speeches` | Export searchable speech database |
| `export-interruptions` | Export interruption rankings (Zwischenrufer) |
| `export-neutral-texts` | Export neutral interjections for analysis |
| `export-raw` | Export pure JSON for research/transparency |

**Recommended workflow:**

```bash
# Generate all web app files at once (faster - loads data once)
bundestag-analysis export-all ./data -r ./results -o ./web-output

# Skip the large speech database (~17MB) if not needed
bundestag-analysis export-all ./data -r ./results -o ./web-output --skip-speeches
```

**Research/Transparency export:**

```bash
# Export raw data for documentation or research
bundestag-analysis export-raw ./data -r ./results -o ./exports

# Creates versioned directory (./exports/v1.0.0/) with:
# - reden.json         (formal speeches with full text)
# - wortbeitraege.json (all contributions)
# - zwischenrufe.json  (interjections with sentiment)
# - sprecher.json      (speaker profiles)
# - parteien.json      (party statistics)
# - ton.json           (tone analysis)
# - gender.json        (gender analysis)
# - themen.json        (topic analysis)
# - manifest.json      (metadata + SHA-256 checksums)

# Files are gzipped by default; use --no-compress to disable
```

## API Services

### NLP Analysis API (Port 8000)

Real-time NLP analysis using spaCy. Requires the German language model.

```bash
bundestag-analysis serve --port 8000
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/extract/speeches` | POST | Parse protocol text into speeches |
| `/analyze/text` | POST | Extract words with frequency analysis |
| `/analyze/tone` | POST | Get tone scores for text |
| `/analyze/topics` | POST | Classify text by political topics |
| `/health` | GET | Health check |

### Wrapped API (Port 8001)

Serves pre-computed speaker/party data for [bundestag-wrapped.de](https://bundestag-wrapped.de). Fast responses, no spaCy required.

```bash
# First generate the data
bundestag-analysis export-all ./data -r ./results -o ./web-output

# Then serve it
bundestag-analysis serve-wrapped --port 8001
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/speakers` | GET | List speakers with filtering (`?party=`, `?search=`, `?limit=`) |
| `/speakers/{slug}` | GET | Complete speaker profile (signature words, tone, topics, rankings) |
| `/parties` | GET | Party statistics and signature words |
| `/analytics/gender` | GET | Gender distribution, top speakers by gender |
| `/analytics/coalition` | GET | Coalition vs opposition comparison |
| `/analytics/overview` | GET | Metadata and summary statistics |
| `/analytics/cross-party` | GET | Cross-party interruption matrix (who interrupts whom) |
| `/analytics/compare` | GET | Compare parties on topics, tone, words (`?parties=AfD,GRÜNE`) |
| `/health` | GET | Data load status |

#### Example Usage

```bash
# List SPD speakers
curl "http://localhost:8001/speakers?party=SPD&limit=10"

# Get specific speaker
curl "http://localhost:8001/speakers/friedrich-merz"

# Get gender analysis
curl "http://localhost:8001/analytics/gender"

# Get coalition vs opposition stats
curl "http://localhost:8001/analytics/coalition"

# Cross-party interruptions (who interrupts whom)
curl "http://localhost:8001/analytics/cross-party"

# Compare parties on topics, tone, signature words
curl "http://localhost:8001/analytics/compare?parties=AfD,GRÜNE,DIE%20LINKE"
```

#### Cross-Party Analysis

The `/analytics/cross-party` endpoint returns:
- **matrix**: `{from_party: {to_party: count}}` - Full interruption matrix
- **topRelationships**: Top 20 cross-party interruption pairs
- **byParty**: Per-party totals (interrupting and interrupted)

#### Party Comparison

The `/analytics/compare` endpoint compares 2+ parties and returns:
- **topics**: All 13 policy topics with scores per party
- **signatureWords**: Distinctive vocabulary for each party
- **tone**: 8 tone metrics (aggression, collaboration, etc.)
- **topDifferences**: Topics where parties differ most

#### Speaker Data Includes

- Speech statistics (formal speeches, Wortbeiträge, Befragung responses)
- Rankings (global and per-party)
- Signature words (distinctive vocabulary vs Bundestag/party average)
- Tone profile (aggression, collaboration, solution focus)
- Topic scores (migration, climate, economy, etc.)
- Spirit animal personality assignment
- Coalition membership flag (`isCoalition: true/false`)

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
# NLP Analysis API (with spaCy model, ~2GB image)
docker build -f Dockerfile.api -t bundestag-analysis .
docker run -p 8000:8000 bundestag-analysis

# Wrapped API (lightweight, serves pre-computed data)
docker run -p 8001:8001 -v ./web-output:/data bundestag-analysis \
  bundestag-analysis serve-wrapped --data-dir /data
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
