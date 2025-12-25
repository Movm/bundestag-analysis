"""Rankings computation mixin."""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .data import WrappedData


class RankingsMixin:
    """Mixin for computing speaker rankings.

    Requires these instance attributes from the main class:
    - _speaker_index: dict[str, dict]
    - _rankings: dict[str, dict]
    - data: WrappedData (for drama_stats)
    - _party_avg_words: dict[str, int]
    - _parliament_avg_words: int
    """

    _speaker_index: dict[str, dict]
    _rankings: dict[str, dict]
    data: "WrappedData"
    _party_avg_words: dict[str, int]
    _parliament_avg_words: int

    def _compute_averages(self):
        """Pre-compute party and parliament average words per speech."""
        # Group by party
        party_words: dict[str, int] = {}
        party_speeches: dict[str, int] = {}

        total_words = 0
        total_speeches = 0

        for info in self._speaker_index.values():
            party = info['party']
            speeches = info['speeches']
            words = info['totalWords']

            if party not in party_words:
                party_words[party] = 0
                party_speeches[party] = 0

            party_words[party] += words
            party_speeches[party] += speeches
            total_words += words
            total_speeches += speeches

        # Compute party averages
        for party in party_words:
            if party_speeches[party] > 0:
                self._party_avg_words[party] = round(party_words[party] / party_speeches[party])
            else:
                self._party_avg_words[party] = 0

        # Compute parliament average
        if total_speeches > 0:
            self._parliament_avg_words = round(total_words / total_speeches)
        else:
            self._parliament_avg_words = 0

    def _compute_rankings(self):
        """Compute global and per-party rankings for each speaker."""
        # Sort by speeches and words
        by_speeches = sorted(
            self._speaker_index.values(),
            key=lambda x: x['speeches'],
            reverse=True
        )
        by_words = sorted(
            self._speaker_index.values(),
            key=lambda x: x['totalWords'],
            reverse=True
        )
        by_avg_words = sorted(
            [i for i in self._speaker_index.values() if i['speeches'] >= 3],  # Min 3 speeches for verbosity
            key=lambda x: x['avgWords'],
            reverse=True
        )
        by_longest = sorted(
            self._speaker_index.values(),
            key=lambda x: x['maxWords'],
            reverse=True
        )

        total_speakers = len(self._speaker_index)

        # Global rankings
        for rank, info in enumerate(by_speeches, 1):
            speaker = info['name']
            if speaker not in self._rankings:
                self._rankings[speaker] = {}
            self._rankings[speaker]['speechRank'] = rank
            self._rankings[speaker]['speechPercentile'] = round((1 - rank / total_speakers) * 100, 1)

        for rank, info in enumerate(by_words, 1):
            speaker = info['name']
            self._rankings[speaker]['wordsRank'] = rank
            self._rankings[speaker]['wordsPercentile'] = round((1 - rank / total_speakers) * 100, 1)

        # Verbosity ranking (avg words per speech, min 3 speeches)
        for rank, info in enumerate(by_avg_words, 1):
            speaker = info['name']
            self._rankings[speaker]['verbosityRank'] = rank
            self._rankings[speaker]['verbosityTotal'] = len(by_avg_words)

        # Longest speech ranking
        for rank, info in enumerate(by_longest, 1):
            speaker = info['name']
            self._rankings[speaker]['longestSpeechRank'] = rank

        # Interrupter ranking
        interrupters = self.data.drama_stats.get("interrupters", Counter())
        sorted_interrupters = interrupters.most_common()
        for rank, ((name, party), count) in enumerate(sorted_interrupters, 1):
            if name in self._rankings:
                self._rankings[name]['interrupterRank'] = rank
                self._rankings[name]['totalInterrupters'] = len(sorted_interrupters)

        # Most interrupted ranking
        interrupted = self.data.drama_stats.get("interrupted", Counter())
        sorted_interrupted = interrupted.most_common()
        for rank, ((name, party), count) in enumerate(sorted_interrupted, 1):
            if name in self._rankings:
                self._rankings[name]['interruptedRank'] = rank
                self._rankings[name]['totalInterrupted'] = len(sorted_interrupted)

        # Per-party rankings
        parties = set(info['party'] for info in self._speaker_index.values())
        for party in parties:
            party_speakers = [
                info for info in self._speaker_index.values()
                if info['party'] == party
            ]

            party_by_speeches = sorted(party_speakers, key=lambda x: x['speeches'], reverse=True)
            party_by_words = sorted(party_speakers, key=lambda x: x['totalWords'], reverse=True)
            party_by_avg = sorted(
                [i for i in party_speakers if i['speeches'] >= 3],
                key=lambda x: x['avgWords'],
                reverse=True
            )

            for rank, info in enumerate(party_by_speeches, 1):
                self._rankings[info['name']]['partySpeechRank'] = rank
                self._rankings[info['name']]['partySize'] = len(party_speakers)

            for rank, info in enumerate(party_by_words, 1):
                self._rankings[info['name']]['partyWordsRank'] = rank

            for rank, info in enumerate(party_by_avg, 1):
                self._rankings[info['name']]['partyVerbosityRank'] = rank
