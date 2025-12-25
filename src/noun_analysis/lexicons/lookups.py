"""Lookup functions for fast word categorization.

Provides efficient category lookups using lazy-initialized reverse lookup tables.
"""

from .categories import (
    AdjectiveCategory,
    VerbCategory,
    ModalCategory,
    TemporalCategory,
    IntensityCategory,
    PronounCategory,
    DiscriminatoryCategory,
)
from .adjectives import ADJECTIVE_LEXICONS
from .verbs import VERB_LEXICONS
from .extended import (
    MODAL_LEXICONS,
    TEMPORAL_LEXICONS,
    INTENSITY_LEXICONS,
    PRONOUN_LEXICONS,
    DISCRIMINATORY_LEXICONS,
)
from .topics import TopicCategory, TOPIC_LEXICONS, TOPIC_MULTI_LABEL
from .multi_label import MULTI_LABEL_TAGS


# =============================================================================
# ADJECTIVE AND VERB LOOKUPS
# =============================================================================

def get_all_categorized_adjectives() -> dict[str, AdjectiveCategory]:
    """Build reverse lookup: word -> category for adjectives."""
    lookup = {}
    for category, words in ADJECTIVE_LEXICONS.items():
        for word in words:
            lookup[word] = category
    return lookup


def get_all_categorized_verbs() -> dict[str, VerbCategory]:
    """Build reverse lookup: word -> category for verbs."""
    lookup = {}
    for category, words in VERB_LEXICONS.items():
        for word in words:
            lookup[word] = category
    return lookup


# Pre-built lookups for performance
_ADJ_LOOKUP: dict[str, AdjectiveCategory] | None = None
_VERB_LOOKUP: dict[str, VerbCategory] | None = None


def categorize_adjective(lemma: str) -> AdjectiveCategory | None:
    """Fast categorization of a single adjective lemma."""
    global _ADJ_LOOKUP
    if _ADJ_LOOKUP is None:
        _ADJ_LOOKUP = get_all_categorized_adjectives()
    return _ADJ_LOOKUP.get(lemma.lower())


def categorize_verb(lemma: str) -> VerbCategory | None:
    """Fast categorization of a single verb lemma."""
    global _VERB_LOOKUP
    if _VERB_LOOKUP is None:
        _VERB_LOOKUP = get_all_categorized_verbs()
    return _VERB_LOOKUP.get(lemma.lower())


# =============================================================================
# EXTENDED CATEGORY LOOKUPS (Scheme E)
# =============================================================================

def get_all_modal_verbs() -> dict[str, ModalCategory]:
    """Build reverse lookup: word -> category for modal verbs."""
    lookup = {}
    for category, words in MODAL_LEXICONS.items():
        for word in words:
            lookup[word] = category
    return lookup


def get_all_temporal_markers() -> dict[str, TemporalCategory]:
    """Build reverse lookup: word -> category for temporal markers."""
    lookup = {}
    for category, words in TEMPORAL_LEXICONS.items():
        for word in words:
            lookup[word] = category
    return lookup


def get_all_intensity_markers() -> dict[str, IntensityCategory]:
    """Build reverse lookup: word -> category for intensity markers."""
    lookup = {}
    for category, words in INTENSITY_LEXICONS.items():
        for word in words:
            lookup[word] = category
    return lookup


def get_all_pronouns() -> dict[str, PronounCategory]:
    """Build reverse lookup: word -> category for pronouns."""
    lookup = {}
    for category, words in PRONOUN_LEXICONS.items():
        for word in words:
            lookup[word] = category
    return lookup


def get_all_discriminatory_terms() -> dict[str, DiscriminatoryCategory]:
    """Build reverse lookup: word -> category for discriminatory terms."""
    lookup = {}
    for category, words in DISCRIMINATORY_LEXICONS.items():
        for word in words:
            lookup[word] = category
    return lookup


# Pre-built lookups for extended categories
_MODAL_LOOKUP: dict[str, ModalCategory] | None = None
_TEMPORAL_LOOKUP: dict[str, TemporalCategory] | None = None
_INTENSITY_LOOKUP: dict[str, IntensityCategory] | None = None
_PRONOUN_LOOKUP: dict[str, PronounCategory] | None = None
_DISCRIMINATORY_LOOKUP: dict[str, DiscriminatoryCategory] | None = None


def categorize_modal(lemma: str) -> ModalCategory | None:
    """Fast categorization of a modal verb lemma."""
    global _MODAL_LOOKUP
    if _MODAL_LOOKUP is None:
        _MODAL_LOOKUP = get_all_modal_verbs()
    return _MODAL_LOOKUP.get(lemma.lower())


def categorize_temporal(lemma: str) -> TemporalCategory | None:
    """Fast categorization of a temporal marker lemma."""
    global _TEMPORAL_LOOKUP
    if _TEMPORAL_LOOKUP is None:
        _TEMPORAL_LOOKUP = get_all_temporal_markers()
    return _TEMPORAL_LOOKUP.get(lemma.lower())


def categorize_intensity(lemma: str) -> IntensityCategory | None:
    """Fast categorization of an intensity marker lemma."""
    global _INTENSITY_LOOKUP
    if _INTENSITY_LOOKUP is None:
        _INTENSITY_LOOKUP = get_all_intensity_markers()
    return _INTENSITY_LOOKUP.get(lemma.lower())


def categorize_pronoun(lemma: str) -> PronounCategory | None:
    """Fast categorization of a pronoun/collective term lemma."""
    global _PRONOUN_LOOKUP
    if _PRONOUN_LOOKUP is None:
        _PRONOUN_LOOKUP = get_all_pronouns()
    return _PRONOUN_LOOKUP.get(lemma.lower())


def categorize_discriminatory(lemma: str) -> DiscriminatoryCategory | None:
    """Fast categorization of a discriminatory term lemma."""
    global _DISCRIMINATORY_LOOKUP
    if _DISCRIMINATORY_LOOKUP is None:
        _DISCRIMINATORY_LOOKUP = get_all_discriminatory_terms()
    return _DISCRIMINATORY_LOOKUP.get(lemma.lower())


def get_multi_label_tags(lemma: str) -> list[tuple[str, float]]:
    """Get all category tags for a word (multi-label support).

    Returns list of (category_name, weight) tuples.
    Returns empty list if word has no multi-label tags.
    """
    return MULTI_LABEL_TAGS.get(lemma.lower(), [])


# =============================================================================
# TOPIC LOOKUPS
# =============================================================================

def get_all_topic_nouns() -> dict[str, TopicCategory]:
    """Build reverse lookup: word -> topic category for single-label nouns."""
    lookup = {}
    for category, words in TOPIC_LEXICONS.items():
        for word in words:
            lookup[word] = category
    return lookup


_TOPIC_LOOKUP: dict[str, TopicCategory] | None = None


def categorize_topic(lemma: str) -> TopicCategory | None:
    """Fast categorization of a noun lemma into a topic.

    For multi-label words, returns the primary (highest-weight) topic.
    Use get_topic_multi_labels() for full multi-label support.
    """
    global _TOPIC_LOOKUP
    lemma_lower = lemma.lower()

    # Check multi-label first, return primary topic
    if lemma_lower in TOPIC_MULTI_LABEL:
        labels = TOPIC_MULTI_LABEL[lemma_lower]
        if labels:
            return max(labels, key=lambda x: x[1])[0]

    # Single-label lookup
    if _TOPIC_LOOKUP is None:
        _TOPIC_LOOKUP = get_all_topic_nouns()
    return _TOPIC_LOOKUP.get(lemma_lower)


def get_topic_multi_labels(lemma: str) -> list[tuple[TopicCategory, float]]:
    """Get all topic labels for a noun with weights.

    Returns list of (TopicCategory, weight) tuples.
    Returns single-item list for single-label words.
    Returns empty list for uncategorized words.
    """
    lemma_lower = lemma.lower()

    # Check multi-label
    if lemma_lower in TOPIC_MULTI_LABEL:
        return TOPIC_MULTI_LABEL[lemma_lower]

    # Single-label lookup
    global _TOPIC_LOOKUP
    if _TOPIC_LOOKUP is None:
        _TOPIC_LOOKUP = get_all_topic_nouns()

    topic = _TOPIC_LOOKUP.get(lemma_lower)
    if topic:
        return [(topic, 1.0)]

    return []
