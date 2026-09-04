"""Intro screen and main-menu prompts."""

from __future__ import annotations

from dataclasses import replace
from enum import Enum

from rich.console import Console
from rich.markup import escape

from holdem.ui.cli.brand import logo_banner
from holdem.ui.cli.interact import Cancelled, Prompter
from holdem.ui.cli.prompts import (
    DEFAULT_DISPLAY_NAME,
    MAX_DISPLAY_NAME_LENGTH,
    LineReader,
    PlayConfig,
    _read_difficulty,
    _read_text,
    prompt_play_config,
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
        logo_banner(subtitle="Play locally against bots, or host and join friends over Iroh.")
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

    console.print()
    console.print(logo_banner())
    console.print(f"[bold]Hi, {escape(display_name)}.[/bold]")
    console.print(f"[dim]Table: {table.summary()}[/dim]")
    console.print()
    try:
        return Prompter(reader=reader, console=console).select(
            "What would you like to do?",
            (
                ("New local game", MenuOption.NEW_GAME),
                ("Host a table", MenuOption.HOST),
                ("Join a table", MenuOption.JOIN),
                ("Table settings", MenuOption.SETTINGS),
                ("Change name", MenuOption.NAME),
                ("Quit", MenuOption.QUIT),
            ),
        )
    except Cancelled:
        return MenuOption.QUIT


def prompt_change_settings(
    *,
    reader: LineReader,
    console: Console,
    table: PlayConfig,
    local: bool = False,
) -> bool:
    """Choose whether to start, edit the settings, or go back."""

    console.print()
    console.print(f"[dim]{table.local_summary() if local else table.summary()}[/dim]")

    def confirmation_reader(_prompt: str) -> str:
        answer = reader("Change these settings? [y/N]: ").strip().lower()
        aliases = {"": "1", "n": "1", "no": "1", "y": "2", "yes": "2"}
        return aliases.get(answer, answer)

    selection_reader = reader if reader is input else confirmation_reader
    return Prompter(reader=selection_reader, console=console).select(
        "Ready to play?",
        (
            ("Start with these settings", False),
            ("Change settings", True),
        ),
        allow_back=True,
    )


def edit_table_settings(
    *,
    reader: LineReader,
    console: Console,
    table: PlayConfig,
    include_bots: bool = True,
) -> PlayConfig:
    """Prompt for table settings, using the current values as defaults."""

    return prompt_play_config(
        reader=reader,
        console=console,
        seed=table.seed,
        players=table.players,
        starting_stack=table.starting_stack,
        blinds=(table.small_blind, table.big_blind),
        bots=table.bots,
        difficulty=table.difficulty,
        include_bots=include_bots,
    )


def prompt_local_difficulty(
    *,
    reader: LineReader,
    console: Console,
    table: PlayConfig,
) -> PlayConfig:
    """Ask which heuristic bot difficulty to use for a local table."""

    return replace(
        table,
        difficulty=_read_difficulty(
            reader=reader,
            console=console,
            default=table.difficulty,
        ),
    )


def prompt_join_ticket(
    *,
    reader: LineReader,
    console: Console,
    ticket: str | None = None,
) -> str:
    """Collect a host ticket."""

    if ticket:
        console.print(f"Ticket: {ticket}")
        return ticket
    return Prompter(reader=reader, console=console).ask_text(
        "Table ticket (leave empty for Back)",
        allow_back=True,
    )


def wait_for_menu(*, reader: LineReader) -> None:
    reader("Press Enter to return to the menu: ")
