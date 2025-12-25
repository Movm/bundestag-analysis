"""Wrapped commands for Bundestag Wrapped exports."""

import json
import time
from collections import Counter
from pathlib import Path

import click

from noun_analysis.wrapped import WrappedData, WrappedRenderer
from noun_analysis.wrapped.speaker_export import SpeakerExporter

from ..constants import console


@click.command()
@click.argument("data_dir", type=click.Path(exists=True), required=False, default="./data_wp21")
@click.option("--results-dir", "-r", type=click.Path(exists=True), default="./results_wp21", help="Results directory")
@click.option("--party", "-p", multiple=True, help="Filter to specific parties")
@click.option("--section", "-s", type=click.Choice(["party", "speaker", "drama", "topic", "all"]), default="all", help="Section to display")
@click.option("--no-emoji", is_flag=True, help="Disable emoji output")
def wrapped(data_dir: str, results_dir: str, party: tuple, section: str, no_emoji: bool):
    """Generate Bundestag Wrapped 2025 - Your Year in Parliament."""
    console.print()

    try:
        data = WrappedData.load(Path(results_dir), Path(data_dir))
    except FileNotFoundError as e:
        console.print(f"[red]Error: Could not load data - {e}[/]")
        console.print("[dim]Make sure to run 'analyze' first to generate results.[/]")
        raise SystemExit(1)

    renderer = WrappedRenderer(console, use_emoji=not no_emoji)
    parties = list(party) if party else None

    if section == "all":
        renderer.render_all(data, parties)
    elif section == "party":
        renderer.render_header(data)
        for p in (parties or data.metadata["parties"]):
            renderer.render_party_section(data, p)
    elif section == "speaker":
        renderer.render_header(data)
        renderer.render_speaker_section(data)
    elif section == "drama":
        renderer.render_header(data)
        renderer.render_drama_section(data)
    elif section == "topic":
        renderer.render_header(data)
        renderer.render_topic_section(data)


@click.command("export-web")
@click.argument("data_dir", type=click.Path(exists=True), required=False, default="./data_wp21")
@click.option("--results-dir", "-r", type=click.Path(exists=True), default="./results_wp21", help="Results directory")
@click.option("--output", "-o", type=click.Path(), default="./web/public/wrapped.json", help="Output JSON file")
def export_web(data_dir: str, results_dir: str, output: str):
    """Export wrapped data as JSON for the web app."""
    console.print(f"[bold]Exporting wrapped data for web app...[/]")
    console.print(f"  Data dir: {data_dir}")
    console.print(f"  Results dir: {results_dir}")

    try:
        data = WrappedData.load(Path(results_dir), Path(data_dir))
    except FileNotFoundError as e:
        console.print(f"[red]Error: Could not load data - {e}[/]")
        console.print("[dim]Make sure to run 'analyze' first to generate results.[/]")
        raise SystemExit(1)

    # Export to JSON
    web_data = data.to_web_json()
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(web_data, ensure_ascii=False, indent=2))

    console.print(f"\n[green]Exported to {output}[/]")
    console.print(f"  Parties: {len(web_data['parties'])}")
    console.print(f"  Top speakers: {len(web_data['topSpeakers'])}")
    console.print(f"  Moin speakers: {len(web_data.get('moinSpeakers', []))}")


@click.command("export-speakers")
@click.argument("data_dir", type=click.Path(exists=True), required=False, default="./data_wp21")
@click.option("--results-dir", "-r", type=click.Path(exists=True), default="./results_wp21", help="Results directory")
@click.option("--output", "-o", type=click.Path(), default="./web/public/speakers/", help="Output directory")
def export_speakers(data_dir: str, results_dir: str, output: str):
    """Export individual Bundestag Wrapped data for each speaker."""
    console.print(f"[bold]Exporting individual speaker wrapped data...[/]")
    console.print(f"  Data dir: {data_dir}")
    console.print(f"  Results dir: {results_dir}")

    try:
        data = WrappedData.load(Path(results_dir), Path(data_dir))
    except FileNotFoundError as e:
        console.print(f"[red]Error: Could not load data - {e}[/]")
        console.print("[dim]Make sure to run 'analyze' first to generate results.[/]")
        raise SystemExit(1)

    exporter = SpeakerExporter(data)
    result = exporter.export_all(Path(output))

    console.print(f"\n[green]Exported to {result['output_dir']}[/]")
    console.print(f"  Index: {result['index_path']}")
    console.print(f"  Speakers: {result['speakers_exported']}")
    if result.get('stale_deleted', 0) > 0:
        console.print(f"  [yellow]Cleaned up: {result['stale_deleted']} stale files[/]")


@click.command("export-speeches")
@click.argument("data_dir", type=click.Path(exists=True), required=False, default="./data_wp21")
@click.option("--output", "-o", type=click.Path(), default="./web/public/speeches_db.json", help="Output JSON file")
def export_speeches(data_dir: str, output: str):
    """Export searchable speech database for transparency page."""
    data_path = Path(data_dir)
    console.print(f"[bold]Exporting speech database...[/]")

    # Load speeches
    speeches_file = data_path / "speeches.json"
    if not speeches_file.exists():
        console.print(f"[red]Error: {speeches_file} not found[/]")
        raise SystemExit(1)

    with open(speeches_file) as f:
        speeches_by_party = json.load(f)

    # Load protocol metadata for dates
    protocols_dir = data_path / "protocols"
    protocol_dates = {}
    if protocols_dir.exists():
        for pfile in protocols_dir.glob("*.json"):
            try:
                with open(pfile) as f:
                    pdata = json.load(f)
                data = pdata.get("data", {})
                doc_num = data.get("dokumentnummer", "")
                datum = data.get("datum", "")
                if doc_num and datum:
                    protocol_dates[doc_num] = datum
            except Exception:
                pass

    # Build speech database
    speeches = []
    speakers_set = set()
    parties_set = set()

    speech_id = 0
    for party, party_speeches in speeches_by_party.items():
        parties_set.add(party)
        for speech in party_speeches:
            speech_id += 1
            speaker = speech.get("speaker", "")
            speakers_set.add(speaker)

            text = speech.get("text", "")
            preview = text[:150].replace("\n", " ").strip()
            if len(text) > 150:
                preview += "..."

            speech_type = speech.get("type", "unknown")
            category = speech.get("category", "rede" if speech_type == "rede" else "wortbeitrag")

            speeches.append({
                "id": speech_id,
                "speaker": speaker,
                "party": party,
                "type": speech_type,
                "category": category,
                "words": speech.get("words", 0),
                "text": text,
                "preview": preview,
            })

    # Sort by speaker name for consistent ordering
    speeches.sort(key=lambda x: (x["speaker"], x["id"]))

    # Reassign IDs after sorting
    for i, s in enumerate(speeches, 1):
        s["id"] = i

    # Build output
    output_data = {
        "speeches": speeches,
        "speakers": sorted(speakers_set),
        "parties": sorted(parties_set),
        "totalSpeeches": len(speeches),
    }

    # Write output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2))

    console.print(f"\n[green]Exported to {output}[/]")
    console.print(f"  Speeches: {len(speeches)}")
    console.print(f"  Speakers: {len(speakers_set)}")
    console.print(f"  Parties: {len(parties_set)}")


@click.command("export-interruptions")
@click.argument("data_dir", type=click.Path(exists=True), required=False, default="./data_wp21")
@click.option("--results-dir", "-r", type=click.Path(exists=True), default="./results_wp21", help="Results directory")
@click.option("--output", "-o", type=click.Path(), default="./web/public/", help="Output directory")
def export_interruptions(data_dir: str, results_dir: str, output: str):
    """Export interruption rankings as JSON files for transparency."""
    console.print(f"[bold]Exporting interruption data...[/]")
    console.print(f"  Data dir: {data_dir}")
    console.print(f"  Results dir: {results_dir}")

    try:
        data = WrappedData.load(Path(results_dir), Path(data_dir))
    except FileNotFoundError as e:
        console.print(f"[red]Error: Could not load data - {e}[/]")
        console.print("[dim]Make sure to run 'analyze' first to generate results.[/]")
        raise SystemExit(1)

    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    # Export all Zwischenrufer (who makes interjections)
    interrupters = data.get_top_interrupters(1000)  # Get all
    positive = data.drama_stats.get("positive_interjections", {})
    negative = data.drama_stats.get("negative_interjections", {})
    neutral = data.drama_stats.get("neutral_interjections", {})

    # Calculate totals
    total_positive = sum(positive.values())
    total_negative = sum(negative.values())
    total_neutral = sum(neutral.values())
    total_all = total_positive + total_negative + total_neutral

    interrupters_data = {
        "title": "Top Zwischenrufer",
        "description": "Abgeordnete nach Anzahl der Zwischenrufe (wer ruft am häufigsten dazwischen)",
        "count": len(interrupters),
        "stats": {
            "total": total_all,
            "positive": total_positive,
            "negative": total_negative,
            "neutral": total_neutral,
            "positivePercent": round(total_positive / total_all * 100, 1) if total_all > 0 else 0,
            "negativePercent": round(total_negative / total_all * 100, 1) if total_all > 0 else 0,
            "neutralPercent": round(total_neutral / total_all * 100, 1) if total_all > 0 else 0,
        },
        "classification": {
            "positive": ["genau", "richtig", "bravo", "stimmt", "sehr gut", "prima", "..."],
            "negative": ["unsinn", "quatsch", "falsch", "lüge", "peinlich", "skandal", "..."],
            "neutral": "Alles andere (Fragen, Kommentare, nicht klar zuordnenbar)",
        },
        "data": [
            {
                "rank": i + 1,
                "name": n,
                "party": p,
                "count": c,
                "positive": positive.get((n, p), 0),
                "negative": negative.get((n, p), 0),
                "neutral": neutral.get((n, p), 0),
            }
            for i, (n, p, c) in enumerate(interrupters)
        ],
    }
    interrupters_file = output_path / "zwischenrufer.json"
    interrupters_file.write_text(json.dumps(interrupters_data, ensure_ascii=False, indent=2))
    console.print(f"  [green]✓[/] {interrupters_file} ({len(interrupters)} entries: {total_positive} positiv, {total_negative} negativ, {total_neutral} neutral)")

    # Export all interrupted (who gets interrupted)
    interrupted = data.get_most_interrupted(1000)  # Get all
    interrupted_data = {
        "title": "Meistens unterbrochen",
        "description": "Abgeordnete nach Anzahl erhaltener Zwischenrufe (wer wird am häufigsten unterbrochen)",
        "count": len(interrupted),
        "data": [
            {"rank": i + 1, "name": n, "party": p, "count": c}
            for i, (n, p, c) in enumerate(interrupted)
        ],
    }
    interrupted_file = output_path / "interrupted.json"
    interrupted_file.write_text(json.dumps(interrupted_data, ensure_ascii=False, indent=2))
    console.print(f"  [green]✓[/] {interrupted_file} ({len(interrupted)} entries)")

    console.print(f"\n[green]Exported interruption data![/]")


@click.command("export-neutral-texts")
@click.argument("data_dir", type=click.Path(exists=True), required=False, default="./data_wp21")
@click.option("--results-dir", "-r", type=click.Path(exists=True), default="./results_wp21", help="Results directory")
@click.option("--output", "-o", type=click.Path(), default="./web/public/neutral_interjections.json", help="Output file")
def export_neutral_texts(data_dir: str, results_dir: str, output: str):
    """Export all neutral interjection texts for pattern analysis."""
    console.print(f"[bold]Exporting neutral interjection texts...[/]")

    try:
        data = WrappedData.load(Path(results_dir), Path(data_dir))
    except FileNotFoundError as e:
        console.print(f"[red]Error: Could not load data - {e}[/]")
        raise SystemExit(1)

    neutral_texts = data.drama_stats.get("neutral_texts", [])

    # Count unique texts
    text_counts = Counter(neutral_texts)

    output_data = {
        "title": "Neutrale Zwischenrufe",
        "description": "Alle neutralen Zwischenruftexte für Muster-Analyse",
        "totalCount": len(neutral_texts),
        "uniqueCount": len(text_counts),
        "data": [
            {"text": text, "count": count}
            for text, count in text_counts.most_common()
        ],
    }

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2))

    console.print(f"  [green]✓[/] {output_path} ({len(neutral_texts)} total, {len(text_counts)} unique)")


@click.command("export-all")
@click.argument("data_dir", type=click.Path(exists=True), required=False, default="./data_wp21")
@click.option("--results-dir", "-r", type=click.Path(exists=True), default="./results_wp21", help="Results directory")
@click.option("--output-dir", "-o", type=click.Path(), default="./web/public", help="Output directory")
@click.option("--skip-speeches", is_flag=True, help="Skip large speech database export (~17MB)")
def export_all(data_dir: str, results_dir: str, output_dir: str, skip_speeches: bool):
    """Export all documentation JSON files at once.

    Loads data once and reuses it for all exports - faster than running
    individual export commands separately.
    """
    start_time = time.time()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Exporting all documentation files...[/]")
    console.print(f"  Data dir: {data_dir}")
    console.print(f"  Results dir: {results_dir}")
    console.print(f"  Output dir: {output_dir}")

    # Load WrappedData once - reuse for all exports
    console.print("\n[cyan]Loading data...[/]")
    try:
        data = WrappedData.load(Path(results_dir), Path(data_dir))
    except FileNotFoundError as e:
        console.print(f"[red]Error: Could not load data - {e}[/]")
        console.print("[dim]Make sure to run 'analyze' first to generate results.[/]")
        raise SystemExit(1)

    # 1. Export main wrapped.json
    console.print("\n[cyan]1/5[/cyan] Exporting wrapped.json...")
    web_data = data.to_web_json()
    wrapped_path = output_path / "wrapped.json"
    wrapped_path.write_text(json.dumps(web_data, ensure_ascii=False, indent=2))
    console.print(f"  [green]✓[/] {wrapped_path}")

    # 2. Export individual speaker profiles (uses optimized SpeakerExporter)
    console.print("\n[cyan]2/5[/cyan] Exporting speaker profiles...")
    speakers_dir = output_path / "speakers"
    exporter = SpeakerExporter(data)
    result = exporter.export_all(speakers_dir)
    console.print(f"  [green]✓[/] {result['speakers_exported']} speakers to {speakers_dir}")

    # 3. Export interruption data
    console.print("\n[cyan]3/5[/cyan] Exporting interruption data...")

    # Zwischenrufer
    interrupters = data.get_top_interrupters(1000)
    positive = data.drama_stats.get("positive_interjections", {})
    negative = data.drama_stats.get("negative_interjections", {})
    neutral = data.drama_stats.get("neutral_interjections", {})
    total_positive = sum(positive.values())
    total_negative = sum(negative.values())
    total_neutral = sum(neutral.values())
    total_all = total_positive + total_negative + total_neutral

    interrupters_data = {
        "title": "Top Zwischenrufer",
        "description": "Abgeordnete nach Anzahl der Zwischenrufe",
        "count": len(interrupters),
        "stats": {
            "total": total_all,
            "positive": total_positive,
            "negative": total_negative,
            "neutral": total_neutral,
        },
        "data": [
            {"rank": i + 1, "name": n, "party": p, "count": c,
             "positive": positive.get((n, p), 0),
             "negative": negative.get((n, p), 0),
             "neutral": neutral.get((n, p), 0)}
            for i, (n, p, c) in enumerate(interrupters)
        ],
    }
    (output_path / "zwischenrufer.json").write_text(json.dumps(interrupters_data, ensure_ascii=False, indent=2))

    # Interrupted
    interrupted = data.get_most_interrupted(1000)
    interrupted_data = {
        "title": "Meistens unterbrochen",
        "description": "Abgeordnete nach Anzahl erhaltener Zwischenrufe",
        "count": len(interrupted),
        "data": [{"rank": i + 1, "name": n, "party": p, "count": c} for i, (n, p, c) in enumerate(interrupted)],
    }
    (output_path / "interrupted.json").write_text(json.dumps(interrupted_data, ensure_ascii=False, indent=2))
    console.print(f"  [green]✓[/] zwischenrufer.json ({len(interrupters)} entries)")
    console.print(f"  [green]✓[/] interrupted.json ({len(interrupted)} entries)")

    # 4. Export neutral interjections
    console.print("\n[cyan]4/5[/cyan] Exporting neutral interjections...")
    neutral_texts = data.drama_stats.get("neutral_texts", [])
    text_counts = Counter(neutral_texts)
    neutral_data = {
        "title": "Neutrale Zwischenrufe",
        "description": "Alle neutralen Zwischenruftexte für Muster-Analyse",
        "totalCount": len(neutral_texts),
        "uniqueCount": len(text_counts),
        "data": [{"text": text, "count": count} for text, count in text_counts.most_common()],
    }
    (output_path / "neutral_interjections.json").write_text(json.dumps(neutral_data, ensure_ascii=False, indent=2))
    console.print(f"  [green]✓[/] neutral_interjections.json ({len(text_counts)} unique)")

    # 5. Export speech databases (optional - large files)
    if not skip_speeches:
        console.print("\n[cyan]5/5[/cyan] Exporting speech database...")
        speeches_file = Path(data_dir) / "speeches.json"
        if speeches_file.exists():
            with open(speeches_file) as f:
                speeches_by_party = json.load(f)

            speeches = []
            for party, party_speeches in speeches_by_party.items():
                for s in party_speeches:
                    speech_type = s.get("type", "other")
                    speeches.append({
                        "speaker": s.get("speaker", ""),
                        "party": party,
                        "text": s.get("text", "")[:500],
                        "words": s.get("words", 0),
                        "type": speech_type,
                        "category": s.get("category", "rede" if speech_type == "rede" else "wortbeitrag"),
                    })

            output_data = {"count": len(speeches), "speeches": speeches}
            (output_path / "speeches_db.json").write_text(json.dumps(output_data, ensure_ascii=False, indent=2))
            console.print(f"  [green]✓[/] speeches_db.json ({len(speeches)} speeches)")
        else:
            console.print(f"  [yellow]⚠[/] speeches.json not found, skipping")
    else:
        console.print("\n[dim]5/5 Skipping speech database (--skip-speeches)[/dim]")

    elapsed = time.time() - start_time
    console.print(f"\n[bold green]✓ All exports complete in {elapsed:.1f}s[/bold green]")
