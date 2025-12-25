"""Government officials mapping and patterns.

This module provides shared mapping of government officials to their party
affiliations, used for parsing speeches where officials speak in their
official capacity (format: "Name, Role:") rather than as MPs ("Name (Party):").

The mapping covers:
- Bundeskanzler
- Bundesminister/innen
- Parlamentarische Staatssekretäre
- Staatsminister/innen
"""

import re

# =============================================================================
# Government Officials → Party Mapping
# =============================================================================
# When government officials speak with "Name, Role:" format (without party),
# we need to look up their party affiliation.

GOVERNMENT_PARTY_MAP = {
    # =========================================================================
    # Kabinett Merz (21. Wahlperiode, seit 6. Mai 2025)
    # =========================================================================

    # --- Bundeskanzler ---
    "Friedrich Merz": "CDU/CSU",

    # --- Bundeskanzleramt ---
    "Thorsten Frei": "CDU/CSU",  # Chef des Bundeskanzleramts
    "Dr. Christiane Schenderlein": "CDU/CSU",  # Staatsministerin für Sport und Ehrenamt
    "Christiane Schenderlein": "CDU/CSU",
    "Dr. Wolfram Weimer": "CDU/CSU",  # Staatsminister für Kultur und Medien (parteilos, CDU-nominiert)
    "Wolfram Weimer": "CDU/CSU",
    "Dr. Michael Meister": "CDU/CSU",  # Staatsminister für Bund-Länder-Zusammenarbeit
    "Michael Meister": "CDU/CSU",

    # --- Finanzen (Vizekanzler Lars Klingbeil) ---
    "Lars Klingbeil": "SPD",  # Bundesminister der Finanzen, Vizekanzler
    "Elisabeth Kaiser": "SPD",  # Parl. Staatssekretärin, Beauftragte für Ostdeutschland
    "Dennis Rohde": "SPD",  # Parl. Staatssekretär
    "Michael Schrodi": "SPD",  # Parl. Staatssekretär

    # --- Inneres (Alexander Dobrindt) ---
    "Alexander Dobrindt": "CDU/CSU",  # Bundesminister des Innern
    "Christoph de Vries": "CDU/CSU",  # Parl. Staatssekretär
    "Daniela Ludwig": "CDU/CSU",  # Parl. Staatssekretärin

    # --- Auswärtiges Amt (Johann Wadephul) ---
    "Dr. Johann David Wadephul": "CDU/CSU",  # Bundesminister des Auswärtigen
    "Johann David Wadephul": "CDU/CSU",
    "Dr. Johann Wadephul": "CDU/CSU",
    "Johann Wadephul": "CDU/CSU",
    "Gunther Krichbaum": "CDU/CSU",  # Staatsminister für Europa
    "Serap Güler": "CDU/CSU",  # Staatsministerin
    "Florian Hahn": "CDU/CSU",  # Staatsminister

    # --- Verteidigung (Boris Pistorius) ---
    "Boris Pistorius": "SPD",  # Bundesminister der Verteidigung
    "Dr. Nils Schmid": "SPD",  # Parl. Staatssekretär
    "Nils Schmid": "SPD",
    "Sebastian Hartmann": "SPD",  # Parl. Staatssekretär

    # --- Wirtschaft und Energie (Katherina Reiche) ---
    "Katherina Reiche": "CDU/CSU",  # Bundesministerin für Wirtschaft und Energie
    "Gitta Connemann": "CDU/CSU",  # Parl. Staatssekretärin, Beauftragte für Mittelstand
    "Stefan Rouenhoff": "CDU/CSU",  # Parl. Staatssekretär

    # --- Forschung, Technologie und Raumfahrt (Dorothee Bär) ---
    "Dorothee Bär": "CDU/CSU",  # Bundesministerin für Forschung
    "Matthias Hauer": "CDU/CSU",  # Parl. Staatssekretär
    "Dr. Silke Launert": "CDU/CSU",  # Parl. Staatssekretärin
    "Silke Launert": "CDU/CSU",

    # --- Justiz und Verbraucherschutz (Stefanie Hubig) ---
    "Stefanie Hubig": "SPD",  # Bundesministerin der Justiz
    "Anette Kramme": "SPD",  # Parl. Staatssekretärin
    "Frank Schwabe": "SPD",  # Parl. Staatssekretär

    # --- Bildung, Familie, Senioren, Frauen und Jugend (Karin Prien) ---
    "Karin Prien": "CDU/CSU",  # Bundesministerin
    "Mareike Wulf": "CDU/CSU",  # Parl. Staatssekretärin
    "Mareike Lotte Wulf": "CDU/CSU",  # Alternate spelling
    "Michael Brand": "CDU/CSU",  # Parl. Staatssekretär, Beauftragter gegen Antiziganismus

    # --- Arbeit und Soziales (Bärbel Bas) ---
    "Bärbel Bas": "SPD",  # Bundesministerin für Arbeit und Soziales
    "Natalie Pawlik": "SPD",  # Parl. Staatssekretärin, Beauftragte für Migration
    "Katja Mast": "SPD",  # Parl. Staatssekretärin
    "Kerstin Griese": "SPD",  # Parl. Staatssekretärin

    # --- Digitales und Staatsmodernisierung (Karsten Wildberger) ---
    "Karsten Wildberger": "CDU/CSU",  # Bundesminister (zunächst parteilos, CDU-nominiert)
    "Philipp Amthor": "CDU/CSU",  # Parl. Staatssekretär
    "Thomas Jarzombek": "CDU/CSU",  # Parl. Staatssekretär

    # --- Verkehr (Patrick Schnieder) ---
    "Patrick Schnieder": "CDU/CSU",  # Bundesminister für Verkehr
    "Christian Hirte": "CDU/CSU",  # Parl. Staatssekretär
    "Ulrich Lange": "CDU/CSU",  # Parl. Staatssekretär

    # --- Umwelt, Klimaschutz, Naturschutz und nukleare Sicherheit (Carsten Schneider) ---
    "Carsten Schneider": "SPD",  # Bundesminister für Umwelt
    "Carsten Träger": "SPD",  # Parl. Staatssekretär
    "Rita Schwarzelühr-Sutter": "SPD",  # Parl. Staatssekretärin

    # --- Gesundheit (Nina Warken) ---
    "Nina Warken": "CDU/CSU",  # Bundesministerin für Gesundheit
    "Georg Kippels": "CDU/CSU",  # Parl. Staatssekretär
    "Tino Sorge": "CDU/CSU",  # Parl. Staatssekretär

    # --- Landwirtschaft, Ernährung und Heimat (Alois Rainer) ---
    "Alois Rainer": "CDU/CSU",  # Bundesminister für Landwirtschaft
    "Silvia Breher": "CDU/CSU",  # Parl. Staatssekretärin
    "Martina Englhardt-Kopf": "CDU/CSU",  # Parl. Staatssekretärin

    # --- Wirtschaftliche Zusammenarbeit und Entwicklung (Reem Alabali-Radovan) ---
    "Reem Alabali-Radovan": "SPD",  # Bundesministerin für Entwicklung
    "Bärbel Kofler": "SPD",  # Parl. Staatssekretärin
    "Johann Saathoff": "SPD",  # Parl. Staatssekretär

    # --- Wohnen, Stadtentwicklung und Bauwesen (Verena Hubertz) ---
    "Verena Hubertz": "SPD",  # Bundesministerin für Wohnen
    "Sören Bartol": "SPD",  # Parl. Staatssekretär
    "Sabine Poschmann": "SPD",  # Parl. Staatssekretärin

    # =========================================================================
    # Kabinett Scholz (20. Wahlperiode, 2021-2025) - Historical
    # =========================================================================
    "Olaf Scholz": "SPD",  # Bundeskanzler
    "Christian Lindner": "FDP",  # Bundesminister der Finanzen
    "Robert Habeck": "GRÜNE",  # Bundesminister für Wirtschaft und Klimaschutz
    "Annalena Baerbock": "GRÜNE",  # Bundesministerin des Auswärtigen
    "Nancy Faeser": "SPD",  # Bundesministerin des Innern
    "Karl Lauterbach": "SPD",  # Bundesminister für Gesundheit
    "Dr. Karl Lauterbach": "SPD",
    "Klara Geywitz": "SPD",  # Bundesministerin für Wohnen
    "Svenja Schulze": "SPD",  # Bundesministerin für Entwicklung
    "Hubertus Heil": "SPD",  # Bundesminister für Arbeit
    "Steffi Lemke": "GRÜNE",  # Bundesministerin für Umwelt
    "Cem Özdemir": "GRÜNE",  # Bundesminister für Landwirtschaft
    "Lisa Paus": "GRÜNE",  # Bundesministerin für Familie
    "Volker Wissing": "FDP",  # Bundesminister für Verkehr
    "Marco Buschmann": "FDP",  # Bundesminister der Justiz
    "Bettina Stark-Watzinger": "FDP",  # Bundesministerin für Bildung

    # =========================================================================
    # Kabinett Merkel (Historical)
    # =========================================================================
    "Angela Merkel": "CDU/CSU",  # Bundeskanzlerin
    "Horst Seehofer": "CDU/CSU",  # Bundesminister des Innern
    "Jens Spahn": "CDU/CSU",  # Bundesminister für Gesundheit
    "Peter Altmaier": "CDU/CSU",  # Bundesminister für Wirtschaft
    "Julia Klöckner": "CDU/CSU",  # Bundesministerin für Landwirtschaft
    "Anja Karliczek": "CDU/CSU",  # Bundesministerin für Bildung
    "Andreas Scheuer": "CDU/CSU",  # Bundesminister für Verkehr
    "Heiko Maas": "SPD",  # Bundesminister des Auswärtigen
    "Franziska Giffey": "SPD",  # Bundesministerin für Familie
    "Christine Lambrecht": "SPD",  # Bundesministerin der Justiz/Verteidigung
}


# =============================================================================
# Government Official Speech Pattern
# =============================================================================
# Matches: "Friedrich Merz, Bundeskanzler:", "Lars Klingbeil, Bundesminister der Finanzen:"
# This format is used in WP21+ for government officials speaking in official capacity.

government_pattern = re.compile(
    r'\n([A-ZÄÖÜ][^,\n]{2,50}),\s*'
    r'(Bundeskanzler(?:in)?|'
    r'Bundesminister(?:in)?(?:\s+[^\n:]{0,60})?|'
    r'Parl\.\s*Staatssekretär(?:in)?(?:\s+[^\n:]{0,80})?|'
    r'Staatsminister(?:in)?(?:\s+[^\n:]{0,60})?):\s*\n'
)


def get_party_for_official(name: str) -> str | None:
    """Look up party affiliation for a government official.

    Tries exact match first, then without academic title prefix.

    Args:
        name: Official's name as it appears in protocol

    Returns:
        Party name or None if not found
    """
    # Try exact match
    party = GOVERNMENT_PARTY_MAP.get(name)
    if party:
        return party

    # Try without academic title prefix
    import re
    name_without_title = re.sub(r'^(?:Dr\.|Prof\.|Dr\s|Prof\s)\s*', '', name).strip()
    return GOVERNMENT_PARTY_MAP.get(name_without_title)
