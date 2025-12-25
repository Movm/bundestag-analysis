"""Multi-label word tags for cross-category analysis.

Words can belong to multiple categories with weights, enabling nuanced
scoring where a word contributes to multiple dimensions.
"""

from dataclasses import dataclass


@dataclass
class WordTag:
    """A category tag with optional weight for a word."""
    category: str
    weight: float = 1.0


# Multi-label mappings: word -> list of (category, weight)
# This allows nuanced scoring where a word contributes to multiple dimensions
MULTI_LABEL_TAGS: dict[str, list[tuple[str, float]]] = {
    # Words that are both aggressive AND problem-focused
    "zerstören": [("problem", 1.0), ("aggressive", 0.7)],
    "vernichten": [("problem", 1.0), ("aggressive", 0.8)],
    "ruinieren": [("problem", 1.0), ("aggressive", 0.6)],

    # Words that are both demanding AND confrontational
    "fordern": [("demanding", 1.0), ("confrontational", 0.3)],
    "verlangen": [("demanding", 1.0), ("confrontational", 0.4)],
    "bestehen": [("demanding", 0.8), ("obligation", 0.5)],

    # Words that are both solution AND collaborative
    "zusammenarbeiten": [("collaborative", 1.0), ("solution", 0.5)],
    "kooperieren": [("collaborative", 1.0), ("solution", 0.4)],

    # Aggressive words that are also labeling
    "ideologisch": [("labeling", 1.0), ("aggressive", 0.3)],
    "radikal": [("labeling", 1.0), ("aggressive", 0.5)],
    "extremistisch": [("labeling", 1.0), ("aggressive", 0.6)],

    # Intensifiers that are also aggressive
    "absurd": [("aggressive", 1.0), ("intense", 0.7)],
    "lächerlich": [("aggressive", 1.0), ("intense", 0.6)],
    "skandalös": [("aggressive", 1.0), ("intense", 0.8)],
    "katastrophal": [("critical", 0.8), ("intense", 1.0)],

    # Modal verbs with temporal overlap
    "wollen": [("intention", 1.0), ("future", 0.6)],
    "werden": [("intention", 0.7), ("future", 1.0)],
    "planen": [("intention", 0.8), ("future", 0.9), ("solution", 0.5)],

    # Discriminatory terms that are also labeling
    "islamisierung": [("islamophobic", 1.0), ("labeling", 0.7), ("xenophobic", 0.5)],
    "genderideologie": [("homophobic", 1.0), ("labeling", 0.8)],
    "bevölkerungsaustausch": [("dog_whistle", 1.0), ("xenophobic", 0.8)],
    "remigration": [("dog_whistle", 1.0), ("xenophobic", 0.7)],
}
