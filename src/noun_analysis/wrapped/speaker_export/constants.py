"""Constants for speaker export module.

Contains spirit animal definitions, scoring criteria, quiz distractors,
and pre-compiled patterns/sets for word analysis.
"""

import re

from noun_analysis.lexicons import ADJECTIVE_LEXICONS, VERB_LEXICONS, TOPIC_LEXICONS, TopicCategory

# Pre-compiled regex pattern for word tokenization (4+ char words)
WORD_PATTERN = re.compile(r'\b[a-zäöüß]{4,}\b')

# Pre-built adjective set from lexicons
ADJECTIVE_SET: set[str] = set()
for _category_words in ADJECTIVE_LEXICONS.values():
    ADJECTIVE_SET.update(_category_words)

# Pre-built verb set from lexicons (for tone analysis)
VERB_SET: set[str] = set()
for _category_words in VERB_LEXICONS.values():
    VERB_SET.update(_category_words)

# Pre-built topic sets from lexicons (for Scheme F topic analysis)
# Maps each word to its primary topic category
TOPIC_WORD_TO_CATEGORY: dict[str, TopicCategory] = {}
for _topic, _topic_words in TOPIC_LEXICONS.items():
    for _word in _topic_words:
        TOPIC_WORD_TO_CATEGORY[_word] = _topic

# All topic nouns as a single set (for quick membership check)
TOPIC_NOUN_SET: set[str] = set(TOPIC_WORD_TO_CATEGORY.keys())

# Quiz distractor words (module-level constants to avoid recreation)
WORD_DISTRACTORS = [
    'bundesregierung', 'gesetzentwurf', 'abstimmung', 'fraktion',
    'antrag', 'haushalt', 'debatte', 'koalition', 'opposition',
    'minister', 'kanzler', 'ausschuss', 'gesetz', 'reform',
    'wirtschaft', 'sicherheit', 'zukunft', 'bürger', 'arbeit',
    'bildung', 'energie', 'klima', 'europa', 'migration',
    'demokratie', 'freiheit', 'verantwortung', 'politik', 'gesellschaft',
    'familie', 'kinder', 'rente', 'steuern', 'investitionen',
]

ADJECTIVE_DISTRACTORS = [
    "wichtig", "notwendig", "erfolgreich", "stark", "sicher", "klar",
    "falsch", "gefährlich", "problematisch", "schlecht", "sozial",
    "wirtschaftlich", "politisch", "europäisch", "national",
    "richtig", "gut", "groß", "neu", "jung", "alt",
]

# Spirit Animal definitions - all positive characterizations!
# Includes gendered title variants: title (male), title_f (female), title_n (neutral/unknown)
SPIRIT_ANIMALS = {
    # Tier 1: Elite Achievers
    "elefant": {
        "emoji": "🐘",
        "name": "Elefant",
        "title": "Wortgewaltiger Redner",
        "title_f": "Wortgewaltige Rednerin",
        "title_n": "Wortgewaltige:r Redner:in",
        "reason": "Mit {words} Wörtern gehörst du zu den wortreichsten Abgeordneten.",
    },
    "adler": {
        "emoji": "🦅",
        "name": "Adler",
        "title": "Parlamentarischer Überflieger",
        "title_f": "Parlamentarische Überfliegerin",
        "title_n": "Parlamentarische:r Überflieger:in",
        "reason": "Top {speech_rank} bei Reden UND Top {words_rank} bei Wörtern – ein echter Überflieger!",
    },
    "loewe": {
        "emoji": "🦁",
        "name": "Löwe",
        "title": "Fraktionsstimme",
        "title_f": "Fraktionsstimme",
        "title_n": "Fraktionsstimme",
        "reason": "Als #{party_rank} in der {party}-Fraktion bist du eine führende Stimme.",
    },
    # Tier 2: Specialists
    "eule": {
        "emoji": "🦉",
        "name": "Eule",
        "title": "Themenexperte",
        "title_f": "Themenexpertin",
        "title_n": "Themenexpert:in",
        "reason": "Dein Fachwort \"{signature_word}\" nutzt du {ratio}× häufiger als deine Fraktion.",
    },
    "pfau": {
        "emoji": "🦚",
        "name": "Pfau",
        "title": "Eloquenter Redner",
        "title_f": "Eloquente Rednerin",
        "title_n": "Eloquente:r Redner:in",
        "reason": "Mit Ø {avg_words} Wörtern pro Rede gehörst du zu den ausführlichsten Rednern.",
    },
    "wolf": {
        "emoji": "🐺",
        "name": "Wolf",
        "title": "Mutiger Einwerfer",
        "title_f": "Mutige Einwerferin",
        "title_n": "Mutige:r Einwerfer:in",
        "reason": "Mit {interruptions} Zwischenrufen mischst du aktiv in Debatten mit.",
    },
    "baer": {
        "emoji": "🐻",
        "name": "Bär",
        "title": "Standhafter Debattierer",
        "title_f": "Standhafte Debattiererin",
        "title_n": "Standhafte:r Debattierer:in",
        "reason": "Trotz {interrupted}× unterbrochen zu werden, bleibst du standhaft.",
    },
    "papagei": {
        "emoji": "🦜",
        "name": "Papagei",
        "title": "Neugieriger Fragesteller",
        "title_f": "Neugierige Fragestellerin",
        "title_n": "Neugierige:r Fragesteller:in",
        "reason": "Mit vielen Fragen bringst du wichtige Themen auf den Tisch.",
    },
    # Tier 3: Work Styles
    "pferd": {
        "emoji": "🐴",
        "name": "Pferd",
        "title": "Fleißiger Debattierer",
        "title_f": "Fleißige Debattiererin",
        "title_n": "Fleißige:r Debattierer:in",
        "reason": "Mit {speeches} Reden gehörst du zu den aktivsten Abgeordneten.",
    },
    "kolibri": {
        "emoji": "🐦",
        "name": "Kolibri",
        "title": "Präziser Wortführer",
        "title_f": "Präzise Wortführerin",
        "title_n": "Präzise:r Wortführer:in",
        "reason": "Viele Redebeiträge, aber immer auf den Punkt gebracht.",
    },
    "delfin": {
        "emoji": "🐬",
        "name": "Delfin",
        "title": "Diplomatischer Redner",
        "title_f": "Diplomatische Rednerin",
        "title_n": "Diplomatische:r Redner:in",
        "reason": "Aktiv im Parlament, aber respektvoll ohne viele Zwischenrufe.",
    },
    "schwan": {
        "emoji": "🦢",
        "name": "Schwan",
        "title": "Bedächtiger Redner",
        "title_f": "Bedächtige Rednerin",
        "title_n": "Bedächtige:r Redner:in",
        "reason": "Wenige, aber durchdachte und ausführliche Reden.",
    },
    "fuchs": {
        "emoji": "🦊",
        "name": "Fuchs",
        "title": "Cleverer Stratege",
        "title_f": "Clevere Strategin",
        "title_n": "Clevere:r Strateg:in",
        "reason": "Mit eigenem Vokabular hebst du dich von der Fraktion ab.",
    },
    # Tier 4: Steady Contributors
    "igel": {
        "emoji": "🦔",
        "name": "Igel",
        "title": "Beharrlicher Redner",
        "title_f": "Beharrliche Rednerin",
        "title_n": "Beharrliche:r Redner:in",
        "reason": "Auch wenn du oft unterbrochen wirst – du lässt dich nicht beirren.",
    },
    "schildkroete": {
        "emoji": "🐢",
        "name": "Schildkröte",
        "title": "Gründlicher Analyst",
        "title_f": "Gründliche Analystin",
        "title_n": "Gründliche:r Analyst:in",
        "reason": "Wenige Reden, aber wenn, dann richtig ausführlich.",
    },
    "eichhoernchen": {
        "emoji": "🐿️",
        "name": "Eichhörnchen",
        "title": "Themenhüter",
        "title_f": "Themenhüterin",
        "title_n": "Themenhüter:in",
        "reason": "Du hast deine Spezialthemen, die du immer wieder einbringst.",
    },
    "biene": {
        "emoji": "🐝",
        "name": "Biene",
        "title": "Fleißiger Abgeordneter",
        "title_f": "Fleißige Abgeordnete",
        "title_n": "Fleißige:r Abgeordnete:r",
        "reason": "Zuverlässig und engagiert – ein wichtiger Teil des Parlaments.",
    },
    # Tone-influenced animals (require sufficient speech data)
    "tiger": {
        "emoji": "🐅",
        "name": "Tiger",
        "title": "Wortgewaltiger Kämpfer",
        "title_f": "Wortgewaltige Kämpferin",
        "title_n": "Wortgewaltige:r Kämpfer:in",
        "reason": "Mit {words} Wörtern und klarer Kante dominierst du Debatten.",
    },
    "biber": {
        "emoji": "🦫",
        "name": "Biber",
        "title": "Konstruktiver Brückenbauer",
        "title_f": "Konstruktive Brückenbauerin",
        "title_n": "Konstruktive:r Brückenbauer:in",
        "reason": "Du baust Brücken zwischen Positionen – kooperativ und lösungsorientiert.",
    },
    "krabbe": {
        "emoji": "🦀",
        "name": "Krabbe",
        "title": "Hartnäckiger Debattierer",
        "title_f": "Hartnäckige Debattiererin",
        "title_n": "Hartnäckige:r Debattierer:in",
        "reason": "Du hältst an deinen Positionen fest und lässt nicht locker.",
    },
    "otter": {
        "emoji": "🦦",
        "name": "Otter",
        "title": "Positiver Teamplayer",
        "title_f": "Positive Teamplayerin",
        "title_n": "Positive:r Teamplayer:in",
        "reason": "Du bringst gute Stimmung und konstruktive Beiträge ins Plenum.",
    },
    "hase": {
        "emoji": "🐇",
        "name": "Hase",
        "title": "Wendiger Optimist",
        "title_f": "Wendige Optimistin",
        "title_n": "Wendige:r Optimist:in",
        "reason": "Mit positivem Blick reagierst du schnell auf neue Themen.",
    },
}

# Criteria for best-fit animal scoring (used in Phase 2 of assignment)
# Each metric has: weight (importance), scale (expected max for normalization)
# Optional: "min" (disqualifies if below), "inverse" (lower is better)
ANIMAL_CRITERIA: dict[str, dict] = {
    # === SPECIALISTS ===
    "eule": {  # Topic expert with distinctive vocabulary
        "sig_ratio": {"weight": 0.5, "scale": 500},
        "sig_word_count": {"weight": 0.3, "scale": 5},
        "speeches": {"min": 5, "weight": 0.2, "scale": 20},
    },
    "wolf": {  # Aggressive interrupter
        "interruptions_given": {"weight": 0.6, "scale": 25},
        "aggression": {"weight": 0.25, "scale": 20},
        "speeches": {"min": 2, "weight": 0.15, "scale": 10},
    },
    "papagei": {  # Curious questioner (proxy: specific vocabulary + concise)
        "sig_word_count": {"weight": 0.4, "scale": 3},
        "speeches": {"weight": 0.3, "scale": 8},
        "avg_words": {"weight": 0.3, "scale": 400, "inverse": True},
    },
    "baer": {  # Often interrupted, stands ground
        "interruptions_received": {"weight": 0.7, "scale": 25},
        "speeches": {"min": 4, "weight": 0.2, "scale": 12},
        "authority": {"weight": 0.1, "scale": 100},
    },
    "pfau": {  # Verbose, eloquent
        "avg_words": {"weight": 0.5, "scale": 800},
        "speeches": {"min": 3, "weight": 0.3, "scale": 12},
        "affirmative": {"weight": 0.2, "scale": 100},
    },
    "otter": {  # Positive, collaborative
        "affirmative": {"weight": 0.4, "scale": 100},
        "collaboration": {"weight": 0.3, "scale": 100},
        "solution_focus": {"weight": 0.3, "scale": 100},
    },

    # === WORK STYLES ===
    "pferd": {  # Active debater, many speeches
        "speeches": {"weight": 0.5, "scale": 15},
        "total_words": {"weight": 0.3, "scale": 8000},
        "interruptions_given": {"weight": 0.2, "scale": 20},
    },
    "kolibri": {  # Frequent but concise
        "speeches": {"min": 5, "weight": 0.5, "scale": 12},
        "avg_words": {"weight": 0.5, "scale": 300, "inverse": True},
    },
    "delfin": {  # Diplomatic, low conflict
        "speeches": {"min": 2, "weight": 0.25, "scale": 10},
        "interruptions_given": {"weight": 0.35, "scale": 5, "inverse": True},
        "collaboration": {"weight": 0.4, "scale": 100},
    },
    "biber": {  # Collaborative bridge-builder
        "collaboration": {"weight": 0.4, "scale": 100},
        "solution_focus": {"weight": 0.3, "scale": 100},
        "interruptions_given": {"weight": 0.3, "scale": 15, "inverse": True},
    },
    "schwan": {  # Few but long, thoughtful speeches
        "avg_words": {"weight": 0.5, "scale": 900},
        "speeches": {"weight": 0.3, "scale": 4, "inverse": True},
        "solution_focus": {"weight": 0.2, "scale": 100},
    },
    "fuchs": {  # Clever, unique vocabulary
        "sig_word_count": {"weight": 0.5, "scale": 5},
        "sig_ratio": {"weight": 0.3, "scale": 200},
        "speeches": {"min": 3, "weight": 0.2, "scale": 15},
    },
    "krabbe": {  # Demanding, persistent
        "demand_intensity": {"weight": 0.5, "scale": 25},
        "speeches": {"min": 2, "weight": 0.3, "scale": 10},
        "authority": {"weight": 0.2, "scale": 100},
    },

    # === STEADY CONTRIBUTORS ===
    "igel": {  # Resilient, often interrupted but persists
        "interruptions_received": {"weight": 0.5, "scale": 20},
        "speeches": {"min": 2, "weight": 0.3, "scale": 8},
        "affirmative": {"weight": 0.2, "scale": 100},
    },
    "schildkroete": {  # Thorough, methodical
        "avg_words": {"weight": 0.4, "scale": 800},
        "speeches": {"weight": 0.3, "scale": 5, "inverse": True},
        "solution_focus": {"weight": 0.3, "scale": 100},
    },
    "eichhoernchen": {  # Topic collector, moderate activity
        "sig_word_count": {"weight": 0.5, "scale": 3},
        "speeches": {"weight": 0.3, "scale": 8},
        "total_words": {"weight": 0.2, "scale": 5000},
    },
    "hase": {  # Optimistic newcomer
        "affirmative": {"weight": 0.4, "scale": 100},
        "solution_focus": {"weight": 0.4, "scale": 100},
        "speeches": {"weight": 0.2, "scale": 8, "inverse": True},
    },

    # === DEFAULT ===
    "biene": {  # Reliable contributor (fallback)
        "speeches": {"weight": 0.5, "scale": 8},
        "total_words": {"weight": 0.5, "scale": 4000},
    },
}
