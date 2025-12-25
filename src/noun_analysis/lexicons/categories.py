"""Category definitions and metadata for lexicon analysis.

Contains all Enum classes defining semantic categories and their associated
metadata (names, descriptions, emojis, colors for visualization).
"""

from dataclasses import dataclass
from enum import Enum


class AdjectiveCategory(Enum):
    """Semantic categories for adjectives (Scheme D)."""
    AFFIRMATIVE = "affirmative"   # Positive evaluations
    CRITICAL = "critical"         # Negative evaluations
    AGGRESSIVE = "aggressive"     # Attacks, ridicule, contempt
    LABELING = "labeling"         # Othering, ideological framing


class VerbCategory(Enum):
    """Semantic categories for verbs (Scheme D)."""
    SOLUTION_ORIENTED = "solution"        # Building, improving, solving
    PROBLEM_FOCUSED = "problem"           # Harming, failing, blocking
    COLLABORATIVE = "collaborative"       # Working together, dialogue
    CONFRONTATIONAL = "confrontational"   # Opposing, attacking, accusing
    DEMANDING = "demanding"               # Insisting, requiring
    ACKNOWLEDGING = "acknowledging"       # Praising, thanking, recognizing


class ModalCategory(Enum):
    """Modal verb categories for authority/certainty analysis."""
    OBLIGATION = "obligation"       # müssen, sollen - authoritative
    POSSIBILITY = "possibility"     # können, dürfen - open-minded
    INTENTION = "intention"         # wollen, werden - future-oriented


class TemporalCategory(Enum):
    """Temporal focus categories for past vs future orientation."""
    RETROSPECTIVE = "past"          # Looking back, criticizing past
    PROSPECTIVE = "future"          # Looking forward, proposing


class IntensityCategory(Enum):
    """Emotional intensity categories."""
    INTENSIFIER = "intense"         # Hyperbolic language
    MODERATOR = "moderate"          # Hedging, nuanced language


class PronounCategory(Enum):
    """Pronoun categories for inclusivity analysis."""
    INCLUSIVE = "we"                # wir, uns, gemeinsam
    EXCLUSIVE = "they"              # sie, die, jene


class DiscriminatoryCategory(Enum):
    """Discriminatory/contested terminology categories."""
    XENOPHOBIC = "xenophobic"       # Anti-foreigner framing
    HOMOPHOBIC = "homophobic"       # Anti-LGBTQ+ terminology
    ISLAMOPHOBIC = "islamophobic"   # Anti-Muslim framing
    DOG_WHISTLE = "dog_whistle"     # Coded extremist terms


@dataclass
class CategoryInfo:
    """Metadata about a semantic category."""
    name: str
    description: str
    emoji: str
    color: str  # CSS color for visualization


ADJECTIVE_CATEGORY_INFO: dict[AdjectiveCategory, CategoryInfo] = {
    AdjectiveCategory.AFFIRMATIVE: CategoryInfo(
        name="Zustimmend",
        description="Positive Bewertungen und Lob",
        emoji="✅",
        color="#22c55e"
    ),
    AdjectiveCategory.CRITICAL: CategoryInfo(
        name="Kritisch",
        description="Negative Bewertungen und Tadel",
        emoji="❌",
        color="#ef4444"
    ),
    AdjectiveCategory.AGGRESSIVE: CategoryInfo(
        name="Aggressiv",
        description="Angriffe, Spott, Verachtung",
        emoji="💢",
        color="#f97316"
    ),
    AdjectiveCategory.LABELING: CategoryInfo(
        name="Etikettierend",
        description="Ideologische Zuschreibungen, Othering",
        emoji="🏷️",
        color="#8b5cf6"
    ),
}

VERB_CATEGORY_INFO: dict[VerbCategory, CategoryInfo] = {
    VerbCategory.SOLUTION_ORIENTED: CategoryInfo(
        name="Lösungsorientiert",
        description="Aufbauen, verbessern, ermöglichen",
        emoji="🔧",
        color="#22c55e"
    ),
    VerbCategory.PROBLEM_FOCUSED: CategoryInfo(
        name="Problemfokussiert",
        description="Schaden, scheitern, blockieren",
        emoji="⚠️",
        color="#ef4444"
    ),
    VerbCategory.COLLABORATIVE: CategoryInfo(
        name="Kooperativ",
        description="Zusammenarbeiten, verhandeln, einigen",
        emoji="🤝",
        color="#3b82f6"
    ),
    VerbCategory.CONFRONTATIONAL: CategoryInfo(
        name="Konfrontativ",
        description="Angreifen, vorwerfen, ablehnen",
        emoji="⚔️",
        color="#f97316"
    ),
    VerbCategory.DEMANDING: CategoryInfo(
        name="Fordernd",
        description="Fordern, verlangen, bestehen auf",
        emoji="📢",
        color="#eab308"
    ),
    VerbCategory.ACKNOWLEDGING: CategoryInfo(
        name="Anerkennend",
        description="Loben, danken, würdigen",
        emoji="👏",
        color="#06b6d4"
    ),
}

MODAL_CATEGORY_INFO: dict[ModalCategory, CategoryInfo] = {
    ModalCategory.OBLIGATION: CategoryInfo(
        name="Verpflichtend",
        description="Müssen, sollen - autoritäre Sprache",
        emoji="⚡",
        color="#dc2626"
    ),
    ModalCategory.POSSIBILITY: CategoryInfo(
        name="Möglich",
        description="Können, dürfen - offene Sprache",
        emoji="🌊",
        color="#3b82f6"
    ),
    ModalCategory.INTENTION: CategoryInfo(
        name="Absicht",
        description="Wollen, werden - zukunftsorientiert",
        emoji="🎯",
        color="#8b5cf6"
    ),
}

TEMPORAL_CATEGORY_INFO: dict[TemporalCategory, CategoryInfo] = {
    TemporalCategory.RETROSPECTIVE: CategoryInfo(
        name="Rückblickend",
        description="Vergangenheitsbezogen, kritisierend",
        emoji="⏪",
        color="#6b7280"
    ),
    TemporalCategory.PROSPECTIVE: CategoryInfo(
        name="Zukunftsorientiert",
        description="Vorausschauend, planend",
        emoji="⏩",
        color="#10b981"
    ),
}

INTENSITY_CATEGORY_INFO: dict[IntensityCategory, CategoryInfo] = {
    IntensityCategory.INTENSIFIER: CategoryInfo(
        name="Intensiv",
        description="Verstärkende, hyperbolische Sprache",
        emoji="🔥",
        color="#f97316"
    ),
    IntensityCategory.MODERATOR: CategoryInfo(
        name="Gemäßigt",
        description="Nuancierte, abwägende Sprache",
        emoji="⚖️",
        color="#6b7280"
    ),
}

PRONOUN_CATEGORY_INFO: dict[PronounCategory, CategoryInfo] = {
    PronounCategory.INCLUSIVE: CategoryInfo(
        name="Inklusiv",
        description="Wir-Sprache, gemeinschaftlich",
        emoji="🤗",
        color="#22c55e"
    ),
    PronounCategory.EXCLUSIVE: CategoryInfo(
        name="Exklusiv",
        description="Sie-Sprache, abgrenzend",
        emoji="👉",
        color="#ef4444"
    ),
}

DISCRIMINATORY_CATEGORY_INFO: dict[DiscriminatoryCategory, CategoryInfo] = {
    DiscriminatoryCategory.XENOPHOBIC: CategoryInfo(
        name="Fremdenfeindlich",
        description="Anti-Ausländer Begriffe",
        emoji="🚫",
        color="#991b1b"
    ),
    DiscriminatoryCategory.HOMOPHOBIC: CategoryInfo(
        name="Homophob",
        description="Anti-LGBTQ+ Begriffe",
        emoji="🚫",
        color="#991b1b"
    ),
    DiscriminatoryCategory.ISLAMOPHOBIC: CategoryInfo(
        name="Islamophob",
        description="Anti-muslimische Begriffe",
        emoji="🚫",
        color="#991b1b"
    ),
    DiscriminatoryCategory.DOG_WHISTLE: CategoryInfo(
        name="Codiert",
        description="Verdeckte extremistische Begriffe",
        emoji="🔔",
        color="#7c2d12"
    ),
}
