"""Classify speech type based on surrounding context.

Analyzes the text BEFORE a speaker's name to determine if this is
a formal speech or an intervention.
"""

import re


def classify_speech_type(context: str) -> str:
    """Classify speech introduction type from preceding context.

    Looks at the text BEFORE a speaker's name to determine if this is
    a formal speech (Rede) or an intervention (Zwischenfrage, question time, etc.).

    Returns one of:
        - 'formal': Real Rede with "Wort erteilen" pattern
        - 'question': Fragestunde/Nachfrage question time
        - 'fragestunde': Fragestunde/Regierungsbefragung session
        - 'zwischenfrage': Intermediate question during speech
        - 'kurzintervention': Short intervention
        - 'continuation': End-of-speech continuation (not a new speech)
        - 'other': Cannot classify
    """
    # EXCLUDE: End-of-speech interruptions (continuation, not new speech)
    end_patterns = [
        r'Zeit ist abgelaufen',
        r'Redezeit ist abgelaufen',
        r'kommen Sie.*zum Ende',
        r'zum Ende.*Rede',
        r'müssen zum Ende',
        r'bitte zum Schluss',
    ]
    for p in end_patterns:
        if re.search(p, context, re.IGNORECASE):
            return 'continuation'

    # Intervention patterns (not formal speeches)
    if 'Kurzintervention' in context:
        return 'kurzintervention'
    if 'Zwischenfrage' in context or 'Gelegenheit, zu antworten' in context:
        return 'zwischenfrage'
    if re.search(r'[Ll]assen Sie.*zu\?|[Gg]estatten Sie|[Ee]rlauben Sie', context):
        return 'zwischenfrage'
    if 'Nachfrage' in context or 'Fragesteller' in context or 'weitere Frage' in context:
        return 'question'
    if 'Regierungsbefragung' in context or 'Fragestunde' in context:
        return 'fragestunde'

    # Formal speech patterns (real Reden)
    formal_patterns = [
        r'eröffne.*Aussprache',
        r'erteile.*(?:das\s+)?Wort',
        r'Das Wort hat',
        r'hat (?:jetzt |nun )?(?:das )?Wort',
        r'das Wort geben',
        r'darf ich aufrufen',
        r'[Nn]ächste[rn]?\s+Rede',
        r'[Nn]ächste[rn]?\s+Redner',
        r'rufe.*auf',
        r'bitte.*ans Mikrofon',
        r'erste Rede',
        r'spricht.*(?:Kolleg|Abgeordnet)',
        r'Für die.*Fraktion (?:hat|spricht)',
    ]
    for p in formal_patterns:
        if re.search(p, context):
            return 'formal'

    return 'other'


def classify_by_preceding_context(text: str, speech_start: int) -> str | None:
    """Classify speech type based on text BEFORE the speech.

    This uses structural markers from the protocol (president introductions)
    to reliably identify Fragestunde questions and answers.

    Args:
        text: Full protocol text
        speech_start: Position where the speech begins

    Returns:
        Speech type ('fragestunde', 'fragestunde_antwort') or None if not determinable
    """
    # Get context before the speech (last 600 chars)
    context = text[max(0, speech_start - 600):speech_start].lower()

    # Pattern 1: Formal question announcement
    # "Ich rufe die Frage X des Abgeordneten Y auf"
    if re.search(r'ich rufe die frage \d+', context):
        return 'fragestunde'

    # Pattern 2: Question introduction variants
    # "Die nächste Hauptfrage stellt..." / "Die nächste Frage stellt..."
    if re.search(r'die nächste (haupt)?frage stellt', context):
        return 'fragestunde'

    # Pattern 3: Follow-up question invitation
    # "ob es eine Nachfrage gibt" / "eine weitere Frage"
    if re.search(r'(nachfrage gibt|weitere frage gibt|nachfrage\s*\.\s*–)', context):
        return 'fragestunde'

    # Pattern 3: Government official answer invitation
    # "Sie haben das Wort" with Staatsminister/Staatssekretär in the SAME sentence
    if re.search(r'(herr|frau)\s+(staatsminister|staatssekretär|bundesminister)[^.]*sie haben das wort', context):
        return 'fragestunde_antwort'
    if re.search(r'sie haben das wort[^.]{0,50}(staatsminister|staatssekretär|bundesminister)', context):
        return 'fragestunde_antwort'

    return None
