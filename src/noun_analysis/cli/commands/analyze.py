"""Analyze commands for word frequency analysis."""

import asyncio

import click
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from noun_analysis.analyzer import WordAnalyzer, AnalysisResult, load_analyzer
from noun_analysis.parser import BundestagMCPClient, test_connection
from noun_analysis.storage import DataStore

from ..constants import console
from ..display import display_results, display_comparison
from ..export import export_scientific_results


@click.command()
@click.pass_context
def test(ctx):
    """Test connection to the MCP server."""
    server = ctx.obj["server"]
    console.print(f"Testing connection to [blue]{server}[/]...")

    success = asyncio.run(test_connection(server))

    if success:
        console.print("[green]Connection successful![/]")
    else:
        console.print("[red]Connection failed![/]")
        raise SystemExit(1)


@click.command()
@click.argument("data_dir", type=click.Path(), required=False)
@click.option("--parties", "-p", multiple=True, help="Parties to analyze (default: all found)")
@click.option("--wahlperiode", "-w", default=20, help="Legislative period")
@click.option("--max-protocols", "-m", default=5, help="Max Plenarprotokolle (0 = all)")
@click.option("--model", default="de_core_news_lg", help="spaCy model")
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for results")
@click.option("--top", "-n", default=30, help="Number of top words to show per type")
@click.option("--quiet", "-q", is_flag=True, help="Suppress table output (for batch processing)")
@click.pass_context
def analyze(ctx, data_dir, parties, wahlperiode, max_protocols, model, output_dir, top, quiet):
    """Analyze word frequency (nouns, adjectives, verbs) across parties.

    If DATA_DIR is provided, reads from cached speeches.json (requires 'parse' step first).
    Otherwise, fetches directly from MCP server.
    """
    server = ctx.obj["server"]
    selected_parties = set(parties) if parties else None

    console.print(f"\n[bold]Bundestag Word Frequency Analysis[/]")

    # Load analyzer
    with console.status("Loading spaCy model..."):
        try:
            analyzer = load_analyzer(model)
        except RuntimeError as e:
            console.print(f"[red]{e}[/]")
            raise SystemExit(1)

    console.print(f"[green]Loaded model: {model}[/]\n")

    # Check if using cached data
    if data_dir:
        store = DataStore(data_dir)
        speeches_by_party = store.load_speeches()

        if speeches_by_party is None:
            console.print(f"[red]No speeches.json found in {data_dir}. Run 'parse' first.[/]")
            raise SystemExit(1)

        console.print(f"Source: [cyan]{data_dir}/speeches.json[/]")
        state = store.load_state()
        wahlperiode = state.get("wahlperiode", wahlperiode)
        console.print(f"Wahlperiode: {wahlperiode}")

        # Filter parties if specified
        if selected_parties:
            speeches_by_party = {
                p: s for p, s in speeches_by_party.items()
                if p in selected_parties
            }
            console.print(f"Filter parties: {', '.join(selected_parties)}")

        console.print(f"\n[bold]Found {len(speeches_by_party)} parties[/]\n")

        # Analyze each party (formal speeches only, matches speaker_stats behavior)
        results = []
        for party, speeches in speeches_by_party.items():
            # Filter to 'rede' type only - excludes ortskraefte, fragestunde, etc.
            rede_speeches = [s for s in speeches if s.get('type') == 'rede']
            with console.status(f"Analyzing {party}..."):
                result = analyzer.analyze_speeches(rede_speeches, party)
                results.append(result)
            console.print(
                f"  [dim]{party}: {len(rede_speeches)} speeches | "
                f"{result.total_nouns:,} nouns, "
                f"{result.total_adjectives:,} adj, "
                f"{result.total_verbs:,} verbs[/]"
            )
    else:
        # Existing behavior: fetch from server
        console.print(f"Server: {server}")
        console.print(f"Wahlperiode: {wahlperiode}")
        if max_protocols == 0:
            console.print("Protocols: [bold]ALL[/]")
        else:
            console.print(f"Max Plenarprotokolle: {max_protocols}")
        if selected_parties:
            console.print(f"Filter parties: {', '.join(selected_parties)}")
        console.print()

        # Use 0 for "all" which the client now handles with pagination
        fetch_limit = max_protocols

        # Fetch and analyze using Plenarprotokolle
        results = asyncio.run(
            _fetch_and_analyze_protocols(
                server, wahlperiode, fetch_limit, analyzer, selected_parties
            )
        )

    if not results:
        console.print("[yellow]No speeches found![/]")
        raise SystemExit(1)

    # Display results (unless quiet mode)
    if not quiet:
        display_results(results, top)

        # Compare parties
        if len(results) > 1:
            display_comparison(analyzer, results, top)

    # Export results
    if output_dir:
        export_scientific_results(results, output_dir, wahlperiode)
        console.print(f"\n[green]Results exported to {output_dir}/[/]")


async def _fetch_and_analyze_protocols(
    server: str,
    wahlperiode: int,
    max_protocols: int,
    analyzer: WordAnalyzer,
    selected_parties: set[str] | None = None,
) -> list[AnalysisResult]:
    """Fetch speeches from Plenarprotokolle and analyze them."""
    results = []

    async with BundestagMCPClient(server) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            # Total will be updated once we know how many protocols exist
            task = progress.add_task("Fetching Plenarprotokolle...", total=None)

            def update_progress(current, total, doc_nr):
                progress.update(task, completed=current, total=total,
                              description=f"Fetching {doc_nr}...")

            # Fetch all speeches grouped by party (batch_size=20 for stability)
            speeches_by_party = await client.get_speeches_from_protocols(
                wahlperiode=wahlperiode,
                max_protocols=max_protocols,
                progress_callback=update_progress,
                batch_size=20,
            )

        # Filter parties if specified
        if selected_parties:
            speeches_by_party = {
                p: s for p, s in speeches_by_party.items()
                if p in selected_parties
            }

        # Analyze each party (formal speeches only, matches speaker_stats behavior)
        console.print(f"\n[bold]Found {len(speeches_by_party)} parties[/]\n")

        for party, speeches in speeches_by_party.items():
            # Filter to 'rede' type only - excludes ortskraefte, fragestunde, etc.
            rede_speeches = [s for s in speeches if s.get('type') == 'rede']
            with console.status(f"Analyzing {party}..."):
                result = analyzer.analyze_speeches(rede_speeches, party)
                results.append(result)
            console.print(
                f"  [dim]{party}: {len(rede_speeches)} speeches | "
                f"{result.total_nouns:,} nouns, "
                f"{result.total_adjectives:,} adj, "
                f"{result.total_verbs:,} verbs[/]"
            )

    return results
