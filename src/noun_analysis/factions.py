"""Faction/party pattern matching and normalization.

Handles the various spellings and OCR errors in historical protocols.

Patterns adapted from Open Discourse project:
https://github.com/open-discourse/open-discourse
"""

import re


FACTION_PATTERNS = {
    "CDU/CSU": r"(?:Gast|-)?(?:\s*C\s*[DSMU]\s*S?[DU]\s*(?:\s*[/,':!.-]?)*\s*(?:\s*C+\s*[DSs]?\s*[UÙ]?\s*)?)(?:-?Hosp\.|-Gast|1)?",
    "SPD": r"\s*'?S(?:PD|DP)(?:\.|-Gast)?",
    "GRÜNE": r"(?:BÜNDNIS\s*(?:90)?/?(?:\s*D[1I]E)?|Bündnis\s*90/(?:\s*D[1I]E)?)?\s*[GC]R[UÜ].?\s*[ÑN]EN?(?:/Bündnis 90)?|BÜNDNISSES?\s*90/\s*DIE\s*GRÜNEN|Grünen",
    "FDP": r"\s*F\.?\s*[PDO][.']?[DP]\.?",
    "AfD": r"^AfD$|Alternative für Deutschland",
    "DIE LINKE": r"DIE\s*LIN\s?KEN?|LIN\s?KEN|Die Linke",
    "BSW": r"^BSW$|Bündnis Sahra Wagenknecht",
    "fraktionslos": r"(?:fraktionslos|Parteilos|parteilos)",
    "SSW": r"^SSW$",
    # Historical parties (for older protocols)
    "PDS": r"(?:Gruppe\s*der\s*)?PDS(?:/(?:LL|Linke Liste))?",
    "GB/BHE": r"(?:GB[/-]\s*)?BHE(?:-DG)?",
    "DP": r"^DP$",
    "KPD": r"^KPD$",
    "FVP": r"^FVP$",
}


def normalize_party(party: str) -> str | None:
    """Normalize party name using regex patterns.

    Uses comprehensive patterns from Open Discourse to handle
    various spellings and OCR errors in historical protocols.
    """
    party = party.strip()

    for normalized, pattern in FACTION_PATTERNS.items():
        if re.search(pattern, party, re.IGNORECASE):
            return normalized

    return None


def extract_parties_from_applause(text: str) -> list[str]:
    """Extract individual party names from applause/heckle text.

    Bundestag protocols contain complex applause annotations like:
    - "(Beifall bei der CDU/CSU sowie bei Abgeordneten der SPD)"
    - "(Beifall bei der AfD und der CDU/CSU)"
    - "(Zuruf des Abg. Dr. Ralf Stegner [SPD])"

    This function parses these and returns normalized party names.

    Args:
        text: The captured applause/heckle text (without parentheses)

    Returns:
        List of normalized party names, e.g. ["CDU/CSU", "SPD"]
    """
    # Strip content after colon (heckle content like "AfD: Oh!")
    text = re.sub(r':\s*[^,)]+', '', text)

    # Split by common separators: "sowie", "und", en-dash, comma
    parts = re.split(r'\s+(?:sowie|und|–|,)\s+', text)

    parties = []
    for part in parts:
        part = part.strip()

        # Try direct normalization first
        party = normalize_party(part)
        if party:
            parties.append(party)
            continue

        # Try extracting from phrases like "bei Abgeordneten der SPD"
        # or "des Abg. Dr. Ralf Stegner [SPD]"
        bracket_match = re.search(r'\[([^\]]+)\]', part)
        if bracket_match:
            party = normalize_party(bracket_match.group(1))
            if party:
                parties.append(party)
                continue

        # Try "der/dem/des PARTY" pattern
        article_match = re.search(r'(?:der|dem|des|bei)\s+(\S+)', part)
        if article_match:
            party = normalize_party(article_match.group(1))
            if party:
                parties.append(party)

    return parties
