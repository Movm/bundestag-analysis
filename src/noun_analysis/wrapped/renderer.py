"""Terminal rendering for wrapped analysis using Rich."""

from __future__ import annotations
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .types import PARTY_COLORS

if TYPE_CHECKING:
    from . import WrappedData


class WrappedRenderer:
    """Render wrapped analysis to terminal using Rich."""

    def __init__(self, console: Console, use_emoji: bool = True):
        self.console = console
        self.use_emoji = use_emoji

    def _bar(self, value: float, max_value: float, width: int = 10) -> str:
        """Create a simple bar visualization."""
        filled = int((value / max_value) * width) if max_value > 0 else 0
        return "█" * filled + "░" * (width - filled)

    def _party_style(self, party: str) -> str:
        """Get Rich style for a party."""
        return PARTY_COLORS.get(party, "white")

    def render_header(self, data: WrappedData) -> None:
        """Render the header panel with summary stats."""
        meta = data.metadata
        total_speeches = meta.get("total_speeches", 0)
        total_words = meta.get("total_words", 0)
        parties = len(meta.get("parties", []))
        speakers = data.get_unique_speaker_count()
        wp = meta.get("wahlperiode", "?")

        header_text = Text()
        header_text.append("BUNDESTAG WRAPPED 2025\n", style="bold magenta")
        header_text.append(f"Wahlperiode {wp} - Your Year in Parliament\n\n", style="dim")
        header_text.append(f"{total_speeches:,} speeches", style="cyan")
        header_text.append(" | ", style="dim")
        header_text.append(f"{total_words:,} words", style="cyan")
        header_text.append(" | ", style="dim")
        header_text.append(f"{parties} parties", style="cyan")
        header_text.append(" | ", style="dim")
        header_text.append(f"{speakers} speakers", style="cyan")

        self.console.print(Panel(header_text, border_style="magenta"))
        self.console.print()

    def render_party_section(self, data: WrappedData, party: str) -> None:
        """Render analysis for a single party."""
        stats = data.party_stats.get(party, {})
        if not stats:
            return

        style = self._party_style(party)

        # Party header - use real_speeches (400+ words) if available
        speeches = stats.get("real_speeches", stats.get("speeches", 0))
        words = stats.get("total_words", 0)

        table = Table(
            title=f"{party}",
            title_style=f"bold {style}",
            border_style=style,
            show_header=False,
            expand=False,
            padding=(0, 1),
        )
        table.add_column("", style="dim")
        table.add_column("")

        table.add_row("Speeches", f"{speeches:,}")
        table.add_row("Words", f"{words:,}")

        # Speech length stats
        min_w = stats.get("min_words", 0)
        max_w = stats.get("max_words", 0)
        avg_w = stats.get("avg_words", 0)
        if max_w > 0:
            table.add_row("Speech length", f"{min_w}-{max_w} words (avg {avg_w:.0f})")

        # Academic title ratio
        dr_ratio = stats.get("dr_ratio", 0)
        dr_count = stats.get("dr_count", 0)
        if dr_count > 0:
            table.add_row("With Dr. title", f"{dr_ratio*100:.1f}% ({dr_count})")

        # Top nouns - expanded to 10
        top_nouns = data.top_words.get(party, {}).get("nouns", [])[:10]
        if top_nouns:
            max_count = top_nouns[0][1] if top_nouns else 1
            table.add_row("", "")
            table.add_row("[bold]Top 10 Words[/]", "")
            for word, count in top_nouns[:10]:
                bar = self._bar(count, max_count, 12)
                table.add_row(f"  {word}", f"{bar} {count:,}")

        # Key Topics (frequent + distinctive)
        key_topics = data.get_key_topics(party, "nouns", 5)
        if key_topics:
            table.add_row("", "")
            table.add_row("[bold]Key Topics[/]", "[dim](frequent + distinctive)[/]")
            for word, count, ratio in key_topics:
                table.add_row(f"  {word}", f"{count:,} ({ratio:.1f}x)")

        # Distinctive words - expanded to 10
        distinctive = data.get_distinctive_words(party, "nouns", 10)
        if distinctive:
            table.add_row("", "")
            table.add_row("[bold]Signature Words (10)[/]", "")
            for word, ratio in distinctive[:10]:
                table.add_row(f"  {word}", f"[dim]{ratio:.1f}x[/]")

        # Top 5 speakers for this party
        top_speakers = data.get_party_top_speakers(party, 5)
        if top_speakers:
            table.add_row("", "")
            table.add_row("[bold]Top Speakers[/]", "")
            medals = ["[yellow]1.[/]", "[white]2.[/]", "[orange3]3.[/]", "4.", "5."]
            for i, (speaker, count) in enumerate(top_speakers):
                rank = medals[i] if i < len(medals) else f"{i+1}."
                table.add_row(f"  {rank} {speaker}", f"{count} speeches")

        self.console.print(table)
        self.console.print()

    def render_speaker_section(self, data: WrappedData) -> None:
        """Render speaker leaderboard with formal speeches and question time."""
        medals = ["[yellow]1.[/]", "[white]2.[/]", "[orange3]3.[/]"]

        # TOP SPEAKERS (Formal Speeches)
        formal_speakers = data.get_formal_speakers(15)
        if formal_speakers:
            table = Table(
                title="TOP SPEAKERS (Formal Speeches)",
                title_style="bold yellow",
                border_style="yellow",
            )
            table.add_column("#", style="dim", width=3)
            table.add_column("Speaker", style="bold")
            table.add_column("Party", style="dim")
            table.add_column("Speeches", justify="right", style="cyan")

            for i, (speaker, party, count) in enumerate(formal_speakers):
                rank = medals[i] if i < 3 else f"{i+1}."
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                table.add_row(rank, speaker, party_styled, f"{count}")

            self.console.print(table)
            self.console.print()

        # QUESTION TIME CHAMPIONS
        question_speakers = data.get_question_time_speakers(10)
        if question_speakers:
            table = Table(
                title="QUESTION TIME CHAMPIONS",
                title_style="bold cyan",
                border_style="cyan",
            )
            table.add_column("#", style="dim", width=3)
            table.add_column("Speaker", style="bold")
            table.add_column("Party", style="dim")
            table.add_column("Questions", justify="right", style="cyan")

            for i, (speaker, party, count) in enumerate(question_speakers):
                rank = medals[i] if i < 3 else f"{i+1}."
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                table.add_row(rank, speaker, party_styled, f"{count}")

            self.console.print(table)
            self.console.print()

    def render_drama_section(self, data: WrappedData) -> None:
        """Render drama stats - interruptions, applause, heckles."""
        table = Table(
            title="DRAMA KINGS & QUEENS",
            title_style="bold red",
            border_style="red",
            show_header=False,
        )
        table.add_column("", width=45)
        table.add_column("", justify="right")

        # Top Interrupters - expanded to 10
        interrupters = data.get_top_interrupters(10)
        if interrupters:
            table.add_row("[bold]Top 10 Interrupters[/]", "")
            for i, (name, party, count) in enumerate(interrupters):
                medal = ["[yellow]1.[/]", "[white]2.[/]", "[orange3]3.[/]"][i] if i < 3 else f"{i+1}."
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                table.add_row(f"  {medal} {name} ({party_styled})", f"{count}")

        table.add_row("", "")

        # Most Interrupted - expanded to 10
        interrupted = data.get_most_interrupted(10)
        if interrupted:
            table.add_row("[bold]Most Interrupted (10)[/]", "")
            for i, (name, party, count) in enumerate(interrupted):
                medal = ["[yellow]1.[/]", "[white]2.[/]", "[orange3]3.[/]"][i] if i < 3 else f"{i+1}."
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                table.add_row(f"  {medal} {name} ({party_styled})", f"{count} times")

        table.add_row("", "")

        # Applause Champions
        applause = data.get_applause_ranking(6)
        if applause:
            table.add_row("[bold]Applause by Party[/]", "")
            for target, count in applause:
                table.add_row(f"  {target}", f"{count:,}")

        table.add_row("", "")

        # Heckle Sources
        heckles = data.get_heckle_ranking(6)
        if heckles:
            table.add_row("[bold]Heckles by Party[/]", "")
            for source, count in heckles:
                table.add_row(f"  {source}", f"{count:,}")

        self.console.print(table)
        self.console.print()

    def render_records_section(self, data: WrappedData) -> None:
        """Render records - marathon speakers, verbose speakers."""
        table = Table(
            title="RECORDS & STATS",
            title_style="bold green",
            border_style="green",
            show_header=False,
        )
        table.add_column("", width=45)
        table.add_column("", justify="right")

        # Marathon speakers (longest single speeches)
        marathon = data.get_marathon_speakers(5)
        if marathon:
            table.add_row("[bold]Longest Speeches[/]", "")
            for i, (name, party, words) in enumerate(marathon):
                medal = ["[yellow]1.[/]", "[white]2.[/]", "[orange3]3.[/]"][i] if i < 3 else f"{i+1}."
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                table.add_row(f"  {medal} {name} ({party_styled})", f"{words:,} words")

        table.add_row("", "")

        # Verbose speakers (highest avg words per speech)
        verbose = data.get_verbose_speakers(5, min_speeches=5)
        if verbose:
            table.add_row("[bold]Most Verbose (avg words, 5+ speeches)[/]", "")
            for i, (name, party, avg, count) in enumerate(verbose):
                medal = ["[yellow]1.[/]", "[white]2.[/]", "[orange3]3.[/]"][i] if i < 3 else f"{i+1}."
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                table.add_row(f"  {medal} {name} ({party_styled})", f"{avg:.0f} avg ({count} speeches)")

        table.add_row("", "")

        # Wordiest speakers (most total words)
        wordiest = data.get_wordiest_speakers(5)
        if wordiest:
            table.add_row("[bold]Most Words Total[/]", "")
            for i, (name, party, total, count) in enumerate(wordiest):
                medal = ["[yellow]1.[/]", "[white]2.[/]", "[orange3]3.[/]"][i] if i < 3 else f"{i+1}."
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                table.add_row(f"  {medal} {name} ({party_styled})", f"{total:,} words ({count} speeches)")

        table.add_row("", "")

        # Academic title ranking
        academic = data.get_academic_ranking()
        if academic:
            table.add_row("[bold]Academic Titles (Dr.) by Party[/]", "")
            for party, ratio, count, total in academic:
                if ratio > 0:
                    party_styled = f"[{self._party_style(party)}]{party}[/]"
                    table.add_row(f"  {party_styled}", f"{ratio*100:.1f}% ({count}/{total})")

        self.console.print(table)
        self.console.print()

    def render_vocabulary_section(self, data: WrappedData) -> None:
        """Render exclusive vocabulary - words only used by one party."""
        exclusive = data.get_exclusive_words(n=5, min_count=10)
        if not exclusive:
            return

        table = Table(
            title="EXCLUSIVE VOCABULARY",
            title_style="bold cyan",
            border_style="cyan",
            show_header=False,
        )
        table.add_column("Party", width=15)
        table.add_column("Words only this party uses", width=50)

        for party in data.metadata.get("parties", []):
            if party in exclusive:
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                words = ", ".join(f"{w} ({c})" for w, c in exclusive[party])
                table.add_row(party_styled, words)

        self.console.print(table)
        self.console.print()

    def render_topic_section(self, data: WrappedData) -> None:
        """Render hot topics and trends."""
        hot_topics = data.get_hot_topics(15)
        if not hot_topics:
            return

        topic_text = Text()
        topic_text.append("HOT TOPICS\n", style="bold cyan")
        topic_text.append("Words discussed by all parties\n\n", style="dim")

        for i, topic in enumerate(hot_topics):
            if i > 0:
                topic_text.append(" | ", style="dim")
            topic_text.append(topic, style="bold")

        self.console.print(Panel(topic_text, border_style="cyan"))
        self.console.print()

    def render_tone_section(self, data: WrappedData) -> None:
        """Render tone analysis section (Scheme D: Communication Style)."""
        if not data.has_tone_data():
            return

        # Main comparison table with Scheme D scores
        table = Table(
            title="TONE ANALYSIS (Communication Style)",
            title_style="bold magenta",
            border_style="magenta",
        )
        table.add_column("Party", style="bold", width=12)
        table.add_column("Affirm.", justify="right", width=8)
        table.add_column("Aggr.", justify="right", width=7)
        table.add_column("Label", justify="right", width=7)
        table.add_column("Collab.", justify="right", width=8)
        table.add_column("Solution", justify="right", width=8)

        for party in data.metadata.get("parties", []):
            if party not in data.tone_data:
                continue
            scores = data.tone_data[party]
            party_styled = f"[{self._party_style(party)}]{party}[/]"

            # Color-code the values (Scheme D)
            aff = scores.get("affirmative", 50)
            agg = scores.get("aggression", 0)
            label = scores.get("labeling", 0)
            collab = scores.get("collaboration", 50)
            sol = scores.get("solution_focus", 50)

            aff_style = "green" if aff > 55 else "red" if aff < 45 else ""
            agg_style = "red" if agg > 10 else "green" if agg < 5 else ""
            label_style = "magenta" if label > 3 else ""  # Highlight labeling
            collab_style = "green" if collab > 55 else "red" if collab < 45 else ""
            sol_style = "green" if sol > 55 else "red" if sol < 45 else ""

            table.add_row(
                party_styled,
                f"[{aff_style}]{aff:.0f}%[/]" if aff_style else f"{aff:.0f}%",
                f"[{agg_style}]{agg:.0f}%[/]" if agg_style else f"{agg:.0f}%",
                f"[{label_style}]{label:.0f}%[/]" if label_style else f"{label:.0f}%",
                f"[{collab_style}]{collab:.0f}%[/]" if collab_style else f"{collab:.0f}%",
                f"[{sol_style}]{sol:.0f}%[/]" if sol_style else f"{sol:.0f}%",
            )

        self.console.print(table)
        self.console.print()

        # Top labeling words by party (key Scheme D insight)
        label_table = Table(
            title="Ideological Labeling (Othering)",
            title_style="bold magenta",
            border_style="magenta",
            show_header=False,
        )
        label_table.add_column("Party", width=12)
        label_table.add_column("Top Labeling Adjectives", width=55)

        for party in data.metadata.get("parties", []):
            words = data.get_top_words_by_category(party, "adjectives", "labeling", 5)
            if words:
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                word_str = ", ".join(f"{w} ({c})" for w, c in words)
                label_table.add_row(party_styled, word_str)

        self.console.print(label_table)
        self.console.print()

        # Top aggressive words by party
        agg_table = Table(
            title="Most Aggressive Language",
            title_style="bold red",
            border_style="red",
            show_header=False,
        )
        agg_table.add_column("Party", width=12)
        agg_table.add_column("Top Aggressive Adjectives", width=55)

        for party in data.metadata.get("parties", []):
            words = data.get_top_words_by_category(party, "adjectives", "aggressive", 5)
            if words:
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                word_str = ", ".join(f"{w} ({c})" for w, c in words)
                agg_table.add_row(party_styled, word_str)

        self.console.print(agg_table)
        self.console.print()

        # Top collaborative words (Scheme D: collaborative verbs)
        collab_table = Table(
            title="Most Collaborative Language",
            title_style="bold blue",
            border_style="blue",
            show_header=False,
        )
        collab_table.add_column("Party", width=12)
        collab_table.add_column("Top Collaborative Verbs", width=55)

        for party in data.metadata.get("parties", []):
            words = data.get_top_words_by_category(party, "verbs", "collaborative", 5)
            if words:
                party_styled = f"[{self._party_style(party)}]{party}[/]"
                word_str = ", ".join(f"{w} ({c})" for w, c in words)
                collab_table.add_row(party_styled, word_str)

        self.console.print(collab_table)
        self.console.print()

    def render_all(self, data: WrappedData, parties: list[str] | None = None) -> None:
        """Render full wrapped report."""
        self.render_header(data)

        # Render party sections
        party_list = parties or data.metadata.get("parties", [])
        for party in party_list:
            self.render_party_section(data, party)

        self.render_speaker_section(data)
        self.render_records_section(data)
        self.render_drama_section(data)
        self.render_tone_section(data)
        self.render_vocabulary_section(data)
        self.render_topic_section(data)

        # Footer
        self.console.print(
            "[dim]Generated by noun-analysis | "
            "Data: Bundestag DIP API[/]"
        )
