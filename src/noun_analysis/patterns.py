"""Shared regex patterns for protocol parsing."""
import re

# Pattern for regular speakers: "Name (Party):"
SPEAKER_PATTERN = re.compile(r'\n([A-ZÄÖÜ][^(\n:]{2,60})\s*\(([^)]+)\):\s*\n')

# Pattern for presiding officers (no party affiliation) - used as boundaries only
# Includes: Präsident(in), Vizepräsident(in), Alterspräsident(in), Bundespräsident(in)
PRESIDENT_PATTERN = re.compile(
    r'\n(Vizepräsident(?:in)?|Präsident(?:in)?|Alterspräsident(?:in)?|'
    r'Bundespräsident(?:in)?)\s+'
    r'([A-ZÄÖÜ][^:\n]{2,40}):\s*\n'
)
