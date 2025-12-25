"""Verb lexicons for semantic categorization.

Words are stored as lemmatized forms (lowercase) matching spaCy output.
"""

from .categories import VerbCategory


VERB_LEXICONS: dict[VerbCategory, set[str]] = {
    VerbCategory.SOLUTION_ORIENTED: {
        # Support
        "unterstützen", "fördern", "stärken", "helfen", "beistehen",
        "assistieren", "beitragen", "mitwirken",
        # Building
        "aufbauen", "entwickeln", "gestalten", "schaffen", "errichten",
        "etablieren", "gründen", "initiieren",
        # Investment
        "bereitstellen", "zuweisen", "bewilligen",
        # Protection
        "schützen", "bewahren", "sichern", "verteidigen", "garantieren",
        "wahren", "erhalten",
        # Improvement
        "verbessern", "optimieren", "modernisieren", "reformieren",
        "erneuern", "weiterentwickeln", "ausbauen", "erweitern",
        # Solving
        "lösen", "beheben", "beseitigen", "überwinden", "meistern",
        # Enabling
        "ermöglichen", "erlauben", "eröffnen", "befähigen",
        "berechtigen", "freigeben",
        # Progress
        "vorankommen", "fortschreiten", "gelingen", "erreichen",
        "verwirklichen", "realisieren", "umsetzen",
        # Healing/Repair
        "heilen", "reparieren", "wiederherstellen", "sanieren",
        "rehabilitieren", "regenerieren",
        # Future
        "vorbereiten", "anstreben", "anvisieren",
        # Ensure
        "gewährleisten",
    },

    VerbCategory.PROBLEM_FOCUSED: {
        # Destruction
        "zerstören", "vernichten", "ruinieren", "demolieren",
        "kaputtmachen", "zunichtemachen", "zersetzen",
        # Reduction
        "kürzen", "streichen", "abbauen",
        "zusammenstreichen", "dezimieren",
        # Undermine
        "unterminieren",
        # Endangerment
        "gefährden", "bedrohen", "riskieren", "aufs-spiel-setzen",
        "untergraben", "aushöhlen",
        # Failure
        "versagen", "scheitern", "fehlschlagen", "versäumen",
        "vernachlässigen", "verpassen",
        # Harm
        "schaden", "schädigen", "beeinträchtigen",
        "schwächen", "beschädigen", "belasten",
        # Blocking
        "blockieren", "verhindern", "sabotieren", "torpedieren",
        "boykottieren", "obstruieren",
        # Escalation/Alarm
        "eskalieren", "verschlimmern", "verschlechtern",
        "verschärfen", "zuspitzen",
        # Collapse
        "zusammenbrechen", "kollabieren", "abstürzen", "einbrechen",
    },

    VerbCategory.COLLABORATIVE: {
        # Agreement
        "zustimmen", "einwilligen", "genehmigen", "billigen",
        "befürworten", "gutheißen",
        # Collaboration
        "zusammenarbeiten", "kooperieren", "mitwirken", "mitarbeiten",
        "partizipieren", "teilnehmen",
        # Compromise
        "einigen", "vermitteln", "ausgleichen", "annähern",
        "überbrücken", "versöhnen",
        # Dialogue
        "verhandeln", "beraten", "diskutieren", "austauschen",
        "konsultieren", "abstimmen",
        # Inclusion
        "einbeziehen", "einbinden", "beteiligen", "integrieren",
        "berücksichtigen", "respektieren",
    },

    VerbCategory.CONFRONTATIONAL: {
        # Attack
        "angreifen", "attackieren", "bekämpfen", "bekriegen",
        "anfechten", "anprangern",
        # Accusation
        "vorwerfen", "beschuldigen", "bezichtigen", "anklagen",
        "unterstellen", "verleumden", "diffamieren",
        # Criticism
        "kritisieren", "tadeln", "rügen", "beanstanden", "bemängeln",
        "monieren", "missbilligen",
        # Rejection
        "ablehnen", "zurückweisen", "verwerfen", "widersprechen",
        "verweigern", "abweisen", "abschmettern",
        # Blame
        "verurteilen", "brandmarken", "geißeln",
        # Discredit
        "diskreditieren", "verharmlosen",
        # Dispute
        "bestreiten", "anzweifeln", "infrage-stellen", "dementieren",
        "widerlegen",
        # Threat/Warning (confrontational context)
        "drohen", "androhen", "warnen", "mahnen",
    },

    VerbCategory.DEMANDING: {
        # Direct demands
        "fordern", "verlangen", "bestehen", "drängen", "pochen",
        "beharren", "insistieren",
        # Necessity/obligation
        "zwingen", "nötigen", "verpflichten",
        "auffordern", "auferlegen",
        # Advocate
        "eintreten-für",
        # Pressure
        "druck-machen", "unter-druck-setzen", "einfordern",
        "durchsetzen", "erzwingen",
        # Urging
        "aufrufen", "appellieren", "anmahnen", "ermahnen",
        "beschwören", "antreiben",
    },

    VerbCategory.ACKNOWLEDGING: {
        # Praise
        "loben", "würdigen", "honorieren", "wertschätzen",
        "anerkennen", "respektieren",
        # Thanks
        "danken", "bedanken", "verdanken",
        # Welcome
        "begrüßen", "willkommen-heißen", "freuen",
        # Recognition
        "gratulieren", "beglückwünschen", "feiern",
        # Appreciation
        "schätzen", "achten", "ehren", "hochachten",
    },
}
