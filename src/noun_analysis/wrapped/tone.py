"""Tone analysis methods for wrapped analysis (Scheme D: Communication Style)."""


class ToneAnalysisMixin:
    """Mixin providing tone analysis methods for WrappedData."""

    def get_tone_comparison(self) -> list[dict]:
        """Get all parties' tone scores for comparison table."""
        comparison = []
        for party in self.metadata.get("parties", []):
            if party in self.tone_data:
                comparison.append({
                    "party": party,
                    **self.tone_data[party]
                })
        return comparison

    def get_aggression_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by aggression index (highest first)."""
        ranking = [
            (party, scores.get("aggression", 0))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_labeling_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by labeling index (highest first).

        Labeling captures "othering" language like "ideologisch", "radikal".
        """
        ranking = [
            (party, scores.get("labeling", 0))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_affirmative_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by affirmative score (highest first)."""
        ranking = [
            (party, scores.get("affirmative", 50))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_collaboration_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by collaboration score (highest first)."""
        ranking = [
            (party, scores.get("collaboration", 50))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_solution_focus_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by solution focus score (highest first)."""
        ranking = [
            (party, scores.get("solution_focus", 50))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_demand_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by demand intensity (highest first)."""
        ranking = [
            (party, scores.get("demand_intensity", 0))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_acknowledgment_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by acknowledgment rate (highest first)."""
        ranking = [
            (party, scores.get("acknowledgment", 0))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    # =========================================================================
    # Extended rankings (Scheme E)
    # =========================================================================

    def get_authority_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by authority index (highest = most authoritative).

        Authority = obligation / (obligation + possibility)
        High score = more "müssen", "sollen" language (authoritative)
        Low score = more "können", "dürfen" language (open-minded)
        """
        ranking = [
            (party, scores.get("authority", 50))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_future_orientation_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by future orientation (highest = most future-focused).

        Future = prospective / (prospective + retrospective)
        High score = more forward-looking, planning language
        Low score = more backward-looking, criticizing past language
        """
        ranking = [
            (party, scores.get("future_orientation", 50))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_emotional_intensity_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by emotional intensity (highest = most intense).

        Intensity = intensifiers / (intensifiers + moderators)
        High score = more hyperbolic language ("absolut", "extrem")
        Low score = more hedging language ("vielleicht", "teilweise")
        """
        ranking = [
            (party, scores.get("emotional_intensity", 50))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_inclusivity_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by inclusivity (highest = most inclusive).

        Inclusivity = inclusive / (inclusive + exclusive)
        High score = more "wir", "gemeinsam" language
        Low score = more "sie", "die" (othering) language
        """
        ranking = [
            (party, scores.get("inclusivity", 50))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    def get_discriminatory_ranking(self) -> list[tuple[str, float]]:
        """Rank parties by discriminatory language usage (highest first).

        Discriminatory = contested terms per 1000 words (per-mille)
        This is a sensitive metric - measures presence of loaded terminology.
        """
        ranking = [
            (party, scores.get("discriminatory", 0))
            for party, scores in self.tone_data.items()
        ]
        return sorted(ranking, key=lambda x: x[1], reverse=True)

    # Legacy aliases for backwards compatibility
    def get_aggressiveness_ranking(self) -> list[tuple[str, float]]:
        """Legacy alias for get_aggression_ranking."""
        return self.get_aggression_ranking()

    def get_positivity_ranking(self) -> list[tuple[str, float]]:
        """Legacy alias for get_affirmative_ranking."""
        return self.get_affirmative_ranking()

    def get_cooperation_ranking(self) -> list[tuple[str, float]]:
        """Legacy alias for get_collaboration_ranking."""
        return self.get_collaboration_ranking()

    def get_hope_ranking(self) -> list[tuple[str, float]]:
        """Legacy alias - returns solution_focus_ranking for Scheme D."""
        return self.get_solution_focus_ranking()

    def get_top_words_by_category(
        self,
        party: str,
        word_type: str,  # "adjectives" or "verbs"
        category: str,
        n: int = 5
    ) -> list[tuple[str, int]]:
        """Get top N words in a category for a party.

        Args:
            party: Party name
            word_type: "adjectives" or "verbs"
            category: Category name (e.g., "aggressive", "cooperative")
            n: Number of words to return

        Returns: [(word, count), ...]
        """
        if party not in self.category_data:
            return []

        cat_data = self.category_data[party].get(word_type, {})
        words = cat_data.get(category, {})

        if isinstance(words, dict):
            return sorted(words.items(), key=lambda x: x[1], reverse=True)[:n]
        return []

    def get_discriminatory_counts(self) -> list[tuple[str, int]]:
        """Get raw discriminatory word counts per party (highest first).

        Returns: [(party, count), ...]
        """
        counts = []
        for party in self.category_data:
            discrim = self.category_data[party].get("discriminatory", {})
            totals = discrim.get("totals", {})
            total = sum(totals.values()) if isinstance(totals, dict) else 0
            counts.append((party, total))
        return sorted(counts, key=lambda x: x[1], reverse=True)

    def has_tone_data(self) -> bool:
        """Check if tone analysis data is available."""
        return bool(self.tone_data)
