"""Lobby loop for local and online tables."""

from __future__ import annotations

from collections.abc import Callable

from rich.console import Console

from holdem.app.host import host_table
from holdem.app.join import join_table
from holdem.app.online import GuestResult, HostResult
from holdem.app.play import play_local
from holdem.connectors import IrohUnavailable
from holdem.ui.cli.interact import Cancelled
from holdem.ui.cli.lobby import (
    MenuOption,
    edit_table_settings,
    prompt_change_settings,
    prompt_display_name,
    prompt_join_ticket,
    prompt_local_difficulty,
    prompt_menu_option,
    show_intro,
    wait_for_menu,
)
from holdem.ui.cli.prompts import LineReader, PlayConfig

PlayFn = Callable[..., int | None]
HostFn = Callable[..., HostResult]
JoinFn = Callable[..., GuestResult | None]


def run_lobby(
    *,
    console: Console,
    reader: LineReader = input,
    table: PlayConfig | None = None,
    display_name: str | None = None,
    opening: MenuOption | None = None,
    join_ticket: str | None = None,
    play: PlayFn = play_local,
    host: HostFn = host_table,
    join: JoinFn = join_table,
) -> None:
    """Run the intro and main menu until the player quits."""

    session = table or PlayConfig()
    show_intro(console)
    try:
        name = display_name if display_name else prompt_display_name(reader=reader, console=console)
    except (Cancelled, KeyboardInterrupt):
        console.print("\nSee you at the table.")
        return
    pending = opening

    while True:
        try:
            choice = pending or prompt_menu_option(
                reader=reader,
                console=console,
                display_name=name,
                table=session,
            )
        except (Cancelled, KeyboardInterrupt):
            choice = MenuOption.QUIT
        pending = None

        if choice is MenuOption.QUIT:
            console.print("See you at the table.")
            return

        if choice is MenuOption.NAME:
            try:
                name = prompt_display_name(reader=reader, console=console, default=name)
            except (Cancelled, KeyboardInterrupt):
                pass
            continue

        if choice is MenuOption.SETTINGS:
            try:
                session = edit_table_settings(reader=reader, console=console, table=session)
            except (Cancelled, KeyboardInterrupt):
                continue
            console.print("[green]Settings saved.[/green]")
            continue

        if choice is MenuOption.NEW_GAME:
            console.print()
            console.print("[bold]New local game[/bold]")
            opponents = session.players - 1
            console.print(
                f"[dim]You against {opponents} {session.difficulty.value} bots. "
                "First to take every chip wins.[/dim]"
            )
            try:
                session = _maybe_edit_local_table(reader=reader, console=console, table=session)
            except (Cancelled, KeyboardInterrupt):
                continue
            try:
                winner = play(session, console=console, reader=reader, display_name=name)
            except (Cancelled, KeyboardInterrupt):
                console.print("[yellow]You left the table.[/yellow]")
                continue
            _announce_winner(console, winner)
            try:
                wait_for_menu(reader=reader)
            except (Cancelled, KeyboardInterrupt):
                pass
            continue

        if choice is MenuOption.HOST:
            try:
                session = _maybe_edit_table(reader=reader, console=console, table=session)
            except (Cancelled, KeyboardInterrupt):
                continue
            try:
                host_result = host(
                    session,
                    console=console,
                    reader=reader,
                    display_name=name,
                )
                _announce_host_winner(console, host_result)
            except (Cancelled, KeyboardInterrupt):
                console.print("[yellow]You left the table.[/yellow]")
                continue
            except (IrohUnavailable, ConnectionError) as exc:
                console.print(f"[bold red]Online session failed:[/bold red] {exc}")
            try:
                wait_for_menu(reader=reader)
            except (Cancelled, KeyboardInterrupt):
                pass
            continue

        try:
            ticket = prompt_join_ticket(reader=reader, console=console, ticket=join_ticket)
        except (Cancelled, KeyboardInterrupt):
            join_ticket = None
            continue
        join_ticket = None
        try:
            guest_result = join(
                ticket,
                console=console,
                reader=reader,
                display_name=name,
            )
            if guest_result is None:
                console.print("[yellow]You left the table.[/yellow]")
            else:
                _announce_guest_winner(console, guest_result)
        except (Cancelled, KeyboardInterrupt):
            console.print("[yellow]You left the table.[/yellow]")
            continue
        except (IrohUnavailable, ConnectionError, ValueError) as exc:
            console.print(f"[bold red]Online session failed:[/bold red] {exc}")
        try:
            wait_for_menu(reader=reader)
        except (Cancelled, KeyboardInterrupt):
            pass


def _maybe_edit_table(
    *,
    reader: LineReader,
    console: Console,
    table: PlayConfig,
) -> PlayConfig:
    if prompt_change_settings(reader=reader, console=console, table=table):
        return edit_table_settings(reader=reader, console=console, table=table)
    return table


def _maybe_edit_local_table(
    *,
    reader: LineReader,
    console: Console,
    table: PlayConfig,
) -> PlayConfig:
    if prompt_change_settings(reader=reader, console=console, table=table, local=True):
        return edit_table_settings(
            reader=reader,
            console=console,
            table=table,
            include_bots=False,
        )
    return prompt_local_difficulty(reader=reader, console=console, table=table)


def _announce_winner(console: Console, winner: int | None) -> None:
    if winner is None:
        console.print("[yellow]You left the table.[/yellow]")
    elif winner == 0:
        console.print("[bold green]You won![/bold green]")
    else:
        console.print(f"[bold]Bot {winner} won.[/bold]")


def _announce_host_winner(console: Console, result: HostResult) -> None:
    winner_name = result.names[result.winner]
    if result.winner == 0:
        console.print(f"[bold green]{winner_name} won![/bold green]")
    else:
        console.print(f"[bold]{winner_name} won.[/bold]")


def _announce_guest_winner(console: Console, result: GuestResult) -> None:
    winner_name = result.names[result.winner]
    if result.winner == result.local_seat:
        console.print(f"[bold green]{winner_name} won![/bold green]")
    else:
        console.print(f"[bold]{winner_name} won.[/bold]")
