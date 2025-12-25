"""Classify speech type based on how the speech starts.

Analyzes the opening content of a speech to determine its type
(formal speech, question, intervention, etc.).
"""

import re


# Pattern lists for different speech types
FRAGESTUNDE_INDICATORS = [
    r'(ich habe|habe ich)\s+(eine\s+)?(nach)?frage',
    r'meine\s+(nach)?frage',
    r'(eine\s+)?zusatzfrage',
    r'ich möchte.*fragen',
    r'darf ich.*fragen',
    r'ich frage\s+(sie|die|den|nach)',  # Exclude rhetorical "Ich frage mich"
]

PRESIDENT_PATTERNS = [
    r'(sehr geehrte[r]?\s+)?(frau|herr)\s+(vize)?präsident',
    r'(sehr geehrte[r]?\s+)?(frau|herr)\s+alterspräsident',
    r'(sehr geehrte[r]?|hochverehrte[r]?)\s+(vize)?präsident',  # without Frau/Herr
    r'(sehr geehrte[r]?|hochverehrte[r]?)\s+alterspräsident',
]

PRAESIDIUM_PATTERN = r'(sehr geehrtes?|verehrtes?|hochverehrtes?|wertes?)\s+präsidium'

BUNDESTAGSPRAESIDENT_PATTERNS = [
    r'^(sehr geehrte[r]?\s+|liebe[r]?\s+)?(frau\s+)?bundestagspräsident',
    r'^liebe[r]?\s+kolleginnen',
]

ABSTIMMUNG_PATTERNS = [
    r'^ich stimme dem',
    r'^dem (sogenannten\s+)?rentenpaket',
    r'^ich habe dem haushaltsgesetz',
    r'^die heutige abstimmung',
    r'^2016 wurde die möglichkeit',
    r'^als abgeordnete.*überzeugung',
]

STATEMENT_PATTERNS = [
    r'^eine echte migrationswende',
    r'^die frage der wehrpflicht',
    r'^sämtliche rentenreformpläne',
    r'^die einzige bedrohung',
    r'^wenn ich das gesundheitssystem',
]

PROTOKOLL_PATTERNS = [
    r'^wir benötigen',
    r'^heute berät der bundestag',
    r'^der vorliegende gesetzentwurf',
    r'^die bedrohungslage',
    r'^wir reden über den haushalt',
    r'^ich will die europäische',
]

ZWISCHENFRAGE_PATTERNS = [
    r'^(sehr geehrte[r]?\s+)?(frau|herr)\s+kolleg',
    r'^(sehr geehrte[r]?\s+)?(frau|herr)\s+minister',
    r'^(sehr geehrte[r]?\s+)?(frau|herr)\s+bachmann',
    r'^(sehr verehrte[r]?\s+)?(frau|herr)\s+kolleg',
    r'^(liebe[r]?\s+)(frau|herr)\s+kolleg',
    r'^(liebe[r]?\s+)boris',
    r'^frau kollegin',
    r'^frau von storch',
    r'^herr kollege',
    r'^weil frau',
    r'^ich mache schon',
    r'^ich muss ihnen',
    r'^ich nehme zur kenntnis',
    r'^also,',
    r'^ihrer frage liegt',
    r'^und zum antrag',
    r'^gut, dass sie',
    r'^erst mal finde ich',
    r'^ich bin, ehrlich gesagt',
    r'^wissen sie, ihre',
    r'^auch der kollege',
    r'^im moment (nicht|sind wir)',
    r'^die erklärung dafür',
    r'^herr kollege, ihnen',
    r'^es ist ein zitat',
    r'^ich würde gern zu ende',
    r'^jetzt müssen sie mir',
    r'^bei der letzten rede',
    r'^und diese müssen sich',
    r'^ich habe das in eine',
    r'^wenn mein vorredner',
    r'^herr hahn, wenn ich',
    r'^es ist schier zum verzweifeln',
    r'^gut, dann spreche ich',
    r'^das hat zwar jetzt',
    r'^genau, das heißt',
    r'^wie mein vorredner',
    r'^das war ein nein',
    r'^jungs, die ohren',
    r'^erstens\.',
    r'^man kann in dieser',
    r'^- nein, danke',
    r'^wie sie hier so',
    r'^ist ja ganz schön',
]


def classify_speech_start(text: str) -> str:
    """Classify speech type based on how it starts.

    Returns one of:
        - 'rede': Formal speech addressing president/chair
        - 'prasidium': Speech addressing "Präsidium" (formal but different pattern)
        - 'erklaerung': Written statement/explanation of vote
        - 'ortskraefte': Coordinated statement about Ortskräfte
        - 'zwischenfrage': Response to intermediate question
        - 'fragestunde': Parliamentary question
        - 'other': Cannot classify
    """
    start = text[:300].lower()
    first_100 = text[:100].lower()

    # Check for Fragestunde/Regierungsbefragung questions first
    for p in FRAGESTUNDE_INDICATORS:
        if re.search(p, start):
            return 'fragestunde'

    # Zwischenfrage - asking permission for intermediate question
    # E.g., "Vielen Dank, dass Sie die Zwischenfrage zulassen"
    if 'zwischenfrage zulassen' in start[:200]:
        return 'zwischenfrage'

    # Continuation - end of interrupted speech, not a new speech
    # E.g., "- ich komme zum Schluss; der letzte Satz, Frau Präsidentin"
    if re.match(r'^-?\s*(ich komme zum schluss|der letzte satz|zum schluss)', first_100):
        return 'continuation'

    # Interruption - not a formal speech
    # E.g., "Frau Präsidentin, ich unterbreche den eigenen Redner nur ungern"
    if 'ich unterbreche' in first_100:
        return 'continuation'

    # Question to specific minister by name
    # E.g., "eine Frage an den Bundesfinanzminister Klingbeil"
    if re.search(r'eine frage an (den|die|das)\s+\w*(minister|staatssekretär)', start[:300]):
        return 'fragestunde'

    # Check for explicit "Nachfrage" (follow-up question)
    if 'nachfrage' in start[:200]:
        return 'fragestunde'

    # CRITICAL: Formal speech starts with "Sehr geehrte/r ... Präsident" → rede
    # This takes priority over minister mentions because ministers are greeted, not questioned
    # E.g., "Sehr geehrte Frau Präsidentin! Sehr geehrter Herr Bundesminister!"
    if re.search(r'^sehr geehrte[r]?\s+(frau|herr)\s+(vize)?präsident', first_100):
        return 'rede'

    # Minister/Staatssekretär address WITHOUT formal president intro → Fragestunde question
    # Pattern: "Vielen Dank, Herr Präsident. - Frau Ministerin..." (informal → question)
    # Matches: Minister, Ministerin, Staatsminister, Staatssekretär, Bundesminister
    if re.search(r'(frau|herr)\s+(staats)?(minister|sekretär|bundesminister)', start[:300]):
        return 'fragestunde'

    # Pattern 1: Formal speech addressing Präsident/in (other patterns)
    for p in PRESIDENT_PATTERNS:
        if re.search(p, start):
            return 'rede'

    # Pattern 2: Speech addressing "Präsidium" (also formal)
    if re.search(PRAESIDIUM_PATTERN, start):
        return 'rede'  # Count as rede since it's formal

    # Pattern 3: Speech starting with "Bundestagspräsidentin" or similar
    for p in BUNDESTAGSPRAESIDENT_PATTERNS:
        if re.search(p, first_100):
            return 'rede'

    # Pattern 4a: Vote explanation (Erklärung zur Abstimmung)
    for p in ABSTIMMUNG_PATTERNS:
        if re.search(p, first_100):
            return 'abstimmung'

    # Pattern 4b: Policy statement (politische Erklärung)
    for p in STATEMENT_PATTERNS:
        if re.search(p, first_100):
            return 'statement'

    # Pattern 4c: Record statement (zu Protokoll)
    for p in PROTOKOLL_PATTERNS:
        if re.search(p, first_100):
            return 'protokoll'

    # Pattern 5: Coordinated Ortskräfte statement
    if 'deutschland hat in den vergangenen jahren' in start and 'ortskräfte' in start:
        return 'ortskraefte'

    # Pattern 6: Fragestunde question (written question read into record)
    if re.match(r'^(wie hoch|wie wird|welche|hat die|was |in welchem|existiert)', first_100):
        if 'bundesregierung' in start or 'bundesministerium' in start or 'anhörung' in start:
            return 'fragestunde'

    # Pattern 7: Direct answer/response (Zwischenfrage answer)
    if re.match(r'^(nein|ja)[.,!\s-]', first_100):
        return 'zwischenfrage'

    # Pattern 8: Response to colleague's question (Zwischenfrage)
    for p in ZWISCHENFRAGE_PATTERNS:
        if re.search(p, first_100):
            return 'zwischenfrage'

    # Pattern 9: Continuation or response without formal address
    # Distinguish between formal speeches and Fragestunde questions:
    # - "Vielen Dank, Herr Präsident! Liebe Kolleginnen..." → rede
    # - "Vielen Dank, Herr Präsident. – Frau Ministerin..." → fragestunde (question to minister)
    if re.match(r'^(vielen dank|herzlichen dank|danke)', first_100):
        # If addressing a minister/staatssekretär early → Fragestunde question
        if re.search(r'(frau|herr)\s+(minister|staatssekretär|bundesminister)', start[:200]):
            return 'fragestunde'
        # If addressing president then mentions "für die frage" → answer to question
        if re.search(r'für (die|ihre) frage', start[:200]):
            return 'fragestunde_antwort'
        # If addressing president without minister → formal speech
        if 'präsident' in start:
            return 'rede'
        return 'zwischenfrage'

    # Pattern 10: Personal statement starting with "Meine Damen und Herren" without president
    if re.match(r'^meine damen und herren', first_100):
        return 'rede'

    return 'other'


def starts_with_president_address(text: str) -> bool:
    """Check if speech starts with addressing the president/chair.

    Legacy function - use classify_speech_start() for more detail.
    """
    return classify_speech_start(text) == 'rede'
