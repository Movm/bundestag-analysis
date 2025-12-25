"""Gender and speaker analysis mixin for WrappedData.

Provides comprehensive gender-based and speaker-based analysis queries
for the Bundestag wrapped analysis.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Gender, GenderStats, SpeakerProfile


class GenderAnalysisMixin:
    """Mixin providing gender-based and advanced speaker analysis queries.

    This mixin expects the following attributes on self:
    - gender_stats: GenderStats instance
    - speaker_profiles: dict[str, SpeakerProfile]
    - party_stats: dict with party info
    """

    # ==================== Gender Distribution ====================

    def get_gender_distribution(self) -> dict[str, int]:
        """Get overall gender distribution of speakers.

        Returns:
            {"male": count, "female": count, "unknown": count}
        """
        if not self.gender_stats:
            return {"male": 0, "female": 0, "unknown": 0}
        gs = self.gender_stats
        return {
            "male": gs.total_male_speakers,
            "female": gs.total_female_speakers,
            "unknown": gs.total_unknown_speakers,
        }

    def get_gender_distribution_by_party(self) -> dict[str, dict[str, int]]:
        """Get gender distribution per party.

        Returns:
            {party: {"male": count, "female": count, "unknown": count}, ...}
        """
        if not self.gender_stats:
            return {}
        result = {}
        for party, stats in self.gender_stats.by_party.items():
            result[party] = {
                "male": stats.male_speakers,
                "female": stats.female_speakers,
                "unknown": stats.unknown_speakers,
            }
        return result

    def get_gender_ratio_by_party(self) -> list[tuple[str, float]]:
        """Get female speaker ratio per party (sorted by highest female ratio).

        Returns:
            [(party, female_ratio), ...] where ratio is 0.0-1.0
        """
        ratios = []
        for party, dist in self.get_gender_distribution_by_party().items():
            total = dist["male"] + dist["female"]
            if total > 0:
                female_ratio = dist["female"] / total
                ratios.append((party, female_ratio))
        return sorted(ratios, key=lambda x: x[1], reverse=True)

    def get_speech_share_by_gender(self) -> dict[str, float]:
        """Get percentage of speeches by gender.

        Returns:
            {"male": pct, "female": pct, "unknown": pct} where pct is 0-100
        """
        if not self.gender_stats:
            return {"male": 0.0, "female": 0.0, "unknown": 0.0}

        total_speeches = 0
        gender_speeches = {"male": 0, "female": 0, "unknown": 0}

        for stats in self.gender_stats.by_party.values():
            gender_speeches["male"] += stats.male_speeches
            gender_speeches["female"] += stats.female_speeches
            gender_speeches["unknown"] += stats.unknown_speeches
            total_speeches += stats.male_speeches + stats.female_speeches + stats.unknown_speeches

        if total_speeches == 0:
            return {"male": 0.0, "female": 0.0, "unknown": 0.0}

        return {
            g: (count / total_speeches) * 100
            for g, count in gender_speeches.items()
        }

    def get_speech_share_by_gender_by_party(self) -> dict[str, dict[str, float]]:
        """Get percentage of speeches by gender per party.

        Returns:
            {party: {"male": pct, "female": pct}, ...}
        """
        if not self.gender_stats:
            return {}

        result = {}
        for party, stats in self.gender_stats.by_party.items():
            total = stats.male_speeches + stats.female_speeches + stats.unknown_speeches
            if total > 0:
                result[party] = {
                    "male": (stats.male_speeches / total) * 100,
                    "female": (stats.female_speeches / total) * 100,
                    "unknown": (stats.unknown_speeches / total) * 100,
                }
            else:
                result[party] = {"male": 0.0, "female": 0.0, "unknown": 0.0}
        return result

    # ==================== Top Speakers by Gender ====================

    def get_top_speakers_by_gender(
        self,
        gender: "Gender",
        n: int = 10,
        formal_only: bool = False,
    ) -> list[tuple[str, str, int]]:
        """Get top N speakers of a specific gender by speech count.

        Args:
            gender: "male", "female", or "unknown"
            n: Number of speakers to return
            formal_only: If True, count only formal speeches (Reden).
                        If False, count all activity (Wortmeldungen).

        Returns:
            [(speaker_name, party, speech_count), ...]
        """
        speakers = []
        for profile in self.speaker_profiles.values():
            if profile.gender == gender:
                count = profile.formal_speeches if formal_only else profile.total_speeches
                speakers.append((profile.name, profile.party, count))
        return sorted(speakers, key=lambda x: x[2], reverse=True)[:n]

    def get_top_female_speakers(
        self, n: int = 10, formal_only: bool = False
    ) -> list[tuple[str, str, int]]:
        """Get top female speakers.

        Args:
            n: Number of speakers
            formal_only: True for Reden only, False for all Wortmeldungen
        """
        return self.get_top_speakers_by_gender("female", n, formal_only)

    def get_top_male_speakers(
        self, n: int = 10, formal_only: bool = False
    ) -> list[tuple[str, str, int]]:
        """Get top male speakers.

        Args:
            n: Number of speakers
            formal_only: True for Reden only, False for all Wortmeldungen
        """
        return self.get_top_speakers_by_gender("male", n, formal_only)

    # ==================== Speech Metrics by Gender ====================

    def get_speech_length_by_gender(self) -> dict[str, float]:
        """Get average speech length (words) by gender.

        Returns:
            {"male": avg_words, "female": avg_words, "unknown": avg_words}
        """
        gender_words: dict[str, int] = {"male": 0, "female": 0, "unknown": 0}
        gender_speeches: dict[str, int] = {"male": 0, "female": 0, "unknown": 0}

        for profile in self.speaker_profiles.values():
            gender_words[profile.gender] += profile.total_words
            gender_speeches[profile.gender] += profile.total_speeches

        return {
            g: gender_words[g] / gender_speeches[g] if gender_speeches[g] > 0 else 0
            for g in ["male", "female", "unknown"]
        }

    def get_speech_length_by_gender_by_party(self) -> dict[str, dict[str, float]]:
        """Get average speech length by gender per party.

        Returns:
            {party: {"male": avg, "female": avg}, ...}
        """
        if not self.gender_stats:
            return {}
        return {
            party: {
                "male": stats.male_avg_speech_length,
                "female": stats.female_avg_speech_length,
            }
            for party, stats in self.gender_stats.by_party.items()
        }

    def get_total_words_by_gender(self) -> dict[str, int]:
        """Get total words spoken by gender.

        Returns:
            {"male": total_words, "female": total_words, "unknown": total_words}
        """
        totals = {"male": 0, "female": 0, "unknown": 0}
        for profile in self.speaker_profiles.values():
            totals[profile.gender] += profile.total_words
        return totals

    # ==================== Interruption Patterns by Gender ====================

    def get_interruption_patterns_by_gender(self) -> dict[str, dict[str, int]]:
        """Analyze interruption patterns by gender.

        Returns:
            {
                "interruptions_made": {"male": count, "female": count, "unknown": count},
                "interruptions_received": {"male": count, "female": count, "unknown": count},
            }
        """
        made = {"male": 0, "female": 0, "unknown": 0}
        received = {"male": 0, "female": 0, "unknown": 0}

        for profile in self.speaker_profiles.values():
            made[profile.gender] += profile.interruptions_made
            received[profile.gender] += profile.interruptions_received

        return {
            "interruptions_made": made,
            "interruptions_received": received,
        }

    def get_interruption_ratio_by_gender(self) -> dict[str, float]:
        """Get ratio of interruptions made to received by gender.

        A ratio > 1 means this gender interrupts more than they are interrupted.

        Returns:
            {"male": ratio, "female": ratio}
        """
        patterns = self.get_interruption_patterns_by_gender()
        result = {}
        for gender in ["male", "female"]:
            made = patterns["interruptions_made"].get(gender, 0)
            received = patterns["interruptions_received"].get(gender, 0)
            if received > 0:
                result[gender] = made / received
            else:
                result[gender] = float(made) if made > 0 else 0.0
        return result

    def get_interruption_patterns_by_gender_by_party(
        self,
    ) -> dict[str, dict[str, dict[str, int]]]:
        """Get interruption patterns by gender per party.

        Returns:
            {party: {"made": {"male": N, "female": N}, "received": {...}}, ...}
        """
        if not self.gender_stats:
            return {}

        result = {}
        for party, stats in self.gender_stats.by_party.items():
            result[party] = {
                "made": {
                    "male": stats.male_interruptions_made,
                    "female": stats.female_interruptions_made,
                },
                "received": {
                    "male": stats.male_interruptions_received,
                    "female": stats.female_interruptions_received,
                },
            }
        return result

    # ==================== Academic Titles by Gender ====================

    def get_academic_titles_by_gender(self) -> dict[str, float]:
        """Get Dr. title ratio by gender.

        Returns:
            {"male": ratio, "female": ratio} where ratio is 0.0-1.0
        """
        dr_count = {"male": 0, "female": 0}
        total_count = {"male": 0, "female": 0}

        for profile in self.speaker_profiles.values():
            if profile.gender in ("male", "female"):
                total_count[profile.gender] += 1
                if profile.acad_title:
                    dr_count[profile.gender] += 1

        return {
            g: dr_count[g] / total_count[g] if total_count[g] > 0 else 0
            for g in ["male", "female"]
        }

    def get_academic_titles_by_gender_by_party(self) -> dict[str, dict[str, float]]:
        """Get Dr. ratio by gender per party.

        Returns:
            {party: {"male": ratio, "female": ratio}, ...}
        """
        if not self.gender_stats:
            return {}
        result = {}
        for party, stats in self.gender_stats.by_party.items():
            male_total = stats.male_speakers
            female_total = stats.female_speakers
            result[party] = {
                "male": stats.male_dr_count / male_total if male_total > 0 else 0,
                "female": stats.female_dr_count / female_total if female_total > 0 else 0,
            }
        return result

    # ==================== Question Time by Gender ====================

    def get_question_time_by_gender(self) -> dict[str, int]:
        """Get question time participation (speech count) by gender.

        Returns:
            {"male": count, "female": count, "unknown": count}
        """
        counts = {"male": 0, "female": 0, "unknown": 0}
        for profile in self.speaker_profiles.values():
            counts[profile.gender] += profile.question_speeches
        return counts

    def get_question_time_share_by_gender(self) -> dict[str, float]:
        """Get question time participation percentage by gender.

        Returns:
            {"male": pct, "female": pct} where pct is 0-100
        """
        counts = self.get_question_time_by_gender()
        total = sum(counts.values())
        if total == 0:
            return {"male": 0.0, "female": 0.0, "unknown": 0.0}
        return {g: (c / total) * 100 for g, c in counts.items()}

    # ==================== Wordiest Speakers by Gender ====================

    def get_wordiest_by_gender(
        self,
        gender: "Gender",
        n: int = 5,
    ) -> list[tuple[str, str, int, int]]:
        """Get speakers with most total words by gender.

        Args:
            gender: "male", "female", or "unknown"
            n: Number of speakers to return

        Returns:
            [(speaker, party, total_words, speech_count), ...]
        """
        speakers = [
            (p.name, p.party, p.total_words, p.total_speeches)
            for p in self.speaker_profiles.values()
            if p.gender == gender
        ]
        return sorted(speakers, key=lambda x: x[2], reverse=True)[:n]

    def get_wordiest_female_speakers(self, n: int = 5) -> list[tuple[str, str, int, int]]:
        """Convenience method for wordiest female speakers."""
        return self.get_wordiest_by_gender("female", n)

    def get_wordiest_male_speakers(self, n: int = 5) -> list[tuple[str, str, int, int]]:
        """Convenience method for wordiest male speakers."""
        return self.get_wordiest_by_gender("male", n)

    # ==================== Additional Speaker Analyses ====================

    def get_speaking_time_distribution(self) -> list[tuple[str, str, int]]:
        """Get all speakers ranked by total words (speaking time proxy).

        Returns:
            [(speaker, party, total_words), ...]
        """
        return sorted(
            [(p.name, p.party, p.total_words) for p in self.speaker_profiles.values()],
            key=lambda x: x[2],
            reverse=True,
        )

    def get_most_active_speakers(
        self,
        n: int = 10,
        min_speeches: int = 1,
    ) -> list[tuple[str, str, int, float]]:
        """Get most active speakers by formal speech count.

        Args:
            n: Number of speakers to return
            min_speeches: Minimum speeches required

        Returns:
            [(speaker, party, formal_speeches, avg_words), ...]
        """
        speakers = [
            (p.name, p.party, p.formal_speeches, p.avg_words_per_speech)
            for p in self.speaker_profiles.values()
            if p.formal_speeches >= min_speeches
        ]
        return sorted(speakers, key=lambda x: x[2], reverse=True)[:n]

    def get_verbose_speakers_by_gender(
        self,
        gender: "Gender",
        n: int = 5,
        min_speeches: int = 3,
    ) -> list[tuple[str, str, float, int]]:
        """Get speakers with highest average words per speech by gender.

        Args:
            gender: "male", "female", or "unknown"
            n: Number of speakers to return
            min_speeches: Minimum speeches to qualify

        Returns:
            [(speaker, party, avg_words, speech_count), ...]
        """
        speakers = [
            (p.name, p.party, p.avg_words_per_speech, p.total_speeches)
            for p in self.speaker_profiles.values()
            if p.gender == gender and p.total_speeches >= min_speeches
        ]
        return sorted(speakers, key=lambda x: x[2], reverse=True)[:n]

    def get_speaker_profile(self, name: str) -> "SpeakerProfile | None":
        """Get detailed profile for a specific speaker.

        Args:
            name: Speaker's full name

        Returns:
            SpeakerProfile or None if not found
        """
        return self.speaker_profiles.get(name)

    def get_speakers_by_party_and_gender(
        self,
        party: str,
        gender: "Gender",
    ) -> list["SpeakerProfile"]:
        """Get all speakers for a specific party and gender.

        Args:
            party: Party name
            gender: "male", "female", or "unknown"

        Returns:
            List of SpeakerProfile instances
        """
        return [
            p
            for p in self.speaker_profiles.values()
            if p.party == party and p.gender == gender
        ]

    def has_gender_data(self) -> bool:
        """Check if gender analysis data is available."""
        return self.gender_stats is not None and len(self.speaker_profiles) > 0
