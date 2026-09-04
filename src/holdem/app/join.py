"""Iroh guest composition root."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from rich.console import Console

from holdem.app.online import GuestResult, play_guest_session
from holdem.connectors import IrohConnector
from holdem.protocol import Envelope, Hello
from holdem.ui.cli import RichActionSource, RichView


def join_table(
    ticket: str,
    *,
    display_name: str,
    console: Console,
    reader: Callable[[str], str] = input,
) -> GuestResult:
    """Join an Iroh table and play until the tournament ends."""

    return asyncio.run(
        _join_table(
            ticket,
            display_name=display_name,
            console=console,
            reader=reader,
        )
    )


async def _join_table(
    ticket: str,
    *,
    display_name: str,
    console: Console,
    reader: Callable[[str], str],
) -> GuestResult:
    connector, host = await IrohConnector.join(ticket)
    try:
        await connector.send(host, Envelope(Hello(display_name)))
        console.print("[green]Connected. Waiting for the host to start…[/green]")
        return await play_guest_session(
            connector,
            host,
            source=RichActionSource(console=console, reader=reader),
            renderer_factory=lambda name, names: RichView(
                console=console,
                display_name=name,
                seat_names=names,
            ),
        )
    finally:
        await connector.close()
