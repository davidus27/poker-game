"""Iroh host composition root."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from rich.console import Console

from holdem.app.online import DEFAULT_ACTION_TIMEOUT, HostResult, play_host_session
from holdem.connectors import IrohConnector, PeerId
from holdem.protocol import Envelope, ErrorMessage, Hello
from holdem.ui.cli import PlayConfig, RichActionSource, RichView
from holdem.ui.cli.prompts import prompt_next_hand


def host_table(
    config: PlayConfig,
    *,
    display_name: str,
    console: Console,
    reader: Callable[[str], str] = input,
    action_timeout: float | None = DEFAULT_ACTION_TIMEOUT,
) -> HostResult:
    """Host an Iroh table until the tournament ends."""

    return asyncio.run(
        _host_table(
            config,
            display_name=display_name,
            console=console,
            reader=reader,
            action_timeout=action_timeout,
        )
    )


async def _host_table(
    config: PlayConfig,
    *,
    display_name: str,
    console: Console,
    reader: Callable[[str], str],
    action_timeout: float | None,
) -> HostResult:
    connector, ticket = await IrohConnector.host()
    try:
        console.print("[bold]Host a table[/bold]")
        console.print("Share this ticket with the other players:")
        console.print(f"[bold cyan]{ticket}[/bold cyan]")
        console.print(f"Waiting for {config.players - 1} player(s)…")
        guests: dict[PeerId, tuple[int, str]] = {}
        for seat in range(1, config.players):
            peer = await connector.accept_peer()
            sender, envelope = await connector.recv()
            if sender != peer or not isinstance(envelope.payload, Hello):
                await connector.send(peer, Envelope(ErrorMessage("A hello message was expected.")))
                raise ConnectionError("guest did not complete the hello handshake")
            guests[peer] = (seat, envelope.payload.name)
            console.print(
                f"[green]{envelope.payload.name} joined as seat {seat} "
                f"({len(guests)}/{config.players - 1}).[/green]"
            )
        seat_names = {0: display_name}
        seat_names.update({seat: name for seat, name in guests.values()})
        winner = await play_host_session(
            config,
            connector,
            guests,
            host_name=display_name,
            source=RichActionSource(console=console, reader=reader),
            renderer=RichView(
                console=console,
                display_name=display_name,
                seat_names=seat_names,
            ),
            action_timeout=action_timeout,
            on_continue=lambda: prompt_next_hand(reader=reader),
        )
        names = tuple(seat_names[seat] for seat in range(config.players))
        return HostResult(winner=winner, names=names)
    finally:
        await connector.close()
