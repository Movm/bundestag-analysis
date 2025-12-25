"""Export helper functions for CLI commands."""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from noun_analysis.analyzer import AnalysisResult

from .constants import console


def export_scientific_results(results: list[AnalysisResult], output_dir: str, wahlperiode: int):
    """Export comprehensive results for scientific analysis.

    Creates multiple files:
    - summary.json: Overview with metadata
    - nouns.csv: All nouns with counts and frequencies per party
    - adjectives.csv: All adjectives with counts and frequencies per party
    - verbs.csv: All verbs with counts and frequencies per party
    - full_data.json: Complete data for programmatic access
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    parties = [r.party for r in results]

    # Summary JSON
    summary = {
        "metadata": {
            "generated_at": timestamp,
            "wahlperiode": wahlperiode,
            "parties": parties,
            "total_speeches": sum(r.speech_count for r in results),
            "total_words": sum(r.total_words for r in results),
        },
        "party_stats": [
            {
                "party": r.party,
                "speeches": r.speech_count,
                "total_words": r.total_words,
                "unique_nouns": len(r.noun_counts),
                "unique_adjectives": len(r.adjective_counts),
                "unique_verbs": len(r.verb_counts),
                "total_nouns": r.total_nouns,
                "total_adjectives": r.total_adjectives,
                "total_verbs": r.total_verbs,
            }
            for r in results
        ],
    }
    (out_path / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)
    )

    # Export each word type to CSV
    for word_type, get_counts in [
        ("nouns", lambda r: r.noun_counts),
        ("adjectives", lambda r: r.adjective_counts),
        ("verbs", lambda r: r.verb_counts),
    ]:
        # Collect all unique words
        all_words = set()
        for r in results:
            all_words.update(get_counts(r).keys())

        rows = []
        for word in sorted(all_words):
            row = {"word": word}
            for r in results:
                count = get_counts(r)[word]
                row[f"{r.party}_count"] = count
                if r.total_words > 0:
                    row[f"{r.party}_per1000"] = round(
                        (count / r.total_words) * 1000, 4
                    )
                else:
                    row[f"{r.party}_per1000"] = 0.0
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(out_path / f"{word_type}.csv", index=False)

    # Full JSON export
    full_data = {
        "metadata": summary["metadata"],
        "results": [r.to_dict() for r in results],
    }
    (out_path / "full_data.json").write_text(
        json.dumps(full_data, ensure_ascii=False, indent=2)
    )

    console.print(f"  [dim]Created: summary.json, nouns.csv, adjectives.csv, verbs.csv, full_data.json[/]")


def export_evaluation_results(results: list, output_path: Path):
    """Export evaluation results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "evaluated_at": datetime.now().isoformat(),
        "protocols": [
            {
                "protocol_id": r.protocol_id,
                "document_number": r.document_number,
                "total_gemini_speeches": r.total_gemini_speeches,
                "total_regex_speeches": r.total_regex_speeches,
                "exact_matches": r.exact_matches,
                "partial_matches": r.partial_matches,
                "missed_by_regex": r.missed_by_regex,
                "false_positives": r.false_positives,
                "duplicates_detected": r.duplicates_detected,
                "precision": r.precision(),
                "recall": r.recall(),
                "f1_score": r.f1_score(),
                "issues": r.issues,
            }
            for r in results
        ],
    }

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
