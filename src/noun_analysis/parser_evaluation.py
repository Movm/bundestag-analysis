"""Parser evaluation using Gemini as ground truth.

Compares regex-based parsing with Gemini extraction to identify:
- Missed speeches (regex didn't catch)
- Duplicates (same speech tracked twice)
- Boundary errors (wrong start/end)
- Speaker/party extraction errors
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Literal

from .gemini_service import GeminiClient
from .parser import parse_speeches_from_protocol
from .storage import DataStore


@dataclass
class GeminiSpeech:
    """Speech as extracted by Gemini."""

    speaker: str
    party: str | None
    role: str | None  # Government role like "Bundeskanzler"
    text_preview: str  # First ~150 chars of speech
    start_marker: str  # How speaker was introduced
    speech_type: str  # formal_speech, question, answer, etc.
    zwischenrufe: list[dict] = field(default_factory=list)


@dataclass
class SpeechMatch:
    """Result of comparing Gemini vs Regex extraction."""

    gemini_speech: GeminiSpeech | None
    regex_speech: dict | None
    match_type: Literal["exact", "partial", "gemini_only", "regex_only"]
    issues: list[str] = field(default_factory=list)

    @property
    def speaker_match(self) -> bool:
        if not self.gemini_speech or not self.regex_speech:
            return False
        return normalize_name(self.gemini_speech.speaker) == normalize_name(
            self.regex_speech.get("speaker", "")
        )

    @property
    def party_match(self) -> bool:
        if not self.gemini_speech or not self.regex_speech:
            return False
        g_party = normalize_party_for_compare(self.gemini_speech.party)
        r_party = normalize_party_for_compare(self.regex_speech.get("party"))
        return g_party == r_party


@dataclass
class EvaluationResult:
    """Complete evaluation result for a protocol."""

    protocol_id: str
    document_number: str
    total_gemini_speeches: int
    total_regex_speeches: int
    exact_matches: int
    partial_matches: int
    missed_by_regex: int  # Gemini found, regex missed
    false_positives: int  # Regex found, Gemini didn't confirm
    duplicates_detected: int
    matches: list[SpeechMatch] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    def precision(self) -> float:
        """Correctly identified / total regex found."""
        if self.total_regex_speeches == 0:
            return 0.0
        return (self.exact_matches + self.partial_matches) / self.total_regex_speeches

    def recall(self) -> float:
        """Correctly identified / total actual speeches (Gemini)."""
        if self.total_gemini_speeches == 0:
            return 0.0
        return (self.exact_matches + self.partial_matches) / self.total_gemini_speeches

    def f1_score(self) -> float:
        p = self.precision()
        r = self.recall()
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)


# Prompts for Gemini extraction
SYSTEM_INSTRUCTION = """You are an expert parser of German Bundestag Plenarprotokolle (parliamentary protocols).
Your task is to identify and extract all speeches from the protocol text.
Output as a JSON array. Be thorough - do not miss any speeches."""

EXTRACTION_PROMPT = """Analyze this German Bundestag Plenarprotokoll and extract ALL speeches.

For each speech, provide:
- speaker: Full name as written (e.g., "Dr. Alice Weidel", "Friedrich Merz")
- party: Party in parentheses if present (e.g., "CDU/CSU", "SPD"), or null for government officials
- role: Government role if applicable (e.g., "Bundeskanzler", "Bundesminister der Finanzen"), or null
- start_marker: The exact text that introduces this speaker (e.g., "Friedrich Merz, Bundeskanzler:" or "Josef Schuster (SPD):")
- text_preview: First 150 characters of the actual speech content (after the speaker line)
- speech_type: One of ["formal_speech", "question", "answer", "befragung", "fragestunde"]
- zwischenrufe: Array of interjections within this speech, each with {text, party} (can be empty)

INCLUDE:
- Government officials: "Name, Role:" format (e.g., "Lars Klingbeil, Bundesminister BMF:")
- Regular MPs: "Name (Party):" format (e.g., "Dr. Götz Frömming (AfD):")

EXCLUDE:
- Presiding officers' procedural remarks (Präsident/in, Vizepräsident/in)
- Table of contents entries at the beginning
- Headers and section titles

Return ONLY valid JSON array, no markdown formatting, no explanation.

Protocol text (may be truncated):
---
{protocol_text}
---"""


def normalize_name(name: str) -> str:
    """Normalize speaker name for comparison."""
    if not name:
        return ""
    # Remove academic titles
    name = re.sub(r"\b(Dr\.?|Prof\.?)\s*", "", name)
    # Remove extra whitespace
    name = " ".join(name.split())
    return name.lower().strip()


def normalize_party_for_compare(party: str | None) -> str:
    """Normalize party name for comparison."""
    if not party:
        return ""
    party = party.upper().strip()
    # Normalize common variations
    if "GRÜNE" in party or "BÜNDNIS" in party:
        return "GRÜNE"
    if "LINKE" in party:
        return "LINKE"
    return party


def text_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity ratio."""
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1[:200].lower(), text2[:200].lower()).ratio()


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def fuzzy_name_match(name1: str, name2: str, threshold: int = 3) -> bool:
    """Check if two names match (fuzzy)."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    # Exact match
    if n1 == n2:
        return True

    # Levenshtein distance
    if levenshtein_distance(n1, n2) <= threshold:
        return True

    # Last name match
    parts1 = n1.split()
    parts2 = n2.split()
    if parts1 and parts2 and parts1[-1] == parts2[-1]:
        return True

    return False


class ParserEvaluator:
    """Orchestrates comparison between Gemini and regex parsing."""

    def __init__(self, gemini_client: GeminiClient, cache_dir: Path | None = None):
        self.gemini = gemini_client
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    async def extract_speeches_with_gemini(
        self, full_text: str, protocol_id: str
    ) -> list[GeminiSpeech]:
        """Extract speeches using Gemini."""
        # Check cache first
        if self.cache_dir:
            cache_file = self.cache_dir / f"{protocol_id}_gemini.json"
            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text())
                    return [GeminiSpeech(**s) for s in data]
                except (json.JSONDecodeError, TypeError):
                    pass

        # Truncate text if too long (Gemini has token limits)
        # ~4 chars per token, 1M tokens for pro, 128K for flash
        max_chars = 400_000  # Safe limit for flash
        truncated = full_text[:max_chars]
        if len(full_text) > max_chars:
            truncated += "\n\n[TEXT TRUNCATED]"

        # Use string concatenation to avoid format issues with curly braces in protocol text
        prompt = EXTRACTION_PROMPT.replace("{protocol_text}", truncated)

        response = await self.gemini.generate(
            prompt=prompt,
            system_instruction=SYSTEM_INSTRUCTION,
            model="gemini-2.5-flash",
        )

        # Parse JSON response
        speeches_data = self._parse_gemini_response(response)

        # Cache the result
        if self.cache_dir:
            cache_file = self.cache_dir / f"{protocol_id}_gemini.json"
            cache_file.write_text(json.dumps(speeches_data, ensure_ascii=False, indent=2))

        # Convert to GeminiSpeech objects with error handling
        speeches = []
        for s in speeches_data:
            try:
                # Ensure required fields have defaults
                speech = GeminiSpeech(
                    speaker=s.get("speaker", "Unknown"),
                    party=s.get("party"),
                    role=s.get("role"),
                    text_preview=s.get("text_preview", ""),
                    start_marker=s.get("start_marker", ""),
                    speech_type=s.get("speech_type", "unknown"),
                    zwischenrufe=s.get("zwischenrufe", []) if isinstance(s.get("zwischenrufe"), list) else [],
                )
                speeches.append(speech)
            except Exception:
                # Skip malformed entries
                continue
        return speeches

    def _parse_gemini_response(self, response: str) -> list[dict]:
        """Parse Gemini's JSON response with error handling."""
        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding array in response
        array_match = re.search(r"\[[\s\S]*\]", response)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass

        # Return empty if all parsing fails
        return []

    def match_speeches(
        self,
        gemini_speeches: list[GeminiSpeech],
        regex_speeches: list[dict],
    ) -> list[SpeechMatch]:
        """Match Gemini-extracted speeches with regex-extracted speeches."""
        matches: list[SpeechMatch] = []
        used_regex: set[int] = set()
        used_gemini: set[int] = set()

        # Pass 1: Exact speaker + party match
        for gi, g in enumerate(gemini_speeches):
            if gi in used_gemini:
                continue
            for ri, r in enumerate(regex_speeches):
                if ri in used_regex:
                    continue
                if fuzzy_name_match(g.speaker, r.get("speaker", "")):
                    g_party = normalize_party_for_compare(g.party)
                    r_party = normalize_party_for_compare(r.get("party"))
                    # Party match or government official (no party)
                    if g_party == r_party or (g.role and not g.party):
                        issues = []
                        if g_party != r_party and g_party and r_party:
                            issues.append(f"party mismatch: {g.party} vs {r.get('party')}")
                        matches.append(
                            SpeechMatch(
                                gemini_speech=g,
                                regex_speech=r,
                                match_type="exact",
                                issues=issues,
                            )
                        )
                        used_regex.add(ri)
                        used_gemini.add(gi)
                        break

        # Pass 2: Fuzzy text match for remaining
        for gi, g in enumerate(gemini_speeches):
            if gi in used_gemini:
                continue
            best_match = None
            best_sim = 0.0
            for ri, r in enumerate(regex_speeches):
                if ri in used_regex:
                    continue
                sim = text_similarity(g.text_preview, r.get("text", "")[:200])
                if sim > 0.5 and sim > best_sim:
                    best_sim = sim
                    best_match = (ri, r)

            if best_match:
                ri, r = best_match
                issues = [f"matched by text similarity ({best_sim:.0%})"]
                if not fuzzy_name_match(g.speaker, r.get("speaker", "")):
                    issues.append(f"speaker mismatch: {g.speaker} vs {r.get('speaker')}")
                matches.append(
                    SpeechMatch(
                        gemini_speech=g,
                        regex_speech=r,
                        match_type="partial",
                        issues=issues,
                    )
                )
                used_regex.add(ri)
                used_gemini.add(gi)

        # Remaining unmatched from Gemini (missed by regex)
        for gi, g in enumerate(gemini_speeches):
            if gi not in used_gemini:
                matches.append(
                    SpeechMatch(
                        gemini_speech=g,
                        regex_speech=None,
                        match_type="gemini_only",
                        issues=[f"MISSED: {g.speaker} ({g.party or g.role})"],
                    )
                )

        # Remaining unmatched from regex (false positives or Gemini missed)
        for ri, r in enumerate(regex_speeches):
            if ri not in used_regex:
                matches.append(
                    SpeechMatch(
                        gemini_speech=None,
                        regex_speech=r,
                        match_type="regex_only",
                        issues=[f"REGEX ONLY: {r.get('speaker')} ({r.get('party')})"],
                    )
                )

        return matches

    def detect_duplicates(
        self, speeches: list[dict]
    ) -> list[tuple[dict, dict, float]]:
        """Find potential duplicates (same speech extracted twice)."""
        duplicates: list[tuple[dict, dict, float]] = []

        for i, s1 in enumerate(speeches):
            for j, s2 in enumerate(speeches[i + 1 :], i + 1):
                # Same speaker
                if fuzzy_name_match(
                    s1.get("speaker", ""), s2.get("speaker", "")
                ):
                    # Check text similarity
                    text1 = s1.get("text", "")[:500]
                    text2 = s2.get("text", "")[:500]
                    sim = SequenceMatcher(None, text1, text2).ratio()
                    if sim > 0.85:
                        duplicates.append((s1, s2, sim))

        return duplicates

    async def evaluate_protocol(
        self,
        protocol_id: str,
        full_text: str,
        document_number: str = "",
    ) -> EvaluationResult:
        """Evaluate parser accuracy for a single protocol."""
        # Run regex parser
        regex_speeches = parse_speeches_from_protocol(full_text)

        # Run Gemini extraction
        gemini_speeches = await self.extract_speeches_with_gemini(full_text, protocol_id)

        # Match speeches
        matches = self.match_speeches(gemini_speeches, regex_speeches)

        # Detect duplicates in regex output
        duplicates = self.detect_duplicates(regex_speeches)

        # Count match types
        exact = sum(1 for m in matches if m.match_type == "exact")
        partial = sum(1 for m in matches if m.match_type == "partial")
        missed = sum(1 for m in matches if m.match_type == "gemini_only")
        false_pos = sum(1 for m in matches if m.match_type == "regex_only")

        # Collect issues
        issues: list[str] = []
        for m in matches:
            if m.issues:
                issues.extend(m.issues)
        for d1, d2, sim in duplicates:
            issues.append(
                f"DUPLICATE ({sim:.0%}): {d1.get('speaker')} appears multiple times"
            )

        return EvaluationResult(
            protocol_id=protocol_id,
            document_number=document_number,
            total_gemini_speeches=len(gemini_speeches),
            total_regex_speeches=len(regex_speeches),
            exact_matches=exact,
            partial_matches=partial,
            missed_by_regex=missed,
            false_positives=false_pos,
            duplicates_detected=len(duplicates),
            matches=matches,
            issues=issues,
        )


async def evaluate_protocols(
    data_dir: Path,
    sample_size: int = 3,
    protocol_id: int | None = None,
    cache_dir: Path | None = None,
) -> list[EvaluationResult]:
    """Evaluate parser on multiple protocols."""
    store = DataStore(data_dir)
    protocols = store.get_downloaded_protocols()

    if not protocols:
        raise ValueError(f"No protocols found in {data_dir}")

    # Filter to specific protocol if requested
    if protocol_id:
        protocols = [p for p in protocols if str(p.get("data", {}).get("id")) == str(protocol_id)]
        if not protocols:
            raise ValueError(f"Protocol {protocol_id} not found")
    else:
        # Sample randomly
        import random
        if len(protocols) > sample_size:
            protocols = random.sample(protocols, sample_size)

    results: list[EvaluationResult] = []

    async with GeminiClient() as client:
        evaluator = ParserEvaluator(client, cache_dir=cache_dir)

        for protocol in protocols:
            data = protocol.get("data", {})
            full_text = protocol.get("fullText", "")
            pid = str(data.get("id", "unknown"))
            doc_num = data.get("dokumentnummer", "")

            result = await evaluator.evaluate_protocol(pid, full_text, doc_num)
            results.append(result)

    return results
