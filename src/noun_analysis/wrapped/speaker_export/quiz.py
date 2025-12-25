"""Quiz generation mixin for speaker export."""

import random

from .constants import ADJECTIVE_DISTRACTORS, WORD_DISTRACTORS


class QuizGeneratorMixin:
    """Mixin for generating signature word/adjective quiz questions."""

    def _generate_signature_quiz(
        self, speaker: str, party: str, signature_words: list[dict]
    ) -> dict | None:
        """Generate a quiz question about the speaker's signature word."""
        if not signature_words:
            return None

        # The correct answer is the top signature word
        correct_word = signature_words[0]['word']
        ratio_party = signature_words[0]['ratioParty']
        ratio_bundestag = signature_words[0]['ratioBundestag']

        # Remove the correct answer and any other signature words from distractors
        signature_set = {w['word'] for w in signature_words}
        available_distractors = [w for w in WORD_DISTRACTORS if w not in signature_set]

        if len(available_distractors) < 3:
            return None

        # Pick 3 random distractors
        distractors = random.sample(available_distractors, 3)

        # Build options (correct answer + 3 distractors), shuffled
        options = [
            {'text': correct_word.capitalize(), 'isCorrect': True},
            {'text': distractors[0].capitalize(), 'isCorrect': False},
            {'text': distractors[1].capitalize(), 'isCorrect': False},
            {'text': distractors[2].capitalize(), 'isCorrect': False},
        ]
        random.shuffle(options)

        return {
            'question': f'Welches Wort nutzt {speaker} häufiger als der Rest der Fraktion?',
            'options': options,
            'explanationParty': f'"{correct_word.capitalize()}" nutzt {speaker} {ratio_party}× häufiger als der {party}-Durchschnitt.',
            'explanationBundestag': f'{ratio_bundestag}× häufiger als der Bundestag-Durchschnitt.',
        }

    def _generate_signature_adjective_quiz(
        self, speaker: str, party: str, signature_adjectives: list[dict]
    ) -> dict | None:
        """Generate a quiz question about the speaker's signature adjective."""
        if not signature_adjectives:
            return None

        # The correct answer is the top signature adjective
        correct_adj = signature_adjectives[0]['word']
        ratio_party = signature_adjectives[0]['ratioParty']
        ratio_bundestag = signature_adjectives[0]['ratioBundestag']

        # Remove the correct answer and any other signature adjectives from distractors
        signature_set = {a['word'] for a in signature_adjectives}
        available_distractors = [a for a in ADJECTIVE_DISTRACTORS if a not in signature_set]

        if len(available_distractors) < 3:
            return None

        # Pick 3 random distractors
        distractors = random.sample(available_distractors, 3)

        # Build options (correct answer + 3 distractors), shuffled
        options = [
            {'text': correct_adj.capitalize(), 'isCorrect': True},
            {'text': distractors[0].capitalize(), 'isCorrect': False},
            {'text': distractors[1].capitalize(), 'isCorrect': False},
            {'text': distractors[2].capitalize(), 'isCorrect': False},
        ]
        random.shuffle(options)

        return {
            'question': f'Welches Adjektiv nutzt {speaker} häufiger als der Rest der {party}-Fraktion?',
            'options': options,
            'explanationParty': f'"{correct_adj.capitalize()}" nutzt {speaker} {ratio_party}× häufiger als der {party}-Durchschnitt.',
            'explanationBundestag': f'{ratio_bundestag}× häufiger als der Bundestag-Durchschnitt.',
        }
