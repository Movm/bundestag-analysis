"""Protocol parsing and speech extraction.

Single source of truth for parsing Bundestag Plenarprotokolle:
- parse_speeches_from_protocol(): Extract speeches from protocol text

Parsing logic adapted from Open Discourse project:
https://github.com/open-discourse/open-discourse
"""

from .patterns import SPEAKER_PATTERN, PRESIDENT_PATTERN
from .government import government_pattern, get_party_for_official
from .text_utils import clean_text, extract_name_parts, strip_parenthetical_content
from .factions import normalize_party
from .classification import (
    classify_speech_start,
    classify_by_preceding_context,
    find_qa_session_ranges,
    is_in_qa_session,
)

# Re-exports for backwards compatibility
from .speech_aggregation import aggregate_speeches_by_type
from bundestag_mcp import BundestagMCPClient, test_connection

__all__ = [
    "parse_speeches_from_protocol",
    "aggregate_speeches_by_type",
    "BundestagMCPClient",
    "test_connection",
]


def parse_speeches_from_protocol(text: str) -> list[dict]:
    """Parse individual speeches from a Plenarprotokoll full text.

    Returns list of dicts with:
        - speaker: Full speaker name
        - party: Normalized party name
        - text: Speech text (parenthetical content stripped)
        - type: Speech type ('rede', 'befragung', 'fragestunde_antwort', etc.)
        - category: High-level category ('rede' for formal speeches, 'wortbeitrag' for others)
        - words: Word count
        - first_name, last_name, acad_title: Name components
        - is_government: True if speaker is a government official

    Uses both regular speaker lines "Name (Party):" AND president lines
    "Vizepräsident Name:" as speech boundaries to avoid merging procedural
    text into speaker speeches.

    Speech text is cleaned to remove parenthetical content (Zwischenrufe,
    Beifall, etc.) which are not the speaker's own words.

    Automatically detects Q&A sessions (Befragung, Fragestunde) to correctly
    classify government official responses vs formal speeches.

    Parsing logic adapted from Open Discourse project.
    """
    # Clean text first (NBSP, dashes, whitespace normalization)
    text = clean_text(text)

    # Detect Q&A session boundaries for proper classification
    qa_session_ranges = find_qa_session_ranges(text)

    speeches = []

    # Find all boundaries (all types)
    boundaries = []

    # Regular speakers with party: "Name (Party):"
    for m in SPEAKER_PATTERN.finditer(text):
        speaker_name = m.group(1).strip()
        # Skip question headers like "Frage des Abgeordneten X"
        if speaker_name.lower().startswith(('frage ', 'frage\xa0', 'anfrage ')):
            continue
        boundaries.append({
            'start': m.start(),
            'end': m.end(),
            'speaker': speaker_name,
            'party': m.group(2).strip(),
            'is_president': False,
            'is_government': False
        })

    # Presiding officers: "Präsident Name:" - used as boundaries only
    for m in PRESIDENT_PATTERN.finditer(text):
        boundaries.append({
            'start': m.start(),
            'end': m.end(),
            'speaker': f"{m.group(1)} {m.group(2).strip()}",
            'party': None,
            'is_president': True,
            'is_government': False
        })

    # Government officials: "Name, Role:" - substantive speeches, NOT skipped
    for m in government_pattern.finditer(text):
        speaker_name = m.group(1).strip()
        role = m.group(2).strip()
        # Look up party from mapping (tries with and without academic title)
        party = get_party_for_official(speaker_name)
        boundaries.append({
            'start': m.start(),
            'end': m.end(),
            'speaker': speaker_name,
            'party': party,  # May be None if not in mapping
            'is_president': False,
            'is_government': True,
            'role': role
        })

    # Sort by position in text
    boundaries.sort(key=lambda x: x['start'])

    # Extract speech text between boundaries
    for i, boundary in enumerate(boundaries):
        # Skip president speeches - we only use them as boundaries
        if boundary['is_president']:
            continue

        # Text starts after this boundary's header
        text_start = boundary['end']

        # Text ends at start of next boundary (or end of document)
        if i + 1 < len(boundaries):
            text_end = boundaries[i + 1]['start']
        else:
            text_end = len(text)

        speech_text = text[text_start:text_end].strip()

        # Remove parenthetical content (Zwischenrufe, Beifall, etc.)
        speech_text = strip_parenthetical_content(speech_text)

        # Skip very short speeches (under 50 chars likely procedural)
        if len(speech_text) < 50:
            continue

        # Get party: for government officials it's already looked up,
        # for regular speakers we normalize from the parsed party string
        if boundary.get('is_government'):
            party = boundary['party']  # Already looked up from GOVERNMENT_PARTY_MAP
        else:
            party = normalize_party(boundary['party'])

        if party:
            word_count = len(speech_text.split())

            # Check if preceded by president boundary (formally introduced)
            prev_boundary = boundaries[i - 1] if i > 0 else None
            is_president_preceded = prev_boundary and prev_boundary['is_president']

            # Classify based on how speech starts
            start_category = classify_speech_start(speech_text)

            # Check context BEFORE speech for Fragestunde detection
            context_type = classify_by_preceding_context(text, boundary['start'])

            # Check if this speech position is within a Q&A session
            in_qa_session, qa_session_type = is_in_qa_session(boundary['start'], qa_session_ranges)

            # Priority 1: Context-based Fragestunde classification (most reliable)
            if context_type in ('fragestunde', 'fragestunde_antwort'):
                speech_type = context_type
            # Priority 2: Government officials in Q&A sessions
            elif boundary.get('is_government'):
                if in_qa_session:
                    # Government official answering questions in Befragung/Fragestunde
                    speech_type = 'befragung' if qa_session_type == 'befragung' else 'fragestunde_antwort'
                else:
                    # Government official giving formal speech (Regierungserklärung, debate)
                    speech_type = 'rede'
            # Priority 3: Filter out continuations (not new speeches)
            elif start_category == 'continuation':
                continue  # Skip - this is end of interrupted speech, not a new one
            # Priority 4: Content-based classification for formal speeches
            elif is_president_preceded and start_category == 'fragestunde':
                speech_type = 'fragestunde'
            elif is_president_preceded and start_category in ('rede', 'prasidium'):
                speech_type = 'rede'
            elif word_count >= 500:
                # Keep substantial speeches with their category
                speech_type = start_category if start_category != 'other' else 'sonstiges'
            else:
                # Skip non-formal short speeches
                continue

            # Extract name components (Dr., first name, last name)
            name_parts = extract_name_parts(boundary['speaker'])

            speeches.append({
                'speaker': boundary['speaker'],
                'party': party,
                'text': speech_text,
                'type': speech_type,
                'category': 'rede' if speech_type == 'rede' else 'wortbeitrag',
                'words': word_count,
                'first_name': name_parts['first_name'],
                'last_name': name_parts['last_name'],
                'acad_title': name_parts['acad_title'],
                'is_government': boundary.get('is_government', False),
                # Include positions for drama parsing from raw fullText
                'start': text_start,
                'end': text_end,
            })

    return speeches
