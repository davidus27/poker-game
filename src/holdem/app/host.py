"""Iroh host composition root."""

from __future__ import annotations

import asyncio
import importlib
import os
import random
import select
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from rich.console import Console

from holdem.actors import Actor, make_bot
from holdem.app.online import DEFAULT_ACTION_TIMEOUT, HostResult, play_host_session
from holdem.connectors import IrohConnector, PeerId
from holdem.protocol import Envelope, ErrorMessage, Hello
from holdem.ui.cli import PlayConfig, RichActionSource, RichView
from holdem.ui.cli.prompts import prompt_next_hand

AcceptGuest = Callable[[], Awaitable[tuple[PeerId, str]]]
GuestJoined = Callable[[PeerId, int, str, int, int], None]


async def collect_guests(
    needed: int,
    accept_one: AcceptGuest,
    start: asyncio.Event,
    on_join: GuestJoined | None = None,
) -> dict[PeerId, tuple[int, str]]:
    """Collect guests in seat order until full or an early-start signal arrives."""

    if needed < 0:
        raise ValueError("needed guest count cannot be negative")

    guests: dict[PeerId, tuple[int, str]] = {}
    while len(guests) < needed and not start.is_set():
        accept_task = asyncio.ensure_future(accept_one())
        start_task = asyncio.create_task(start.wait())
        try:
            done, _pending = await asyncio.wait(
                {accept_task, start_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if accept_task in done:
                peer, name = accept_task.result()
                seat = len(guests) + 1
                guests[peer] = (seat, name)
                if on_join is not None:
                    on_join(peer, seat, name, len(guests), needed)
            start_only = start_task in done and accept_task not in done
        finally:
            for task in (accept_task, start_task):
                if not task.done():
                    task.cancel()
            await asyncio.gather(accept_task, start_task, return_exceptions=True)
        if start_only:
            break
    return guests


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
        console.print(
            f"Waiting for {config.guest_slots} player(s). "
            f"{config.bots} {config.difficulty.value} bot(s) will sit the rest."
        )

        async def accept_one() -> tuple[PeerId, str]:
            peer = await connector.accept_peer()
            sender, envelope = await connector.recv()
            if sender != peer or not isinstance(envelope.payload, Hello):
                await connector.send(peer, Envelope(ErrorMessage("A hello message was expected.")))
                raise ConnectionError("guest did not complete the hello handshake")
            return peer, envelope.payload.name

        def on_join(
            _peer: PeerId,
            seat: int,
            name: str,
            joined: int,
            needed: int,
        ) -> None:
            console.print(f"[green]{name} joined as seat {seat} ({joined}/{needed}).[/green]")

        start = asyncio.Event()
        start_watcher: asyncio.Task[None] | None = None
        if config.guest_slots:
            console.print("Press Enter to start now and fill empty seats with bots.")
            start_watcher = asyncio.create_task(_watch_for_start(start))
        try:
            guests = await collect_guests(config.guest_slots, accept_one, start, on_join)
        finally:
            if start_watcher is not None:
                start_watcher.cancel()
                await asyncio.gather(start_watcher, return_exceptions=True)

        random_source = random.Random(config.seed)
        guest_seats = {seat for seat, _name in guests.values()}
        bots: dict[int, Actor] = {
            seat: make_bot(
                config.difficulty,
                random.Random(random_source.getrandbits(64)),
            )
            for seat in range(1, config.players)
            if seat not in guest_seats
        }
        seat_names = {0: display_name}
        seat_names.update({seat: name for seat, name in guests.values()})
        seat_names.update({seat: f"Bot {seat}" for seat in bots})
        winner = await play_host_session(
            config,
            connector,
            guests,
            bots=bots,
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


async def _watch_for_start(start: asyncio.Event) -> None:
    """Consume one input line and signal an early table start."""

    if os.name == "nt":
        keyboard: Any = importlib.import_module("msvcrt")

        while not start.is_set():
            if keyboard.kbhit():
                while keyboard.getwch() not in {"\r", "\n"}:
                    pass
                start.set()
                return
            await asyncio.sleep(0.05)
        return

    while not start.is_set():
        readable, _, _ = select.select([sys.stdin], [], [], 0)
        if readable:
            if sys.stdin.readline() != "":
                start.set()
                return
        await asyncio.sleep(0.05)
