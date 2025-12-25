"""Download and parse commands for protocol data."""

import asyncio
import subprocess
import sys

import click
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from noun_analysis.parser import BundestagMCPClient, parse_speeches_from_protocol
from noun_analysis.storage import DataStore

from ..constants import console


@click.command()
@click.option("--model", default="de_core_news_lg", help="spaCy model to download")
def download_model(model: str):
    """Download the required spaCy model."""
    console.print(f"Downloading spaCy model: {model}")
    subprocess.run([sys.executable, "-m", "spacy", "download", model], check=True)
    console.print(f"[green]Model {model} downloaded successfully![/]")


@click.command()
@click.argument("data_dir", type=click.Path())
@click.option("--wahlperiode", "-w", default=20, help="Legislative period")
@click.option("--max-protocols", "-m", default=0, help="Max protocols (0 = all)")
@click.pass_context
def download(ctx, data_dir: str, wahlperiode: int, max_protocols: int):
    """Download Plenarprotokolle to disk for later analysis.

    Supports resume: if state.json exists, continues from where it left off.
    """
    server = ctx.obj["server"]
    store = DataStore(data_dir)

    # Check for resume mode
    if store.has_state():
        state = store.load_state()
        console.print(f"[yellow]Resuming download from {data_dir}[/]")
        console.print(f"  Server: {state['server']}")
        console.print(f"  Wahlperiode: {state['wahlperiode']}")

        pending = store.get_pending_ids(state)
        console.print(f"  Already downloaded: {len(state['downloaded'])}")
        console.print(f"  Pending: {len(pending)}")

        if not pending:
            console.print("[green]Download already complete![/]")
            return

        # Use server from state
        server = state["server"]
    else:
        state = None
        pending = None
        console.print(f"[bold]Starting fresh download to {data_dir}[/]")
        console.print(f"  Server: {server}")
        console.print(f"  Wahlperiode: {wahlperiode}")
        if max_protocols:
            console.print(f"  Max protocols: {max_protocols}")

    asyncio.run(_download_protocols(store, server, wahlperiode, max_protocols, state, pending))


async def _download_protocols(
    store: DataStore,
    server: str,
    wahlperiode: int,
    max_protocols: int,
    state: dict | None,
    pending: list[int] | None,
):
    """Download protocols with progress tracking."""
    async with BundestagMCPClient(server) as client:
        # If no state, fetch protocol list first
        if state is None:
            console.print("\nFetching protocol list...")
            protocols = await client.get_all_protocol_ids(
                wahlperiode=wahlperiode,
                herausgeber="BT",
                max_protocols=max_protocols,
            )
            protocol_ids = [int(p["id"]) for p in protocols]
            console.print(f"  Found {len(protocol_ids)} protocols")

            state = store.init_state(wahlperiode, server, protocol_ids)
            pending = protocol_ids

        # Download each protocol
        total = len(pending)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading...", total=total)

            for i, protocol_id in enumerate(pending):
                progress.update(task, description=f"Protocol {protocol_id}")

                try:
                    result = await client.get_plenarprotokoll(protocol_id, include_full_text=True)
                    if result:
                        store.save_protocol(protocol_id, result)
                        store.mark_downloaded(state, protocol_id)
                    else:
                        store.mark_failed(state, protocol_id)
                except Exception as e:
                    console.print(f"\n[red]Failed {protocol_id}: {e}[/]")
                    store.mark_failed(state, protocol_id)

                progress.update(task, completed=i + 1)

    # Summary
    summary = store.get_progress_summary()
    console.print(f"\n[green]Download complete![/]")
    console.print(f"  Downloaded: {summary['downloaded']}")
    if summary["failed"]:
        console.print(f"  [yellow]Failed: {summary['failed']} (will retry on next run)[/]")


@click.command()
@click.argument("data_dir", type=click.Path(exists=True))
def parse(data_dir: str):
    """Parse downloaded protocols into speeches.json."""
    store = DataStore(data_dir)

    if not store.has_state():
        console.print("[red]No state.json found. Run 'download' first.[/]")
        raise SystemExit(1)

    state = store.load_state()
    downloaded = state.get("downloaded", [])

    if not downloaded:
        console.print("[yellow]No protocols downloaded yet.[/]")
        raise SystemExit(1)

    console.print(f"[bold]Parsing {len(downloaded)} protocols...[/]")

    speeches_by_party: dict[str, list[dict]] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Parsing...", total=len(downloaded))

        for i, protocol_id in enumerate(downloaded):
            progress.update(task, description=f"Protocol {protocol_id}")

            protocol = store.load_protocol(protocol_id)
            if not protocol:
                continue

            full_text = protocol.get("fullText", "")
            if not full_text or not isinstance(full_text, str):
                continue

            speeches = parse_speeches_from_protocol(full_text)
            for speech in speeches:
                party = speech["party"]
                if party not in speeches_by_party:
                    speeches_by_party[party] = []
                speeches_by_party[party].append(speech)

            progress.update(task, completed=i + 1)

    # Save speeches
    store.save_speeches(speeches_by_party)

    # Update state
    state["parsed"] = True
    store.save_state(state)

    # Summary
    total_speeches = sum(len(s) for s in speeches_by_party.values())
    console.print(f"\n[green]Parsing complete![/]")
    console.print(f"  Total speeches: {total_speeches}")
    console.print(f"  Parties: {', '.join(speeches_by_party.keys())}")
    console.print(f"  Saved to: {store.speeches_file}")


@click.command()
@click.argument("data_dir", type=click.Path(exists=True))
def status(data_dir: str):
    """Show download/parse progress for a data directory."""
    store = DataStore(data_dir)
    summary = store.get_progress_summary()

    if summary["status"] == "not_started":
        console.print("[yellow]No download started in this directory.[/]")
        return

    table = Table(title=f"Status: {data_dir}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Wahlperiode", str(summary["wahlperiode"]))
    table.add_row("Server", summary["server"])
    table.add_row("Total protocols", str(summary["total_protocols"]))
    table.add_row("Downloaded", f"[green]{summary['downloaded']}[/]")
    table.add_row("Pending", str(summary["pending"]))
    if summary["failed"]:
        table.add_row("Failed", f"[red]{summary['failed']}[/]")
    table.add_row("Parsed", "[green]Yes[/]" if summary["parsed"] else "[yellow]No[/]")
    table.add_row("Last updated", summary["last_updated"] or "-")

    console.print(table)
