"""Analytics query methods for wrapped analysis (mixin class)."""

import math
from collections import Counter

# Event-specific words to exclude from distinctive word calculations
# These skew statistics due to specific debates (e.g., Afghanistan/Ortskräfte debate)
EVENT_STOPWORDS = {
    "afghanistan", "afghan", "afghaninn", "afghane", "afghanen", "afghaninnen",
    "ortskraft", "ortskräfte", "aufnahmezusage", "aufnahmezusagen",
}

# Party self-reference words to exclude from signature word calculations
# These have high ratios but aren't meaningful policy/ideological markers
PARTY_STOPWORDS = {
    # Faction names
    "spd-fraktion", "cdu-fraktion", "csu-fraktion", "unionsfraktion",
    "grüne-fraktion", "grünen-fraktion", "afd-fraktion", "linke-fraktion",
    "fdp-fraktion", "bsw-fraktion",
    # Party member terms
    "sozialdemokrat", "sozialdemokratin", "sozialdemokraten", "sozialdemokratinnen",
    "christdemokrat", "christdemokratin", "christdemokraten",
    # Party abbreviations in compounds
    "spd-geführt", "cdu-geführt", "grün-geführt",
}


class WrappedDataQueries:
    """Mixin providing all get_* query methods for WrappedData."""

    def get_distinctive_words(
        self, party: str, word_type: str = "nouns", top_n: int = 5
    ) -> list[tuple[str, float]]:
        """Find words distinctive to this party (high relative frequency).

        Uses a balanced algorithm:
        1. Minimum count: 0.05% of party's total words (scales with speaking time)
        2. Distinctiveness: ratio vs other parties must be > 2.0
        3. Stopword filtering: Excludes event-specific and party self-reference words
        4. Balanced score: ratio × √per1000 (rewards both distinctiveness AND frequency)
        """
        if word_type not in self.word_frequencies:
            return []

        df = self.word_frequencies[word_type]
        party_col = f"{party}_per1000"
        party_count_col = f"{party}_count"

        if party_col not in df.columns or party_count_col not in df.columns:
            return []

        other_parties = [p for p in self.metadata["parties"] if p != party]
        other_cols = [f"{p}_per1000" for p in other_parties if f"{p}_per1000" in df.columns]

        if not other_cols:
            return []

        # Calculate 0.05% minimum count (scales with party's total words)
        total_words = df[party_count_col].sum()
        min_count = total_words * 0.0005  # 0.05%

        # Calculate ratio and balanced score
        df = df.copy()
        df["others_avg"] = df[other_cols].mean(axis=1)
        df["ratio"] = df[party_col] / (df["others_avg"] + 0.001)
        # Balanced score: ratio × √per1000 (rewards both distinctiveness AND frequency)
        df["score"] = df["ratio"] * df[party_col].apply(lambda x: math.sqrt(x))

        # Filter: 0.05% min count, ratio > 2.0, exclude stopwords
        distinctive = df[
            (df[party_count_col] >= min_count) &
            (df["ratio"] > 2.0) &
            (~df["word"].isin(EVENT_STOPWORDS)) &
            (~df["word"].isin(PARTY_STOPWORDS))
        ]
        # Rank by balanced score
        distinctive = distinctive.nlargest(top_n, "score")

        return [(row["word"], row["ratio"]) for _, row in distinctive.iterrows()]

    def get_key_topics(
        self, party: str, word_type: str = "nouns", top_n: int = 10
    ) -> list[tuple[str, int, float]]:
        """Find words frequently discussed by this party.

        Key topics are the most frequently used words that still show
        some distinctiveness (ratio > 1.5). Ranked by count, not ratio.

        Returns: [(word, count, ratio), ...]
        """
        if word_type not in self.word_frequencies:
            return []

        df = self.word_frequencies[word_type]
        party_count_col = f"{party}_count"
        party_freq_col = f"{party}_per1000"

        if party_count_col not in df.columns:
            return []

        other_parties = [p for p in self.metadata["parties"] if p != party]
        other_cols = [f"{p}_per1000" for p in other_parties if f"{p}_per1000" in df.columns]

        if not other_cols:
            return []

        # Calculate 0.05% minimum count (scales with party's total words)
        total_words = df[party_count_col].sum()
        min_count = total_words * 0.0005  # 0.05%

        df = df.copy()
        df["others_avg"] = df[other_cols].mean(axis=1)
        df["ratio"] = df[party_freq_col] / (df["others_avg"] + 0.001)

        # Filter: 0.05% min count, ratio > 1.5 (mild distinctiveness), exclude stopwords
        key_topics = df[
            (df[party_count_col] >= min_count) &
            (df["ratio"] > 1.5) &
            (~df["word"].isin(EVENT_STOPWORDS)) &
            (~df["word"].isin(PARTY_STOPWORDS))
        ]
        # Rank by count (most talked about), not ratio
        key_topics = key_topics.nlargest(top_n * 2, party_count_col)

        results = [
            (row["word"], int(row[party_count_col]), row["ratio"])
            for _, row in key_topics.iterrows()
        ]

        # Filter out substring duplicates (e.g., "merz" when "friedrich merz" exists)
        # Keep the more specific (longer) version
        filtered = []
        words_added = set()
        for word, count, ratio in results:
            # Check if this word is a substring of an already added word
            is_substring = any(word in added and word != added for added in words_added)
            # Check if an already added word is a substring of this word
            supersedes = [added for added in words_added if added in word and added != word]

            if is_substring:
                continue  # Skip, we already have the full name
            if supersedes:
                # Remove the shorter version, add this longer one
                filtered = [(w, c, r) for w, c, r in filtered if w not in supersedes]
                words_added -= set(supersedes)

            filtered.append((word, count, ratio))
            words_added.add(word)

            if len(filtered) >= top_n:
                break

        return filtered[:top_n]

    def get_communication_style(self, party: str) -> dict:
        """Calculate style metrics for a party."""
        stats = self.party_stats.get(party, {})
        if not stats:
            return {}

        total_words = stats.get("total_words", 1)
        speeches = stats.get("speeches", 1)

        return {
            "avg_speech_length": total_words / speeches,
            "vocabulary_richness": stats.get("unique_nouns", 0) / max(stats.get("total_nouns", 1), 1),
            "descriptiveness": stats.get("total_adjectives", 0) / max(stats.get("total_nouns", 1), 1),
            "action_orientation": stats.get("total_verbs", 0) / max(stats.get("total_nouns", 1), 1),
        }

    def get_top_speakers(self, n: int = 10) -> list[tuple[str, str, int]]:
        """Get top N speakers across all parties (formal speeches only)."""
        all_speakers = []
        for party, counts in self.speaker_stats.items():
            for speaker, count in counts.items():
                all_speakers.append((speaker, party, count))

        all_speakers.sort(key=lambda x: x[2], reverse=True)
        return all_speakers[:n]

    def get_formal_speakers(self, n: int = 10) -> list[tuple[str, str, int]]:
        """Get top N formal speech speakers (same as get_top_speakers)."""
        return self.get_top_speakers(n)

    def get_question_time_speakers(self, n: int = 10) -> list[tuple[str, str, int]]:
        """Get top N question time participants."""
        all_speakers = []
        for party, counts in self.question_speaker_stats.items():
            for speaker, count in counts.items():
                all_speakers.append((speaker, party, count))

        all_speakers.sort(key=lambda x: x[2], reverse=True)
        return all_speakers[:n]

    def get_top_befragung_responders(self, n: int = 10) -> list[tuple[str, str, int]]:
        """Get top N speakers by Befragung/Fragestunde responses.

        These are typically government officials answering questions in Q&A sessions.
        """
        all_speakers = []
        for party, counts in self.befragung_speaker_stats.items():
            for speaker, count in counts.items():
                all_speakers.append((speaker, party, count))

        all_speakers.sort(key=lambda x: x[2], reverse=True)
        return all_speakers[:n]

    def get_party_champion(self, party: str) -> tuple[str, int] | None:
        """Get the most active speaker for a party."""
        if party not in self.speaker_stats:
            return None
        counts = self.speaker_stats[party]
        if not counts:
            return None
        speaker, count = counts.most_common(1)[0]
        return (speaker, count)

    def get_hot_topics(self, n: int = 10) -> list[str]:
        """Get words that are top across multiple parties.

        Returns words sorted by:
        1. Number of parties that have it in their top-50 (primary)
        2. Total frequency across all parties (tie-breaker)
        """
        word_party_count: Counter = Counter()
        word_total_count: Counter = Counter()

        for party in self.metadata["parties"]:
            if party not in self.top_words:
                continue
            top_50 = self.top_words[party]["nouns"][:50]
            for word, count in top_50:
                word_party_count[word] += 1
                word_total_count[word] += count

        # Filter to words discussed by 3+ parties
        # Sort by party_count DESC, then total_count DESC (tie-breaker)
        hot = [(w, pc, word_total_count[w]) for w, pc in word_party_count.items() if pc >= 3]
        hot.sort(key=lambda x: (x[1], x[2]), reverse=True)

        return [w for w, _, _ in hot[:n]]

    def get_unique_speaker_count(self) -> int:
        """Get total number of unique speakers."""
        all_speakers = set()
        for counts in self.speaker_stats.values():
            all_speakers.update(counts.keys())
        return len(all_speakers)

    def get_top_interrupters(self, n: int = 10) -> list[tuple[str, str, int]]:
        """Get speakers who interrupt the most."""
        interrupters = self.drama_stats.get("interrupters", Counter())
        top = interrupters.most_common(n)
        return [(name, party, count) for (name, party), count in top]

    def get_most_interrupted(self, n: int = 10) -> list[tuple[str, str, int]]:
        """Get speakers who get interrupted the most."""
        interrupted = self.drama_stats.get("interrupted", Counter())
        top = interrupted.most_common(n)
        return [(name, party, count) for (name, party), count in top]

    def get_applause_ranking(self, n: int = 10) -> list[tuple[str, int]]:
        """Get parties/groups by applause received."""
        applause = self.drama_stats.get("applause_by_party", Counter())
        return applause.most_common(n)

    def get_heckle_ranking(self, n: int = 10) -> list[tuple[str, int]]:
        """Get parties/groups by interjections made (aggregated from individuals)."""
        interrupters = self.drama_stats.get("interrupters", Counter())
        party_counts: Counter = Counter()
        for (name, party), count in interrupters.items():
            party_counts[party] += count
        return party_counts.most_common(n)

    def get_marathon_speakers(self, n: int = 5) -> list[tuple[str, str, int]]:
        """Get speakers with the longest individual speeches."""
        if not self.all_speeches:
            return []
        sorted_speeches = sorted(self.all_speeches, key=lambda x: x.get('words', 0), reverse=True)
        return [(s['speaker'], s['party'], s['words']) for s in sorted_speeches[:n]]

    def get_verbose_speakers(self, n: int = 5, min_speeches: int = 5) -> list[tuple[str, str, float, int]]:
        """Get speakers with highest average words per speech.

        Returns: [(speaker, party, avg_words, speech_count), ...]
        """
        if not self.all_speeches:
            return []

        speaker_words: dict = {}
        speaker_counts: Counter = Counter()
        speaker_party: dict = {}

        for s in self.all_speeches:
            key = s['speaker']
            speaker_words[key] = speaker_words.get(key, 0) + s.get('words', 0)
            speaker_counts[key] += 1
            speaker_party[key] = s['party']

        verbose = [
            (speaker, speaker_party[speaker], speaker_words[speaker] / count, count)
            for speaker, count in speaker_counts.items()
            if count >= min_speeches
        ]
        verbose.sort(key=lambda x: x[2], reverse=True)
        return verbose[:n]

    def get_wordiest_speakers(self, n: int = 5) -> list[tuple[str, str, int, int]]:
        """Get speakers with most total words spoken.

        Returns: [(speaker, party, total_words, speech_count), ...]
        """
        if not self.all_speeches:
            return []

        speaker_words: dict = {}
        speaker_counts: Counter = Counter()
        speaker_party: dict = {}

        for s in self.all_speeches:
            key = s['speaker']
            speaker_words[key] = speaker_words.get(key, 0) + s.get('words', 0)
            speaker_counts[key] += 1
            speaker_party[key] = s['party']

        wordiest = [
            (speaker, speaker_party[speaker], speaker_words[speaker], speaker_counts[speaker])
            for speaker in speaker_words
        ]
        wordiest.sort(key=lambda x: x[2], reverse=True)
        return wordiest[:n]

    def get_speakers_by_avg_words(
        self, n: int = 20, min_speeches: int = 5
    ) -> list[tuple[str, str, int, int, int]]:
        """Get speakers with highest average words per formal Rede.

        Only counts speeches with type='rede' (excludes befragung, fragestunde, etc.)

        Args:
            n: Number of speakers to return
            min_speeches: Minimum Reden required to qualify

        Returns: [(speaker, party, avg_words, total_words, speech_count), ...]
        """
        if not self.all_speeches:
            return []

        speaker_words: dict = {}
        speaker_counts: Counter = Counter()
        speaker_party: dict = {}

        for s in self.all_speeches:
            # Only count formal Reden
            if s.get('type') != 'rede':
                continue
            key = s['speaker']
            speaker_words[key] = speaker_words.get(key, 0) + s.get('words', 0)
            speaker_counts[key] += 1
            speaker_party[key] = s['party']

        speakers_with_avg = [
            (
                speaker,
                speaker_party[speaker],
                speaker_words[speaker] // speaker_counts[speaker],
                speaker_words[speaker],
                speaker_counts[speaker],
            )
            for speaker in speaker_words
            if speaker_counts[speaker] >= min_speeches
        ]

        speakers_with_avg.sort(key=lambda x: x[2], reverse=True)
        return speakers_with_avg[:n]

    def get_party_top_speakers(self, party: str, n: int = 3) -> list[tuple[str, int]]:
        """Get top N speakers for a specific party."""
        if party not in self.speaker_stats:
            return []
        return self.speaker_stats[party].most_common(n)

    def get_academic_ranking(self) -> list[tuple[str, float, int, int]]:
        """Get parties ranked by percentage of speakers with academic titles.

        Returns: [(party, dr_ratio, dr_count, total), ...]
        """
        ranking = []
        for party, stats in self.party_stats.items():
            dr_ratio = stats.get("dr_ratio", 0)
            dr_count = stats.get("dr_count", 0)
            total = stats.get("speeches", 0)
            ranking.append((party, dr_ratio, dr_count, total))
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking

    def get_exclusive_words(self, n: int = 3, min_count: int = 10) -> dict[str, list[tuple[str, int]]]:
        """Get words exclusively used by each party.

        Returns: {party: [(word, count), ...]}
        """
        if "nouns" not in self.word_frequencies:
            return {}

        df = self.word_frequencies["nouns"]
        party_cols = [c for c in df.columns if c.endswith('_count')]
        result = {}

        for col in party_cols:
            party = col.replace('_count', '')
            # Find words where this party has min_count+ and others have 0
            mask = (df[col] >= min_count)
            for other_col in party_cols:
                if other_col != col:
                    mask = mask & (df[other_col] == 0)

            exclusive = df[mask].nlargest(n, col)
            if len(exclusive) > 0:
                result[party] = [(row['word'], int(row[col])) for _, row in exclusive.iterrows()]

        return result

    def get_speech_length_stats(self) -> list[tuple[str, int, int, int]]:
        """Get speech length stats per party.

        Returns: [(party, min, avg, max), ...]
        """
        stats = []
        for party in self.metadata.get("parties", []):
            ps = self.party_stats.get(party, {})
            stats.append((
                party,
                ps.get("min_words", 0),
                int(ps.get("avg_words", 0)),
                ps.get("max_words", 0),
            ))
        return stats
