"""Adjective lexicons for semantic categorization.

Words are stored as lemmatized forms (lowercase) matching spaCy output.
"""

from .categories import AdjectiveCategory


ADJECTIVE_LEXICONS: dict[AdjectiveCategory, set[str]] = {
    AdjectiveCategory.AFFIRMATIVE: {
        # Strength/Success
        "stark", "erfolgreich", "wirksam", "effektiv", "leistungsfähig",
        "kompetent", "qualifiziert", "professionell", "zuverlässig",
        "kraftvoll", "tatkräftig", "verantwortungsvoll",
        # Safety/Security
        "sicher", "stabil", "geschützt", "bewährt", "solide",
        "verlässlich", "beständig",
        # Importance/Value
        "bedeutend", "wertvoll", "wesentlich", "zentral",
        "entscheidend", "maßgeblich", "grundlegend", "elementar",
        # Quality
        "hervorragend", "ausgezeichnet", "vorbildlich", "beispielhaft",
        "exzellent", "erstklassig", "hochwertig", "brillant",
        # Progress
        "innovativ", "zukunftsfähig", "fortschrittlich",
        "nachhaltig", "zukunftsweisend", "bahnbrechend",
        # Fairness
        "gerecht", "fair", "ausgewogen", "vernünftig", "angemessen",
        "sachlich", "konstruktiv", "lösungsorientiert",
        # Social
        "solidarisch", "sozial", "menschlich", "würdig",
        "respektvoll", "demokratisch", "freiheitlich",
        # Economic
        "wirtschaftlich", "rentabel", "produktiv", "wettbewerbsfähig",
    },

    AdjectiveCategory.CRITICAL: {
        # Danger
        "gefährlich", "riskant", "bedrohlich", "kritisch", "prekär",
        "unsicher", "instabil",
        # Failure
        "gescheitert", "verfehlt", "misslungen", "fehlgeschlagen",
        "erfolglos", "wirkungslos",
        # Wrong
        "falsch", "irrig", "fehlerhaft", "mangelhaft",
        "unzutreffend", "irreführend",
        # Bad quality
        "schlecht", "schlimm", "übel", "miserabel", "katastrophal",
        "desaströs", "verheerend", "fatal",
        # Unacceptable
        "unhaltbar", "inakzeptabel",
        # Harmful
        "schädlich", "nachteilig", "destruktiv", "kontraproduktiv",
        "problematisch", "bedenklich",
        # Unfair
        "ungerecht", "unfair", "einseitig", "parteiisch",
        "willkürlich", "diskriminierend",
        # Weakness
        "schwach", "ineffektiv", "unzureichend",
        "ungenügend", "insuffizient", "inadäquat",
        # Economic
        "teuer", "kostspielig", "unbezahlbar", "verschwenderisch",
    },

    AdjectiveCategory.AGGRESSIVE: {
        # Absurdity/Ridicule
        "absurd", "lächerlich", "grotesk", "bizarr", "abwegig",
        "unsinnig", "wahnwitzig", "irrsinnig", "haarsträubend",
        "hanebüchen", "aberwitzig",
        # Irresponsibility
        "unverantwortlich", "fahrlässig", "rücksichtslos", "skrupellos",
        "verantwortungslos", "gewissenlos", "leichtsinnig",
        # Scandal
        "skandalös", "empörend", "unerhört", "unverschämt", "dreist",
        "ungeheuerlich", "unfassbar", "bodenlos", "schändlich",
        # Incompetence
        "inkompetent", "unfähig", "dilettantisch", "stümperhaft",
        "amateurhaft", "unprofessionell", "planlos", "kopflos",
        # Dishonesty
        "verlogen", "heuchlerisch", "scheinheilig", "unehrlich",
        "unglaubwürdig", "doppelzüngig", "korrupt", "betrügerisch",
        # Contempt
        "erbärmlich", "armselig", "kläglich", "jämmerlich",
        "peinlich", "beschämend", "blamabel",
        # Cynicism
        "zynisch",
    },

    AdjectiveCategory.LABELING: {
        # Ideological labeling
        "ideologisch", "ideologiegetrieben", "ideologieverblendet",
        # Political extremism labels
        "radikal", "extremistisch", "fanatisch", "fundamentalistisch",
        "verblendet", "verbohrt", "dogmatisch",
        # Left-right labels (when used pejoratively)
        "links", "linksradikal", "linksextrem", "linksgrün",
        "rechts", "rechtsradikal", "rechtsextrem", "rechtspopulistisch",
        # Movement labels
        "populistisch", "nationalistisch", "sozialistisch", "kommunistisch",
        "klimahysterisch", "klimaleugnerisch", "woke",
        # Othering
        "weltfremd", "realitätsfern", "abgehoben", "elitär",
        # Anti-system
        "staatsfeindlich", "verfassungsfeindlich",
    },
}
