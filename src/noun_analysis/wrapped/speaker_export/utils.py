"""Utility functions for speaker export module."""

import re
import unicodedata


def generate_slug(name: str) -> str:
    """Generate URL-safe slug from speaker name.

    Examples:
        "Dr. Paula Piechotta" -> "paula-piechotta"
        "Jens Spahn" -> "jens-spahn"
        "Müller, Hans" -> "hans-mueller"
    """
    # Remove academic titles
    name = re.sub(r'\b(Dr\.|Prof\.|Dr\s|Prof\s)\s*', '', name)
    name = name.strip()

    # Handle "Lastname, Firstname" format
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            name = f"{parts[1].strip()} {parts[0].strip()}"

    # Lowercase
    name = name.lower()

    # Replace German umlauts
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'ae', 'Ö': 'oe', 'Ü': 'ue',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)

    # Normalize unicode and remove accents
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))

    # Replace spaces and special chars with hyphens
    name = re.sub(r'[^a-z0-9]+', '-', name)

    # Clean up multiple hyphens and trim
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')

    return name
