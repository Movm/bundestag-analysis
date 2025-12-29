"""Type definitions and constants for wrapped analysis."""

from dataclasses import dataclass, field
from typing import Literal
import re

# Gender type for type hints
Gender = Literal["male", "female", "unknown"]

# Regex patterns for parsing parliamentary annotations
# Note: Party group includes digits for "BÜNDNIS 90/DIE GRÜNEN"
INTERRUPTER_PATTERN = re.compile(
    r'\(([A-ZÄÖÜ][^\[\]]{2,40})\s*\[([A-ZÄÖÜa-zäöü0-9/\s-]+)\]:[^)]+\)'
)
APPLAUSE_PATTERN = re.compile(
    r'\(Beifall bei (?:der |dem )?([^)]+)\)'
)
HECKLE_PATTERN = re.compile(
    r'\(Zurufe? (?:von der |vom |der )?([^)]+)\)'
)

# Party color mappings for Rich console output
PARTY_COLORS = {
    "SPD": "red",
    "CDU/CSU": "bright_black",
    "GRÜNE": "green",
    "AfD": "blue",
    "fraktionslos": "white",
    "FDP": "yellow",
    "DIE LINKE": "magenta",
    "BSW": "cyan",
}

PARTY_EMOJI = {
    "SPD": ":red_circle:",
    "CDU/CSU": ":black_circle:",
    "GRÜNE": ":green_circle:",
    "AfD": ":blue_circle:",
    "fraktionslos": ":white_circle:",
}


def normalize_name_for_comparison(name: str) -> str:
    """Extract lastname for self-interruption detection."""
    cleaned = name.replace("Dr.", "").replace("Prof.", "").strip()
    parts = cleaned.split()
    return parts[-1].lower() if parts else ""


@dataclass
class SpeakerProfile:
    """Comprehensive profile for a single speaker with aggregated statistics."""

    name: str
    first_name: str
    last_name: str
    party: str
    gender: Gender
    acad_title: str | None
    total_speeches: int = 0
    total_words: int = 0
    formal_speeches: int = 0  # category='rede' (formal podium speeches)
    wortbeitraege: int = 0  # category='wortbeitrag' (questions, interventions, etc.)
    befragung_responses: int = 0  # Government Q&A answers (Befragung/Regierungsbefragung)
    question_speeches: int = 0
    avg_words_per_speech: float = 0.0
    interruptions_made: int = 0
    interruptions_received: int = 0


@dataclass
class GenderPartyStats:
    """Gender statistics for a single party."""

    total_speakers: int = 0
    male_speakers: int = 0
    female_speakers: int = 0
    unknown_speakers: int = 0
    male_speeches: int = 0
    female_speeches: int = 0
    unknown_speeches: int = 0
    male_words: int = 0
    female_words: int = 0
    unknown_words: int = 0
    male_avg_speech_length: float = 0.0
    female_avg_speech_length: float = 0.0
    unknown_avg_speech_length: float = 0.0
    male_interruptions_made: int = 0
    female_interruptions_made: int = 0
    male_interruptions_received: int = 0
    female_interruptions_received: int = 0
    male_dr_count: int = 0
    female_dr_count: int = 0


@dataclass
class GenderStats:
    """Overall gender statistics container."""

    total_male_speakers: int = 0
    total_female_speakers: int = 0
    total_unknown_speakers: int = 0
    by_party: dict[str, GenderPartyStats] = field(default_factory=dict)


@dataclass
class WrappedDataBase:
    """Container for all wrapped analysis data (fields only)."""

    metadata: dict
    party_stats: dict
    top_words: dict
    speaker_stats: dict = field(default_factory=dict)
    befragung_speaker_stats: dict = field(default_factory=dict)  # Government Q&A responses
    question_speaker_stats: dict = field(default_factory=dict)
    word_frequencies: dict = field(default_factory=dict)
    drama_stats: dict = field(default_factory=dict)
    all_speeches: list = field(default_factory=list)
    speeches_by_party: dict = field(default_factory=dict)
    tone_data: dict = field(default_factory=dict)
    category_data: dict = field(default_factory=dict)
    # Gender and speaker analysis fields
    gender_stats: GenderStats | None = None
    speaker_profiles: dict[str, SpeakerProfile] = field(default_factory=dict)
