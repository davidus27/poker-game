"""Test helpers: scripted actors and predetermined decks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from holdem.actors import ScriptedActor
from holdem.domain.actions import Action
from holdem.domain.cards import Card, parse_card, parse_cards
from holdem.domain.events import Event
from holdem.engine.deck import standard_deck
from holdem.engine.table import Table


def clockwise_from(n_seats: int, after: int) -> list[int]:
    return [(after + 1 + i) % n_seats for i in range(n_seats)]


def build_deck(
    n_seats: int,
    button: int,
    holes: Mapping[int, tuple[str, str] | str],
    board: str = "",
    *,
    live: Sequence[int] | None = None,
) -> list[Card]:
    """Assemble a deck that deals the given holes (left of button first) then the board."""
    sitting = list(live) if live is not None else list(range(n_seats))
    deal_order = [seat for seat in clockwise_from(n_seats, button) if seat in sitting]

    parsed: dict[int, tuple[Card, Card]] = {}
    for seat, hole in holes.items():
        if isinstance(hole, str):
            cards = parse_cards(hole)
        else:
            cards = (parse_card(hole[0]), parse_card(hole[1]))
        if len(cards) != 2:
            raise ValueError(f"hole for seat {seat} must be two cards")
        parsed[seat] = (cards[0], cards[1])

    ordered: list[Card] = []
    for round_index in range(2):
        for seat in deal_order:
            ordered.append(parsed[seat][round_index])
    ordered.extend(parse_cards(board))

    used = set(ordered)
    unused = [card for card in standard_deck() if card not in used]
    return ordered + unused


def play_script(
    table: Table,
    scripts: Mapping[int, Sequence[Action]],
    *,
    cards: Sequence[Card] | None = None,
    start: bool = True,
) -> list[Event]:
    """Start a hand (optional) and apply scripted actions until the hand ends."""
    actors = {seat: ScriptedActor(actions) for seat, actions in scripts.items()}
    events: list[Event] = []
    if start:
        events.extend(table.start_hand(cards=cards))
    while table.to_act is not None:
        seat = table.to_act
        if seat not in actors:
            raise AssertionError(f"no script for seat {seat}")
        view = table.seat_view(seat)
        events.extend(table.apply(actors[seat].decide(view)))
    return events
