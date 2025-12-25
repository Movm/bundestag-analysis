"""Text cleaning and name extraction utilities.

Utilities for cleaning raw protocol text and extracting
name components from speaker names.

Adapted from Open Discourse project:
https://github.com/open-discourse/open-discourse
"""

import re


# Academic titles to extract from names (from Open Discourse)
ACADEMIC_TITLES = [
    "Dr", "Prof", "Frau", "D", "-Ing",
    "von", "und", "zu", "van", "de",
    "Baron", "Freiherr", "Freifrau", "Prinz", "Graf",
    "h", "c",  # for "h.c." (honoris causa)
]


def clean_text(text: str) -> str:
    """Clean raw protocol text (adapted from Open Discourse).

    Normalizes:
    - Non-breaking spaces (U+00A0) → regular spaces
    - Various dash characters → standard hyphen
    - Multiple whitespace → single space
    - Tabs → spaces
    """
    # Replace non-breaking space with regular space
    text = text.replace('\xa0', ' ')

    # Handle other unicode spaces
    text = re.sub(r'[\u00a0\u2007\u202f\u2060]', ' ', text)

    # Normalize dashes (from Open Discourse clean_text)
    text = text.replace('—', '-')  # em dash
    text = text.replace('–', '-')  # en dash

    # Normalize whitespace
    text = re.sub(r'\t+', ' ', text)
    text = re.sub(r'  +', ' ', text)

    return text


def extract_name_parts(name_raw: str) -> dict:
    """Extract name components and academic titles.

    Returns dict with 'first_name', 'last_name', 'acad_title', 'full_name'.
    Adapted from Open Discourse 02_clean_speeches.py.
    """
    # Remove non-alphabetic chars except hyphen, umlauts, and accented chars
    # Keep: Latin letters, German umlauts, common accented chars (é, ğ, ş, ç, ó, ñ, etc.)
    name_clean = re.sub(r"[^a-zA-ZÀ-ÿÖÄÜäöüßğşçıİ\-\s]", " ", name_raw)
    name_clean = re.sub(r"  +", " ", name_clean).strip()

    parts = name_clean.split()

    # Extract academic titles
    titles = [p for p in parts if p in ACADEMIC_TITLES]
    name_parts = [p for p in parts if p not in ACADEMIC_TITLES]

    # Determine first and last name
    if len(name_parts) == 0:
        first_name, last_name = "", ""
    elif len(name_parts) == 1:
        first_name, last_name = "", name_parts[0]
    else:
        first_name = " ".join(name_parts[:-1])
        last_name = name_parts[-1]

    return {
        'first_name': first_name,
        'last_name': last_name,
        'acad_title': " ".join(titles) if titles else None,
        'full_name': name_raw.strip(),
    }


def strip_parenthetical_content(text: str) -> str:
    """Remove parenthetical content from speech text.

    This strips out:
    - Zwischenrufe: (Zuruf von der CDU/CSU: ...)
    - Named interruptions: (Stephan Brandner [AfD]: ...)
    - Applause: (Beifall bei der AfD)
    - Laughter: (Heiterkeit bei der SPD)
    - Other reactions: (Lachen ...), (Widerspruch ...)

    These are NOT the speaker's own words and should not be counted
    in word frequency analysis.
    """
    # Remove all parenthetical content
    # Use non-greedy match to handle nested parens correctly
    cleaned = re.sub(r'\([^)]+\)', '', text)
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()
