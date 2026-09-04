"""Every street including the river is actually played."""

from __future__ import annotations

from holdem.domain.actions import Action
from holdem.domain.events import StreetDealt
from holdem.domain.views import Street
from holdem.engine.table import Table
from tests.engine.helpers import build_deck, play_script


def test_flop_turn_river_are_dealt_in_order() -> None:
    cards = build_deck(
        2,
        button=0,
        holes={0: "As Kd", 1: "7c 3h"},
        board="2s 8d 9c Th Jd",
    )
    table = Table(stacks=[100, 100], small_blind=5, big_blind=10)
    events = play_script(
        table,
        {
            0: [Action.call(), Action.check(), Action.check(), Action.check()],
            1: [Action.check(), Action.check(), Action.check(), Action.check()],
        },
        cards=cards,
    )
    dealt = [e for e in events if isinstance(e, StreetDealt)]
    assert [e.street for e in dealt] == [Street.FLOP, Street.TURN, Street.RIVER]
    assert len(dealt[0].cards) == 3
    assert len(dealt[1].cards) == 1
    assert len(dealt[2].cards) == 1
    assert table.board == tuple(cards[4:9])  # 2 holes × 2 seats, then the board


def test_river_betting_happens() -> None:
    table = Table(stacks=[200, 200], small_blind=5, big_blind=10)
    table.start_hand()
    table.apply(Action.call())
    table.apply(Action.check())
    table.apply(Action.check())
    table.apply(Action.check())
    table.apply(Action.check())
    table.apply(Action.check())
    assert table.street == Street.RIVER
    assert table.to_act is not None
    table.apply(Action.raise_to(20))
    assert table.street == Street.RIVER
    assert table.to_act is not None
    table.apply(Action.fold())
    assert table.is_hand_over


def test_all_in_does_not_skip_remaining_actors() -> None:
    """A short all-in does not dump the board; the other player must still act."""
    table = Table(stacks=[200, 15, 200], small_blind=5, big_blind=10)
    table.start_hand()
    # seat 0 UTG raises all-in? seat 1 is SB with 15, already posted 5, has 10 behind
    table.apply(Action.raise_to(40))
    assert table.to_act == 1
    table.apply(Action.all_in())
    # seat 2 still to act — board must not have been dumped
    assert table.street == Street.PREFLOP
    assert table.to_act == 2
    assert table.board == ()
