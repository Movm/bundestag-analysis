"""Spirit animal assignment mixin."""

from .constants import ANIMAL_CRITERIA, SPIRIT_ANIMALS


class SpiritAnimalMixin:
    """Mixin for spirit animal assignment logic.

    Requires these instance attributes from the main class:
    - _speaker_tone_scores: dict[str, dict]
    """

    _speaker_tone_scores: dict[str, dict]

    def _build_speaker_data(
        self,
        speaker: str,
        rankings: dict,
        info: dict,
        drama: dict,
        signature_words: list[dict],
        comparison: dict,
    ) -> dict:
        """Consolidate all speaker metrics into a single dict for scoring."""
        tone = self._speaker_tone_scores.get(speaker, {})
        scores = tone.get("scores", {})

        return {
            # Rankings
            "words_rank": rankings.get("wordsRank", 999),
            "speech_rank": rankings.get("speechRank", 999),
            "party_speech_rank": rankings.get("partySpeechRank", 999),
            "party_size": rankings.get("partySize", 0),
            "verbosity_rank": rankings.get("verbosityRank") or 999,

            # Activity
            "speeches": info.get("speeches", 0) + info.get("wortbeitraege", 0),
            "total_words": info.get("totalWords", 0),
            "avg_words": info.get("avgWords", 0),
            "party": info.get("party", ""),

            # Drama
            "interruptions_given": drama.get("interruptionsGiven", 0),
            "interruptions_received": drama.get("interruptionsReceived", 0),

            # Signature words
            "sig_ratio": signature_words[0]["ratioParty"] if signature_words else 0,
            "sig_word_count": len([w for w in signature_words if w["ratioParty"] >= 5]),
            "top_sig_word": signature_words[0] if signature_words else None,

            # Tone scores (0-100)
            "aggression": scores.get("aggression", 0),
            "collaboration": scores.get("collaboration", 50),
            "affirmative": scores.get("affirmative", 50),
            "solution_focus": scores.get("solution_focus", 50),
            "demand_intensity": scores.get("demand_intensity", 0),
            "authority": scores.get("authority", 50),

            # Derived metrics
            "persistence": (info.get("speeches", 1) / max(1, drama.get("interruptionsReceived", 1))) * 10,
        }

    def _calculate_fit_score(self, speaker_data: dict, criteria: dict) -> float:
        """Calculate how well a speaker fits an animal's criteria.

        Returns a score >= 0 for valid fits, -1.0 if disqualified by min requirements.
        """
        score = 0.0

        for metric, config in criteria.items():
            value = speaker_data.get(metric, 0)
            weight = config.get("weight", 1.0)
            scale = config.get("scale", 100)

            # Handle minimum requirements (must meet to be considered)
            if "min" in config and value < config["min"]:
                return -1.0  # Disqualify completely

            # Inverse metrics (lower is better)
            if config.get("inverse"):
                value = max(0, scale - value)

            # Normalize to 0-1 range and apply weight
            normalized = min(1.0, value / scale) if scale > 0 else 0
            score += weight * normalized

        return score

    def _format_animal(
        self, animal_id: str, speaker_data: dict, gender: str = "unknown"
    ) -> dict:
        """Build animal dict with formatted reason text and gendered title.

        Args:
            animal_id: The spirit animal identifier
            speaker_data: Speaker metrics for formatting reason text
            gender: Speaker gender ("male", "female", or "unknown")
        """
        animal = SPIRIT_ANIMALS[animal_id].copy()
        animal["id"] = animal_id

        # Select gendered title
        if gender == "female" and "title_f" in animal:
            animal["title"] = animal["title_f"]
        elif gender == "unknown" and "title_n" in animal:
            animal["title"] = animal["title_n"]
        # else: keep default male title

        # Remove unused title variants from output
        animal.pop("title_f", None)
        animal.pop("title_n", None)

        # Format the reason with speaker data
        format_data = {
            "words": f"{speaker_data.get('total_words', 0):,}".replace(",", "."),
            "speeches": speaker_data.get("speeches", 0),
            "speech_rank": speaker_data.get("speech_rank", 0),
            "words_rank": speaker_data.get("words_rank", 0),
            "party_rank": speaker_data.get("party_speech_rank", 0),
            "party": speaker_data.get("party", ""),
            "avg_words": speaker_data.get("avg_words", 0),
            "interruptions": speaker_data.get("interruptions_given", 0),
            "interrupted": speaker_data.get("interruptions_received", 0),
            "signature_word": (
                speaker_data.get("top_sig_word", {}).get("word", "").capitalize()
                if speaker_data.get("top_sig_word")
                else ""
            ),
            "ratio": round(speaker_data.get("sig_ratio", 0), 1),
        }

        try:
            animal["reason"] = animal["reason"].format(**format_data)
        except KeyError:
            pass  # Keep original reason if formatting fails

        return animal

    def _get_top_animals(self, data: dict, count: int = 3) -> list[tuple[str, float]]:
        """Calculate scores for all animals and return top N sorted by score."""
        scores: dict[str, float] = {}
        for animal_id, criteria in ANIMAL_CRITERIA.items():
            score = self._calculate_fit_score(data, criteria)
            if score >= 0:  # Not disqualified by min requirements
                scores[animal_id] = score

        # Sort by score descending and return top N
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:count]

    def _build_animal_with_alternatives(
        self,
        primary_id: str,
        data: dict,
        alternatives: list[tuple[str, float]],
        gender: str = "unknown",
    ) -> dict:
        """Build primary animal dict with alternatives array."""
        primary = self._format_animal(primary_id, data, gender)

        # Add alternatives (excluding primary if it appears in the list)
        alt_list = []
        for animal_id, score in alternatives:
            if animal_id != primary_id:
                alt = self._format_animal(animal_id, data, gender)
                alt["score"] = round(score, 3)
                alt_list.append(alt)

        primary["alternatives"] = alt_list[:2]  # Max 2 alternatives
        return primary

    def _assign_spirit_animal(
        self,
        speaker: str,
        rankings: dict,
        info: dict,
        drama: dict,
        signature_words: list[dict],
        comparison: dict,
        gender: str = "unknown",
    ) -> dict | None:
        """Assign a spirit animal using hybrid best-fit algorithm.

        Two-phase approach:
        1. Elite exclusives: Hard-coded checks for truly exceptional speakers
        2. Best-fit competition: All animals compete via scoring for everyone else

        Args:
            gender: Speaker gender for gendered titles ("male", "female", "unknown")

        Returns primary animal with top 2 alternatives.
        """
        # No spirit animals for AfD politicians
        if info.get('party') == 'AfD':
            return None

        # Build unified speaker data for scoring
        data = self._build_speaker_data(
            speaker, rankings, info, drama, signature_words, comparison
        )

        # Calculate top alternatives for all speakers (used by both phases)
        top_animals = self._get_top_animals(data, count=3)

        # === PHASE 1: Elite Exclusives (hard-coded, ~15-20 speakers) ===
        # These are truly exceptional and should stay rare

        # Top 10 word count speakers
        if data["words_rank"] <= 10:
            elite_id = "tiger" if data["aggression"] > 15 else "elefant"
            return self._build_animal_with_alternatives(elite_id, data, top_animals, gender)

        # Top speech + word count combo
        if data["speech_rank"] <= 10 and data["words_rank"] <= 20:
            return self._build_animal_with_alternatives("adler", data, top_animals, gender)

        # Top 3 in party (large parties only)
        if data["party_speech_rank"] <= 3 and data["party_size"] >= 20:
            return self._build_animal_with_alternatives("loewe", data, top_animals, gender)

        # === PHASE 2: Best-Fit Competition ===
        # All other animals compete - speaker gets whichever fits best

        if top_animals:
            best_id = top_animals[0][0]
            return self._build_animal_with_alternatives(best_id, data, top_animals, gender)

        # Fallback (should rarely happen)
        return self._build_animal_with_alternatives("biene", data, [], gender)
