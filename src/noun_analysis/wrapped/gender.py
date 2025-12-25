"""Gender detection for German first names.

Uses a built-in dictionary of German first names with gender information,
plus heuristics for unknown names and support for custom overrides.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import json
import logging

Gender = Literal["male", "female", "unknown"]

logger = logging.getLogger(__name__)


@dataclass
class GenderResult:
    """Result of gender detection."""

    gender: Gender
    confidence: float  # 0.0 - 1.0
    source: str  # "dictionary", "manual", "heuristic", "unknown"


class GenderDetector:
    """Detect gender from German first names.

    Lookup order:
    1. Custom mappings (manual overrides)
    2. Built-in German name dictionary
    3. Heuristic fallback (German name endings)
    4. Mark as unknown and log for review
    """

    # Common German male first names
    # Compiled from Bundestag member lists and common German names
    MALE_NAMES: set[str] = {
        # A
        "achim", "adalbert", "adam", "adrian", "albrecht", "alexander", "alexej",
        "alfons", "alfred", "ali", "alois", "amin", "andreas", "andrej", "andrew",
        "andré", "ansgar", "anton", "armand", "armin", "arnd", "arndt", "arne",
        "arno", "arnold", "arthur", "artur", "axel",
        # B
        "bastian", "benedikt", "benjamin", "bengt", "benno", "bernd", "bernhard",
        "bert", "berthold", "bertram", "bijan", "björn", "boris", "bruno", "burkhard",
        "burkhardt",
        # C
        "carl", "carlos", "carsten", "chris", "christian", "christoph", "christos",
        "christopher", "claus", "clemens", "curt",
        # D
        "daniel", "david", "dennis", "detlef", "detlev", "dierk", "dieter",
        "diethelm", "dietmar", "dietrich", "dirk", "dominik", "dominique",
        # E
        "eberhard", "eckard", "eckart", "eckhard", "eckhart", "edgar", "edmund",
        "eduard", "edwin", "egon", "eike", "ekkehard", "elmar", "enak", "enrico",
        "erhard", "eric", "erich", "erik", "ernst", "erwin", "eugen",
        # F
        "fabian", "falko", "felix", "ferdinand", "florian", "frank", "franz",
        "fred", "frederik", "fridolin", "friedbert", "friedemann", "frieder",
        "friedhelm", "friedrich", "fritz",
        # G
        "gabriel", "georg", "gereon", "gerald", "gerd", "gerhard", "gerhart",
        "gernot", "gero", "gerold", "gerrit", "gitta", "gottfried", "gotthard",
        "gregor", "günter", "günther", "guido", "gunther", "gustav", "götz",
        # H
        "hagen", "hakan", "hannes", "hanno", "hans", "hansgeorg", "hansjörg",
        "hansjürgen", "harald", "hartmut", "hartwig", "heiko", "heiner", "heinrich",
        "heinz", "helge", "hellmut", "helmut", "hendrik", "henning", "henry",
        "herbert", "heribert", "hermann", "hieronymus", "hilmar", "hinrich",
        "holger", "horst", "hubert", "hubertus", "hugo",
        # I
        "ingo", "ingolf", "iwan",
        # J
        "jakob", "jan", "janosch", "jannik", "janos", "jens", "jeremias", "joachim",
        "jochem", "jochen", "joe", "johann", "johannes", "jonas", "jonathan",
        "josef", "joseph", "josip", "jost", "jörg", "jörn", "jürgen", "julian",
        "julius", "justus",
        # K
        "kai", "karl", "karlheinz", "karsten", "kaspar", "kay", "kees", "kevin",
        "kilian", "klaus", "knut", "konrad", "konstantin", "kristian", "kurt",
        # L
        "lars", "leif", "lennard", "lennart", "leo", "leon", "leonard", "leonhard",
        "lorenz", "lothar", "luca", "lucas", "ludger", "ludwig", "lukas", "lutz",
        # M
        "maik", "malte", "manfred", "manuel", "marc", "marcel", "marco", "marcus",
        "mario", "marius", "mark", "marlon", "markus", "martin", "mathias",
        "matthias", "max", "maximilian", "metin", "michael", "michel", "mike",
        "mirko", "moritz", "muhanad",
        # N
        "nico", "nicolai", "nicolas", "niels", "niklas", "nils", "norbert",
        # O
        "olaf", "olav", "oliver", "omid", "ortwin", "oscar", "oskar", "oswald",
        "ottmar", "otto",
        # P
        "pascal", "patrick", "paul", "peter", "petr", "philip", "philipp", "pio",
        # Q
        "quentin",
        # R
        "rafael", "rainer", "ralf", "ralph", "randolf", "raphael", "rasmus",
        "reginald", "reiner", "reinhard", "reinhold", "rené", "richard",
        "robert", "robin", "roger", "roland", "rolf", "roman", "ronald", "ruben",
        "rüdiger", "rudolf", "rupert", "ruprecht",
        # S
        "sascha", "sebastian", "sepp", "siegbert", "siegfried", "siegmund", "sigmar",
        "simon", "sönke", "sören", "stefan", "steffen", "stephan", "sven",
        # T
        "thies", "thilo", "thomas", "thorsten", "tibor", "till", "tilman", "tilmann",
        "tim", "timo", "timon", "tino", "tobias", "tom", "toralf", "torben",
        "torsten", "tristan",
        # U
        "udo", "ulf", "uli", "ulrich", "uwe",
        # V
        "valentin", "victor", "viktor", "vincent", "vinzenz", "volker", "volkmar",
        # W
        "waldemar", "walter", "wendelin", "wenzel", "werner", "wiegand", "wilfried",
        "wilhelm", "willi", "willibald", "willy", "winfried", "wolf", "wolfgang",
        "wolfram",
        # X-Z
        "xaver", "yannick", "yorick", "yusuf", "zeki",
    }

    # Common German female first names
    FEMALE_NAMES: set[str] = {
        # A
        "agnieszka", "agnes", "alexandra", "alice", "alina", "aline", "almut",
        "amelie", "andrea", "angela", "angelika", "anika", "anja", "anke", "anna",
        "annalena", "anne", "annegret", "anneliese", "annemarie", "annette", "antje",
        "ariane", "astrid", "aydan",
        # B
        "barbara", "bärbel", "beate", "beatrice", "beatrix", "bettina", "bianca",
        "birgit", "britta", "brunhilde",
        # C
        "canan", "cansel", "caren", "carina", "carla", "carmen", "carola",
        "carolin", "carolina", "caroline", "catharina", "cécile", "chantal",
        "charlotte", "christa", "christel", "christiane", "christina", "christine",
        "clara", "claudia", "constanze", "cordula", "corinna", "cornelia",
        # D
        "dagmar", "daniela", "deborah", "denise", "diana", "dietlind", "dora",
        "doris", "dorothea", "dorothee",
        # E
        "edith", "ekin", "eleonore", "elfriede", "elisabeth", "elke", "ella",
        "ellen", "elvira", "emilia", "emily", "emmi", "emma", "erika", "erna",
        "esther", "eva",
        # F
        "felicitas", "filiz", "franziska", "frauke", "friederike",
        # G
        "gabriele", "gabi", "gerda", "gerlinde", "gertrud", "gesa", "gisela",
        "grete", "gudrun", "gyde", "gökay", "gülistan",
        # H
        "hanna", "hannah", "hannelore", "harriet", "hedwig", "heide", "heidi",
        "heidrun", "heike", "helen", "helena", "helene", "helga", "henriette",
        "hertha", "hilde", "hildegard", "hildegund",
        # I
        "ilona", "ilse", "imke", "ina", "ines", "inga", "inge", "ingeborg",
        "ingrid", "irene", "iris", "irmgard", "irmtraud", "isabel", "isabell",
        "isabella",
        # J
        "jana", "janine", "jasmin", "jennifer", "jessica", "johanna", "josephine",
        "judith", "julia", "juliane", "julie", "jutta",
        # K
        "karen", "karin", "karoline", "katarina", "katharina", "kathleen", "kathrin",
        "katja", "katrin", "kerstin", "kirsten", "klara", "kornelia", "kristina", "kristine",
        # L
        "larissa", "laura", "lea", "lena", "leni", "leonie", "lieselotte", "lilian",
        "liliane", "lilli", "linda", "lisa", "lore", "lotte", "louisa", "lucia",
        "lucie", "luise", "lydia",
        # M
        "madeleine", "magdalena", "maja", "manuela", "maren", "mareike", "margarete",
        "margarethe", "margit", "margot", "margret", "maria", "marianne", "marie",
        "marika", "marina", "marion", "marita", "marlene", "marlies", "marta",
        "martha", "martina", "mechthild", "melanie", "melis", "melitta", "merle",
        "michaela", "michelle", "miriam", "monika", "monique",
        # N
        "nadine", "nadja", "natalie", "natascha", "nezahat", "nicole", "nina",
        "nora", "nyke",
        # O
        "olivia", "ortrud", "ottilie",
        # P
        "pamela", "patricia", "paula", "pauline", "peggy", "petra", "pia",
        # R
        "ramona", "rebecca", "reem", "regina", "renate", "ricarda", "rita",
        "rosalie", "rosel", "rosemarie", "roswitha", "ruth",
        # S
        "sabine", "sahra", "sanae", "sandra", "sara", "sarah", "serap", "sibylle",
        "siemtje", "silke", "silvia", "simone", "sonja", "sophie", "stefanie",
        "steffi", "stephanie", "susanna", "susanne", "svenja", "swantje",
        # T
        "tabea", "tamara", "tanja", "teresa", "theresa", "theresia", "tina",
        "traudel", "traute",
        # U
        "ulrike", "ursula", "uta", "ute",
        # V
        "vanessa", "vera", "verena", "veronika", "victoria", "viktoria", "viola",
        "viviane",
        # W
        "waltraud", "wencke", "wiebke", "wilhelmine",
        # Y-Z
        "yasmin", "yvonne", "zaklin", "zita", "zoe",
    }

    # Names that can be used for both genders (in German context)
    AMBIGUOUS_NAMES: set[str] = {
        "kim",
        "dominique",
        "robin",
        "alex",
        "jesse",
        "nikita",
        "luca",
        "andrea",  # Female in German, male in Italian
        "sascha",  # Traditional male, but used for both
        "toni",
        "kerstin",  # Rare male variant exists
        "marion",  # Rare male variant (French)
    }

    # Manual overrides for known Bundestag members with ambiguous/international names
    BUNDESTAG_OVERRIDES: dict[str, Gender] = {
        # German ambiguous
        "andrea": "female",  # In German Bundestag context, Andrea is female
        "sascha": "male",  # More commonly male in Bundestag
        # Turkish/Kurdish names
        "ateş": "male", "ates": "male",  # Ateş Gürpinar
        "sevim": "female",  # Sevim Dağdelen
        "macit": "male",  # Macit Karaahmetoğlu
        # Arabic/Persian names
        "kassem": "male", "kassem taher": "male",  # Kassem Taher Saleh
        "takis": "male", "takis mehmet": "male",  # Takis Mehmet Ali
        "kaweh": "male",  # Kaweh Mansoori
        "misbah": "female",  # Misbah Khan
        "adis": "male",  # Adis Ahmetovic
        "awet": "female",  # Awet Tesfaiesus
        # Greek names
        "ye-one": "female",  # Ye-One Rhie (Korean)
        # Hungarian
        "anikó": "female", "aniko": "female",  # Anikó Glogowski-Merten
        # Compound German names (first part determines gender)
        "hans-jürgen": "male",
        "klaus-peter": "male",
        "hermann-josef": "male",
        "leif-erik": "male",
        "jan-niclas": "male",
        "kay-uwe": "male",
        "ann-veruschka": "female",
        "christina-johanne": "female",
        "marie-agnes": "female",
        "mareike lotte": "female",
        "bettina margarethe": "female",
        # Short/uncommon German names
        "ulle": "female",  # Ulle Schauws
        "ruppert": "male",  # Ruppert Stüwe
        "cademartori": "female",  # Isabel Cademartori Dujisin (last name as first)
        # From 21. Wahlperiode Wikipedia list - male
        "sanae": "female",  # Sanae Abdi
        "knut": "male",  # Knut Abraham
        "adis": "male",  # Adis Ahmetovic
        "reem": "female",  # Reem Alabali Radovan
        "alaa": "male",  # Alaa Alhamwi
        "tarek": "male",  # Tarek Al-Wazir
        "moses": "male",  # Moses Arndt
        "reza": "male",  # Reza Asghari
        "tijen": "female",  # Tijen Ataoğlu
        "cornell": "female",  # Cornell Babendererde
        "hakan": "male",  # Hakan Demir
        "timon": "male",  # Timon Dzienus
        "mirze": "male",  # Mirze Edis
        "cem": "male",  # Cem Ince
        "ferat": "male",  # Ferat Koçak
        "cansın": "female",  # Cansın Köktürk
        "luke": "male",  # Luke Hoß
        "jorrit": "male",  # Jorrit Bosch
        "vinzenz": "male",  # Vinzenz Glaser
        "sepp": "male",  # Sepp Müller
        "bodo": "male",  # Bodo Ramelow
        "truels": "male",  # Truels Reichardt
        "gerold": "male",  # Gerold Otten
        "schahina": "female",  # Schahina Gambir
        "jeanne": "female",  # Jeanne Dillschneider
        "hülya": "female",  # Hülya Düber
        "ayse": "female",  # Ayse Asar
        "zada": "female",  # Zada Salihović
        "nyke": "female",  # Nyke Slawik
        "cansu": "female",  # Cansu Özdemir
        "mayra": "female",  # Mayra Vriesema
        "stella": "female",  # Stella Merendino
        "katalin": "female",  # Katalin Gennburg
        "donata": "female",  # Donata Vogtschmidt
        "serdar": "male",  # Serdar Yüksel
        "mahmut": "male",  # Mahmut Özdemir
        "metin": "male",  # Metin Hakverdi
        "parsa": "male",  # Parsa Marvi
        "luigi": "male",  # Luigi Pantisano
        "aaron": "male",  # Aaron Valent
        "sieghard": "male",  # Sieghard Knodel
    }

    def __init__(
        self,
        custom_mappings: dict[str, Gender] | None = None,
        unknown_log_path: Path | None = None,
    ):
        """Initialize detector with optional custom mappings.

        Args:
            custom_mappings: Override dict for specific names (full first name -> gender)
            unknown_log_path: Path to log unknown names for manual review
        """
        self._custom_mappings = custom_mappings or {}
        self._unknown_log_path = unknown_log_path
        self._cache: dict[str, GenderResult] = {}
        self._unknown_names: set[str] = set()

    def detect(self, first_name: str) -> GenderResult:
        """Detect gender from first name.

        Uses multiple sources in order:
        1. Custom mappings (manual overrides from file)
        2. Bundestag-specific overrides
        3. Built-in German name dictionary
        4. Heuristics based on name endings
        5. Mark as unknown and log

        Args:
            first_name: The first name to analyze

        Returns:
            GenderResult with gender, confidence, and source
        """
        if not first_name:
            return GenderResult("unknown", 0.0, "empty")

        # Handle compound first names - use the first part
        name_parts = first_name.strip().split()
        primary_name = name_parts[0].lower() if name_parts else ""

        if not primary_name:
            return GenderResult("unknown", 0.0, "empty")

        # Check cache first
        if primary_name in self._cache:
            return self._cache[primary_name]

        result = self._detect_uncached(primary_name)
        self._cache[primary_name] = result
        return result

    def _detect_uncached(self, name_lower: str) -> GenderResult:
        """Internal detection without caching."""
        # 1. Check custom mappings (from file)
        if name_lower in self._custom_mappings:
            return GenderResult(
                self._custom_mappings[name_lower],
                1.0,
                "manual",
            )

        # 2. Check Bundestag-specific overrides
        if name_lower in self.BUNDESTAG_OVERRIDES:
            return GenderResult(
                self.BUNDESTAG_OVERRIDES[name_lower],
                0.9,
                "bundestag_override",
            )

        # 3. Check built-in dictionaries
        is_ambiguous = name_lower in self.AMBIGUOUS_NAMES

        if name_lower in self.FEMALE_NAMES:
            confidence = 0.7 if is_ambiguous else 0.95
            return GenderResult("female", confidence, "dictionary")

        if name_lower in self.MALE_NAMES:
            confidence = 0.7 if is_ambiguous else 0.95
            return GenderResult("male", confidence, "dictionary")

        # 4. Try heuristics for German names
        result = self._heuristic_detect(name_lower)
        if result.confidence >= 0.6:
            return result

        # 5. Mark as unknown and log
        self._log_unknown(name_lower)
        return GenderResult("unknown", 0.0, "unknown")

    def _heuristic_detect(self, name: str) -> GenderResult:
        """Apply German naming heuristics based on common endings.

        German name ending patterns:
        - Female: -a, -e (except diminutives), -ine, -ina, -ella, -ette, -ie
        - Male: -o, -us, -ian, -er, -ert, -olf, -ald, -hard, -helm, -bert, -fried
        """
        # Female endings (more specific first)
        female_endings = (
            "ine", "ina", "ella", "ette", "ina", "ika", "ika",
            "heid", "gard", "traud", "trud", "linde", "hilde",
        )
        if name.endswith(female_endings):
            return GenderResult("female", 0.8, "heuristic")

        # Male endings (more specific first)
        male_endings = (
            "bert", "brecht", "fried", "hard", "hart", "helm", "hold",
            "mar", "mut", "olf", "wald", "ward", "win", "rich",
            "ian", "ius", "us",
        )
        if name.endswith(male_endings):
            return GenderResult("male", 0.8, "heuristic")

        # Less specific endings
        if name.endswith("a") and not name.endswith(("ska", "ka")):
            # -a is typically female in German (except Slavic -ska)
            return GenderResult("female", 0.65, "heuristic")

        if name.endswith("o"):
            return GenderResult("male", 0.65, "heuristic")

        return GenderResult("unknown", 0.0, "heuristic_failed")

    def _log_unknown(self, name: str) -> None:
        """Log unknown name for manual review."""
        if name not in self._unknown_names:
            self._unknown_names.add(name)
            logger.debug(f"Unknown gender for name: {name}")

            if self._unknown_log_path:
                try:
                    with open(self._unknown_log_path, "a", encoding="utf-8") as f:
                        f.write(f"{name}\n")
                except IOError as e:
                    logger.warning(f"Failed to write unknown name to log: {e}")

    def get_unknown_names(self) -> set[str]:
        """Return set of names that couldn't be classified."""
        return self._unknown_names.copy()

    def add_mapping(self, name: str, gender: Gender) -> None:
        """Add a manual mapping (for runtime updates).

        Args:
            name: First name to map
            gender: Gender to assign
        """
        self._custom_mappings[name.lower()] = gender
        # Clear from cache to use new mapping
        self._cache.pop(name.lower(), None)
        # Remove from unknown if previously logged
        self._unknown_names.discard(name.lower())

    def get_stats(self) -> dict:
        """Get detector statistics."""
        return {
            "male_names_count": len(self.MALE_NAMES),
            "female_names_count": len(self.FEMALE_NAMES),
            "ambiguous_names_count": len(self.AMBIGUOUS_NAMES),
            "custom_mappings_count": len(self._custom_mappings),
            "cached_results": len(self._cache),
            "unknown_names": len(self._unknown_names),
        }


def load_custom_mappings(path: Path) -> dict[str, Gender]:
    """Load custom name->gender mappings from JSON file.

    Expected format: {"firstname": "male"|"female", ...}

    Args:
        path: Path to JSON file with mappings

    Returns:
        Dict mapping lowercase names to genders
    """
    if not path.exists():
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            # Normalize to lowercase
            return {k.lower(): v for k, v in data.items()}
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load custom gender mappings from {path}: {e}")
        return {}
