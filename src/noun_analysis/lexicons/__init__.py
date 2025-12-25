"""Semantic lexicons for German parliamentary speech analysis.

Scheme D: Communication Style categorization
Focus on HOW things are said, not political content.

Lexicons are organized by word type (adjectives, verbs) and semantic category.
Words are stored as lemmatized forms (lowercase) matching spaCy output.

This package re-exports all public symbols for backward compatibility.
"""

# Categories and metadata
from .categories import (
    CategoryInfo,
    AdjectiveCategory,
    VerbCategory,
    ModalCategory,
    TemporalCategory,
    IntensityCategory,
    PronounCategory,
    DiscriminatoryCategory,
    ADJECTIVE_CATEGORY_INFO,
    VERB_CATEGORY_INFO,
    MODAL_CATEGORY_INFO,
    TEMPORAL_CATEGORY_INFO,
    INTENSITY_CATEGORY_INFO,
    PRONOUN_CATEGORY_INFO,
    DISCRIMINATORY_CATEGORY_INFO,
)

# Core lexicons
from .adjectives import ADJECTIVE_LEXICONS
from .verbs import VERB_LEXICONS

# Extended lexicons (Scheme E)
from .extended import (
    MODAL_LEXICONS,
    TEMPORAL_LEXICONS,
    INTENSITY_LEXICONS,
    PRONOUN_LEXICONS,
    DISCRIMINATORY_LEXICONS,
)

# Topic lexicons (Scheme F)
from .topics import (
    TopicCategory,
    TOPIC_CATEGORY_INFO,
    TOPIC_LEXICONS,
    TOPIC_MULTI_LABEL,
)

# Multi-label support
from .multi_label import WordTag, MULTI_LABEL_TAGS

# Lookup functions
from .lookups import (
    # Adjective/verb lookups
    get_all_categorized_adjectives,
    get_all_categorized_verbs,
    categorize_adjective,
    categorize_verb,
    # Extended category lookups
    get_all_modal_verbs,
    get_all_temporal_markers,
    get_all_intensity_markers,
    get_all_pronouns,
    get_all_discriminatory_terms,
    categorize_modal,
    categorize_temporal,
    categorize_intensity,
    categorize_pronoun,
    categorize_discriminatory,
    get_multi_label_tags,
    # Topic lookups
    get_all_topic_nouns,
    categorize_topic,
    get_topic_multi_labels,
)


__all__ = [
    # Categories
    "CategoryInfo",
    "AdjectiveCategory",
    "VerbCategory",
    "ModalCategory",
    "TemporalCategory",
    "IntensityCategory",
    "PronounCategory",
    "DiscriminatoryCategory",
    "TopicCategory",
    # Category info dicts
    "ADJECTIVE_CATEGORY_INFO",
    "VERB_CATEGORY_INFO",
    "MODAL_CATEGORY_INFO",
    "TEMPORAL_CATEGORY_INFO",
    "INTENSITY_CATEGORY_INFO",
    "PRONOUN_CATEGORY_INFO",
    "DISCRIMINATORY_CATEGORY_INFO",
    "TOPIC_CATEGORY_INFO",
    # Lexicons
    "ADJECTIVE_LEXICONS",
    "VERB_LEXICONS",
    "MODAL_LEXICONS",
    "TEMPORAL_LEXICONS",
    "INTENSITY_LEXICONS",
    "PRONOUN_LEXICONS",
    "DISCRIMINATORY_LEXICONS",
    "TOPIC_LEXICONS",
    "TOPIC_MULTI_LABEL",
    # Multi-label
    "WordTag",
    "MULTI_LABEL_TAGS",
    # Lookup functions
    "get_all_categorized_adjectives",
    "get_all_categorized_verbs",
    "get_all_modal_verbs",
    "get_all_temporal_markers",
    "get_all_intensity_markers",
    "get_all_pronouns",
    "get_all_discriminatory_terms",
    "get_all_topic_nouns",
    "categorize_adjective",
    "categorize_verb",
    "categorize_modal",
    "categorize_temporal",
    "categorize_intensity",
    "categorize_pronoun",
    "categorize_discriminatory",
    "categorize_topic",
    "get_multi_label_tags",
    "get_topic_multi_labels",
]
