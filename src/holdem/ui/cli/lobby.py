"""Intro screen, main menu, and coming-soon host/join flows."""

from __future__ import annotations

from enum import Enum

from rich.console import Console
from rich.markup import escape

from holdem.ui.cli.brand import logo_banner
from holdem.ui.cli.prompts import (
    DEFAULT_DISPLAY_NAME,
    MAX_DISPLAY_NAME_LENGTH,
    LineReader,
    PlayConfig,
    _read_text,
    _read_yes_no,
    prompt_play_config,
)

ONLINE_UNAVAILABLE = (
    "Online play is not available yet. The host/join lobby via Iroh lands in a later version."
)


class MenuOption(Enum):
    NEW_GAME = "1"
    HOST = "2"
    JOIN = "3"
    SETTINGS = "4"
    NAME = "5"
    QUIT = "6"


def show_intro(console: Console) -> None:
    """Print the one-time welcome banner."""

    console.print(
        logo_banner(
            subtitle="Play locally against bots. Host or join friends when online play lands."
        )
    )


def prompt_display_name(
    *,
    reader: LineReader,
    console: Console,
    default: str = DEFAULT_DISPLAY_NAME,
) -> str:
    """Ask what to call the local player."""

    return _read_text(
        "What should we call you?",
        reader=reader,
        console=console,
        default=default,
        maximum=MAX_DISPLAY_NAME_LENGTH,
    )


def prompt_menu_option(
    *,
    reader: LineReader,
    console: Console,
    display_name: str,
    table: PlayConfig,
) -> MenuOption:
    """Greet the player and collect a main-menu choice."""

    aliases = {"q": MenuOption.QUIT, "quit": MenuOption.QUIT}
    choices = {option.value: option for option in MenuOption}

    console.print()
    console.print(logo_banner())
    console.print(f"[bold]Hi, {escape(display_name)}.[/bold]")
    console.print(f"[dim]Table: {table.summary()}[/dim]")
    console.print()
    console.print("What would you like to do?")
    console.print("  [cyan]1[/cyan]. New local game")
    console.print("  [cyan]2[/cyan]. Host a table     [dim]coming soon[/dim]")
    console.print("  [cyan]3[/cyan]. Join a table     [dim]coming soon[/dim]")
    console.print("  [cyan]4[/cyan]. Table settings")
    console.print("  [cyan]5[/cyan]. Change name")
    console.print("  [cyan]6[/cyan]. Quit")

    while True:
        raw = reader("Choose: ").strip().lower()
        selected = choices.get(raw) or aliases.get(raw)
        if selected is not None:
            return selected
        console.print("[red]Choose one of the listed numbers.[/red]")


def prompt_change_settings(
    *,
    reader: LineReader,
    console: Console,
    table: PlayConfig,
) -> bool:
    """Ask whether to edit the current table settings."""

    console.print()
    console.print(f"[dim]{table.summary()}[/dim]")
    return _read_yes_no(
        "Change these settings?",
        reader=reader,
        console=console,
        default=False,
    )


def edit_table_settings(
    *,
    reader: LineReader,
    console: Console,
    table: PlayConfig,
) -> PlayConfig:
    """Prompt for table settings, using the current values as defaults."""

    return prompt_play_config(
        reader=reader,
        console=console,
        seed=table.seed,
        players=table.players,
        starting_stack=table.starting_stack,
        blinds=(table.small_blind, table.big_blind),
    )


def prompt_join_ticket(
    *,
    reader: LineReader,
    console: Console,
    ticket: str | None = None,
) -> str:
    """Collect a host ticket. Empty is allowed; joining is not wired up yet."""

    if ticket:
        console.print(f"Ticket: {ticket}")
        return ticket
    return reader("Table ticket: ").strip()


def show_host_unavailable(console: Console, table: PlayConfig) -> None:
    """Show the host-table screen without starting a network session."""

    console.print()
    console.print("[bold]Host a table[/bold]")
    console.print("Friends would see a ticket here and join your game.")
    console.print(f"[dim]This table: {table.summary()}[/dim]")
    console.print(f"[yellow]{ONLINE_UNAVAILABLE}[/yellow]")


def show_join_unavailable(console: Console, ticket: str) -> None:
    """Show the join-table screen without connecting."""

    console.print()
    console.print("[bold]Join a table[/bold]")
    if ticket:
        console.print(f"Ticket [cyan]{ticket}[/cyan] would be used to find the host.")
    else:
        console.print("You would paste a ticket from the host here.")
    console.print(f"[yellow]{ONLINE_UNAVAILABLE}[/yellow]")


def wait_for_menu(*, reader: LineReader) -> None:
    reader("Press Enter to return to the menu: ")
