"""Main SpeakerExporter class for individual Bundestag Wrapped profiles."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

import orjson

from noun_analysis.analyzer import WordAnalyzer
from noun_analysis.categorizer import WordCategorizer

from .constants import ADJECTIVE_SET, VERB_SET, WORD_PATTERN, TOPIC_NOUN_SET, TOPIC_WORD_TO_CATEGORY
from .quiz import QuizGeneratorMixin
from .rankings import RankingsMixin
from .signatures import SignatureWordsMixin
from .spirit_animals import SpiritAnimalMixin
from .utils import generate_slug

if TYPE_CHECKING:
    from ..data import WrappedData


class SpeakerExporter(
    SignatureWordsMixin,
    QuizGeneratorMixin,
    SpiritAnimalMixin,
    RankingsMixin,
):
    """Export individual Wrapped data for each speaker."""

    def __init__(self, wrapped_data: "WrappedData"):
        self.data = wrapped_data
        self._speaker_index: dict[str, dict] = {}
        self._rankings: dict[str, dict] = {}
        self._speaker_speeches: dict[str, list] = {}  # Store actual speech data

        # Cached stopwords reference (avoid repeated property access)
        self._stopwords = WordAnalyzer.STOPWORD_GENERIC

        # Pre-computed word counts for O(1) signature word lookup
        self._speaker_word_counts: dict[str, Counter] = {}
        self._speaker_total_words: dict[str, int] = {}
        self._speaker_adj_counts: dict[str, Counter] = {}
        self._speaker_verb_counts: dict[str, Counter] = {}  # For tone analysis
        self._party_word_counts: dict[str, Counter] = {}
        self._party_total_words: dict[str, int] = {}
        self._party_adj_counts: dict[str, Counter] = {}
        self._party_verb_counts: dict[str, Counter] = {}  # For tone analysis
        self._bundestag_word_counts: Counter = Counter()
        self._bundestag_total_words: int = 0
        self._bundestag_adj_counts: Counter = Counter()
        self._bundestag_verb_counts: Counter = Counter()  # For tone analysis

        # Per-speaker tone scores (computed after word counts)
        self._speaker_tone_scores: dict[str, dict] = {}

        # Per-speaker topic counts (computed during _precompute_word_counts)
        self._speaker_topic_counts: dict[str, dict[str, Counter]] = {}
        self._party_topic_counts: dict[str, dict[str, Counter]] = {}
        self._bundestag_topic_counts: dict[str, Counter] = {}

        # Pre-computed averages for O(1) comparison lookup
        self._party_avg_words: dict[str, int] = {}
        self._parliament_avg_words: int = 0

        self._build_speaker_index()
        self._precompute_word_counts()
        self._compute_speaker_tone_scores()
        self._compute_speaker_topic_scores()

    def _build_speaker_index(self):
        """Build index of all speakers with aggregated stats."""
        speaker_words: dict[str, int] = {}
        speaker_speeches: dict[str, int] = {}  # Formal speeches only (category='rede')
        speaker_wortbeitraege: dict[str, int] = {}  # Non-formal speeches (category='wortbeitrag')
        speaker_befragung: dict[str, int] = {}  # Q&A responses (type='befragung'/'fragestunde_antwort')
        speaker_total_interventions: dict[str, int] = {}  # All entries
        speaker_party: dict[str, str] = {}
        speaker_titles: dict[str, str | None] = {}
        speaker_min_words: dict[str, int] = {}
        speaker_max_words: dict[str, int] = {}

        for speech in self.data.all_speeches:
            speaker = speech['speaker']
            party = speech['party']
            words = speech.get('words', 0)
            speech_type = speech.get('type', 'other')
            category = speech.get('category', 'rede' if speech_type == 'rede' else 'wortbeitrag')

            if speaker not in speaker_words:
                speaker_words[speaker] = 0
                speaker_speeches[speaker] = 0
                speaker_wortbeitraege[speaker] = 0
                speaker_befragung[speaker] = 0
                speaker_total_interventions[speaker] = 0
                speaker_party[speaker] = party
                speaker_titles[speaker] = speech.get('acad_title')
                speaker_min_words[speaker] = words
                speaker_max_words[speaker] = words
                self._speaker_speeches[speaker] = []

            speaker_words[speaker] += words
            speaker_total_interventions[speaker] += 1

            # Count by category (high-level)
            if category == 'rede':
                speaker_speeches[speaker] += 1
            else:
                speaker_wortbeitraege[speaker] += 1

            # Also track detailed type for befragung
            if speech_type in ('befragung', 'fragestunde_antwort'):
                speaker_befragung[speaker] += 1

            speaker_min_words[speaker] = min(speaker_min_words[speaker], words)
            speaker_max_words[speaker] = max(speaker_max_words[speaker], words)
            self._speaker_speeches[speaker].append(speech)

        # Build index
        for speaker in speaker_words:
            slug = generate_slug(speaker)
            total_count = speaker_speeches[speaker] + speaker_wortbeitraege[speaker]
            self._speaker_index[speaker] = {
                'name': speaker,
                'slug': slug,
                'party': speaker_party[speaker],
                'speeches': speaker_speeches[speaker],  # Formal speeches (category='rede')
                'wortbeitraege': speaker_wortbeitraege[speaker],  # Non-formal (category='wortbeitrag')
                'befragungResponses': speaker_befragung[speaker],  # Q&A answers (subset of wortbeitraege)
                'totalInterventions': speaker_total_interventions[speaker],  # All entries
                'totalWords': speaker_words[speaker],
                'avgWords': round(speaker_words[speaker] / total_count) if total_count > 0 else 0,
                'minWords': speaker_min_words[speaker],
                'maxWords': speaker_max_words[speaker],
                'academicTitle': speaker_titles[speaker],
            }

        # Handle slug collisions
        self._resolve_slug_collisions()

        # Pre-compute party and parliament averages
        self._compute_averages()

        # Compute rankings
        self._compute_rankings()

    def _resolve_slug_collisions(self):
        """Add party suffix to slugs that collide."""
        slug_counts: Counter = Counter()
        for info in self._speaker_index.values():
            slug_counts[info['slug']] += 1

        collisions = {slug for slug, count in slug_counts.items() if count > 1}

        if collisions:
            for speaker, info in self._speaker_index.items():
                if info['slug'] in collisions:
                    party_suffix = generate_slug(info['party'])
                    info['slug'] = f"{info['slug']}-{party_suffix}"

    def _precompute_word_counts(self):
        """Pre-compute word counts for all speakers, parties, and Bundestag.

        This runs once during init and makes signature word calculation O(1)
        instead of O(n²) where n = number of speeches.
        """
        from noun_analysis.lexicons import TopicCategory

        # Initialize party aggregates
        parties = set(info['party'] for info in self._speaker_index.values())
        topic_names = [t.value for t in TopicCategory]

        for party in parties:
            self._party_word_counts[party] = Counter()
            self._party_total_words[party] = 0
            self._party_adj_counts[party] = Counter()
            self._party_verb_counts[party] = Counter()
            # Initialize topic counts per party
            self._party_topic_counts[party] = {t: Counter() for t in topic_names}

        # Initialize Bundestag-wide topic counts
        self._bundestag_topic_counts = {t: Counter() for t in topic_names}

        # Single pass through all speeches - tokenize once per speech
        for speaker, speeches in self._speaker_speeches.items():
            party = self._speaker_index.get(speaker, {}).get('party')
            if not party:
                continue

            speaker_words = Counter()
            speaker_adjs = Counter()
            speaker_verbs = Counter()
            speaker_topics = {t: Counter() for t in topic_names}
            speaker_total = 0

            for speech in speeches:
                # Skip ortskraefte to avoid skewing word statistics
                # (15 identical SPD statements about Afghanistan local staff)
                if speech.get('type') == 'ortskraefte':
                    continue

                text = speech.get('text', '').lower()
                # Use pre-compiled regex pattern
                words = WORD_PATTERN.findall(text)
                speaker_total += len(words)

                # Count words
                speaker_words.update(words)

                # Count adjectives, verbs, and topic nouns using pre-built sets
                for word in words:
                    if word in ADJECTIVE_SET:
                        speaker_adjs[word] += 1
                    if word in VERB_SET:
                        speaker_verbs[word] += 1
                    if word in TOPIC_NOUN_SET:
                        topic = TOPIC_WORD_TO_CATEGORY[word]
                        speaker_topics[topic.value][word] += 1

            # Store speaker counts
            self._speaker_word_counts[speaker] = speaker_words
            self._speaker_total_words[speaker] = speaker_total
            self._speaker_adj_counts[speaker] = speaker_adjs
            self._speaker_verb_counts[speaker] = speaker_verbs
            self._speaker_topic_counts[speaker] = speaker_topics

            # Add to party aggregates
            self._party_word_counts[party] += speaker_words
            self._party_total_words[party] += speaker_total
            self._party_adj_counts[party] += speaker_adjs
            self._party_verb_counts[party] += speaker_verbs
            for t in topic_names:
                self._party_topic_counts[party][t] += speaker_topics[t]

            # Add to Bundestag aggregates
            self._bundestag_word_counts += speaker_words
            self._bundestag_total_words += speaker_total
            self._bundestag_adj_counts += speaker_adjs
            self._bundestag_verb_counts += speaker_verbs
            for t in topic_names:
                self._bundestag_topic_counts[t] += speaker_topics[t]

    def _compute_speaker_tone_scores(self) -> None:
        """Compute tone scores for each speaker using their word counts.

        Speakers with sufficient data (≥3 speeches, ≥300 words) get tone scores
        that can be used for tone-influenced spirit animal assignment.
        """
        categorizer = WordCategorizer()

        for speaker, info in self._speaker_index.items():
            adj_counts = self._speaker_adj_counts.get(speaker, Counter())
            verb_counts = self._speaker_verb_counts.get(speaker, Counter())
            word_counts = self._speaker_word_counts.get(speaker, Counter())
            total_words = self._speaker_total_words.get(speaker, 0)

            # Determine confidence level based on sample size
            speech_count = info.get('speeches', 0) + info.get('wortbeitraege', 0)
            if speech_count >= 3 and total_words >= 300:
                confidence = 'sufficient'
            else:
                confidence = 'low'

            # Calculate tone scores using existing categorizer
            category_counts = categorizer.categorize_words(
                adj_counts, verb_counts, word_counts
            )
            tone_scores = categorizer.calculate_tone_scores(category_counts)

            self._speaker_tone_scores[speaker] = {
                'scores': tone_scores.to_dict(),
                'confidence': confidence,
                'sampleSize': {
                    'speeches': speech_count,
                    'words': total_words,
                    'adjectives': sum(adj_counts.values()),
                    'verbs': sum(verb_counts.values()),
                }
            }

    def _compute_speaker_topic_scores(self) -> None:
        """Compute topic scores for each speaker using their topic word counts.

        Calculates per-1000 word frequencies for each topic area (Scheme F).
        """
        from noun_analysis.lexicons import TopicCategory

        topic_names = [t.value for t in TopicCategory]
        self._speaker_topic_data: dict[str, dict] = {}

        for speaker, info in self._speaker_index.items():
            topic_counts = self._speaker_topic_counts.get(speaker, {})
            total_words = self._speaker_total_words.get(speaker, 0)

            if total_words == 0:
                continue

            # Calculate per-1000 frequencies for each topic
            scores = {}
            for topic_name in topic_names:
                counter = topic_counts.get(topic_name, Counter())
                topic_total = sum(counter.values())
                scores[topic_name] = round((topic_total / total_words) * 1000, 2)

            # Get top topics (sorted by score)
            top_topics = sorted(
                [(name, score) for name, score in scores.items() if score > 0],
                key=lambda x: x[1],
                reverse=True
            )[:5]

            # Get top words per topic (for display)
            topic_words = {}
            for topic_name in topic_names:
                counter = topic_counts.get(topic_name, Counter())
                if sum(counter.values()) > 0:
                    topic_words[topic_name] = [
                        {"word": w, "count": c}
                        for w, c in counter.most_common(5)
                    ]

            self._speaker_topic_data[speaker] = {
                "scores": scores,
                "topTopics": [
                    {"topic": name, "score": score, "rank": i + 1}
                    for i, (name, score) in enumerate(top_topics)
                ],
                "topicWords": topic_words,
            }

    def _get_speaker_drama(self, speaker: str, party: str) -> dict:
        """Get drama stats for a specific speaker."""
        interrupters = self.data.drama_stats.get("interrupters", Counter())
        interrupted = self.data.drama_stats.get("interrupted", Counter())

        interruptions_given = interrupters.get((speaker, party), 0)
        interruptions_received = interrupted.get((speaker, party), 0)

        rankings = self._rankings.get(speaker, {})

        return {
            'interruptionsGiven': interruptions_given,
            'interruptionsReceived': interruptions_received,
            'interrupterRank': rankings.get('interrupterRank'),
            'interruptedRank': rankings.get('interruptedRank'),
        }

    def _get_speaker_words(self, speaker: str) -> dict:
        """Get top words for a specific speaker using pre-computed counts."""
        word_counts = self._speaker_word_counts.get(speaker, Counter())

        top_words = [
            {'word': word, 'count': count}
            for word, count in word_counts.most_common(50)
            if word not in self._stopwords
        ][:10]

        return {
            'topWords': top_words,
        }

    def _get_speaker_comparison(self, speaker: str, party: str) -> dict:
        """Get comparison vs party and parliament averages using pre-computed values."""
        info = self._speaker_index.get(speaker, {})
        speaker_avg = info.get('avgWords', 0)

        # Use pre-computed averages (O(1) instead of O(n))
        party_avg = self._party_avg_words.get(party, 0)
        parliament_avg = self._parliament_avg_words

        return {
            'speakerAvgWords': speaker_avg,
            'partyAvgWords': party_avg,
            'parliamentAvgWords': parliament_avg,
            'vsParty': round(speaker_avg / party_avg, 2) if party_avg > 0 else 1.0,
            'vsParliament': round(speaker_avg / parliament_avg, 2) if parliament_avg > 0 else 1.0,
        }

    def _generate_fun_facts(self, speaker: str, party: str, drama: dict) -> list[dict]:
        """Generate fun facts for a speaker. Accepts pre-computed drama dict."""
        info = self._speaker_index.get(speaker, {})
        rankings = self._rankings.get(speaker, {})

        facts = []

        # Speech count fact
        speeches = info.get('speeches', 0)
        facts.append({
            'emoji': '🎤',
            'label': 'Reden gehalten',
            'value': str(speeches),
        })

        # Words spoken
        total_words = info.get('totalWords', 0)
        if total_words >= 1000:
            facts.append({
                'emoji': '📝',
                'label': 'Wörter gesprochen',
                'value': f"{total_words:,}".replace(',', '.'),
            })

        # Top speech rank
        speech_rank = rankings.get('speechRank', 0)
        total_speakers = len(self._speaker_index)
        if speech_rank <= 20:
            facts.append({
                'emoji': '🏆',
                'label': 'Rang (Reden)',
                'value': f"#{speech_rank} von {total_speakers}",
            })

        # Verbosity ranking (wortreichste Redner)
        verbosity_rank = rankings.get('verbosityRank')
        verbosity_total = rankings.get('verbosityTotal')
        if verbosity_rank and verbosity_rank <= 20:
            facts.append({
                'emoji': '📚',
                'label': 'Wortreichster',
                'value': f"#{verbosity_rank} von {verbosity_total}",
            })

        # Longest speech ranking
        longest_rank = rankings.get('longestSpeechRank', 0)
        max_words = info.get('maxWords', 0)
        if longest_rank <= 10 and max_words > 0:
            facts.append({
                'emoji': '📏',
                'label': 'Längste Rede',
                'value': f"#{longest_rank} ({max_words:,} Wörter)".replace(',', '.'),
            })

        # Interrupter ranking
        interrupter_rank = drama.get('interrupterRank')
        if interrupter_rank and interrupter_rank <= 20:
            facts.append({
                'emoji': '⚡',
                'label': 'Zwischenrufer',
                'value': f"#{interrupter_rank} ({drama['interruptionsGiven']}x)",
            })
        elif drama['interruptionsGiven'] >= 10:
            facts.append({
                'emoji': '⚡',
                'label': 'Zwischenrufe',
                'value': str(drama['interruptionsGiven']),
            })

        # Party rank
        party_rank = rankings.get('partySpeechRank', 0)
        party_size = rankings.get('partySize', 0)
        if party_rank <= 5 and party_size > 10:
            facts.append({
                'emoji': '🥇',
                'label': f'Rang in {party}',
                'value': f"#{party_rank} von {party_size}",
            })

        # Percentile (for those not in top 20)
        percentile = rankings.get('speechPercentile', 0)
        if percentile >= 90 and speech_rank > 20:
            facts.append({
                'emoji': '📊',
                'label': 'Top-Redner',
                'value': f"Top {100 - int(percentile)}%",
            })

        return facts[:6]  # Max 6 fun facts

    def generate_speaker_data(self, speaker: str) -> dict | None:
        """Generate full wrapped data for a single speaker."""
        if speaker not in self._speaker_index:
            return None

        info = self._speaker_index[speaker]
        party = info['party']
        rankings = self._rankings.get(speaker, {})

        # Get words data and add signature words
        words_data = self._get_speaker_words(speaker)
        signature_words = self._get_speaker_signature_words(speaker, party)
        words_data['signatureWords'] = signature_words

        # Get signature adjectives
        signature_adjectives = self._get_speaker_signature_adjectives(speaker, party)
        words_data['signatureAdjectives'] = signature_adjectives

        # Generate signature word quiz
        signature_quiz = self._generate_signature_quiz(speaker, party, signature_words)

        # Generate signature adjective quiz
        signature_adjective_quiz = self._generate_signature_adjective_quiz(speaker, party, signature_adjectives)

        # Get drama and comparison for spirit animal calculation
        drama = self._get_speaker_drama(speaker, party)
        comparison = self._get_speaker_comparison(speaker, party)

        # Get speaker gender for gendered spirit animal titles
        profile = self.data.speaker_profiles.get(speaker)
        gender = profile.gender if profile else "unknown"

        # Assign spirit animal based on speaker behavior
        spirit_animal = self._assign_spirit_animal(
            speaker, rankings, info, drama, signature_words, comparison, gender
        )

        return {
            'name': info['name'],
            'party': party,
            'slug': info['slug'],
            'academicTitle': info['academicTitle'],
            'speeches': info['speeches'],
            'wortbeitraege': info['wortbeitraege'],
            'befragungResponses': info['befragungResponses'],
            'totalWords': info['totalWords'],
            'avgWords': info['avgWords'],
            'minWords': info['minWords'],
            'maxWords': info['maxWords'],
            'rankings': {
                'speechRank': rankings.get('speechRank', 0),
                'wordsRank': rankings.get('wordsRank', 0),
                'partySpeechRank': rankings.get('partySpeechRank', 0),
                'partyWordsRank': rankings.get('partyWordsRank', 0),
                'partySize': rankings.get('partySize', 0),
                'totalSpeakers': len(self._speaker_index),
                'percentile': rankings.get('speechPercentile', 0),
                # New rankings
                'verbosityRank': rankings.get('verbosityRank'),
                'verbosityTotal': rankings.get('verbosityTotal'),
                'partyVerbosityRank': rankings.get('partyVerbosityRank'),
                'longestSpeechRank': rankings.get('longestSpeechRank', 0),
            },
            'drama': drama,
            'words': words_data,
            'comparison': comparison,
            'funFacts': self._generate_fun_facts(speaker, party, drama),
            'signatureQuiz': signature_quiz,
            'signatureAdjectiveQuiz': signature_adjective_quiz,
            'spiritAnimal': spirit_animal,
            'toneProfile': self._speaker_tone_scores.get(speaker),
            'topics': self._speaker_topic_data.get(speaker),
        }

    def generate_index(self) -> dict:
        """Generate the speakers index file."""
        speakers = sorted(
            [
                {
                    'slug': info['slug'],
                    'name': info['name'],
                    'party': info['party'],
                    'speeches': info['speeches'],
                    'wortbeitraege': info['wortbeitraege'],
                    'befragungResponses': info['befragungResponses'],
                    'words': info['totalWords'],
                }
                for info in self._speaker_index.values()
            ],
            key=lambda x: x['speeches'],
            reverse=True
        )

        return {
            'speakers': speakers,
            'totalSpeakers': len(speakers),
            'parties': sorted(set(info['party'] for info in self._speaker_index.values())),
        }

    def _export_speaker(self, speaker: str, output_dir: Path) -> int:
        """Export a single speaker file. Returns 1 if exported, 0 otherwise."""
        data = self.generate_speaker_data(speaker)
        if data:
            slug = data['slug']
            speaker_path = output_dir / f"{slug}.json"
            speaker_path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))
            return 1
        return 0

    def export_all(self, output_dir: Path) -> dict:
        """Export index and all individual speaker files.

        Uses orjson for fast serialization and ThreadPoolExecutor for parallel I/O.

        Returns:
            Dict with export statistics
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export index using orjson
        index = self.generate_index()
        index_path = output_dir / "index.json"
        index_path.write_bytes(orjson.dumps(index, option=orjson.OPT_INDENT_2))

        # Export individual speaker files in parallel
        speakers = list(self._speaker_index.keys())
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(
                lambda s: self._export_speaker(s, output_dir),
                speakers
            ))
        exported = sum(results)

        # Clean up stale files that no longer correspond to valid speakers
        valid_slugs = {self._speaker_index[s]['slug'] for s in speakers}
        valid_slugs.add("index")  # Don't delete index.json
        stale_deleted = 0
        for json_file in output_dir.glob("*.json"):
            slug = json_file.stem
            if slug not in valid_slugs:
                json_file.unlink()
                stale_deleted += 1

        return {
            'index_path': str(index_path),
            'speakers_exported': exported,
            'stale_deleted': stale_deleted,
            'output_dir': str(output_dir),
        }
