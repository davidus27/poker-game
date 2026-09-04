"""Blinds, button, heads-up posting, rotation, short-stack blinds."""

from __future__ import annotations

from holdem.domain.actions import Action
from holdem.domain.events import BlindKind, BlindPosted, HandStarted
from holdem.domain.views import SeatStatus, Street
from holdem.engine.table import Table
from tests.engine.helpers import play_script


def _blinds(events: list[object]) -> list[BlindPosted]:
    return [e for e in events if isinstance(e, BlindPosted)]


def test_three_handed_blinds_and_first_to_act() -> None:
    table = Table(stacks=[200, 200, 200], small_blind=5, big_blind=10)
    events = table.start_hand()
    started = next(e for e in events if isinstance(e, HandStarted))
    assert started.button == 0
    blinds = _blinds(events)
    assert [(b.seat_id, b.kind, b.amount) for b in blinds] == [
        (1, BlindKind.SMALL, 5),
        (2, BlindKind.BIG, 10),
    ]
    assert table.to_act == 0  # button / UTG acts first preflop
    assert table.street == Street.PREFLOP
    view = table.seat_view(0)
    assert view.seats[1].street_bet == 5
    assert view.seats[2].street_bet == 10
    assert view.pot_total == 15


def test_heads_up_button_posts_small_blind_and_acts_first() -> None:
    table = Table(stacks=[100, 100], small_blind=5, big_blind=10)
    table.start_hand()
    assert table.button == 0
    view = table.seat_view(0)
    assert view.seats[0].street_bet == 5
    assert view.seats[1].street_bet == 10
    assert table.to_act == 0


def test_heads_up_postflop_big_blind_acts_first() -> None:
    table = Table(stacks=[100, 100], small_blind=5, big_blind=10)
    table.start_hand()
    table.apply(Action.call())
    table.apply(Action.check())
    assert table.street == Street.FLOP
    assert table.to_act == 1


def test_button_rotates_after_each_hand() -> None:
    table = Table(stacks=[200, 200, 200], small_blind=5, big_blind=10)
    play_script(
        table,
        {
            0: [Action.fold()],
            1: [Action.fold()],
        },
    )
    assert table.button == 0
    assert table.is_hand_over
    table.start_hand()
    assert table.button == 1
    view = table.seat_view(1)
    # button=1 → SB=2, BB=0
    assert view.seats[2].street_bet == 5
    assert view.seats[0].street_bet == 10
    assert table.to_act == 1


def test_short_stack_posts_all_in_blind() -> None:
    table = Table(stacks=[200, 3, 200], small_blind=5, big_blind=10)
    events = table.start_hand()
    sb = next(e for e in events if isinstance(e, BlindPosted) and e.kind is BlindKind.SMALL)
    assert sb.seat_id == 1
    assert sb.amount == 3
    assert sb.is_all_in
    assert table.seat_view(1).seats[1].status is SeatStatus.ALL_IN
    assert table.seat_view(1).seats[1].stack == 0


def test_button_skips_busted_seats() -> None:
    table = Table(stacks=[200, 0, 200], small_blind=5, big_blind=10)
    table.start_hand()
    assert table.button == 0
    # HU among seats 0 and 2: button 0 is SB, seat 2 is BB
    view = table.seat_view(0)
    assert view.seats[0].street_bet == 5
    assert view.seats[2].street_bet == 10
    assert view.seats[1].status is SeatStatus.BUSTED
