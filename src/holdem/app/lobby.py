"""Lobby loop: intro, menu, local play, and host/join placeholders."""

from __future__ import annotations

from collections.abc import Callable

from rich.console import Console

from holdem.app.play import play_local
from holdem.ui.cli.lobby import (
    MenuOption,
    edit_table_settings,
    prompt_change_settings,
    prompt_display_name,
    prompt_join_ticket,
    prompt_menu_option,
    show_host_unavailable,
    show_intro,
    show_join_unavailable,
    wait_for_menu,
)
from holdem.ui.cli.prompts import LineReader, PlayConfig

PlayFn = Callable[..., int | None]


def run_lobby(
    *,
    console: Console,
    reader: LineReader = input,
    table: PlayConfig | None = None,
    display_name: str | None = None,
    opening: MenuOption | None = None,
    join_ticket: str | None = None,
    play: PlayFn = play_local,
) -> None:
    """Run the intro and main menu until the player quits."""

    session = table or PlayConfig()
    show_intro(console)
    name = display_name if display_name else prompt_display_name(reader=reader, console=console)
    pending = opening

    while True:
        choice = pending or prompt_menu_option(
            reader=reader,
            console=console,
            display_name=name,
            table=session,
        )
        pending = None

        if choice is MenuOption.QUIT:
            console.print("See you at the table.")
            return

        if choice is MenuOption.NAME:
            name = prompt_display_name(reader=reader, console=console, default=name)
            continue

        if choice is MenuOption.SETTINGS:
            session = edit_table_settings(reader=reader, console=console, table=session)
            console.print("[green]Settings saved.[/green]")
            continue

        if choice is MenuOption.NEW_GAME:
            console.print()
            console.print("[bold]New local game[/bold]")
            console.print("[dim]You against random bots. First to take every chip wins.[/dim]")
            session = _maybe_edit_table(reader=reader, console=console, table=session)
            winner = play(session, console=console, reader=reader, display_name=name)
            _announce_winner(console, winner)
            wait_for_menu(reader=reader)
            continue

        if choice is MenuOption.HOST:
            session = _maybe_edit_table(reader=reader, console=console, table=session)
            show_host_unavailable(console, session)
            wait_for_menu(reader=reader)
            continue

        ticket = prompt_join_ticket(reader=reader, console=console, ticket=join_ticket)
        join_ticket = None
        show_join_unavailable(console, ticket)
        wait_for_menu(reader=reader)


def _maybe_edit_table(
    *,
    reader: LineReader,
    console: Console,
    table: PlayConfig,
) -> PlayConfig:
    if prompt_change_settings(reader=reader, console=console, table=table):
        return edit_table_settings(reader=reader, console=console, table=table)
    return table


def _announce_winner(console: Console, winner: int | None) -> None:
    if winner is None:
        console.print("[yellow]You left the table.[/yellow]")
    elif winner == 0:
        console.print("[bold green]You won![/bold green]")
    else:
        console.print(f"[bold]Bot {winner} won.[/bold]")
