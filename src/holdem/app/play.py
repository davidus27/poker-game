"""Composition root for a local human-versus-bots game."""

from __future__ import annotations

import random
import time
from collections.abc import Callable

from rich.console import Console

from holdem.actors import Actor, LocalHuman, RandomBot
from holdem.domain.views import SeatStatus
from holdem.engine import Table
from holdem.ui.cli import PlayConfig, RichActionSource, RichView
from holdem.ui.cli.prompts import prompt_bust_choice

Pause = Callable[[float], None]
BustChoice = Callable[[], bool]

BOT_THINK_MIN = 0.45
BOT_THINK_MAX = 1.6
BOT_REVEAL_PAUSE = 0.7


def play_local(
    config: PlayConfig,
    *,
    console: Console | None = None,
    reader: Callable[[str], str] = input,
    display_name: str = "You",
    pause: Pause | None = None,
    on_bust: BustChoice | None = None,
) -> int | None:
    """Run a tournament. Return the winning seat, or None if the human left after busting."""

    output = console or Console()
    wait = pause if pause is not None else time.sleep
    random_source = random.Random(config.seed)
    think_rng = random.Random(random_source.getrandbits(64))
    table = Table(
        [config.starting_stack] * config.players,
        small_blind=config.small_blind,
        big_blind=config.big_blind,
        rng=random.Random(random_source.getrandbits(64)),
    )
    actors: dict[int, Actor] = {
        0: LocalHuman(RichActionSource(console=output, reader=reader)),
    }
    actors.update(
        {
            seat: RandomBot(random.Random(random_source.getrandbits(64)))
            for seat in range(1, config.players)
        }
    )
    renderer = RichView(console=output, display_name=display_name)
    human_seat = 0
    spectating = False

    events = table.start_hand()
    renderer.render(events, table.seat_view(human_seat))

    while not table.is_tournament_over:
        while table.to_act is not None:
            seat_id = table.to_act
            if seat_id != human_seat:
                renderer.render(
                    [],
                    table.seat_view(human_seat),
                    thinking_seat=seat_id,
                    spectating=spectating,
                )
                wait(think_rng.uniform(BOT_THINK_MIN, BOT_THINK_MAX))
            action = actors[seat_id].decide(table.seat_view(seat_id))
            events = table.apply(action)
            renderer.render(events, table.seat_view(human_seat), spectating=spectating)
            if seat_id != human_seat:
                wait(BOT_REVEAL_PAUSE)
        if table.is_tournament_over:
            break
        if _is_busted(table, human_seat) and not spectating:
            spectating = _ask_spectate(output, reader, on_bust)
            if not spectating:
                return None
        events = table.start_hand()
        renderer.render(events, table.seat_view(human_seat), spectating=spectating)

    stacks = table.stacks_now()
    return max(range(len(stacks)), key=stacks.__getitem__)


def _is_busted(table: Table, seat_id: int) -> bool:
    view = table.seat_view(seat_id)
    seat = next(seat for seat in view.seats if seat.seat_id == seat_id)
    return seat.status is SeatStatus.BUSTED


def _ask_spectate(
    console: Console,
    reader: Callable[[str], str],
    on_bust: BustChoice | None,
) -> bool:
    watch = (
        on_bust()
        if on_bust is not None
        else prompt_bust_choice(reader=reader, console=console) == "spectate"
    )
    if watch:
        console.print("[dim]Spectating the rest of the table.[/dim]")
    return watch
