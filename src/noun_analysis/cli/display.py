"""Display helper functions for CLI output."""

from rich.table import Table

from noun_analysis.analyzer import WordAnalyzer, AnalysisResult

from .constants import console


def display_results(results: list[AnalysisResult], top_n: int):
    """Display individual party results for all word types."""
    for result in results:
        # Nouns
        table = Table(title=f"\n{result.party} - Top {top_n} Nouns")
        table.add_column("Noun", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("per 1000", justify="right")

        freq = result.noun_frequency_per_1000()
        for word, count in result.top_nouns(top_n):
            table.add_row(word, str(count), f"{freq.get(word, 0):.2f}")
        console.print(table)

        # Adjectives
        table = Table(title=f"{result.party} - Top {top_n} Adjectives")
        table.add_column("Adjective", style="yellow")
        table.add_column("Count", justify="right")
        table.add_column("per 1000", justify="right")

        freq = result.adjective_frequency_per_1000()
        for word, count in result.top_adjectives(top_n):
            table.add_row(word, str(count), f"{freq.get(word, 0):.2f}")
        console.print(table)

        # Verbs
        table = Table(title=f"{result.party} - Top {top_n} Verbs")
        table.add_column("Verb", style="green")
        table.add_column("Count", justify="right")
        table.add_column("per 1000", justify="right")

        freq = result.verb_frequency_per_1000()
        for word, count in result.top_verbs(top_n):
            table.add_row(word, str(count), f"{freq.get(word, 0):.2f}")
        console.print(table)


def display_comparison(
    analyzer: WordAnalyzer, results: list[AnalysisResult], top_n: int
):
    """Display party comparison tables for all word types."""
    parties = [r.party for r in results]

    for word_type, title, style in [
        ("noun", "Nouns", "cyan"),
        ("adjective", "Adjectives", "yellow"),
        ("verb", "Verbs", "green"),
    ]:
        comparison = analyzer.compare_parties(results, top_n, word_type=word_type)

        table = Table(title=f"\n{title} - Party Comparison (per 1000 words)")
        table.add_column(title[:-1], style=style)

        for party in parties:
            table.add_column(party, justify="right")

        # Show top 20 most differentiating words
        for word, freqs in list(comparison.items())[:20]:
            row = [word]
            values = [freqs.get(p, 0) for p in parties]
            max_val = max(values) if values else 0

            for party in parties:
                val = freqs.get(party, 0)
                if val == max_val and max_val > 0:
                    row.append(f"[bold green]{val:.2f}[/]")
                else:
                    row.append(f"{val:.2f}")

            table.add_row(*row)

        console.print(table)


def display_evaluation_result(result, verbose: bool = False):
    """Display evaluation result for a single protocol."""
    console.print(f"\n[bold]Protocol {result.document_number or result.protocol_id}[/]")
    console.print("=" * 50)

    # Metrics table
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Precision", f"{result.precision():.1%}")
    table.add_row("Recall", f"{result.recall():.1%}")
    table.add_row("F1 Score", f"{result.f1_score():.1%}")
    console.print(table)
    console.print()

    # Counts table
    counts_table = Table(box=None)
    counts_table.add_column("", style="dim")
    counts_table.add_column("Gemini", justify="right")
    counts_table.add_column("Regex", justify="right")
    counts_table.add_column("Matched", justify="right", style="green")

    counts_table.add_row(
        "Speeches",
        str(result.total_gemini_speeches),
        str(result.total_regex_speeches),
        str(result.exact_matches + result.partial_matches),
    )
    counts_table.add_row(
        "Missed by regex",
        str(result.missed_by_regex),
        "-",
        "-",
        style="yellow" if result.missed_by_regex > 0 else None,
    )
    counts_table.add_row(
        "Regex only",
        "-",
        str(result.false_positives),
        "-",
        style="yellow" if result.false_positives > 0 else None,
    )
    counts_table.add_row(
        "Duplicates",
        "-",
        str(result.duplicates_detected),
        "-",
        style="red" if result.duplicates_detected > 0 else None,
    )
    console.print(counts_table)

    # Issues
    if result.issues:
        console.print("\n[bold]Issues Found:[/]")
        for issue in result.issues[:20]:  # Limit to 20 issues
            if "MISSED" in issue:
                console.print(f"  [yellow]⚠[/] {issue}")
            elif "DUPLICATE" in issue:
                console.print(f"  [red]✗[/] {issue}")
            else:
                console.print(f"  [dim]•[/] {issue}")
        if len(result.issues) > 20:
            console.print(f"  [dim]... and {len(result.issues) - 20} more issues[/]")

    # Verbose: show all matches
    if verbose and result.matches:
        console.print("\n[bold]Detailed Matches:[/]")
        for match in result.matches:
            match_type = match.match_type
            if match_type == "exact":
                icon = "[green]✓[/]"
            elif match_type == "partial":
                icon = "[yellow]~[/]"
            elif match_type == "gemini_only":
                icon = "[red]✗[/] MISSED"
            else:
                icon = "[blue]?[/] REGEX ONLY"

            speaker = match.gemini_speech.speaker if match.gemini_speech else match.regex_speech.get("speaker", "?")
            party = (match.gemini_speech.party if match.gemini_speech else match.regex_speech.get("party")) or "?"
            console.print(f"  {icon} {speaker} ({party})")


def display_aggregate_summary(results: list):
    """Display aggregate summary for multiple protocols."""
    console.print(f"\n[bold]Aggregate Summary ({len(results)} protocols)[/]")
    console.print("=" * 50)

    total_gemini = sum(r.total_gemini_speeches for r in results)
    total_regex = sum(r.total_regex_speeches for r in results)
    total_matched = sum(r.exact_matches + r.partial_matches for r in results)
    total_missed = sum(r.missed_by_regex for r in results)
    total_false_pos = sum(r.false_positives for r in results)
    total_duplicates = sum(r.duplicates_detected for r in results)

    precision = total_matched / total_regex if total_regex > 0 else 0
    recall = total_matched / total_gemini if total_gemini > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Overall Precision", f"{precision:.1%}")
    table.add_row("Overall Recall", f"{recall:.1%}")
    table.add_row("Overall F1 Score", f"{f1:.1%}")
    table.add_row("", "")
    table.add_row("Total Speeches (Gemini)", str(total_gemini))
    table.add_row("Total Speeches (Regex)", str(total_regex))
    table.add_row("Total Matched", str(total_matched))
    table.add_row("Total Missed", str(total_missed), style="yellow" if total_missed > 0 else None)
    table.add_row("Total False Positives", str(total_false_pos), style="yellow" if total_false_pos > 0 else None)
    table.add_row("Total Duplicates", str(total_duplicates), style="red" if total_duplicates > 0 else None)

    console.print(table)
