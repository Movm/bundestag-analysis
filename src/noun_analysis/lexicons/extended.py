"""Extended lexicons (Scheme E) - Modal, Temporal, Intensity, Pronoun, Discriminatory.

These lexicons extend the basic adjective/verb analysis with additional dimensions
for analyzing communication style and potentially problematic language.
"""

from .categories import (
    ModalCategory,
    TemporalCategory,
    IntensityCategory,
    PronounCategory,
    DiscriminatoryCategory,
)


MODAL_LEXICONS: dict[ModalCategory, set[str]] = {
    ModalCategory.OBLIGATION: {
        # Direct obligation
        "müssen", "sollen", "haben",  # "haben zu"
        # Forced/required
        "brauchen", "gehören",  # "gehört gemacht"
        # Necessity expressions as verbs
        "verpflichten", "zwingen", "nötigen",
    },
    ModalCategory.POSSIBILITY: {
        # Permission/ability
        "können", "dürfen", "mögen",
        # Conditional
        "würden",  # Konjunktiv II
    },
    ModalCategory.INTENTION: {
        # Will/want
        "wollen", "werden", "beabsichtigen",
        "vorhaben", "planen", "anstreben",
        "möchten",
    },
}

TEMPORAL_LEXICONS: dict[TemporalCategory, set[str]] = {
    TemporalCategory.RETROSPECTIVE: {
        # Past tense auxiliaries (as lemmas they appear)
        "war", "wurden", "hatten", "gewesen",
        # Past-focused verbs
        "scheiterte", "versagte", "verfehlte",
        "vergaß", "unterließ", "versäumte",
        # Critical retrospection
        "hätte", "wäre",  # "hätte sollen", "wäre besser"
    },
    TemporalCategory.PROSPECTIVE: {
        # Future auxiliary
        "werden", "wird",
        # Future-oriented verbs
        "planen", "vorhaben", "beabsichtigen",
        "anstreben", "vorsehen", "vorbereiten",
        # Promise/commitment
        "versprechen", "zusagen", "garantieren",
        "sicherstellen", "gewährleisten",
    },
}

INTENSITY_LEXICONS: dict[IntensityCategory, set[str]] = {
    IntensityCategory.INTENSIFIER: {
        # Absolute intensifiers
        "absolut", "total", "komplett", "völlig", "vollständig",
        "gänzlich", "restlos", "hundertprozentig",
        # Extreme degree
        "extrem", "massiv", "enorm", "immens", "gewaltig",
        "unglaublich", "ungeheuer", "außerordentlich",
        # Superlatives
        "größte", "schlimmste", "beste", "höchste", "tiefste",
        # Emphatic
        "eindeutig", "offensichtlich", "zweifellos", "unbestreitbar",
        "definitiv", "fraglos", "unzweifelhaft",
        # Dramatic
        "dramatisch", "katastrophal", "desaströs", "verheerend",
        "historisch", "beispiellos", "einmalig",
    },
    IntensityCategory.MODERATOR: {
        # Hedging
        "etwas", "teilweise", "gewissermaßen", "bedingt",
        "möglicherweise", "vielleicht", "eventuell", "unter-umständen",
        # Nuance
        "tendenziell", "grundsätzlich", "prinzipiell", "im-wesentlichen",
        "überwiegend", "größtenteils", "weitgehend",
        # Qualification
        "relativ", "vergleichsweise", "verhältnismäßig", "einigermaßen",
        # Uncertainty markers
        "vermutlich", "wahrscheinlich", "offenbar", "anscheinend",
        "scheinbar", "mutmaßlich",
    },
}

PRONOUN_LEXICONS: dict[PronounCategory, set[str]] = {
    PronounCategory.INCLUSIVE: {
        # First person plural
        "wir", "uns", "unser", "unsere", "unserem", "unseren",
        # Collective terms
        "gemeinsam", "zusammen", "miteinander", "alle",
        "jeder", "jedermann", "sämtliche",
        # Unity language
        "land", "gesellschaft", "gemeinschaft", "bürger",
        "bevölkerung", "volk",  # neutral collective uses
    },
    PronounCategory.EXCLUSIVE: {
        # Third person (opposition reference)
        "sie", "ihnen", "ihr", "ihre", "deren", "denen",
        # Distancing
        "jene", "diese", "solche",
        # Explicit othering phrases (as words that appear)
        "regierung",  # "diese Regierung" pattern
        "koalition",  # "diese Koalition" pattern
        "ampel",  # Ampel-Koalition reference
    },
}

DISCRIMINATORY_LEXICONS: dict[DiscriminatoryCategory, set[str]] = {
    DiscriminatoryCategory.XENOPHOBIC: {
        # Anti-foreigner framing
        "überfremdung", "masseneinwanderung", "massenmigration",
        "migrationswelle", "flüchtlingswelle", "asylflut",
        "einwanderungsflut", "migrantenkriminalität",
        # Othering nationality terms (when used pejoratively)
        "ausländerkriminalität", "ausländergewalt",
        # Border/control framing
        "kontrollverlust",
    },
    DiscriminatoryCategory.HOMOPHOBIC: {
        # Anti-LGBTQ+ terminology
        "genderideologie", "genderwahn", "gendergaga",
        "frühsexualisierung", "regenbogenideologie",
        "transideologie", "transwahn",
        # Traditional family framing (when used to exclude)
        "gendersprache", "gendersternchen",
    },
    DiscriminatoryCategory.ISLAMOPHOBIC: {
        # Clearly loaded/fear-mongering terms only
        # (Neutral terms like 'islamismus', 'scharia', 'parallelgesellschaft' removed)
        "islamisierung", "islamofaschismus", "kopftuchzwang",
    },
    DiscriminatoryCategory.DOG_WHISTLE: {
        # Coded extremist terms (Great Replacement theory)
        "bevölkerungsaustausch", "umvolkung", "großer-austausch",
        "remigration", "rückführungsoffensive",
        # Volkisch/nationalist coding
        "ethnokulturell", "biodeutsch", "passdeutsch",
        "altparteien", "systemmedien", "lügenpresse",
        # Conspiracy framing
        "globalisten", "eliten", "davos",
        "great-reset", "plandemie",
        # Dehumanizing
        "asyltourismus", "volksverräter",
    },
}
