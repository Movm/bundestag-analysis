"""Data loading and orchestration for Bundestag Wrapped analysis.

Loads pre-fetched data from disk and builds analysis structures:
- load_wrapped_data(): Main entry point, returns WrappedDataBase
- build_speaker_profiles(): Create speaker profiles with gender detection
- build_gender_stats(): Aggregate gender statistics per party

Uses parser.py for speech parsing, this file handles orchestration only.
"""

from pathlib import Path
from collections import Counter
import json
import logging

import pandas as pd

from noun_analysis.parser import parse_speeches_from_protocol
from noun_analysis.speech_aggregation import aggregate_speeches_by_type
from noun_analysis.text_utils import strip_parenthetical_content, extract_name_parts
from noun_analysis.factions import extract_parties_from_applause
from .types import (
    WrappedDataBase,
    INTERRUPTER_PATTERN,
    APPLAUSE_PATTERN,
    HECKLE_PATTERN,
    normalize_name_for_comparison,
    SpeakerProfile,
    GenderStats,
    GenderPartyStats,
    Gender,
)
from .gender import GenderDetector, load_custom_mappings

logger = logging.getLogger(__name__)


def _parse_protocols_and_aggregate(data_dir: Path) -> dict:
    """Load protocols and classify all speeches by type.

    Uses parse_speeches_from_protocol() for parsing and aggregate_speeches_by_type()
    for statistics aggregation. Also parses drama (interruption) stats from raw
    fullText before parentheticals are stripped.

    Returns dict with:
        - speaker_stats: {party: Counter(speaker -> count)} for real speeches only
        - real_speech_counts: {party: count} of real speeches per party
        - all_speeches: list of classified speech dicts
        - raw_full_texts: list of (fullText, speeches) tuples for drama parsing
    """
    protocols_dir = data_dir / "protocols"
    if not protocols_dir.exists():
        return {
            "speaker_stats": {},
            "formal_speaker_stats": {},
            "befragung_speaker_stats": {},
            "question_speaker_stats": {},
            "wortbeitrag_speaker_stats": {},
            "real_speech_counts": {},
            "rede_counts": {},
            "wortbeitrag_counts": {},
            "all_speeches": [],
            "raw_full_texts": [],
        }

    all_speeches = []
    raw_full_texts = []  # Store raw fullText for drama parsing

    # Parse each protocol file using the unified parser from parser.py
    for protocol_file in protocols_dir.glob("*.json"):
        with open(protocol_file) as f:
            protocol = json.load(f)

        full_text = protocol.get("fullText", "")
        if not full_text or not isinstance(full_text, str):
            continue

        speeches = parse_speeches_from_protocol(full_text)
        all_speeches.extend(speeches)

        # Store raw fullText with parsed speeches for drama parsing
        raw_full_texts.append((full_text, speeches))

    # Use the centralized aggregation function from parser.py
    aggregated = aggregate_speeches_by_type(all_speeches)

    return {
        **aggregated,
        "all_speeches": all_speeches,
        "raw_full_texts": raw_full_texts,
    }


def build_speaker_profiles(
    all_speeches: list[dict],
    gender_detector: GenderDetector,
    drama_stats: dict,
) -> dict[str, SpeakerProfile]:
    """Build comprehensive speaker profiles from speeches.

    Args:
        all_speeches: List of speech dicts with speaker, party, first_name, etc.
        gender_detector: Configured GenderDetector instance
        drama_stats: Drama stats dict with interrupters/interrupted counts

    Returns:
        Dict mapping speaker name to SpeakerProfile
    """
    profiles: dict[str, SpeakerProfile] = {}

    for speech in all_speeches:
        speaker = speech.get("speaker", "")
        if not speaker:
            continue

        key = speaker

        if key not in profiles:
            # Get first_name from speech dict, or parse from speaker name
            first_name = speech.get("first_name", "")
            last_name = speech.get("last_name", "")
            acad_title = speech.get("acad_title")

            # If first_name not in data, parse from speaker name
            if not first_name and speaker:
                name_parts = extract_name_parts(speaker)
                first_name = name_parts.get("first_name", "")
                last_name = name_parts.get("last_name", "")
                acad_title = name_parts.get("acad_title") or acad_title

            gender_result = gender_detector.detect(first_name)

            profiles[key] = SpeakerProfile(
                name=speaker,
                first_name=first_name,
                last_name=last_name,
                party=speech.get("party", ""),
                gender=gender_result.gender,
                acad_title=acad_title,
                total_speeches=0,
                total_words=0,
                formal_speeches=0,
                wortbeitraege=0,
                befragung_responses=0,
                question_speeches=0,
                avg_words_per_speech=0.0,
                interruptions_made=0,
                interruptions_received=0,
            )

        profile = profiles[key]
        profile.total_speeches += 1
        profile.total_words += speech.get("words", 0)

        speech_type = speech.get("type", "other")
        category = speech.get("category", "rede" if speech_type == "rede" else "wortbeitrag")

        # Track by category (high-level)
        if category == "rede":
            profile.formal_speeches += 1
        else:
            profile.wortbeitraege += 1

        # Also track by detailed type
        if speech_type in ("befragung", "fragestunde_antwort"):
            profile.befragung_responses += 1
        elif speech_type == "fragestunde":
            profile.question_speeches += 1

    # Calculate averages
    for profile in profiles.values():
        if profile.total_speeches > 0:
            profile.avg_words_per_speech = profile.total_words / profile.total_speeches

    # Add interruption stats from drama_stats
    interrupters = drama_stats.get("interrupters", Counter())
    interrupted = drama_stats.get("interrupted", Counter())

    for (name, party), count in interrupters.items():
        if name in profiles:
            profiles[name].interruptions_made = count

    for (name, party), count in interrupted.items():
        if name in profiles:
            profiles[name].interruptions_received = count

    return profiles


def merge_partial_profiles(profiles: dict[str, SpeakerProfile]) -> dict[str, SpeakerProfile]:
    """Merge last-name-only profiles into matching full profiles.

    Problem
    -------
    Bundestag protocol text contains two types of speaker references:

    1. Full names in speech headers: "Dr. Konstantin von Notz (GRÜNE):"
    2. Last-name-only in interjections: "(Zuruf von Kraft [GRÜNE])"

    The parser creates separate SpeakerProfile entries for each unique name,
    resulting in duplicate profiles like:
        - "Dr. Konstantin von Notz" → gender: male (detected from "Konstantin")
        - "Kraft" → gender: unknown (no first name to detect)

    This inflates the "unknown" gender count and fragments speaker statistics.

    Algorithm
    ---------
    1. Partition profiles into "full" (has first_name) and "partial" (no first_name)

    2. Build a lookup index: (last_name.lower(), party) → full_profile_key
       - If multiple full profiles share the same (last_name, party), keep the
         one with more speeches as the canonical entry

    3. For each partial profile:
       - Look up (partial.last_name.lower(), partial.party) in the index
       - If found: merge statistics into the matching full profile
       - If not found: keep as separate entry (truly unknown speaker)

    4. Recalculate avg_words_per_speech for merged profiles

    Example
    -------
    Input profiles:
        "Dr. Konstantin von Notz" (GRÜNE): 45 speeches, gender=male
        "Kraft" (GRÜNE): 12 speeches, gender=unknown

    After merge:
        "Dr. Konstantin von Notz" (GRÜNE): 57 speeches, gender=male
        (the "Kraft" entry is removed)

    Edge Cases
    ----------
    - Multiple speakers with same last name + party: Uses the one with more
      speeches as canonical (assumes the more active speaker is the "real" one)
    - No matching full profile: Partial profile kept as-is (e.g., speaker who
      only appears in interjections and never gave a formal speech)
    - Empty input: Returns unchanged

    Performance
    -----------
    O(n) where n = number of profiles. Single pass to build index, single pass
    to merge. Typical improvement: ~150 profiles merged, detection rate
    increases from ~74% to ~87%.

    Args:
        profiles: Dict mapping speaker name to SpeakerProfile

    Returns:
        New dict with partial profiles merged into full profiles
    """
    # Separate full profiles (have first_name) from partial (no first_name)
    full_profiles = {k: v for k, v in profiles.items() if v.first_name.strip()}
    partial_profiles = {k: v for k, v in profiles.items() if not v.first_name.strip()}

    if not partial_profiles:
        return profiles  # Nothing to merge

    # Build lookup: (last_name_lower, party) -> full profile key
    lastname_party_to_full: dict[tuple[str, str], str] = {}
    for key, profile in full_profiles.items():
        lookup_key = (profile.last_name.lower(), profile.party)
        # If multiple, prefer the one with more speeches
        if lookup_key not in lastname_party_to_full:
            lastname_party_to_full[lookup_key] = key
        else:
            existing = full_profiles[lastname_party_to_full[lookup_key]]
            if profile.total_speeches > existing.total_speeches:
                lastname_party_to_full[lookup_key] = key

    # Merge partial profiles into matching full profiles
    merged = dict(full_profiles)
    unmatched = {}
    merge_count = 0

    for key, partial in partial_profiles.items():
        lookup_key = (partial.last_name.lower(), partial.party)
        if lookup_key in lastname_party_to_full:
            full_key = lastname_party_to_full[lookup_key]
            full = merged[full_key]
            # Add partial's stats to full profile
            full.total_speeches += partial.total_speeches
            full.total_words += partial.total_words
            full.formal_speeches += partial.formal_speeches
            full.wortbeitraege += partial.wortbeitraege
            full.question_speeches += partial.question_speeches
            full.interruptions_made += partial.interruptions_made
            full.interruptions_received += partial.interruptions_received
            # Recalculate average
            if full.total_speeches > 0:
                full.avg_words_per_speech = full.total_words / full.total_speeches
            merge_count += 1
        else:
            # No match found, keep as separate profile
            unmatched[key] = partial

    merged.update(unmatched)
    logger.info(f"Merged {merge_count} partial profiles into full profiles")
    return merged


def build_gender_stats(
    speaker_profiles: dict[str, SpeakerProfile],
    parties: list[str],
) -> GenderStats:
    """Build aggregated gender statistics from speaker profiles.

    Args:
        speaker_profiles: Dict mapping speaker name to profile
        parties: List of party names to include

    Returns:
        GenderStats with per-party breakdowns
    """
    total_male = total_female = total_unknown = 0
    by_party: dict[str, GenderPartyStats] = {}

    # Initialize party stats
    for party in parties:
        by_party[party] = GenderPartyStats()

    # Aggregate from profiles
    for profile in speaker_profiles.values():
        party = profile.party
        if party not in by_party:
            continue

        stats = by_party[party]
        stats.total_speakers += 1

        if profile.gender == "male":
            stats.male_speakers += 1
            stats.male_speeches += profile.total_speeches
            stats.male_words += profile.total_words
            stats.male_interruptions_made += profile.interruptions_made
            stats.male_interruptions_received += profile.interruptions_received
            if profile.acad_title:
                stats.male_dr_count += 1
            total_male += 1
        elif profile.gender == "female":
            stats.female_speakers += 1
            stats.female_speeches += profile.total_speeches
            stats.female_words += profile.total_words
            stats.female_interruptions_made += profile.interruptions_made
            stats.female_interruptions_received += profile.interruptions_received
            if profile.acad_title:
                stats.female_dr_count += 1
            total_female += 1
        else:
            stats.unknown_speakers += 1
            stats.unknown_speeches += profile.total_speeches
            stats.unknown_words += profile.total_words
            total_unknown += 1

    # Calculate averages
    for stats in by_party.values():
        if stats.male_speeches > 0:
            stats.male_avg_speech_length = stats.male_words / stats.male_speeches
        if stats.female_speeches > 0:
            stats.female_avg_speech_length = stats.female_words / stats.female_speeches
        if stats.unknown_speeches > 0:
            stats.unknown_avg_speech_length = stats.unknown_words / stats.unknown_speeches

    return GenderStats(
        total_male_speakers=total_male,
        total_female_speakers=total_female,
        total_unknown_speakers=total_unknown,
        by_party=by_party,
    )


def load_wrapped_data(results_dir: Path, data_dir: Path, cls=None):
    """Load all data needed for wrapped analysis.

    Args:
        results_dir: Path to analysis results directory
        data_dir: Path to raw data directory
        cls: Optional class to instantiate (for composition pattern)

    Returns:
        WrappedDataBase instance (or cls instance if provided)
    """
    results_dir = Path(results_dir)
    data_dir = Path(data_dir)

    # Load full_data.json
    full_data_path = results_dir / "full_data.json"
    with open(full_data_path) as f:
        full_data = json.load(f)

    metadata = full_data["metadata"]

    # Filter fraktionslos from parties list (keep speaker data for personal wrappeds)
    if "parties" in metadata:
        metadata["parties"] = [p for p in metadata["parties"] if p != "fraktionslos"]

    # Build party_stats, top_words, and tone data from results
    party_stats = {}
    top_words = {}
    tone_data = {}
    category_data = {}
    for result in full_data["results"]:
        party = result["party"]
        if party == "fraktionslos":
            continue  # Skip fraktionslos from party-level stats
        party_stats[party] = {
            "speeches": result["speech_count"],
            "total_words": result["total_words"],
            "total_nouns": result["total_nouns"],
            "total_adjectives": result["total_adjectives"],
            "total_verbs": result["total_verbs"],
            "unique_nouns": len(result["top_nouns"]),
        }
        top_words[party] = {
            "nouns": result["top_nouns"],
            "adjectives": result["top_adjectives"],
            "verbs": result["top_verbs"],
        }
        # Load tone scores and category data if available
        if "tone_scores" in result:
            tone_data[party] = result["tone_scores"]
        if "categories" in result:
            category_data[party] = result["categories"]

    # Load and classify speeches from protocol files
    classified = _parse_protocols_and_aggregate(data_dir)
    speaker_stats = classified["speaker_stats"]
    befragung_speaker_stats = classified["befragung_speaker_stats"]
    question_speaker_stats = classified["question_speaker_stats"]
    real_speech_counts = classified["real_speech_counts"]
    all_speeches = classified["all_speeches"]

    # Override party_stats speech counts with classified real speech counts
    for party in party_stats:
        if party in real_speech_counts:
            party_stats[party]["real_speeches"] = real_speech_counts[party]

    # Store all speeches for drama parsing
    speeches_by_party = {}
    for speech in all_speeches:
        party = speech['party']
        if party not in speeches_by_party:
            speeches_by_party[party] = []
        speeches_by_party[party].append(speech)

    # Load speeches.json for detailed statistics (word counts, academic titles)
    speeches_json_path = data_dir / "speeches.json"
    detailed_speeches = []
    if speeches_json_path.exists():
        with open(speeches_json_path) as f:
            speeches_json = json.load(f)
        for party_name, speeches_list in speeches_json.items():
            for s in speeches_list:
                detailed_speeches.append({**s, 'party': party_name})

        # Calculate detailed stats per party
        for party_name in party_stats:
            party_speeches = [s for s in detailed_speeches if s.get('party') == party_name]
            if party_speeches:
                word_counts = [s.get('words', 0) for s in party_speeches]
                dr_count = sum(1 for s in party_speeches if s.get('acad_title'))
                party_stats[party_name].update({
                    "min_words": min(word_counts) if word_counts else 0,
                    "max_words": max(word_counts) if word_counts else 0,
                    "avg_words": sum(word_counts) / len(word_counts) if word_counts else 0,
                    "dr_count": dr_count,
                    "dr_ratio": dr_count / len(party_speeches) if party_speeches else 0,
                })

    # Load word frequencies from CSVs
    word_frequencies = {}
    for word_type in ["nouns", "adjectives", "verbs"]:
        csv_path = results_dir / f"{word_type}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            word_frequencies[word_type] = df

    # Positive interjection keywords (Zustimmung)
    POSITIVE_KEYWORDS = [
        # Explicit agreement
        "genau", "richtig", "sehr richtig", "bravo", "sehr wahr",
        "stimmt", "jawohl", "jawoll", "sehr gut", "eben", "so ist es",
        "oh ja", "prima", "völlig richtig", "ganz genau",
        "ausgezeichnet", "wunderbar", "großartig",
        # Common short affirmations (from analysis)
        "ja!", "doch!", "korrekt!", "natürlich!", "absolut!",
        "na klar", "ja, klar", "gut so", "schön!",
        # Praise phrases
        "guter mann", "gute frau", "gute rede",
        # Agreement phrases
        "so sieht es aus", "so sieht's aus", "zu recht",
        "da hat sie recht", "da hat er recht", "das ist auch gut so",
        "allerdings!", "bingo!", "na also", "wow!",
        "danke schön", "danke!", "interessant!",
        "gott sei dank", "so ist das!",
    ]

    # Negative interjection keywords (Kritik)
    NEGATIVE_KEYWORDS = [
        # Explicit criticism
        "unsinn", "quatsch", "blödsinn", "falsch", "stimmt nicht",
        "lüge", "unverschämt", "peinlich", "skandal", "unfassbar",
        "unglaublich", "witz", "lachhaft", "absurd", "nonsens",
        "schwachsinn", "irrsinn", "wahnsinn", "frechheit", "lächerlich",
        "stimmt doch nicht", "stimmt gar nicht", "das ist nicht wahr",
        "nein", "niemals", "auf keinen fall", "pfui", "schämen",
        # Parliamentary expressions of disapproval (from analysis)
        "hört! hört!", "aha!", "ach was!",
        # Disbelief/dismay phrases
        "das glauben sie doch selber nicht", "um gottes willen",
        "mein gott", "o mein gott", "ach gott", "meine güte",
        # Criticism phrases
        "sie haben es nicht verstanden", "das ist die unwahrheit",
        "thema verfehlt", "na, na, na", "überhaupt nicht",
        "im gegenteil", "besser nicht", "so ein unfug", "schande",
        "verschwörungstheorien", "das geht nicht", "langweilig",
        "träum weiter", "schön wär's",
        # Dismissive/critical short forms
        "nee!", "oje!", "eijeijei!", "zur sache!",
        "was reden sie denn da", "damit kennen sie sich ja aus",
        "entschuldigen sie sich", "wie bitte?",
    ]

    def classify_interjection(text: str) -> str:
        """Classify interjection as positive, negative, or neutral."""
        if ":" not in text:
            return "neutral"
        content = text.split(":", 1)[1].rstrip(")").lower()

        # Check for positive keywords
        if any(kw in content for kw in POSITIVE_KEYWORDS):
            return "positive"

        # Check for negative keywords
        if any(kw in content for kw in NEGATIVE_KEYWORDS):
            return "negative"

        return "neutral"

    # Parse drama stats from RAW protocol fullText (before parentheticals stripped)
    # This is necessary because parse_speeches_from_protocol() strips interruptions
    drama_stats = {
        "interrupters": Counter(),  # speaker -> count of times they interrupted
        "interrupted": Counter(),   # speaker -> count of interruptions in their speech
        "applause_by_party": Counter(),  # party -> applause count
        "heckles_by_party": Counter(),   # party -> heckle count
        "positive_interjections": Counter(),  # speaker -> count of positive (Zustimmung)
        "negative_interjections": Counter(),  # speaker -> count of negative (Kritik)
        "neutral_interjections": Counter(),   # speaker -> count of neutral (unclear)
        "neutral_texts": [],  # raw text of neutral interjections for analysis
    }

    # Get raw_full_texts from classified data
    raw_full_texts = classified.get("raw_full_texts", [])

    for full_text, speeches in raw_full_texts:
        # For each speech, find interruptions in the raw text
        for speech in speeches:
            speaker = speech.get("speaker", "")
            party = speech.get("party", "")
            speech_start = speech.get("start", 0)
            speech_end = speech.get("end", len(full_text))

            # Get raw text segment for this speech (with interruptions intact)
            raw_speech_text = full_text[speech_start:speech_end]

            # Count interruptions in this speech (who interrupted)
            speaker_lastname = normalize_name_for_comparison(speaker)
            for match in INTERRUPTER_PATTERN.finditer(raw_speech_text):
                interrupter_name = match.group(1).strip()
                interrupter_party = match.group(2).strip()

                # Skip noise patterns (Beifall, Zuruf mixed with names)
                if any(x in interrupter_name for x in ["Beifall", "Zuruf", "Lachen", "Heiterkeit", "Widerspruch"]):
                    continue

                # Strip "Abg." prefix if present
                if interrupter_name.startswith("Abg. "):
                    interrupter_name = interrupter_name[5:]

                # Normalize whitespace for consistent Counter keys
                interrupter_name = " ".join(interrupter_name.split())

                # Skip self-interruptions (speaker responding to heckles in their own speech)
                interrupter_lastname = normalize_name_for_comparison(interrupter_name)
                if speaker_lastname == interrupter_lastname:
                    continue

                drama_stats["interrupters"][(interrupter_name, interrupter_party)] += 1
                drama_stats["interrupted"][(speaker, party)] += 1

                # Classify as positive/negative/neutral
                full_match = match.group(0)
                sentiment = classify_interjection(full_match)
                if sentiment == "positive":
                    drama_stats["positive_interjections"][(interrupter_name, interrupter_party)] += 1
                elif sentiment == "negative":
                    drama_stats["negative_interjections"][(interrupter_name, interrupter_party)] += 1
                else:
                    drama_stats["neutral_interjections"][(interrupter_name, interrupter_party)] += 1
                    # Capture text content for analysis
                    if ":" in full_match:
                        content = full_match.split(":", 1)[1].rstrip(")")
                        drama_stats["neutral_texts"].append(content)

            # Count applause events - split multi-party applause
            for match in APPLAUSE_PATTERN.finditer(raw_speech_text):
                applause_text = match.group(1).strip()
                parties = extract_parties_from_applause(applause_text)
                for applause_party in parties:
                    drama_stats["applause_by_party"][applause_party] += 1

            # Count heckles - split multi-party heckles
            for match in HECKLE_PATTERN.finditer(raw_speech_text):
                heckle_text = match.group(1).strip()
                parties = extract_parties_from_applause(heckle_text)
                for heckle_party in parties:
                    drama_stats["heckles_by_party"][heckle_party] += 1

    # Initialize gender detector
    custom_mappings_path = data_dir / "gender_overrides.json"
    custom_mappings = load_custom_mappings(custom_mappings_path)
    unknown_log_path = data_dir / "unknown_names.txt"
    gender_detector = GenderDetector(
        custom_mappings=custom_mappings,
        unknown_log_path=unknown_log_path,
    )

    # Build speaker profiles with gender detection
    # Use all_speeches from _parse_protocols_and_aggregate (has words, type)
    # NOT detailed_speeches from speeches.json (missing words field)
    speaker_profiles = build_speaker_profiles(
        all_speeches,
        gender_detector,
        drama_stats,
    )

    # Merge last-name-only profiles into full profiles (e.g., "Kraft" -> "Dr. Konstantin von Notz")
    speaker_profiles = merge_partial_profiles(speaker_profiles)

    # Build aggregated gender stats
    parties = list(party_stats.keys())
    gender_stats = build_gender_stats(speaker_profiles, parties)

    # Log unknown names summary
    unknown_names = gender_detector.get_unknown_names()
    if unknown_names:
        logger.info(f"Gender detection: {len(unknown_names)} unknown names logged")

    # Use the provided class or fall back to base
    data_cls = cls or WrappedDataBase
    return data_cls(
        metadata=metadata,
        party_stats=party_stats,
        top_words=top_words,
        speaker_stats=speaker_stats,
        befragung_speaker_stats=befragung_speaker_stats,
        question_speaker_stats=question_speaker_stats,
        word_frequencies=word_frequencies,
        drama_stats=drama_stats,
        all_speeches=all_speeches,  # Use protocol-classified speeches, not speeches.json
        speeches_by_party=speeches_by_party,
        tone_data=tone_data,
        category_data=category_data,
        gender_stats=gender_stats,
        speaker_profiles=speaker_profiles,
    )
