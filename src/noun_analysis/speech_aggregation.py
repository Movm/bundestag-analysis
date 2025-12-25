"""Speech aggregation and statistics.

Aggregates speech data by type and speaker for statistical analysis.
"""

from collections import Counter


def aggregate_speeches_by_type(speeches: list[dict]) -> dict:
    """Aggregate speech statistics by type and speaker.

    Takes a list of speech dicts (from parse_speeches_from_protocol) and
    builds per-party Counters for different speech types.

    Args:
        speeches: List of speech dicts with 'speaker', 'party', 'type', 'category' keys

    Returns:
        Dict with:
        - speaker_stats: {party: Counter(speaker -> count)} for formal speeches
        - formal_speaker_stats: Same as speaker_stats (backwards compat)
        - befragung_speaker_stats: {party: Counter} for Q&A responses
        - question_speaker_stats: {party: Counter} for Fragestunde questions
        - real_speech_counts: {party: count} of formal speeches
        - rede_counts: {party: count} of category='rede' speeches
        - wortbeitrag_counts: {party: count} of category='wortbeitrag' speeches
        - wortbeitrag_speaker_stats: {party: Counter(speaker -> count)} for wortbeitraege
    """
    speaker_stats = {}
    formal_speaker_stats = {}
    befragung_speaker_stats = {}
    question_speaker_stats = {}
    real_speech_counts = {}
    rede_counts = {}
    wortbeitrag_counts = {}
    wortbeitrag_speaker_stats = {}

    for speech in speeches:
        party = speech['party']
        speaker = speech['speaker']
        speech_type = speech['type']
        category = speech.get('category', 'rede' if speech_type == 'rede' else 'wortbeitrag')

        if party not in speaker_stats:
            speaker_stats[party] = Counter()
            formal_speaker_stats[party] = Counter()
            befragung_speaker_stats[party] = Counter()
            question_speaker_stats[party] = Counter()
            wortbeitrag_speaker_stats[party] = Counter()
            real_speech_counts[party] = 0
            rede_counts[party] = 0
            wortbeitrag_counts[party] = 0

        # Category-based counting (high-level)
        if category == 'rede':
            rede_counts[party] += 1
        else:
            wortbeitrag_counts[party] += 1
            wortbeitrag_speaker_stats[party][speaker] += 1

        # Formal speeches: 'rede' type (president-introduced with formal address)
        if speech_type == 'rede':
            speaker_stats[party][speaker] += 1
            formal_speaker_stats[party][speaker] += 1
            real_speech_counts[party] += 1

        # Befragung responses: government officials answering in Q&A sessions
        if speech_type in ('befragung', 'fragestunde_antwort'):
            befragung_speaker_stats[party][speaker] += 1

        # Question time: 'fragestunde' type
        if speech_type == 'fragestunde':
            question_speaker_stats[party][speaker] += 1

    return {
        "speaker_stats": speaker_stats,
        "formal_speaker_stats": formal_speaker_stats,
        "befragung_speaker_stats": befragung_speaker_stats,
        "question_speaker_stats": question_speaker_stats,
        "wortbeitrag_speaker_stats": wortbeitrag_speaker_stats,
        "real_speech_counts": real_speech_counts,
        "rede_counts": rede_counts,
        "wortbeitrag_counts": wortbeitrag_counts,
    }
