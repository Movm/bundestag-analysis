"""Word categorization engine for semantic analysis.

Scheme D: Communication Style categorization
Scheme E: Extended categories (Modal, Temporal, Intensity, Pronoun, Discriminatory)
"""

from collections import Counter
from dataclasses import dataclass, field

from .lexicons import (
    AdjectiveCategory,
    VerbCategory,
    ModalCategory,
    TemporalCategory,
    IntensityCategory,
    PronounCategory,
    DiscriminatoryCategory,
    TopicCategory,
    categorize_adjective,
    categorize_verb,
    categorize_modal,
    categorize_temporal,
    categorize_intensity,
    categorize_pronoun,
    categorize_discriminatory,
    get_multi_label_tags,
    get_topic_multi_labels,
)


@dataclass
class CategoryCounts:
    """Counts of words in each semantic category (Scheme D + E)."""

    # Adjective categories (Scheme D)
    adj_affirmative: Counter = field(default_factory=Counter)
    adj_critical: Counter = field(default_factory=Counter)
    adj_aggressive: Counter = field(default_factory=Counter)
    adj_labeling: Counter = field(default_factory=Counter)

    # Verb categories (Scheme D)
    verb_solution: Counter = field(default_factory=Counter)
    verb_problem: Counter = field(default_factory=Counter)
    verb_collaborative: Counter = field(default_factory=Counter)
    verb_confrontational: Counter = field(default_factory=Counter)
    verb_demanding: Counter = field(default_factory=Counter)
    verb_acknowledging: Counter = field(default_factory=Counter)

    # Modal verb categories (Scheme E)
    modal_obligation: Counter = field(default_factory=Counter)
    modal_possibility: Counter = field(default_factory=Counter)
    modal_intention: Counter = field(default_factory=Counter)

    # Temporal categories (Scheme E)
    temporal_retrospective: Counter = field(default_factory=Counter)
    temporal_prospective: Counter = field(default_factory=Counter)

    # Intensity categories (Scheme E)
    intensity_intensifier: Counter = field(default_factory=Counter)
    intensity_moderator: Counter = field(default_factory=Counter)

    # Pronoun categories (Scheme E)
    pronoun_inclusive: Counter = field(default_factory=Counter)
    pronoun_exclusive: Counter = field(default_factory=Counter)

    # Discriminatory categories (Scheme E)
    discrim_xenophobic: Counter = field(default_factory=Counter)
    discrim_homophobic: Counter = field(default_factory=Counter)
    discrim_islamophobic: Counter = field(default_factory=Counter)
    discrim_dog_whistle: Counter = field(default_factory=Counter)

    # Topic categories (Scheme F)
    topic_migration: Counter = field(default_factory=Counter)
    topic_klima: Counter = field(default_factory=Counter)
    topic_wirtschaft: Counter = field(default_factory=Counter)
    topic_soziales: Counter = field(default_factory=Counter)
    topic_sicherheit: Counter = field(default_factory=Counter)
    topic_gesundheit: Counter = field(default_factory=Counter)
    topic_europa: Counter = field(default_factory=Counter)
    topic_digital: Counter = field(default_factory=Counter)
    topic_bildung: Counter = field(default_factory=Counter)
    topic_finanzen: Counter = field(default_factory=Counter)
    topic_justiz: Counter = field(default_factory=Counter)
    topic_arbeit: Counter = field(default_factory=Counter)
    topic_mobilitaet: Counter = field(default_factory=Counter)

    # Totals for normalization
    total_adjectives: int = 0
    total_verbs: int = 0
    total_nouns: int = 0  # Total nouns analyzed (for topic calculations)
    total_words: int = 0  # Total words analyzed (for per-mille calculations)

    def get_adjective_counter(self, category: AdjectiveCategory) -> Counter:
        """Get counter for adjective category."""
        return {
            AdjectiveCategory.AFFIRMATIVE: self.adj_affirmative,
            AdjectiveCategory.CRITICAL: self.adj_critical,
            AdjectiveCategory.AGGRESSIVE: self.adj_aggressive,
            AdjectiveCategory.LABELING: self.adj_labeling,
        }[category]

    def get_verb_counter(self, category: VerbCategory) -> Counter:
        """Get counter for verb category."""
        return {
            VerbCategory.SOLUTION_ORIENTED: self.verb_solution,
            VerbCategory.PROBLEM_FOCUSED: self.verb_problem,
            VerbCategory.COLLABORATIVE: self.verb_collaborative,
            VerbCategory.CONFRONTATIONAL: self.verb_confrontational,
            VerbCategory.DEMANDING: self.verb_demanding,
            VerbCategory.ACKNOWLEDGING: self.verb_acknowledging,
        }[category]

    def adjective_category_totals(self) -> dict[AdjectiveCategory, int]:
        """Get total count per adjective category."""
        return {
            AdjectiveCategory.AFFIRMATIVE: sum(self.adj_affirmative.values()),
            AdjectiveCategory.CRITICAL: sum(self.adj_critical.values()),
            AdjectiveCategory.AGGRESSIVE: sum(self.adj_aggressive.values()),
            AdjectiveCategory.LABELING: sum(self.adj_labeling.values()),
        }

    def verb_category_totals(self) -> dict[VerbCategory, int]:
        """Get total count per verb category."""
        return {
            VerbCategory.SOLUTION_ORIENTED: sum(self.verb_solution.values()),
            VerbCategory.PROBLEM_FOCUSED: sum(self.verb_problem.values()),
            VerbCategory.COLLABORATIVE: sum(self.verb_collaborative.values()),
            VerbCategory.CONFRONTATIONAL: sum(self.verb_confrontational.values()),
            VerbCategory.DEMANDING: sum(self.verb_demanding.values()),
            VerbCategory.ACKNOWLEDGING: sum(self.verb_acknowledging.values()),
        }

    def modal_category_totals(self) -> dict[ModalCategory, int]:
        """Get total count per modal verb category."""
        return {
            ModalCategory.OBLIGATION: sum(self.modal_obligation.values()),
            ModalCategory.POSSIBILITY: sum(self.modal_possibility.values()),
            ModalCategory.INTENTION: sum(self.modal_intention.values()),
        }

    def temporal_category_totals(self) -> dict[TemporalCategory, int]:
        """Get total count per temporal category."""
        return {
            TemporalCategory.RETROSPECTIVE: sum(self.temporal_retrospective.values()),
            TemporalCategory.PROSPECTIVE: sum(self.temporal_prospective.values()),
        }

    def intensity_category_totals(self) -> dict[IntensityCategory, int]:
        """Get total count per intensity category."""
        return {
            IntensityCategory.INTENSIFIER: sum(self.intensity_intensifier.values()),
            IntensityCategory.MODERATOR: sum(self.intensity_moderator.values()),
        }

    def pronoun_category_totals(self) -> dict[PronounCategory, int]:
        """Get total count per pronoun category."""
        return {
            PronounCategory.INCLUSIVE: sum(self.pronoun_inclusive.values()),
            PronounCategory.EXCLUSIVE: sum(self.pronoun_exclusive.values()),
        }

    def discriminatory_category_totals(self) -> dict[DiscriminatoryCategory, int]:
        """Get total count per discriminatory category."""
        return {
            DiscriminatoryCategory.XENOPHOBIC: sum(self.discrim_xenophobic.values()),
            DiscriminatoryCategory.HOMOPHOBIC: sum(self.discrim_homophobic.values()),
            DiscriminatoryCategory.ISLAMOPHOBIC: sum(self.discrim_islamophobic.values()),
            DiscriminatoryCategory.DOG_WHISTLE: sum(self.discrim_dog_whistle.values()),
        }

    def get_modal_counter(self, category: ModalCategory) -> Counter:
        """Get counter for modal category."""
        return {
            ModalCategory.OBLIGATION: self.modal_obligation,
            ModalCategory.POSSIBILITY: self.modal_possibility,
            ModalCategory.INTENTION: self.modal_intention,
        }[category]

    def get_temporal_counter(self, category: TemporalCategory) -> Counter:
        """Get counter for temporal category."""
        return {
            TemporalCategory.RETROSPECTIVE: self.temporal_retrospective,
            TemporalCategory.PROSPECTIVE: self.temporal_prospective,
        }[category]

    def get_intensity_counter(self, category: IntensityCategory) -> Counter:
        """Get counter for intensity category."""
        return {
            IntensityCategory.INTENSIFIER: self.intensity_intensifier,
            IntensityCategory.MODERATOR: self.intensity_moderator,
        }[category]

    def get_pronoun_counter(self, category: PronounCategory) -> Counter:
        """Get counter for pronoun category."""
        return {
            PronounCategory.INCLUSIVE: self.pronoun_inclusive,
            PronounCategory.EXCLUSIVE: self.pronoun_exclusive,
        }[category]

    def get_discriminatory_counter(self, category: DiscriminatoryCategory) -> Counter:
        """Get counter for discriminatory category."""
        return {
            DiscriminatoryCategory.XENOPHOBIC: self.discrim_xenophobic,
            DiscriminatoryCategory.HOMOPHOBIC: self.discrim_homophobic,
            DiscriminatoryCategory.ISLAMOPHOBIC: self.discrim_islamophobic,
            DiscriminatoryCategory.DOG_WHISTLE: self.discrim_dog_whistle,
        }[category]

    def get_topic_counter(self, category: TopicCategory) -> Counter:
        """Get counter for topic category."""
        return {
            TopicCategory.MIGRATION: self.topic_migration,
            TopicCategory.KLIMA: self.topic_klima,
            TopicCategory.WIRTSCHAFT: self.topic_wirtschaft,
            TopicCategory.SOZIALES: self.topic_soziales,
            TopicCategory.SICHERHEIT: self.topic_sicherheit,
            TopicCategory.GESUNDHEIT: self.topic_gesundheit,
            TopicCategory.EUROPA: self.topic_europa,
            TopicCategory.DIGITAL: self.topic_digital,
            TopicCategory.BILDUNG: self.topic_bildung,
            TopicCategory.FINANZEN: self.topic_finanzen,
            TopicCategory.JUSTIZ: self.topic_justiz,
            TopicCategory.ARBEIT: self.topic_arbeit,
            TopicCategory.MOBILITAET: self.topic_mobilitaet,
        }[category]

    def topic_category_totals(self) -> dict[TopicCategory, int]:
        """Get total count per topic category."""
        return {
            TopicCategory.MIGRATION: sum(self.topic_migration.values()),
            TopicCategory.KLIMA: sum(self.topic_klima.values()),
            TopicCategory.WIRTSCHAFT: sum(self.topic_wirtschaft.values()),
            TopicCategory.SOZIALES: sum(self.topic_soziales.values()),
            TopicCategory.SICHERHEIT: sum(self.topic_sicherheit.values()),
            TopicCategory.GESUNDHEIT: sum(self.topic_gesundheit.values()),
            TopicCategory.EUROPA: sum(self.topic_europa.values()),
            TopicCategory.DIGITAL: sum(self.topic_digital.values()),
            TopicCategory.BILDUNG: sum(self.topic_bildung.values()),
            TopicCategory.FINANZEN: sum(self.topic_finanzen.values()),
            TopicCategory.JUSTIZ: sum(self.topic_justiz.values()),
            TopicCategory.ARBEIT: sum(self.topic_arbeit.values()),
            TopicCategory.MOBILITAET: sum(self.topic_mobilitaet.values()),
        }

    def to_dict(self) -> dict:
        """Export to dictionary for JSON serialization."""
        return {
            "adjectives": {
                "affirmative": dict(self.adj_affirmative.most_common(50)),
                "critical": dict(self.adj_critical.most_common(50)),
                "aggressive": dict(self.adj_aggressive.most_common(50)),
                "labeling": dict(self.adj_labeling.most_common(50)),
                "totals": {
                    cat.value: count
                    for cat, count in self.adjective_category_totals().items()
                },
                "total_analyzed": self.total_adjectives,
            },
            "verbs": {
                "solution": dict(self.verb_solution.most_common(50)),
                "problem": dict(self.verb_problem.most_common(50)),
                "collaborative": dict(self.verb_collaborative.most_common(50)),
                "confrontational": dict(self.verb_confrontational.most_common(50)),
                "demanding": dict(self.verb_demanding.most_common(50)),
                "acknowledging": dict(self.verb_acknowledging.most_common(50)),
                "totals": {
                    cat.value: count
                    for cat, count in self.verb_category_totals().items()
                },
                "total_analyzed": self.total_verbs,
            },
            # Extended categories (Scheme E)
            "modal": {
                "obligation": dict(self.modal_obligation.most_common(20)),
                "possibility": dict(self.modal_possibility.most_common(20)),
                "intention": dict(self.modal_intention.most_common(20)),
                "totals": {
                    cat.value: count
                    for cat, count in self.modal_category_totals().items()
                },
            },
            "temporal": {
                "retrospective": dict(self.temporal_retrospective.most_common(20)),
                "prospective": dict(self.temporal_prospective.most_common(20)),
                "totals": {
                    cat.value: count
                    for cat, count in self.temporal_category_totals().items()
                },
            },
            "intensity": {
                "intensifier": dict(self.intensity_intensifier.most_common(30)),
                "moderator": dict(self.intensity_moderator.most_common(30)),
                "totals": {
                    cat.value: count
                    for cat, count in self.intensity_category_totals().items()
                },
            },
            "pronouns": {
                "inclusive": dict(self.pronoun_inclusive.most_common(20)),
                "exclusive": dict(self.pronoun_exclusive.most_common(20)),
                "totals": {
                    cat.value: count
                    for cat, count in self.pronoun_category_totals().items()
                },
            },
            "discriminatory": {
                "xenophobic": dict(self.discrim_xenophobic.most_common(20)),
                "homophobic": dict(self.discrim_homophobic.most_common(20)),
                "islamophobic": dict(self.discrim_islamophobic.most_common(20)),
                "dog_whistle": dict(self.discrim_dog_whistle.most_common(20)),
                "totals": {
                    cat.value: count
                    for cat, count in self.discriminatory_category_totals().items()
                },
            },
            # Topic categories (Scheme F)
            "topics": {
                "migration": dict(self.topic_migration.most_common(30)),
                "klima": dict(self.topic_klima.most_common(30)),
                "wirtschaft": dict(self.topic_wirtschaft.most_common(30)),
                "soziales": dict(self.topic_soziales.most_common(30)),
                "sicherheit": dict(self.topic_sicherheit.most_common(30)),
                "gesundheit": dict(self.topic_gesundheit.most_common(30)),
                "europa": dict(self.topic_europa.most_common(30)),
                "digital": dict(self.topic_digital.most_common(30)),
                "bildung": dict(self.topic_bildung.most_common(30)),
                "finanzen": dict(self.topic_finanzen.most_common(30)),
                "justiz": dict(self.topic_justiz.most_common(30)),
                "arbeit": dict(self.topic_arbeit.most_common(30)),
                "mobilitaet": dict(self.topic_mobilitaet.most_common(30)),
                "totals": {
                    cat.value: count
                    for cat, count in self.topic_category_totals().items()
                },
                "total_nouns_analyzed": self.total_nouns,
            },
            "total_words": self.total_words,
        }


@dataclass
class ToneScores:
    """Aggregate tone/sentiment scores derived from categorization (Scheme D + E).

    All scores are on a 0-100 scale unless noted otherwise.
    """

    # Adjective-based scores (Scheme D)
    affirmative_score: float = 50.0      # AFFIRMATIVE / (AFFIRMATIVE + CRITICAL)
    aggression_index: float = 0.0        # AGGRESSIVE / total_categorized_adj
    labeling_index: float = 0.0          # LABELING / total_categorized_adj

    # Verb-based scores (Scheme D)
    solution_focus: float = 50.0         # SOLUTION / (SOLUTION + PROBLEM)
    collaboration_score: float = 50.0    # COLLABORATIVE / (COLLAB + CONFRONT)
    demand_intensity: float = 0.0        # DEMANDING / total_categorized_verbs
    acknowledgment_rate: float = 0.0     # ACKNOWLEDGING / total_categorized_verbs

    # Extended scores (Scheme E)
    authority_index: float = 50.0        # OBLIGATION / (OBLIGATION + POSSIBILITY)
    future_orientation: float = 50.0     # PROSPECTIVE / (PROSPECTIVE + RETROSPECTIVE)
    emotional_intensity: float = 50.0    # INTENSIFIER / (INTENSIFIER + MODERATOR)
    inclusivity_index: float = 50.0      # INCLUSIVE / (INCLUSIVE + EXCLUSIVE)
    discriminatory_index: float = 0.0    # Sum of discrim terms / total_words × 1000 (per-mille)

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            # Scheme D
            "affirmative": round(self.affirmative_score, 1),
            "aggression": round(self.aggression_index, 1),
            "labeling": round(self.labeling_index, 1),
            "solution_focus": round(self.solution_focus, 1),
            "collaboration": round(self.collaboration_score, 1),
            "demand_intensity": round(self.demand_intensity, 1),
            "acknowledgment": round(self.acknowledgment_rate, 1),
            # Scheme E
            "authority": round(self.authority_index, 1),
            "future_orientation": round(self.future_orientation, 1),
            "emotional_intensity": round(self.emotional_intensity, 1),
            "inclusivity": round(self.inclusivity_index, 1),
            "discriminatory": round(self.discriminatory_index, 2),  # per-mille, more precision
        }


@dataclass
class TopicScores:
    """Per-mille topic frequencies for comparing party focus areas (Scheme F).

    All scores are per-1000 words unless noted otherwise.
    """

    migration: float = 0.0
    klima: float = 0.0
    wirtschaft: float = 0.0
    soziales: float = 0.0
    sicherheit: float = 0.0
    gesundheit: float = 0.0
    europa: float = 0.0
    digital: float = 0.0
    bildung: float = 0.0
    finanzen: float = 0.0
    justiz: float = 0.0
    arbeit: float = 0.0
    mobilitaet: float = 0.0

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "migration": round(self.migration, 2),
            "klima": round(self.klima, 2),
            "wirtschaft": round(self.wirtschaft, 2),
            "soziales": round(self.soziales, 2),
            "sicherheit": round(self.sicherheit, 2),
            "gesundheit": round(self.gesundheit, 2),
            "europa": round(self.europa, 2),
            "digital": round(self.digital, 2),
            "bildung": round(self.bildung, 2),
            "finanzen": round(self.finanzen, 2),
            "justiz": round(self.justiz, 2),
            "arbeit": round(self.arbeit, 2),
            "mobilitaet": round(self.mobilitaet, 2),
        }

    def top_topics(self, n: int = 5) -> list[tuple[str, float]]:
        """Get top N topics by score, sorted descending."""
        scores = [
            ("migration", self.migration),
            ("klima", self.klima),
            ("wirtschaft", self.wirtschaft),
            ("soziales", self.soziales),
            ("sicherheit", self.sicherheit),
            ("gesundheit", self.gesundheit),
            ("europa", self.europa),
            ("digital", self.digital),
            ("bildung", self.bildung),
            ("finanzen", self.finanzen),
            ("justiz", self.justiz),
            ("arbeit", self.arbeit),
            ("mobilitaet", self.mobilitaet),
        ]
        return sorted(scores, key=lambda x: x[1], reverse=True)[:n]


class WordCategorizer:
    """Categorizes words into semantic categories using lexicons."""

    def categorize_words(
        self,
        adjective_counts: Counter,
        verb_counts: Counter,
        all_word_counts: Counter | None = None,
        noun_counts: Counter | None = None,
    ) -> CategoryCounts:
        """Categorize word counts from analysis results.

        Args:
            adjective_counts: Counter of adjective lemmas -> count
            verb_counts: Counter of verb lemmas -> count
            all_word_counts: Counter of all word lemmas -> count (for extended categories)
            noun_counts: Counter of noun lemmas -> count (for topic categories)

        Returns:
            CategoryCounts with counts per category
        """
        counts = CategoryCounts()
        counts.total_adjectives = sum(adjective_counts.values())
        counts.total_verbs = sum(verb_counts.values())
        counts.total_nouns = sum(noun_counts.values()) if noun_counts else 0
        counts.total_words = sum(all_word_counts.values()) if all_word_counts else 0

        # Scheme D: Adjectives
        for adj, count in adjective_counts.items():
            category = categorize_adjective(adj)
            if category:
                counts.get_adjective_counter(category)[adj] += count

        # Scheme D: Verbs
        for verb, count in verb_counts.items():
            category = categorize_verb(verb)
            if category:
                counts.get_verb_counter(category)[verb] += count

        # Scheme E: Extended categories (process all words)
        if all_word_counts:
            self._categorize_extended(all_word_counts, counts)

        # Scheme F: Topic categories (process nouns)
        if noun_counts:
            self._categorize_topics(noun_counts, counts)

        return counts

    def _categorize_extended(
        self,
        all_word_counts: Counter,
        counts: CategoryCounts,
    ) -> None:
        """Categorize words into extended categories (Scheme E).

        Modifies counts in-place.
        """
        for word, count in all_word_counts.items():
            # Modal verbs
            modal_cat = categorize_modal(word)
            if modal_cat:
                counts.get_modal_counter(modal_cat)[word] += count

            # Temporal markers
            temporal_cat = categorize_temporal(word)
            if temporal_cat:
                counts.get_temporal_counter(temporal_cat)[word] += count

            # Intensity markers
            intensity_cat = categorize_intensity(word)
            if intensity_cat:
                counts.get_intensity_counter(intensity_cat)[word] += count

            # Pronouns / collective terms
            pronoun_cat = categorize_pronoun(word)
            if pronoun_cat:
                counts.get_pronoun_counter(pronoun_cat)[word] += count

            # Discriminatory terms
            discrim_cat = categorize_discriminatory(word)
            if discrim_cat:
                counts.get_discriminatory_counter(discrim_cat)[word] += count

    def calculate_tone_scores(self, counts: CategoryCounts) -> ToneScores:
        """Calculate aggregate tone scores from category counts (Scheme D + E).

        Score formulas (Scheme D):
        - Affirmative: AFFIRMATIVE / (AFFIRMATIVE + CRITICAL) * 100
        - Aggression: AGGRESSIVE / total_categorized_adj * 100
        - Labeling: LABELING / total_categorized_adj * 100
        - Solution Focus: SOLUTION / (SOLUTION + PROBLEM) * 100
        - Collaboration: COLLABORATIVE / (COLLABORATIVE + CONFRONTATIONAL) * 100
        - Demand Intensity: DEMANDING / total_categorized_verbs * 100
        - Acknowledgment: ACKNOWLEDGING / total_categorized_verbs * 100

        Score formulas (Scheme E):
        - Authority: OBLIGATION / (OBLIGATION + POSSIBILITY) * 100
        - Future Orientation: PROSPECTIVE / (PROSPECTIVE + RETROSPECTIVE) * 100
        - Emotional Intensity: INTENSIFIER / (INTENSIFIER + MODERATOR) * 100
        - Inclusivity: INCLUSIVE / (INCLUSIVE + EXCLUSIVE) * 100
        - Discriminatory: sum(all_discrim) / total_words * 1000 (per-mille)
        """
        scores = ToneScores()

        adj_totals = counts.adjective_category_totals()
        verb_totals = counts.verb_category_totals()

        # =========================================
        # Scheme D scores
        # =========================================

        # Affirmative vs Critical
        aff = adj_totals[AdjectiveCategory.AFFIRMATIVE]
        crit = adj_totals[AdjectiveCategory.CRITICAL]
        if aff + crit > 0:
            scores.affirmative_score = (aff / (aff + crit)) * 100

        # Aggression Index (% of categorized adjectives that are aggressive)
        total_cat_adj = sum(adj_totals.values())
        if total_cat_adj > 0:
            scores.aggression_index = (
                adj_totals[AdjectiveCategory.AGGRESSIVE] / total_cat_adj
            ) * 100
            # Labeling Index
            scores.labeling_index = (
                adj_totals[AdjectiveCategory.LABELING] / total_cat_adj
            ) * 100

        # Solution Focus (SOLUTION vs PROBLEM)
        sol = verb_totals[VerbCategory.SOLUTION_ORIENTED]
        prob = verb_totals[VerbCategory.PROBLEM_FOCUSED]
        if sol + prob > 0:
            scores.solution_focus = (sol / (sol + prob)) * 100

        # Collaboration Score (COLLABORATIVE vs CONFRONTATIONAL)
        collab = verb_totals[VerbCategory.COLLABORATIVE]
        conf = verb_totals[VerbCategory.CONFRONTATIONAL]
        if collab + conf > 0:
            scores.collaboration_score = (collab / (collab + conf)) * 100

        # Demand and Acknowledgment indices (% of categorized verbs)
        total_cat_verb = sum(verb_totals.values())
        if total_cat_verb > 0:
            scores.demand_intensity = (
                verb_totals[VerbCategory.DEMANDING] / total_cat_verb
            ) * 100
            scores.acknowledgment_rate = (
                verb_totals[VerbCategory.ACKNOWLEDGING] / total_cat_verb
            ) * 100

        # =========================================
        # Scheme E scores
        # =========================================

        modal_totals = counts.modal_category_totals()
        temporal_totals = counts.temporal_category_totals()
        intensity_totals = counts.intensity_category_totals()
        pronoun_totals = counts.pronoun_category_totals()
        discrim_totals = counts.discriminatory_category_totals()

        # Authority Index (OBLIGATION vs POSSIBILITY)
        oblig = modal_totals[ModalCategory.OBLIGATION]
        poss = modal_totals[ModalCategory.POSSIBILITY]
        if oblig + poss > 0:
            scores.authority_index = (oblig / (oblig + poss)) * 100

        # Future Orientation (PROSPECTIVE vs RETROSPECTIVE)
        prosp = temporal_totals[TemporalCategory.PROSPECTIVE]
        retro = temporal_totals[TemporalCategory.RETROSPECTIVE]
        if prosp + retro > 0:
            scores.future_orientation = (prosp / (prosp + retro)) * 100

        # Emotional Intensity (INTENSIFIER vs MODERATOR)
        intense = intensity_totals[IntensityCategory.INTENSIFIER]
        moderate = intensity_totals[IntensityCategory.MODERATOR]
        if intense + moderate > 0:
            scores.emotional_intensity = (intense / (intense + moderate)) * 100

        # Inclusivity Index (INCLUSIVE vs EXCLUSIVE)
        incl = pronoun_totals[PronounCategory.INCLUSIVE]
        excl = pronoun_totals[PronounCategory.EXCLUSIVE]
        if incl + excl > 0:
            scores.inclusivity_index = (incl / (incl + excl)) * 100

        # Discriminatory Index (per-mille of total words)
        total_discrim = sum(discrim_totals.values())
        if counts.total_words > 0:
            scores.discriminatory_index = (total_discrim / counts.total_words) * 1000

        return scores

    def _categorize_topics(
        self,
        noun_counts: Counter,
        counts: CategoryCounts,
    ) -> None:
        """Categorize nouns into topic categories (Scheme F).

        Supports multi-label categorization with weights for nouns
        that span multiple topics (e.g., "pflege" -> Gesundheit + Soziales).

        Modifies counts in-place.
        """
        for noun, count in noun_counts.items():
            # Get all topic labels (may be multi-label with weights)
            labels = get_topic_multi_labels(noun)

            for topic, weight in labels:
                # Apply weighted count for multi-label support
                weighted_count = int(count * weight) if weight < 1.0 else count
                if weighted_count > 0:
                    counts.get_topic_counter(topic)[noun] += weighted_count

    def calculate_topic_scores(self, counts: CategoryCounts) -> TopicScores:
        """Calculate per-mille topic frequencies from category counts (Scheme F).

        Score formula: topic_count / total_words * 1000 (per-mille)

        This allows comparing topic focus across parties with different
        total word counts.
        """
        scores = TopicScores()

        if counts.total_words == 0:
            return scores

        topic_totals = counts.topic_category_totals()

        # Calculate per-1000 word frequencies for each topic
        scores.migration = (topic_totals[TopicCategory.MIGRATION] / counts.total_words) * 1000
        scores.klima = (topic_totals[TopicCategory.KLIMA] / counts.total_words) * 1000
        scores.wirtschaft = (topic_totals[TopicCategory.WIRTSCHAFT] / counts.total_words) * 1000
        scores.soziales = (topic_totals[TopicCategory.SOZIALES] / counts.total_words) * 1000
        scores.sicherheit = (topic_totals[TopicCategory.SICHERHEIT] / counts.total_words) * 1000
        scores.gesundheit = (topic_totals[TopicCategory.GESUNDHEIT] / counts.total_words) * 1000
        scores.europa = (topic_totals[TopicCategory.EUROPA] / counts.total_words) * 1000
        scores.digital = (topic_totals[TopicCategory.DIGITAL] / counts.total_words) * 1000
        scores.bildung = (topic_totals[TopicCategory.BILDUNG] / counts.total_words) * 1000
        scores.finanzen = (topic_totals[TopicCategory.FINANZEN] / counts.total_words) * 1000
        scores.justiz = (topic_totals[TopicCategory.JUSTIZ] / counts.total_words) * 1000
        scores.arbeit = (topic_totals[TopicCategory.ARBEIT] / counts.total_words) * 1000
        scores.mobilitaet = (topic_totals[TopicCategory.MOBILITAET] / counts.total_words) * 1000

        return scores
