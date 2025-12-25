"""Party category classification based on tone analysis.

Two-dimension model (Politolinguistik):
- TONALITÄT (Tone): Adjectives/verbs measure evaluative style (HOW things are said)
- FRAMING (Schlagwörter): Nouns measure conceptual framing (WHAT terms are invoked)

These are separate dimensions - parties are ranked only on Tonalität categories.
Framing (discriminatory) is shown separately, not competing in the ranking.
"""

from dataclasses import dataclass
from typing import Callable

from ..categorizer import ToneScores


@dataclass
class TraitCategory:
    """A tone analysis category."""

    id: str           # Unique identifier (matches score field name)
    name: str         # Display name (German)
    emoji: str        # Representative emoji
    description: str  # Short description


# =============================================================================
# TONALITÄT CATEGORIES (Scheme D) - Adjective/Verb based
# These compete in party rankings
# =============================================================================
TONE_CATEGORIES: dict[str, TraitCategory] = {
    "aggression": TraitCategory(
        id="aggression",
        name="Aggressiv",
        emoji="😤",
        description="Höchster Aggressionsindex (Adjektive)",
    ),
    "demand_intensity": TraitCategory(
        id="demand_intensity",
        name="Fordernd",
        emoji="💪",
        description="Höchste Forderungsintensität (Verben)",
    ),
    "collaboration": TraitCategory(
        id="collaboration",
        name="Kooperativ",
        emoji="🤝",
        description="Höchster Kooperationswert (Verben)",
    ),
    "solution_focus": TraitCategory(
        id="solution_focus",
        name="Lösungsorientiert",
        emoji="🔧",
        description="Höchste Lösungsorientierung (Verben)",
    ),
    "affirmative": TraitCategory(
        id="affirmative",
        name="Positiv",
        emoji="😊",
        description="Höchster Positivitätswert (Adjektive)",
    ),
}

# =============================================================================
# PARTY-SPECIFIC EMOJIS
# Based on overall tone profile, not category
# =============================================================================
PARTY_EMOJIS: dict[str, str] = {
    "CDU/CSU": "🏛️",   # Government (has chancellor)
    "SPD": "🛠️",       # Solution-focused, cooperative
    "GRÜNE": "⚖️",     # Balanced, middle-ground
    "AfD": "😤",       # Aggressive, confrontational
    "DIE LINKE": "✊",  # Demanding, pushing hard
}

# =============================================================================
# FRAMING CATEGORIES (Scheme E) - Noun/Schlagwörter based
# These are shown separately, NOT competing in party rankings
# =============================================================================
FRAMING_CATEGORIES: dict[str, TraitCategory] = {
    "discriminatory": TraitCategory(
        id="discriminatory",
        name="Ausgrenzend",
        emoji="⛔",
        description="Ausgrenzende Schlagwörter (Substantive)",
    ),
}

# Combined for backwards compatibility and display
TRAIT_CATEGORIES: dict[str, TraitCategory] = {
    **TONE_CATEGORIES,
    **FRAMING_CATEGORIES,
}

# Fallback when no clear category
DEFAULT_CATEGORY = TraitCategory(
    id="balanced",
    name="Ausgewogen",
    emoji="⚖️",
    description="Ausgewogenes Kommunikationsprofil",
)


def _get_score_accessor(category_id: str) -> Callable[[ToneScores], float]:
    """Get the score accessor function for a category."""
    accessors = {
        "aggression": lambda s: s.aggression_index,
        "discriminatory": lambda s: s.discriminatory_index,
        "demand_intensity": lambda s: s.demand_intensity,
        "collaboration": lambda s: s.collaboration_score,
        "solution_focus": lambda s: s.solution_focus,
        "affirmative": lambda s: s.affirmative_score,
        "inclusivity": lambda s: s.inclusivity_index,
    }
    return accessors.get(category_id, lambda s: 0.0)


def compute_party_rankings(
    all_party_scores: dict[str, ToneScores],
    categories: dict[str, TraitCategory] | None = None,
) -> dict[str, dict[str, tuple[int, float]]]:
    """Compute rankings for all parties across specified categories.

    Args:
        all_party_scores: Dict mapping party name to ToneScores
        categories: Categories to rank on (default: TONE_CATEGORIES only)

    Returns:
        Dict mapping party -> category -> (rank, score)
        Where rank is 1-based (1 = highest score)
    """
    # Only rank on Tonalität categories by default (not Framing)
    if categories is None:
        categories = TONE_CATEGORIES

    rankings: dict[str, dict[str, tuple[int, float]]] = {
        party: {} for party in all_party_scores
    }

    for cat_id in categories:
        score_fn = _get_score_accessor(cat_id)

        # Get all parties' scores for this category
        party_scores = [
            (party, score_fn(scores))
            for party, scores in all_party_scores.items()
        ]

        # Sort by score descending (highest = rank 1)
        party_scores.sort(key=lambda x: x[1], reverse=True)

        # Assign ranks
        for rank, (party, score) in enumerate(party_scores, start=1):
            rankings[party][cat_id] = (rank, score)

    return rankings


def classify_party_by_rank(
    party: str,
    all_party_scores: dict[str, ToneScores]
) -> tuple[TraitCategory, int, float]:
    """Classify a party based on which TONE category they rank #1 in.

    Note: Only uses Tonalität categories (adjective/verb-based).
    Framing categories (discriminatory/noun-based) are separate.

    Args:
        party: Party name to classify
        all_party_scores: All parties' ToneScores for comparison

    Returns:
        Tuple of (category, rank, score) for the party's best TONE category
    """
    # Only rank on Tonalität categories (not Framing)
    rankings = compute_party_rankings(all_party_scores, TONE_CATEGORIES)
    party_rankings = rankings.get(party, {})

    if not party_rankings:
        return DEFAULT_CATEGORY, 0, 0.0

    # Find category where this party has the best rank
    # Tie-breaker: higher absolute score
    best_cat_id = min(
        party_rankings.keys(),
        key=lambda c: (party_rankings[c][0], -party_rankings[c][1])
    )

    rank, score = party_rankings[best_cat_id]
    category = TONE_CATEGORIES.get(best_cat_id, DEFAULT_CATEGORY)

    return category, rank, score


def get_party_traits(
    party: str,
    scores: ToneScores,
    all_party_scores: dict[str, ToneScores],
    top_n: int = 3,
) -> list[str]:
    """Get the top N distinguishing traits for a party.

    Only includes traits where the party ranks #1 or #2.
    Uses relative rankings, not absolute deviation from midpoint.
    """
    # Start with core tone categories
    all_categories = dict(TONE_CATEGORIES)

    # Only include inclusivity if there's meaningful variance (not all defaults)
    inclusivity_scores = [s.inclusivity_index for s in all_party_scores.values()]
    if len(set(inclusivity_scores)) > 1:  # Not all the same value
        all_categories["inclusivity"] = TraitCategory(
            id="inclusivity",
            name="Inklusiv",
            emoji="🤗",
            description="Höchste Inklusivität (Pronomen)",
        )

    # Compute rankings across all parties
    rankings = compute_party_rankings(all_party_scores, all_categories)
    party_rankings = rankings.get(party, {})
    n_parties = len(all_party_scores)

    # Collect traits where this party ranks in top 2
    winning_traits = []
    for cat_id, (rank, score) in party_rankings.items():
        if rank <= 2:  # Only top 2 ranks
            category = all_categories.get(cat_id)
            if category:
                # Higher rank difference from middle = more distinguishing
                extremity = (n_parties + 1) / 2 - rank
                winning_traits.append((category.name, extremity, rank))

    # Sort by extremity (most extreme first), then by rank
    winning_traits.sort(key=lambda x: (-x[1], x[2]))
    return [name for name, _, _ in winning_traits[:top_n]]


@dataclass
class PartyProfile:
    """Complete profile for a political party."""

    party: str
    category: TraitCategory
    rank: int           # 1 = highest in this category
    score: float        # Raw score value
    total_parties: int  # Total number of parties compared
    traits: list[str]   # Top distinguishing traits
    scores: ToneScores

    def to_dict(self) -> dict:
        """Export to dictionary for JSON serialization."""
        # Use party-specific emoji, fallback to category emoji
        emoji = PARTY_EMOJIS.get(self.party, self.category.emoji)
        return {
            "party": self.party,
            "category": self.category.id,
            "categoryName": self.category.name,
            "emoji": emoji,
            "description": self.category.description,
            "rank": self.rank,
            "totalParties": self.total_parties,
            "score": round(self.score, 2),
            "traits": self.traits,
            "scores": self.scores.to_dict(),
        }


def build_party_profile(
    party: str,
    scores: ToneScores,
    all_party_scores: dict[str, ToneScores]
) -> PartyProfile:
    """Build a complete party profile from tone scores.

    Args:
        party: Party name
        scores: ToneScores for this party
        all_party_scores: All parties' scores for ranking comparison

    Returns:
        Complete PartyProfile with category, rank, and traits
    """
    category, rank, score = classify_party_by_rank(party, all_party_scores)
    traits = get_party_traits(party, scores, all_party_scores, top_n=3)

    return PartyProfile(
        party=party,
        category=category,
        rank=rank,
        score=score,
        total_parties=len(all_party_scores),
        traits=traits,
        scores=scores,
    )


# Legacy aliases for backwards compatibility
PartyArchetype = TraitCategory
TRAIT_ARCHETYPES = TRAIT_CATEGORIES
DEFAULT_ARCHETYPE = DEFAULT_CATEGORY


def classify_party(scores: ToneScores) -> TraitCategory:
    """Legacy function - classifies based on single party's scores only.

    For accurate ranking, use classify_party_by_rank() with all party scores.
    """
    # Fallback: use highest absolute score
    score_map = {
        "aggression": scores.aggression_index,
        "discriminatory": scores.discriminatory_index,
        "demand_intensity": scores.demand_intensity,
        "collaboration": scores.collaboration_score,
        "solution_focus": scores.solution_focus,
        "affirmative": scores.affirmative_score,
    }

    # For index scores, higher is more notable
    # For percentage scores, deviation from 50 is more notable
    weighted = {
        "aggression": score_map["aggression"] * 3,  # Weight index scores higher
        "discriminatory": score_map["discriminatory"] * 5,  # Weight discriminatory highest
        "demand_intensity": score_map["demand_intensity"] * 3,
        "collaboration": abs(score_map["collaboration"] - 50),
        "solution_focus": abs(score_map["solution_focus"] - 50),
        "affirmative": abs(score_map["affirmative"] - 50),
    }

    best_cat = max(weighted, key=lambda k: weighted[k])
    return TRAIT_CATEGORIES.get(best_cat, DEFAULT_CATEGORY)
