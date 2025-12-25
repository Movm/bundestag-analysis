"""Q&A session detection for Bundestag protocols.

Detects parliamentary Q&A sessions (Befragung, Fragestunde) where
government officials answer questions from MPs.
"""

import re


# Patterns to detect Q&A session start
QA_SESSION_START_PATTERNS = [
    (re.compile(r'Befragung der Bundesregierung', re.IGNORECASE), 'befragung'),
    (re.compile(r'Regierungsbefragung', re.IGNORECASE), 'befragung'),
]

# Fragestunde is handled separately (it's for all MPs, not just government)
FRAGESTUNDE_START_PATTERN = re.compile(r'(?:^|\n)Fragestunde\s*(?:\n|$)', re.MULTILINE)

# End patterns for Q&A sessions
QA_SESSION_END_PATTERN = re.compile(
    r'(?:schließe ich die|beende ich die|Ende der)\s+'
    r'(?:Befragung|Fragestunde|Regierungsbefragung)',
    re.IGNORECASE
)


def find_qa_session_ranges(full_text: str) -> list[tuple[int, int, str]]:
    """Find (start_pos, end_pos, session_type) for Q&A sessions in protocol text.

    Detects:
    - 'befragung': Befragung der Bundesregierung / Regierungsbefragung
    - 'fragestunde': Fragestunde (general question time)

    Returns:
        List of (start_position, end_position, session_type) tuples
    """
    ranges = []

    # Find Befragung/Regierungsbefragung sessions
    for pattern, session_type in QA_SESSION_START_PATTERNS:
        for start_match in pattern.finditer(full_text):
            start_pos = start_match.start()
            # Find the next session end marker after this start
            end_match = QA_SESSION_END_PATTERN.search(full_text, start_pos + 1)
            if end_match:
                end_pos = end_match.end()
            else:
                # If no explicit end, assume session goes to end of protocol
                end_pos = len(full_text)
            ranges.append((start_pos, end_pos, session_type))

    # Find Fragestunde sessions
    for start_match in FRAGESTUNDE_START_PATTERN.finditer(full_text):
        start_pos = start_match.start()
        # Find the next session end marker after this start
        end_match = QA_SESSION_END_PATTERN.search(full_text, start_pos + 1)
        if end_match:
            end_pos = end_match.end()
        else:
            end_pos = len(full_text)
        ranges.append((start_pos, end_pos, 'fragestunde'))

    # Sort by start position and remove overlapping ranges
    ranges.sort(key=lambda x: x[0])

    return ranges


def is_in_qa_session(position: int, qa_ranges: list[tuple[int, int, str]]) -> tuple[bool, str | None]:
    """Check if a position in text falls within a Q&A session.

    Returns:
        (is_in_session, session_type) - session_type is 'befragung', 'fragestunde', or None
    """
    for start, end, session_type in qa_ranges:
        if start <= position < end:
            return True, session_type
    return False, None
