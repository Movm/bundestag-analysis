"""Parser evaluation command using Gemini."""

import asyncio
from pathlib import Path

import click

from noun_analysis.parser_evaluation import evaluate_protocols

from ..constants import console
from ..display import display_evaluation_result, display_aggregate_summary
from ..export import export_evaluation_results


@click.command("evaluate-parser")
@click.argument("data_dir", type=click.Path(exists=True), required=False, default="./data_wp21")
@click.option("--protocol-id", "-p", type=int, help="Specific protocol ID to evaluate")
@click.option("--sample-size", "-n", default=3, help="Number of protocols to sample")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed match information")
@click.option("--output", "-o", type=click.Path(), help="Export results to JSON")
@click.option("--model", default="gemini-2.5-flash", help="Gemini model to use")
@click.option("--cache-dir", type=click.Path(), default="./.eval_cache", help="Cache directory for Gemini responses")
def evaluate_parser(data_dir: str, protocol_id: int | None, sample_size: int, verbose: bool, output: str | None, model: str, cache_dir: str):
    """Evaluate regex parser accuracy against Gemini extraction.

    Uses Gemini to independently extract speeches from protocols
    and compares results with the regex-based parser.

    Metrics reported:
    - Precision: correctly identified / total regex found
    - Recall: correctly identified / total actual speeches
    - Missed speeches: Gemini found but regex missed
    - Duplicates: same speech tracked twice
    """
    console.print(f"\n[bold]Parser Evaluation (Gemini vs Regex)[/]")
    console.print(f"Data: [cyan]{data_dir}[/]")
    console.print(f"Model: [cyan]{model}[/]")

    if protocol_id:
        console.print(f"Protocol: [cyan]{protocol_id}[/]")
    else:
        console.print(f"Sample size: [cyan]{sample_size}[/]")

    console.print()

    try:
        with console.status("Evaluating protocols with Gemini..."):
            results = asyncio.run(
                evaluate_protocols(
                    data_dir=Path(data_dir),
                    sample_size=sample_size,
                    protocol_id=protocol_id,
                    cache_dir=Path(cache_dir) if cache_dir else None,
                )
            )
    except ValueError as e:
        console.print(f"[red]Error: {e}[/]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error during evaluation: {e}[/]")
        raise SystemExit(1)

    # Display results for each protocol
    for result in results:
        display_evaluation_result(result, verbose)

    # Aggregate summary if multiple protocols
    if len(results) > 1:
        display_aggregate_summary(results)

    # Export to JSON if requested
    if output:
        export_evaluation_results(results, Path(output))
        console.print(f"\n[green]Results exported to {output}[/]")
